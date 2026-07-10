from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "task.started",
    "agent.started",
    "task.progress",
    "content.delta",
    "profile.patch",
    "media.ready",
    "resource.ready",
    "task.completed",
    "task.failed",
    "heartbeat",
]


class GatewayError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: Any | None = None


class GatewayEvent(BaseModel):
    event: EventType
    task_id: str
    seq: int = 0
    trace_id: str
    current_agent: str | None = None
    progress: int = Field(default=0, ge=0, le=100)
    resource_type: str | None = None
    content: str = ""
    media_url: str | None = None
    finish_flag: bool = False
    resource_ids: list[str] = Field(default_factory=list)
    profile_patch: dict[str, Any] | None = None
    error: GatewayError | None = None
    demo_mode: bool = False
