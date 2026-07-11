from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel, Field

from app.schemas.profile import StudentProfileData
from app.schemas.qa import AnswerMode
from app.schemas.evaluation import EvaluationDraft, EvaluationEvidence
from app.schemas.learning import LearningPathDraft
from app.schemas.resource import ResourceSummary, ResourceType
from app.schemas.task import GatewayEvent


class ResourceDraft(BaseModel):
    resource_type: ResourceType
    title: str
    payload: dict
    media_url: str | None = None


class ResourceAgentEvent(BaseModel):
    event: str
    current_agent: str
    progress: int = Field(ge=0, le=99)
    resource_type: ResourceType
    content: str = ""
    resource: ResourceDraft | None = None
    demo_mode: bool = False


class AgentProvider(ABC):
    @abstractmethod
    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def build_learning_path(
        self,
        *,
        user_id: str,
        course_name: str,
        profile: StudentProfileData,
        resources: list[ResourceSummary],
    ) -> LearningPathDraft:
        raise NotImplementedError

    @abstractmethod
    async def stream_qa(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        question: str,
        answer_mode: AnswerMode,
        profile: StudentProfileData,
    ) -> AsyncIterator[GatewayEvent]:
        raise NotImplementedError

    @abstractmethod
    async def build_evaluation(
        self,
        *,
        user_id: str,
        course_name: str,
        evidence: EvaluationEvidence,
    ) -> EvaluationDraft:
        raise NotImplementedError
