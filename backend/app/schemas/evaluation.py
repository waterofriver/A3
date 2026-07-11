from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.learning import LearningPathData


class EvaluationQuizAttemptEvidence(BaseModel):
    score: int = Field(ge=0, le=100)
    incorrect_points: list[str] = Field(default_factory=list)


class EvaluationPracticeNodeEvidence(BaseModel):
    stage_name: str
    completed: bool


class EvaluationEvidence(BaseModel):
    attempts: list[EvaluationQuizAttemptEvidence] = Field(default_factory=list)
    practice_nodes: list[EvaluationPracticeNodeEvidence] = Field(default_factory=list)
    question_weak_points: list[str] = Field(default_factory=list)
    quiz_resource_id: str | None = None


class EvaluationWeakPoint(BaseModel):
    name: str
    frequency: int = Field(ge=1)


class EvaluationRecommendedChange(BaseModel):
    stage_name: str
    difficulty: str
    reason: str
    resource_id: str | None = None


class EvaluationDraft(BaseModel):
    theory_score: int = Field(ge=0, le=100)
    practice_score: int = Field(ge=0, le=100)
    weak_points: list[EvaluationWeakPoint]
    recommended_changes: list[EvaluationRecommendedChange]


class EvaluationReportData(EvaluationDraft):
    id: str
    user_id: str
    course_name: str
    source_path_id: str
    applied_path_id: str | None = None
    created_at: datetime


class EvaluationReportResponse(BaseModel):
    data: EvaluationReportData
    trace_id: str


class EvaluationApplyRequest(BaseModel):
    report_id: str = Field(min_length=1, max_length=36)


class EvaluationApplyResponse(BaseModel):
    data: LearningPathData
    trace_id: str
