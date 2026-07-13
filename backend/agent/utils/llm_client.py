"""
DeepSeek API 统一封装层
=======================
提供同步/异步调用、流式输出、自动重试、统一返回格式。
所有 Agent 和工作流都通过此模块调用 DeepSeek，不直接使用 openai SDK。

特性：
- 同步 & 异步双模式
- 流式输出支持（同步生成器 + 异步生成器）
- 指数退避自动重试（网络抖动、限流自动恢复）
- 统一返回结构（含 reasoning_content 适配 deepseek-reasoner）
- 自动注入 system prompt 格式转换
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Generator, AsyncGenerator, Optional, Any

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..config import Config

# ── 日志 ──
logger = logging.getLogger("llm_client")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(name)s] %(levelname)s - %(message)s"))
    logger.addHandler(h)


# ═══════════════════════════════════════════════════════════════
# 统一返回结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class LLMResponse:
    """所有 LLM 调用的统一返回格式"""
    content: str                              # 模型最终回复文本
    reasoning_content: Optional[str] = None   # deepseek-reasoner 的推理链（思维过程）
    model: str = ""                           # 实际使用的模型名
    finish_reason: str = "stop"               # 结束原因: stop / length / content_filter
    usage: dict = field(default_factory=dict) # token 用量: {prompt_tokens, completion_tokens, total_tokens}
    success: bool = True                      # 调用是否成功
    error: Optional[str] = None               # 失败时的错误信息


# ═══════════════════════════════════════════════════════════════
# 内部工具
# ═══════════════════════════════════════════════════════════════

def _build_messages(
    system_prompt: Optional[str],
    user_message: str,
    history: Optional[list[dict]] = None,
) -> list[dict]:
    """
    构建标准的 messages 列表。
    - 如果提供 system_prompt，插入为 system 角色
    - history 是已有的对话记录 [{"role": "user", "content": "..."}, ...]
    - 最后追加当前 user_message
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


def _parse_response(completion: ChatCompletion) -> LLMResponse:
    """将 OpenAI SDK 返回的 ChatCompletion 解析为统一的 LLMResponse"""
    choice = completion.choices[0]
    message = choice.message

    # 提取 reasoning_content（deepseek-reasoner 特有字段）
    reasoning = getattr(message, "reasoning_content", None)

    # 提取 usage
    usage = {}
    if completion.usage:
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

    return LLMResponse(
        content=message.content or "",
        reasoning_content=reasoning,
        model=completion.model,
        finish_reason=choice.finish_reason or "stop",
        usage=usage,
    )


def _should_retry(error: Exception, attempt: int, max_retries: int) -> bool:
    """判断是否应该重试。网络错误和限流错误可重试，认证错误不重试。"""
    if attempt >= max_retries:
        return False

    error_str = str(error).lower()
    # 可重试的错误类型
    retryable = [
        "timeout", "timed out", "connection", "connect error",
        "rate limit", "too many requests", "429",
        "server error", "500", "502", "503",
        "overloaded", "service unavailable",
    ]
    # 不可重试的错误
    non_retryable = [
        "401", "403", "invalid api key", "authentication",
        "insufficient_quota",
    ]

    for keyword in non_retryable:
        if keyword in error_str:
            return False

    for keyword in retryable:
        if keyword in error_str:
            return True

    # 默认不重试未知错误
    return False


def _retry_sleep(attempt: int) -> float:
    """指数退避：第1次等1秒，第2次等2秒，第3次等4秒"""
    wait = 2 ** (attempt - 1)
    time.sleep(wait)
    return wait


# ═══════════════════════════════════════════════════════════════
# 同步客户端
# ═══════════════════════════════════════════════════════════════

class LLMClient:
    """
    同步 LLM 客户端，封装 DeepSeek API。

    用法:
        client = LLMClient()
        resp = client.chat("你好，请介绍一下你自己")
        print(resp.content)

        # 指定 system prompt
        resp = client.chat("什么是二叉树", system_prompt="你是一个数据结构老师")

        # 流式输出
        for chunk, reasoning in client.chat_stream("讲一个故事"):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.base_url = base_url or Config.DEEPSEEK_BASE_URL
        self.model = model or Config.DEEPSEEK_MODEL
        self.timeout = timeout or Config.DEEPSEEK_TIMEOUT
        self.max_retries = max_retries or Config.DEEPSEEK_MAX_RETRIES

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    # ── 非流式调用 ──────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        同步非流式调用。

        参数:
            user_message: 用户消息
            system_prompt: 系统提示词
            history: 多轮对话历史
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大输出 token 数
            **kwargs: 传递给 API 的其他参数

        返回:
            LLMResponse: 统一响应结构
        """
        messages = _build_messages(system_prompt, user_message, history)

        api_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        api_kwargs.update(kwargs)

        last_error = None
        for attempt in range(1, self.max_retries + 2):  # 1 次正常 + max_retries 次重试
            try:
                logger.info(f"调用 DeepSeek (同步) | model={self.model} | attempt={attempt}/{self.max_retries + 1}")
                completion = self._client.chat.completions.create(**api_kwargs)
                logger.info(f"调用成功 | tokens={completion.usage.total_tokens if completion.usage else 'N/A'}")
                return _parse_response(completion)

            except Exception as e:
                last_error = e
                logger.warning(f"调用失败 (attempt={attempt}): {e}")

                if not _should_retry(e, attempt, self.max_retries):
                    break
                waited = _retry_sleep(attempt)
                logger.info(f"重试等待 {waited}s...")

        # 所有重试都失败
        logger.error(f"所有重试已耗尽: {last_error}")
        return LLMResponse(
            content="",
            success=False,
            error=str(last_error),
            model=self.model,
        )

    # ── 流式调用 ────────────────────────────────────────────

    def chat_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Generator[tuple[str, Optional[str]], None, None]:
        """
        同步流式调用，逐步产出内容。

        每次 yield 一个元组:
            (增量文本, 增量推理内容)

        用法:
            for text, reasoning in client.chat_stream("你好"):
                print(text, end="", flush=True)
        """
        messages = _build_messages(system_prompt, user_message, history)

        api_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        api_kwargs.update(kwargs)

        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                logger.info(f"调用 DeepSeek (同步流式) | model={self.model} | attempt={attempt}")
                stream = self._client.chat.completions.create(**api_kwargs)

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    text = delta.content or ""
                    reasoning = getattr(delta, "reasoning_content", None)
                    if text or reasoning:
                        yield (text, reasoning)

                return  # 流式完成

            except Exception as e:
                last_error = e
                logger.warning(f"流式调用失败 (attempt={attempt}): {e}")

                if not _should_retry(e, attempt, self.max_retries):
                    break
                waited = _retry_sleep(attempt)
                logger.info(f"重试等待 {waited}s...")

        # 所有重试都失败，yield 错误信息
        logger.error(f"流式调用所有重试已耗尽: {last_error}")
        yield (f"[ERROR] {last_error}", None)


