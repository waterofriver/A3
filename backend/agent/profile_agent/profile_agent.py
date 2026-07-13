# -*- coding: utf-8 -*-
"""
画像构建 Agent (Profile Agent)
==============================
负责从学生的自由对话文本中提取 6 维度学习画像。

设计原则：
- 无状态：调用方（Supervisor / UI）管理对话循环
- 每次调用返回 ProfileExtractionResult，包含画像、追问、完成状态
- 支持增量更新：可合并到已有 StudentProfile
- 同步和异步两套 API

用法示例::

    from profile_agent import ProfileAgent

    agent = ProfileAgent()
    profile = None  # 初始为空

    # 第一轮
    result = agent.extract("大家好，我是计算机大三的学生")
    profile = result.profile
    print(result.follow_up_question)  # "你目前熟悉哪些编程语言？"

    # 第二轮（增量更新）
    result = agent.extract("Python 比较熟，C++ 了解一些", existing_profile=profile)
    profile = result.profile
    if result.is_complete:
        print("画像收集完成！")
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..config import Config
from ..utils import LLMClient, LLMResponse, get_client
from ..utils.json_parser import extract_json
from ..models import (
    StudentProfile,
    KnowledgeBaseItem,
    WeakPoint,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════


@dataclass
class ProfileExtractionResult:
    """每次对话轮次返回的结果。

    调用方根据 is_complete 决定是否继续询问，根据 follow_up_question 展示追问。
    """

    profile: Optional[StudentProfile] = None
    """合并后的学生画像；LLM 调用失败时可能为 None"""

    follow_up_question: str = ""
    """下一轮追问问题；空字符串表示无需追问"""

    is_complete: bool = False
    """画像收集是否完成（所有关键维度已覆盖）"""

    rationale: str = ""
    """本次提取/改动了什么，用于日志和 UI 展示"""

    success: bool = True
    """LLM 调用和 JSON 解析是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""

    reasoning_content: Optional[str] = None
    """deepseek-reasoner 思维链，用于调试"""


# ═══════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """
你是一个学生画像构建助手。你的任务是从学生的自由对话文本中逐步提取信息，
构建一个 6 维度的学习画像。

## 核心原则
- 逐步提问：每次对话轮次只问 1-2 个问题，聚焦于尚未覆盖的维度
- 基于已知追问：如果已有部分信息，基于已知信息深入追问
- 使用友好的中文口语
- 从学生的自由文本中推断隐含信息（例如提到"刷题"暗示 practice_oriented）

## 6 维度说明

### 1. 基础信息
- major: 专业名称（如"计算机科学与技术"）
- grade: 年级（如"大三"）

### 2. 知识基础 (knowledge_base)
- 已知知识点列表，每项包含：
  - knowledge_point_id: 知识点唯一标识（英文小写+下划线，如 "python_basics"）
  - knowledge_point_name: 知识点中文名（如"Python 基础"）
  - mastery: 掌握程度，必须是以下之一：proficient（熟练）、familiar（熟悉）、exposed（了解）、unknown（未知）

### 3. 认知风格 (cognitive_style)
- 必须是以下之一：theory_oriented（偏理论）、practice_oriented（偏实践）、balanced（均衡）

### 4. 学习目标
- learning_goal_short: 短期目标（如"通过期末考试"）
- learning_goal_long: 长期目标（如"成为全栈工程师"）

### 5. 薄弱环节 (weak_points)
- 常错知识点列表，每项包含：
  - knowledge_point_id: 知识点标识
  - knowledge_point_name: 知识点名称
  - error_pattern: 错误模式描述（如"递归终止条件常写错"）
  - occurrence_count: 出现次数（整数）

### 6. 学习节奏与兴趣
- learning_pace: 必须是以下之一：intensive（密集突击）、distributed（分散学习）、flexible（灵活适应）
- interest_domains: 感兴趣的应用领域列表（如["游戏开发", "Web 后端"]）

## 输出格式

你必须严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块，不要输出任何其他文字。

