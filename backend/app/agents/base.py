from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel, Field

from app.schemas.profile import StudentProfileData
from app.schemas.resource import ResourceType
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
