from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

LearningEventType = Literal[
    "resource_opened",
    "resource_closed",
    "path_node_completed",
    "path_node_reset",
    "question_asked",
    "video_progress",
]


class LearningEventInput(BaseModel):
    event_type: LearningEventType
    resource_id: str | None = None
    path_node_id: str | None = None
    client_started_at: datetime | None = None
    client_ended_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class LearningEventBatchRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    course_name: str = Field(min_length=1, max_length=160)
    events: list[LearningEventInput] = Field(min_length=1, max_length=100)


class LearningEventBatchData(BaseModel):
    accepted: int


class LearningEventBatchResponse(BaseModel):
    data: LearningEventBatchData
    trace_id: str


class LearningPathNodeData(BaseModel):
    id: str
    position: int
    stage_name: str
    difficulty: str
    resource_id: str | None = None
    completed_at: datetime | None = None


class LearningPathData(BaseModel):
    id: str
    user_id: str
    course_name: str
    version: int
    nodes: list[LearningPathNodeData]


class LearningPathResponse(BaseModel):
    data: LearningPathData
    trace_id: str


class LearningPathNodeDraft(BaseModel):
    stage_name: str
    difficulty: str
    resource_id: str | None = None


class LearningPathDraft(BaseModel):
    nodes: list[LearningPathNodeDraft]
