# -*- coding: utf-8 -*-
"""
会话调度 Agent (Supervisor)
===========================
负责意图分类、Agent 分发和 SessionState 管理。

设计原则：
- 无状态方法 + SessionState：每次 handle() 接收完整 state，返回更新后的 state
- LLM 分类意图 → dispatching → 状态更新 → 返回用户回复
- 支持同步和异步两套 API

用法示例::

    from supervisor import Supervisor

    sup = Supervisor()
    session = SessionState(session_id="test-001")

    result = sup.handle("大家好，我是计算机大三的学生", session)
    print(result.reply)   # Agent 的追问或回复
    session = result.session  # 更新后的状态
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..config import Config
from ..utils import LLMClient, LLMResponse, get_client
from ..utils.json_parser import extract_json
from ..models import (
    StudentProfile,
    KnowledgeDAG,
    LearningPath,
    SessionState,
    TaskIntent,
    Task,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════


@dataclass
class SupervisorResult:
    """每次 handle() 调用返回的结果。"""

    reply: str = ""
    """给用户的文本回复"""

    session: Optional[SessionState] = None
    """更新后的会话状态"""

    intent: Optional[TaskIntent] = None
    """分类后的意图"""

    success: bool = True
    """处理是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""


# ═══════════════════════════════════════════════════════════════
# System Prompts
# ═══════════════════════════════════════════════════════════════

_INTENT_PROMPT = """
你是一个会话意图分类器。根据用户输入和当前会话状态，判断用户的意图。

## 意图类型

- **extract_profile**: 用户在介绍自己、回答画像问题、提供学习背景或个人学习偏好信息。首次对话默认为此意图。
- **plan_path**: 用户请求生成或调整学习路径、询问"接下来学什么"、"帮我规划学习"。
- **answer_question**: 用户提问知识问题、请求解释概念或原理。已有画像和路径时，这类问题更常见。
- **chitchat**: 闲聊、问候、感谢、无明确学习意图的社交对话。
- **generate_resource**: 用户请求生成具体学习资料（如"帮我出一份题"、"写一份讲义"）。
- **evaluate**: 用户请求评估学习效果、进行自测或检查学习进度。

## 判定优先级

1. 如果用户明确说"生成"、"出题"、"写讲义" → generate_resource
2. 如果用户在介绍自己或回答关于学习的个人问题 → extract_profile
3. 如果用户问"学什么"、"规划"、"路径" → plan_path
4. 如果用户提问知识概念、请求解释 → answer_question
5. 如果只是打招呼、感谢、闲聊 → chitchat

## 当前会话状态

{state_summary}

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块。

```json
{{
    "intent": "extract_profile",
    "confidence": 0.95,
    "rationale": "用户在描述自己的学习背景"
}}
```
""".strip()

_CHITCHAT_PROMPT = """
你是一个友好的学习助手。请用中文简短回复用户的闲聊消息。
保持温暖、鼓励的语气，并在适当的时候引导用户聊聊学习相关话题。
回复控制在 2-3 句话以内。
""".strip()

_ANSWER_PROMPT = """
你是一个知识渊博的学习导师。请用中文回答学生的问题。

要求：
- 解释清晰易懂，适合学生当前水平
- 适当举例说明
- 如果问题超出你的知识范围，诚实说明
- 回复长度适中，不要过于冗长
""".strip()


# ═══════════════════════════════════════════════════════════════
# Supervisor
# ═══════════════════════════════════════════════════════════════