```json
{
    "extracted_fields": {
        "major": "示例专业",
        "grade": "大三",
        "knowledge_base": [
            {"knowledge_point_id": "python_basics", "knowledge_point_name": "Python 基础", "mastery": "proficient"}
        ],
        "cognitive_style": "practice_oriented",
        "learning_goal_short": "通过期末考试",
        "learning_goal_long": "成为全栈工程师",
        "weak_points": [
            {"knowledge_point_id": "recursion", "knowledge_point_name": "递归", "error_pattern": "递归终止条件常写错", "occurrence_count": 3}
        ],
        "learning_pace": "distributed",
        "interest_domains": ["游戏开发", "Web 后端"]
    },
    "follow_up_question": "你能详细说说在递归上的具体困难吗？",
    "is_complete": false,
    "rationale": "已提取基础信息和知识背景，薄弱环节和学习节奏尚未明确，仍需进一步询问。"
}
```

## is_complete 判定标准
- 当至少 4 个维度有具体信息时，设为 true
- 当学生明确表示不想继续时，设为 true
- 否则设为 false，并通过 follow_up_question 询问缺失的维度

## 仅输出新信息的规则
- 如果 extracted_fields 中某个字段在本次输入中没有新信息，将该字段设为 null（JSON null）
- 例如：学生没说新知识点，knowledge_base 就是 null
- 但如果学生提到了新信息，就需要在 extracted_fields 中包含更新后的完整字段值
- follow_up_question 始终提供（除非 is_complete 为 true）

