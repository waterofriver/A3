import asyncio
from collections.abc import AsyncIterator

from app.agents.base import AgentProvider, ResourceAgentEvent, ResourceDraft
from app.core.config import Settings
from app.schemas.learning import LearningPathDraft, LearningPathNodeDraft
from app.schemas.profile import StudentProfileData
from app.schemas.resource import ResourceSummary, ResourceType
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

    async def stream_resources(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        course_name: str,
        weak_point: str,
        resource_types: list[ResourceType],
    ) -> AsyncIterator[ResourceAgentEvent]:
        for index, resource_type in enumerate(resource_types):
            agent = self._resource_agent_name(resource_type)
            progress = min(95, 8 + index * max(1, 82 // max(1, len(resource_types))))
            yield ResourceAgentEvent(
                event="agent.started",
                current_agent=agent,
                progress=progress,
                resource_type=resource_type,
            )
            if self.settings.mock_event_delay_ms:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

            yield ResourceAgentEvent(
                event="content.delta",
                current_agent=agent,
                progress=min(97, progress + 8),
                resource_type=resource_type,
                content=f"正在生成 {resource_type} 演示资源。",
            )
            if self.settings.mock_event_delay_ms:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

            yield ResourceAgentEvent(
                event="resource.ready",
                current_agent=agent,
                progress=min(99, progress + 14),
                resource_type=resource_type,
                resource=self._resource_draft(
                    resource_type=resource_type,
                    course_name=course_name,
                    weak_point=weak_point,
                ),
            )
            if self.settings.mock_event_delay_ms and index < len(resource_types) - 1:
                await asyncio.sleep(self.settings.mock_event_delay_ms / 1000)

    @staticmethod
    def _resource_agent_name(resource_type: ResourceType) -> str:
        return {
            "handout": "讲义编写Agent",
            "mindmap": "思维导图Agent",
            "quiz": "题库Agent",
            "code": "代码案例Agent",
            "video": "多模态素材Agent",
        }[resource_type]

    @staticmethod
    def _resource_draft(
        *, resource_type: ResourceType, course_name: str, weak_point: str
    ) -> ResourceDraft:
        title = f"演示资源 · {course_name} · {weak_point or '核心知识点'}"
        if resource_type == "handout":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}讲义",
                payload={
                    "markdown": (
                        f"# {course_name}\n\n"
                        f"## 聚焦知识点\n\n{weak_point or '核心知识点'}\n\n"
                        "## 学习步骤\n\n1. 建立概念模型\n2. 阅读代码示例\n3. 完成针对性练习"
                    )
                },
            )
        if resource_type == "mindmap":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}思维导图",
                payload={
                    "nodes": [
                        {"id": "root", "label": course_name, "parent_id": None},
                        {"id": "focus", "label": weak_point or "核心知识点", "parent_id": "root"},
                        {"id": "practice", "label": "练习验证", "parent_id": "focus"},
                    ]
                },
            )
        if resource_type == "quiz":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}题库",
                payload={
                    "questions": [
                        {
                            "id": "q1",
                            "question_type": "choice",
                            "prompt": "ROS2 节点通信中，发布端通常通过什么方式发送消息？",
                            "options": ["A", "B", "C", "D"],
                            "answer": "B",
                            "explanation": "演示题使用 B 作为正确选项。",
                        },
                        {
                            "id": "q2",
                            "question_type": "blank",
                            "prompt": "ROS2 的运行单元称为____。",
                            "options": [],
                            "answer": "节点",
                            "explanation": "节点是 ROS2 应用的基本运行单元。",
                        },
                        {
                            "id": "q3",
                            "question_type": "programming",
                            "prompt": "写出发布消息的核心调用。",
                            "options": [],
                            "answer": "publisher.publish(message)",
                            "explanation": "演示评分比较规范化后的期望输出。",
                        },
                    ]
                },
            )
        if resource_type == "code":
            return ResourceDraft(
                resource_type=resource_type,
                title=f"{title}代码案例",
                payload={
                    "language": "python",
                    "description": "ROS2 发布节点最小示例。",
                    "code": (
                        "import rclpy\n\n"
                        "def publish_once(publisher, message):\n"
                        "    publisher.publish(message)\n"
                    ),
                },
            )
        return ResourceDraft(
            resource_type="video",
            title=f"{title}视频讲解",
            payload={
                "summary": "等待真实多模态 Agent 返回教学视频链接后即可预览。",
                "poster_url": "",
                "duration_seconds": 180,
            },
            media_url=None,
        )

    async def build_learning_path(
        self,
        *,
        user_id: str,
        course_name: str,
        profile: StudentProfileData,
        resources: list[ResourceSummary],
    ) -> LearningPathDraft:
        resource_by_type = {resource.resource_type: resource.id for resource in resources}
        return LearningPathDraft(
            nodes=[
                LearningPathNodeDraft(
                    stage_name="基础补全",
                    difficulty="基础",
                    resource_id=resource_by_type.get("handout"),
                ),
                LearningPathNodeDraft(
                    stage_name="知识点学习",
                    difficulty="进阶",
                    resource_id=resource_by_type.get("mindmap")
                    or resource_by_type.get("handout"),
                ),
                LearningPathNodeDraft(
                    stage_name="习题训练",
                    difficulty="巩固",
                    resource_id=resource_by_type.get("quiz"),
                ),
                LearningPathNodeDraft(
                    stage_name="代码实操",
                    difficulty="实操",
                    resource_id=resource_by_type.get("code"),
                ),
                LearningPathNodeDraft(
                    stage_name="拓展视频",
                    difficulty="拓展",
                    resource_id=resource_by_type.get("video"),
                ),
            ]
        )
