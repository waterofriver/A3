from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ResourceType = Literal["handout", "mindmap", "quiz", "code", "video"]


class HandoutPayload(BaseModel):
    markdown: str


class MindMapNode(BaseModel):
    id: str
    label: str
    parent_id: str | None = None


class MindMapPayload(BaseModel):
    nodes: list[MindMapNode]


class QuizQuestion(BaseModel):
    id: str
    question_type: Literal["choice", "blank", "programming"]
    prompt: str
    options: list[str] = Field(default_factory=list)
    answer: str
    explanation: str


class QuizPayload(BaseModel):
    questions: list[QuizQuestion]


class CodePayload(BaseModel):
    language: str
    code: str
    description: str


class VideoPayload(BaseModel):
    summary: str
    poster_url: str
    duration_seconds: int = Field(ge=0)


class ResourceDetailBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str | None = None
    course_name: str | None = None
    title: str
    media_url: str | None = None
    created_at: datetime | None = None


class HandoutResourceDetail(ResourceDetailBase):
    resource_type: Literal["handout"]
    payload: HandoutPayload


class MindMapResourceDetail(ResourceDetailBase):
    resource_type: Literal["mindmap"]
    payload: MindMapPayload


class QuizResourceDetail(ResourceDetailBase):
    resource_type: Literal["quiz"]
    payload: QuizPayload


class CodeResourceDetail(ResourceDetailBase):
    resource_type: Literal["code"]
    payload: CodePayload


class VideoResourceDetail(ResourceDetailBase):
    resource_type: Literal["video"]
    payload: VideoPayload


ResourceDetail = Annotated[
    HandoutResourceDetail
    | MindMapResourceDetail
    | QuizResourceDetail
    | CodeResourceDetail
    | VideoResourceDetail,
    Field(discriminator="resource_type"),
]


class ResourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    course_name: str
    resource_type: ResourceType
    title: str
    media_url: str | None = None
    created_at: datetime


class ResourceGenerateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    course_name: str = Field(min_length=1, max_length=160)
    weak_point: str = Field(default="", max_length=1000)
    resource_type_list: list[ResourceType] = Field(min_length=1, max_length=5)


class TaskAcceptedData(BaseModel):
    task_id: str
    status: str = "queued"
    deduplicated: bool = False
    retry_of_task_id: str | None = None


class TaskAcceptedResponse(BaseModel):
    data: TaskAcceptedData
    trace_id: str


class ResourceListData(BaseModel):
    resources: list[ResourceSummary]


class ResourceListResponse(BaseModel):
    data: ResourceListData
    trace_id: str


class ResourceDetailResponse(BaseModel):
    data: ResourceDetail
    trace_id: str


class QuizSubmitRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    resource_id: str = Field(min_length=1, max_length=36)
    answers: dict[str, str]


class QuizQuestionResult(BaseModel):
    question_id: str
    correct: bool
    submitted_answer: str
    expected_answer: str
    explanation: str


class QuizSubmitData(BaseModel):
    attempt_id: str
    score: int = Field(ge=0, le=100)
    results: list[QuizQuestionResult]


class QuizSubmitResponse(BaseModel):
    data: QuizSubmitData
    trace_id: str