## 增量更新规则（当提供了"现有画像"时）
如果用户消息中包含"现有画像"部分，说明这不是第一轮对话。你需要：
1. 从新输入中提取任何新的或更新的信息
2. 在 extracted_fields 中给出完整的字段（已有的 + 新提取的），不是仅返回新增部分
3. 如果新信息与已有信息矛盾，以新信息为准
4. 在 rationale 中说明哪些字段被更新了
""".strip()


# ═══════════════════════════════════════════════════════════════
# ProfileAgent
# ═══════════════════════════════════════════════════════════════


class ProfileAgent:
    """无状态画像提取 Agent。

    调用方管理对话循环：

        result = agent.extract(user_text, existing_profile)
        if result.follow_up_question:
            # 向用户展示追问
            ...
        if result.is_complete:
            # 画像完成，进入下一阶段
            ...

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认 deepseek-reasoner 模型
        temperature: LLM 温度，默认 0.2（低温度保证 JSON 稳定性）
        max_tokens: 最大输出 token 数，默认 4096
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        self._client = client or get_client()
        self._model = model or Config.DEEPSEEK_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens

    # ── 公开 API ──────────────────────────────────────────

    def extract(
        self,
        user_text: str,
        existing_profile: Optional[StudentProfile] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> ProfileExtractionResult:
        """同步提取学生画像。

        参数:
            user_text: 学生当前轮次的自由文本
            existing_profile: 已有画像（增量更新场景）
            conversation_history: 多轮对话历史 [{"role": "user", "content": "..."}, ...]

        返回:
            ProfileExtractionResult: 包含合并后的画像和追问信息
        """
        return self._extract_impl(user_text, existing_profile, conversation_history)

    async def extract_async(
        self,
        user_text: str,
        existing_profile: Optional[StudentProfile] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> ProfileExtractionResult:
        """异步提取学生画像。签名与 extract 一致。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        return await self._extract_impl_async(
            client, user_text, existing_profile, conversation_history
        )

    # ── 内部实现 ──────────────────────────────────────────

    def _extract_impl(
        self,
        user_text: str,
        existing_profile: Optional[StudentProfile],
        conversation_history: Optional[list[dict]],
    ) -> ProfileExtractionResult:
        """同步提取的核心实现。"""

        # 0. 空输入校验
        if not user_text or not user_text.strip():
            return ProfileExtractionResult(
                success=False,
                error="输入文本为空",
                rationale="未收到有效输入",
            )

        # 1. 构建消息
        system_prompt = self._build_system_prompt(existing_profile)
        user_message = self._build_user_message(user_text, existing_profile)

        logger.info(
            f"ProfileAgent.extract | model={self._model} | "
            f"has_existing={existing_profile is not None} | "
            f"input_len={len(user_text)}"
        )

        # 2. 调用 LLM
        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            history=conversation_history,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        # 3. 处理响应
        return self._handle_response(response, existing_profile)

    async def _extract_impl_async(
        self,
        client,
        user_text: str,
        existing_profile: Optional[StudentProfile],
        conversation_history: Optional[list[dict]],
    ) -> ProfileExtractionResult:
        """异步提取的核心实现。"""

        if not user_text or not user_text.strip():
            return ProfileExtractionResult(
                success=False,
                error="输入文本为空",
                rationale="未收到有效输入",
            )

        system_prompt = self._build_system_prompt(existing_profile)
        user_message = self._build_user_message(user_text, existing_profile)

        logger.info(
            f"ProfileAgent.extract_async | model={self._model} | "
            f"has_existing={existing_profile is not None}"
        )

        response = await client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            history=conversation_history,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(response, existing_profile)

    def _handle_response(
        self,
        response: LLMResponse,
        existing_profile: Optional[StudentProfile],
    ) -> ProfileExtractionResult:
        """统一处理 LLM 响应：解析 JSON → 构建画像 → 合并 → 检查完成度。"""

        # LLM 调用失败
        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return ProfileExtractionResult(
                success=False,
                error=response.error or "LLM 调用失败",
                rationale="API 调用出错，请检查网络和 API Key",
            )

        # 解析 JSON
        parsed, json_error = extract_json(response.content)

        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return ProfileExtractionResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                rationale="LLM 输出格式异常，无法提取画像信息",
                reasoning_content=response.reasoning_content,
            )

        # 提取各个字段
        extracted_fields = parsed.get("extracted_fields", parsed)

        # 构建 StudentProfile
        try:
            new_profile = self._build_profile(extracted_fields)
        except Exception as e:
            logger.warning(f"构建 StudentProfile 失败: {e}")
            return ProfileExtractionResult(
                success=False,
                error=f"画像构建失败: {e}",
                rationale="提取的字段与模型定义不匹配",
                reasoning_content=response.reasoning_content,
            )

        # 合并
        if existing_profile is not None:
            final_profile = self._merge_profiles(existing_profile, new_profile)
        else:
            final_profile = new_profile

        # LLM 判定的 is_complete
        llm_is_complete = parsed.get("is_complete", False)

        # Agent 层兜底：维度不足时强制 false
        is_complete = self._check_completion_override(final_profile, llm_is_complete)

        follow_up = parsed.get("follow_up_question") or ""
        rationale = parsed.get("rationale") or ""

        logger.info(
            f"ProfileAgent 结果 | is_complete={is_complete} | "
            f"dimensions_filled={self._count_dimensions(final_profile)} | "
            f"follow_up_len={len(follow_up)}"
        )

        return ProfileExtractionResult(
            profile=final_profile,
            follow_up_question=follow_up if not is_complete else "",
            is_complete=is_complete,
            rationale=rationale,
            success=True,
            reasoning_content=response.reasoning_content,
        )

    # ── System Prompt 构建 ────────────────────────────────

    def _build_system_prompt(
        self,
        existing_profile: Optional[StudentProfile],
    ) -> str:
        """构建 System Prompt，包含增量更新指引。"""
        prompt = _SYSTEM_PROMPT

        if existing_profile is not None:
            snapshot = existing_profile.snapshot()
            if snapshot.strip():
                prompt += f"""

## 现有画像（请基于此做增量更新）

以下是已收集到的学生画像信息。你需要在 extracted_fields 中输出合并后的完整画像。
{snapshot}
"""

        return prompt

    # ── User Message 构建 ─────────────────────────────────

    def _build_user_message(
        self,
        user_text: str,
        existing_profile: Optional[StudentProfile],
    ) -> str:
        """构建发送给 LLM 的 user message。"""
        if existing_profile is not None:
            snapshot = existing_profile.snapshot()
            if snapshot.strip():
                return (
                    "以下是学生的已有画像信息和新的对话内容。"
                    "请基于新输入更新画像，在 extracted_fields 中给出合并后的完整画像。\n\n"
                    f"【已有画像】\n{snapshot}\n\n"
                    f"【新输入】\n{user_text}"
                )

        return user_text

    # ── 画像构建 ──────────────────────────────────────────

    def _build_profile(self, fields: dict) -> StudentProfile:
        """从 LLM 提取的字段字典构建 StudentProfile。

        使用 Pydantic model_validate，自动处理枚举值和默认值。
        对于不合法字段值，Pydantic 会抛出异常。
        """
        # 过滤掉纯 null 值（JSON 中的 null → Python None）
        cleaned = {}
        for k, v in fields.items():
            if v is not None:
                cleaned[k] = v

        # 处理 knowledge_base：将 dict 列表转为 KnowledgeBaseItem 列表
        if "knowledge_base" in cleaned and isinstance(cleaned["knowledge_base"], list):
            cleaned["knowledge_base"] = [
                KnowledgeBaseItem(**item) if isinstance(item, dict) else item
                for item in cleaned["knowledge_base"]
            ]

        # 处理 weak_points
        if "weak_points" in cleaned and isinstance(cleaned["weak_points"], list):
            cleaned["weak_points"] = [
                WeakPoint(**item) if isinstance(item, dict) else item
                for item in cleaned["weak_points"]
            ]

        return StudentProfile.model_validate(cleaned)

    # ── 增量合并 ──────────────────────────────────────────

    def _merge_profiles(
        self,
        existing: StudentProfile,
        extracted: StudentProfile,
    ) -> StudentProfile:
        """
        将 extracted 合并到 existing，以 extracted 的非默认值优先。

        规则:
        - 标量字段：extracted 有非默认值则覆盖
        - knowledge_base：按 knowledge_point_id 去重，extracted 覆盖
        - weak_points：按 knowledge_point_id 去重，occurrence_count 累加
        - interest_domains：字符串集合去重合并
        - updated_at 更新为当前时间
        """
        merged = existing.model_copy(deep=True)

        # ── 标量字段 ──
        if extracted.major:
            merged.major = extracted.major
        if extracted.grade:
            merged.grade = extracted.grade
        if extracted.cognitive_style != CognitiveStyle.BALANCED:
            merged.cognitive_style = extracted.cognitive_style
        if extracted.learning_goal_short:
            merged.learning_goal_short = extracted.learning_goal_short
        if extracted.learning_goal_long:
            merged.learning_goal_long = extracted.learning_goal_long
        if extracted.learning_pace != LearningPace.FLEXIBLE:
            merged.learning_pace = extracted.learning_pace

        # ── knowledge_base: 按 knowledge_point_id 去重合并 ──
        existing_kb_ids = {k.knowledge_point_id for k in merged.knowledge_base}
        for new_item in extracted.knowledge_base:
            if new_item.knowledge_point_id in existing_kb_ids:
                # 更新已有条目
                for i, existing_item in enumerate(merged.knowledge_base):
                    if existing_item.knowledge_point_id == new_item.knowledge_point_id:
                        merged.knowledge_base[i] = new_item
                        break
            else:
                merged.knowledge_base.append(new_item)

        # ── weak_points: 按 knowledge_point_id 去重，occurrence_count 累加 ──
        existing_wp_ids = {w.knowledge_point_id for w in merged.weak_points}
        for new_item in extracted.weak_points:
            if new_item.knowledge_point_id in existing_wp_ids:
                for i, existing_item in enumerate(merged.weak_points):
                    if existing_item.knowledge_point_id == new_item.knowledge_point_id:
                        # 更新错误模式（如有新描述），累加出现次数
                        if new_item.error_pattern:
                            existing_item.error_pattern = new_item.error_pattern
                        existing_item.occurrence_count += new_item.occurrence_count
                        break
            else:
                merged.weak_points.append(new_item)

        # ── interest_domains: 去重合并 ──
        existing_domains = set(merged.interest_domains)
        for domain in extracted.interest_domains:
            if domain not in existing_domains:
                merged.interest_domains.append(domain)

        # ── 时间戳 ──
        merged.updated_at = datetime.now()

        return merged

    # ── 完成度判定 ────────────────────────────────────────

    def _check_completion_override(
        self,
        profile: StudentProfile,
        llm_is_complete: bool,
    ) -> bool:
        """Agent 侧兜底：维度不足时强制覆盖为 false。"""
        if not llm_is_complete:
            return False

        dim_count = self._count_dimensions(profile)
        # 至少需要 2 个维度才算有意义
        if dim_count < 2:
            logger.info(f"完成度覆盖: LLM 判定完成但仅 {dim_count} 个维度有效 → 强制 incomplete")
            return False

        return True

    @staticmethod
    def _count_dimensions(profile: StudentProfile) -> int:
        """统计有多少个维度包含有效数据（非默认值）。"""
        count = 0

        # 维度 1: 基础信息
        if profile.major or profile.grade:
            count += 1

        # 维度 2: 知识基础
        if profile.knowledge_base:
            count += 1

        # 维度 3: 认知风格
        if profile.cognitive_style != CognitiveStyle.BALANCED:
            count += 1

        # 维度 4: 学习目标
        if profile.learning_goal_short or profile.learning_goal_long:
            count += 1

        # 维度 5: 薄弱环节
        if profile.weak_points:
            count += 1

        # 维度 6: 学习节奏与兴趣
        if profile.learning_pace != LearningPace.FLEXIBLE or profile.interest_domains:
            count += 1

        return count