class Supervisor:
    """会话调度 Agent。

    负责：意图分类 → Agent 分发 → SessionState 更新。

    用法::

        sup = Supervisor()
        session = SessionState(session_id="test-001")

        result = sup.handle("大家好，我是计算机大三的学生", session)
        print(result.reply)
        session = result.session
        # 继续下一轮对话...
        result = sup.handle("Python 比较熟", result.session)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认 deepseek-reasoner 模型
        temperature: LLM 温度，默认 0.2
        max_tokens: 最大输出 token 数，默认 4096
        dag_path: knowledge_dag.json 的路径，用于 Planner 自动加载
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        dag_path: Optional[str] = None,
    ):
        self._client = client or get_client()
        self._model = model or Config.DEEPSEEK_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._dag_path = dag_path

        # 延迟初始化子 Agent
        self._profile_agent = None
        self._planner_agent = None

    # ── 公开 API ──────────────────────────────────────────

    def handle(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """同步处理用户输入。

        参数:
            user_text: 用户当前轮次的输入文本
            session: 当前会话状态

        返回:
            SupervisorResult: 包含回复文本和更新后的会话状态
        """
        return self._handle_impl(user_text, session)

    async def handle_async(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """异步处理用户输入。签名与 handle 一致。"""
        return await self._handle_impl_async(user_text, session)

    # ── 意图分类 ──────────────────────────────────────────

    def classify_intent(
        self,
        user_text: str,
        session: SessionState,
    ) -> tuple[TaskIntent, float, str]:
        """分类用户意图。

        参数:
            user_text: 用户输入文本
            session: 当前会话状态

        返回:
            (intent, confidence, rationale) 三元组
        """
        state_summary = self._build_state_summary(session)
        system_prompt = _INTENT_PROMPT.format(state_summary=state_summary)

        response = self._client.chat(
            user_message=user_text,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=512,
            model=self._model,
        )

        if not response.success:
            logger.warning(f"意图分类 LLM 调用失败: {response.error}")
            # 兜底：首次对话 → 画像；已有画像无路径 → 路径；否则 → 闲聊
            if session.student_profile is None:
                return TaskIntent.EXTRACT_PROFILE, 0.5, "LLM 失败兜底：无画像，默认画像收集"
            elif session.current_learning_path is None:
                return TaskIntent.PLAN_PATH, 0.5, "LLM 失败兜底：有画像无路径，默认规划"
            else:
                return TaskIntent.CHITCHAT, 0.3, "LLM 失败兜底：默认闲聊"

        parsed, _ = extract_json(response.content)

        if parsed is None:
            logger.warning("意图分类 JSON 解析失败，使用兜底逻辑")
            if session.student_profile is None:
                return TaskIntent.EXTRACT_PROFILE, 0.5, "JSON 失败兜底：无画像"
            else:
                return TaskIntent.ANSWER_QUESTION, 0.5, "JSON 失败兜底：默认答疑"

        intent_str = parsed.get("intent") or ""
        confidence = float(parsed.get("confidence", 0.5))
        rationale = parsed.get("rationale") or ""

        # 字符串 → 枚举
        try:
            intent = TaskIntent(intent_str)
        except ValueError:
            logger.warning(f"未知意图: {intent_str}，默认闲聊")
            intent = TaskIntent.CHITCHAT
            confidence = 0.3

        return intent, confidence, rationale

    # ── 内部实现 ──────────────────────────────────────────

    def _handle_impl(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """同步处理的核心实现。"""

        # 0. 空输入校验
        if not user_text or not user_text.strip():
            return SupervisorResult(
                reply="你好，请问有什么可以帮助你的？",
                session=session,
                intent=TaskIntent.CHITCHAT,
                success=True,
            )

        # 1. 意图分类
        intent, confidence, rationale = self.classify_intent(user_text, session)

        logger.info(
            f"Supervisor.handle | intent={intent.value} | "
            f"confidence={confidence:.2f} | "
            f"rationale={rationale[:50]}"
        )

        # 2. 按意图分发
        if intent == TaskIntent.EXTRACT_PROFILE:
            return self._handle_extract_profile(user_text, session)
        elif intent == TaskIntent.PLAN_PATH:
            return self._handle_plan_path(user_text, session)
        elif intent == TaskIntent.ANSWER_QUESTION:
            return self._handle_answer_question(user_text, session)
        elif intent == TaskIntent.CHITCHAT:
            return self._handle_chitchat(user_text, session)
        elif intent == TaskIntent.GENERATE_RESOURCE:
            return self._handle_placeholder(user_text, session, intent, "资源生成")
        elif intent == TaskIntent.EVALUATE:
            return self._handle_placeholder(user_text, session, intent, "学习评估")
        else:
            return SupervisorResult(
                reply="抱歉，我还不太理解你的意图。可以换个方式说说吗？",
                session=session,
                intent=intent,
                success=True,
            )

    async def _handle_impl_async(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """异步处理的核心实现。

        使用 asyncio.to_thread 将同步逻辑在线程池中执行，
        避免阻塞事件循环。这是 Python 异步编程的推荐模式。
        """
        import asyncio
        return await asyncio.to_thread(self._handle_impl, user_text, session)

    # ── 意图处理器 ────────────────────────────────────────

    def _handle_extract_profile(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """处理画像抽取意图：调用 ProfileAgent。"""
        from ..profile_agent import ProfileAgent

        agent = ProfileAgent(client=self._client, model=self._model)
        result = agent.extract(
            user_text=user_text,
            existing_profile=session.student_profile,
            conversation_history=session.conversation_history,
        )

        if not result.success:
            return SupervisorResult(
                reply="抱歉，我在理解你的信息时遇到了一些问题，可以再详细说说吗？",
                session=session,
                intent=TaskIntent.EXTRACT_PROFILE,
                success=False,
                error=result.error,
            )

        # 更新 SessionState
        updated_session = session.model_copy(deep=True)
        updated_session.student_profile = result.profile
        updated_session.updated_at = datetime.now()

        # 追加对话历史
        updated_session.conversation_history.append({"role": "user", "content": user_text})
        updated_session.conversation_history.append({"role": "assistant", "content": result.follow_up_question or result.rationale})

        # 构建回复
        if result.is_complete:
            reply = (
                f"好的，我已经对你的学习情况有了比较全面的了解。{result.rationale}\n\n"
                f"接下来，要不要我帮你规划一个个性化的学习路径？"
            )
        elif result.follow_up_question:
            reply = result.follow_up_question
        else:
            reply = result.rationale or "明白了，请继续。"

        return SupervisorResult(
            reply=reply,
            session=updated_session,
            intent=TaskIntent.EXTRACT_PROFILE,
            success=True,
        )

    def _handle_plan_path(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """处理路径规划意图：调用 PlannerAgent。"""
        from ..planner import PlannerAgent
        from ..utils.dag_loader import load_knowledge_dag

        # 检查是否有画像
        if session.student_profile is None:
            return SupervisorResult(
                reply="在规划学习路径之前，我需要先了解你的学习情况。可以先简单介绍一下自己吗？比如你的专业、年级、熟悉哪些知识、有什么学习目标？",
                session=session,
                intent=TaskIntent.PLAN_PATH,
                success=True,
            )

        # 加载 DAG
        dag_path = self._dag_path
        if dag_path is None:
            return SupervisorResult(
                reply="抱歉，知识库还没有配置好。请先设置知识库路径。",
                session=session,
                intent=TaskIntent.PLAN_PATH,
                success=False,
                error="dag_path 未配置",
            )

        try:
            dag = load_knowledge_dag(dag_path)
        except Exception as e:
            logger.error(f"加载知识 DAG 失败: {e}")
            return SupervisorResult(
                reply=f"抱歉，知识库加载失败：{e}",
                session=session,
                intent=TaskIntent.PLAN_PATH,
                success=False,
                error=str(e),
            )

        # 调用 Planner
        planner = PlannerAgent(client=self._client, model=self._model)
        plan_result = planner.plan(
            student_profile=session.student_profile,
            knowledge_dag=dag,
            existing_path=session.current_learning_path,
        )

        if not plan_result.success:
            return SupervisorResult(
                reply="抱歉，学习路径生成失败了。请稍后再试。",
                session=session,
                intent=TaskIntent.PLAN_PATH,
                success=False,
                error=plan_result.error,
            )

        # 更新 SessionState
        updated_session = session.model_copy(deep=True)
        updated_session.current_learning_path = plan_result.learning_path
        updated_session.updated_at = datetime.now()

        updated_session.conversation_history.append({"role": "user", "content": user_text})
        updated_session.conversation_history.append({"role": "assistant", "content": "已生成学习路径"})

        # 构建回复
        path = plan_result.learning_path
        node_lines = []
        for node in path.nodes:
            depth_label = {1: "了解", 2: "掌握", 3: "精通"}.get(node.depth, "掌握")
            weak_tag = " [薄弱环节]" if node.is_weak_point else ""
            resource_names = ", ".join(rt.value for rt in node.recommended_resource_types)
            node_lines.append(
                f"  {node.order}. **{node.knowledge_point_name}** "
                f"（{depth_label}，{node.estimated_time_minutes}分钟，资源: {resource_names}）{weak_tag}"
            )

        reply = (
            f"根据你的学习情况，我为你规划了以下学习路径（共 {len(path.nodes)} 个知识点，"
            f"预计总时长 {path.total_estimated_minutes} 分钟）：\n\n"
            + "\n".join(node_lines) +
            f"\n\n你可以从第一个知识点开始学习。需要我为你生成某个知识点的学习资料吗？"
        )

        # ── 追加 Planner 警告 ──
        if plan_result.warnings:
            reply += "\n\n⚠️ 提示：\n" + "\n".join(f"  • {w}" for w in plan_result.warnings)

        return SupervisorResult(
            reply=reply,
            session=updated_session,
            intent=TaskIntent.PLAN_PATH,
            success=True,
        )

    def _handle_answer_question(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """处理答疑意图：直接 LLM 回复。"""
        response = self._client.chat(
            user_message=user_text,
            system_prompt=_ANSWER_PROMPT,
            temperature=0.5,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        if not response.success:
            return SupervisorResult(
                reply="抱歉，我现在无法回答这个问题。请稍后再试。",
                session=session,
                intent=TaskIntent.ANSWER_QUESTION,
                success=False,
                error=response.error,
            )

        updated_session = session.model_copy(deep=True)
        updated_session.conversation_history.append({"role": "user", "content": user_text})
        updated_session.conversation_history.append({"role": "assistant", "content": response.content})
        updated_session.updated_at = datetime.now()

        return SupervisorResult(
            reply=response.content,
            session=updated_session,
            intent=TaskIntent.ANSWER_QUESTION,
            success=True,
        )

    def _handle_chitchat(
        self,
        user_text: str,
        session: SessionState,
    ) -> SupervisorResult:
        """处理闲聊意图：简短友好回复。"""
        response = self._client.chat(
            user_message=user_text,
            system_prompt=_CHITCHAT_PROMPT,
            temperature=0.7,
            max_tokens=256,
            model=self._model,
        )

        if not response.success:
            return SupervisorResult(
                reply="你好！有什么可以帮你的吗？",
                session=session,
                intent=TaskIntent.CHITCHAT,
                success=True,
            )

        updated_session = session.model_copy(deep=True)
        updated_session.conversation_history.append({"role": "user", "content": user_text})
        updated_session.conversation_history.append({"role": "assistant", "content": response.content})
        updated_session.updated_at = datetime.now()

        return SupervisorResult(
            reply=response.content,
            session=updated_session,
            intent=TaskIntent.CHITCHAT,
            success=True,
        )

    def _handle_placeholder(
        self,
        user_text: str,
        session: SessionState,
        intent: TaskIntent,
        label: str,
    ) -> SupervisorResult:
        """未实现功能的占位处理。

        对于尚未完成的 Agent，给出明确的状态提示和替代建议，
        避免让用户困惑。
        """
        updated_session = session.model_copy(deep=True)
        updated_session.conversation_history.append({"role": "user", "content": user_text})
        updated_session.updated_at = datetime.now()

        if intent == TaskIntent.GENERATE_RESOURCE:
            hint = (
                "资源生成功能正在开发中。\n\n"
                "当前你可以：\n"
                "  - 继续完善学习画像（告诉我你的学习情况）\n"
                "  - 查看个性化学习路径（说「帮我规划学习」）\n"
                "  - 向我提问课程相关问题"
            )
        elif intent == TaskIntent.EVALUATE:
            hint = (
                "学习评估功能正在开发中。\n\n"
                "当前你可以：\n"
                "  - 继续完成学习路径上的知识点\n"
                "  - 向我提问来检验你的理解\n"
                "  - 查看课程知识库内容"
            )
        else:
            hint = (
                f"{label}功能还在开发中，敬请期待！目前我可以帮你了解学习情况、"
                f"规划学习路径，或者回答学习问题。"
            )

        return SupervisorResult(
            reply=hint,
            session=updated_session,
            intent=intent,
            success=True,
        )

    # ── 辅助方法 ──────────────────────────────────────────

    @staticmethod
    def _build_state_summary(session: SessionState) -> str:
        """构建会话状态摘要文本，用于意图分类 prompt（包含最近对话上下文）。"""
        parts = []

        if session.student_profile is None:
            parts.append("- 尚未收集学生画像")
        else:
            p = session.student_profile
            dims = []
            if p.major or p.grade:
                dims.append("基础信息")
            if p.knowledge_base:
                dims.append("知识基础")
            if p.cognitive_style != "balanced":
                dims.append("认知风格")
            if p.learning_goal_short or p.learning_goal_long:
                dims.append("学习目标")
            if p.weak_points:
                dims.append("薄弱环节")
            if p.learning_pace != "flexible" or p.interest_domains:
                dims.append("学习节奏/兴趣")
            parts.append(f"- 已有学生画像（已收集维度: {', '.join(dims) if dims else '基础信息'}）")

        if session.current_learning_path is None:
            parts.append("- 尚未生成学习路径")
        else:
            path = session.current_learning_path
            parts.append(f"- 已有学习路径（{len(path.nodes)} 个节点, 版本 {path.version}）")

        parts.append(f"- 对话历史轮次: {len(session.conversation_history) // 2}")

        # ── 融入最近对话上下文，帮助 LLM 理解当前对话阶段 ──
        if session.conversation_history:
            recent = session.conversation_history[-4:]  # 最近 2 轮
            recent_lines = []
            for msg in recent:
                role = "用户" if msg["role"] == "user" else "助手"
                text = str(msg.get("content", ""))[:80]
                recent_lines.append(f"  [{role}] {text}")
            if recent_lines:
                parts.append("- 最近对话:\n" + "\n".join(recent_lines))

        return "\n".join(parts)
