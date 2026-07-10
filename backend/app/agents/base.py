from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas.profile import StudentProfileData
from app.schemas.task import GatewayEvent


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
