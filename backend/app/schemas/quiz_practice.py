"""题库练习 & 错题本 Schema"""

from pydantic import BaseModel, Field

from app.schemas.resource import ResourceType


class QuizGenerateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    course_name: str = Field(min_length=1, max_length=160)
    weak_point: str = Field(default="", max_length=500)
    count: int = Field(default=5, ge=1, le=20)


class QuizTaskAcceptedData(BaseModel):
    task_id: str
    status: str = "queued"


class QuizTaskResponse(BaseModel):
    data: QuizTaskAcceptedData
    trace_id: str


class ErrorQuestionItem(BaseModel):
    question_id: str
    attempt_id: str
    quiz_title: str
    prompt: str
    question_type: str
    options: list[str] = Field(default_factory=list)
    user_answer: str
    correct_answer: str
    explanation: str
    concept: str  # 概念化知识点名
    created_at: str  # ISO


class ErrorNotebookData(BaseModel):
    questions: list[ErrorQuestionItem]
    total_errors: int
    unique_concepts: int


class ErrorNotebookResponse(BaseModel):
    data: ErrorNotebookData
    trace_id: str
