import asyncio
from collections.abc import AsyncIterator

from app.agents.base import AgentProvider
from app.core.config import Settings
from app.schemas.profile import StudentProfileData
from app.schemas.task import GatewayEvent


class MockAgentProvider(AgentProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        profile = StudentProfileData(
            knowledge_foundation="具备入门基础，需要通过结构化练习巩固概念。",
            cognitive_style="偏好案例驱动与步骤化讲解。",
            weak_points=[chat_text.strip()[:80]],
            learning_pace="分阶段推进，每个阶段包含讲解与练习。",
            content_preferences=["图解", "代码案例"],
            short_term_goal="完成当前课程薄弱知识点的强化学习。",
        )
        events = [
            GatewayEvent(
                event="task.started",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="主管Agent",
                progress=0,
                demo_mode=True,
            ),
            GatewayEvent(
                event="agent.started",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=10,
                demo_mode=True,
            ),
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=35,
                content="正在理解你的学习背景，",
                demo_mode=True,
            ),
            GatewayEvent(
                event="content.delta",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=60,
                content="画像的六个维度已完成本轮更新。",
                demo_mode=True,
            ),
            GatewayEvent(
                event="profile.patch",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=85,
                profile_patch=profile.model_dump(),
                demo_mode=True,
            ),
            GatewayEvent(
                event="task.completed",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="画像抽取Agent",
                progress=100,
                finish_flag=True,
                demo_mode=True,
            ),
        ]

        for index, event in enumerate(events):
            yield event
            if self.settings.mock_event_delay_ms and index < len(events) - 1:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)
