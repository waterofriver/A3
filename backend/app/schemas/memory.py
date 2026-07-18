from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CurvePoint(BaseModel):
    day: int = Field(ge=0)
    retention: int = Field(ge=0, le=100)


class MemoryBlockage(BaseModel):
    knowledge_point_id: str
    name: str
    reason: str


class MemoryKnowledgePoint(BaseModel):
    id: str
    name: str
    retention: int = Field(ge=0, le=100)
    base_mastery: int = Field(ge=0, le=100)
    days_since_review: int = Field(ge=0)
    risk_level: Literal["stable", "review_soon", "urgent"]
    curve: list[CurvePoint]
    recommendation: str
    blockage: MemoryBlockage | None = None

    @field_validator("curve")
    @classmethod
    def curve_must_use_review_milestones(cls, curve: list[CurvePoint]) -> list[CurvePoint]:
        if [point.day for point in curve] != [0, 1, 3, 7]:
            raise ValueError("curve must contain days 0, 1, 3, 7 in order")
        return curve


class MemoryAction(BaseModel):
    knowledge_point_id: str
    title: str
    minutes: int = Field(ge=1, le=30)
    action_type: Literal["recall", "quiz", "practice"]
    reason: str


class MemoryReportData(BaseModel):
    memory_health: int = Field(ge=0, le=100)
    summary: str
    has_personal_evidence: bool
    knowledge_points: list[MemoryKnowledgePoint]
    today_actions: list[MemoryAction] = Field(max_length=3)


class MemoryReportResponse(BaseModel):
    data: MemoryReportData
    trace_id: str
