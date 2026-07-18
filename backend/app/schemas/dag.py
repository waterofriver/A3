"""知识 DAG 着色状态 Schema"""

from pydantic import BaseModel, Field


class KnowledgeDagNodeStatus(BaseModel):
    kp_id: str
    kp_name: str
    difficulty: int = Field(ge=1, le=5)
    category: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    status: str = "untouched"  # untouched | learning | weak | mastered


class KnowledgeDagStatusResponse(BaseModel):
    data: list[KnowledgeDagNodeStatus]
    trace_id: str