# ═══════════════════════════════════════════════════════════════
# 异步客户端
# ═══════════════════════════════════════════════════════════════

class AsyncLLMClient:
    """
    异步 LLM 客户端，封装 DeepSeek API。
    用于 Supervisor 中并行调用多个 Agent 的场景。

    用法:
        client = AsyncLLMClient()
        resp = await client.chat("你好")
        print(resp.content)

        # 并行调用多个 Agent
        import asyncio
        tasks = [
            client.chat("生成讲义", system_prompt=doc_prompt),
            client.chat("生成思维导图", system_prompt=mindmap_prompt),
            client.chat("生成题库", system_prompt=quiz_prompt),
        ]
        results = await asyncio.gather(*tasks)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.base_url = base_url or Config.DEEPSEEK_BASE_URL
        self.model = model or Config.DEEPSEEK_MODEL
        self.timeout = timeout or Config.DEEPSEEK_TIMEOUT
        self.max_retries = max_retries or Config.DEEPSEEK_MAX_RETRIES

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    # ── 非流式调用 ──────────────────────────────────────────

    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """异步非流式调用，参数与同步版一致"""
        messages = _build_messages(system_prompt, user_message, history)

        api_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        api_kwargs.update(kwargs)

        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                logger.info(f"调用 DeepSeek (异步) | model={self.model} | attempt={attempt}")
                completion = await self._client.chat.completions.create(**api_kwargs)
                logger.info(f"调用成功 | tokens={completion.usage.total_tokens if completion.usage else 'N/A'}")
                return _parse_response(completion)

            except Exception as e:
                last_error = e
                logger.warning(f"异步调用失败 (attempt={attempt}): {e}")

                if not _should_retry(e, attempt, self.max_retries):
                    break
                waited = _retry_sleep(attempt)
                logger.info(f"重试等待 {waited}s...")

        logger.error(f"异步调用所有重试已耗尽: {last_error}")
        return LLMResponse(
            content="",
            success=False,
            error=str(last_error),
            model=self.model,
        )

    # ── 流式调用 ────────────────────────────────────────────

    async def chat_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[tuple[str, Optional[str]], None]:
        """异步流式调用，逐步产出 (增量文本, 增量推理内容)"""
        messages = _build_messages(system_prompt, user_message, history)

        api_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            api_kwargs["max_tokens"] = max_tokens
        api_kwargs.update(kwargs)

        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                logger.info(f"调用 DeepSeek (异步流式) | model={self.model} | attempt={attempt}")
                stream = await self._client.chat.completions.create(**api_kwargs)

                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    text = delta.content or ""
                    reasoning = getattr(delta, "reasoning_content", None)
                    if text or reasoning:
                        yield (text, reasoning)

                return  # 流式完成

            except Exception as e:
                last_error = e
                logger.warning(f"异步流式调用失败 (attempt={attempt}): {e}")

                if not _should_retry(e, attempt, self.max_retries):
                    break
                waited = _retry_sleep(attempt)
                logger.info(f"重试等待 {waited}s...")

        logger.error(f"异步流式调用所有重试已耗尽: {last_error}")
        yield (f"[ERROR] {last_error}", None)


# ═══════════════════════════════════════════════════════════════
# 便捷工厂函数
# ═══════════════════════════════════════════════════════════════

# 全局单例（懒加载）
_sync_client: Optional[LLMClient] = None
_async_client: Optional[AsyncLLMClient] = None


def get_client() -> LLMClient:
    """获取同步客户端单例"""
    global _sync_client
    if _sync_client is None:
        _sync_client = LLMClient()
    return _sync_client


def get_async_client() -> AsyncLLMClient:
    """获取异步客户端单例"""
    global _async_client
    if _async_client is None:
        _async_client = AsyncLLMClient()
    return _async_client
