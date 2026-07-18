"""知识 DAG 着色状态 API"""

from fastapi import APIRouter, Query, Request

from app.schemas.dag import KnowledgeDagStatusResponse
from app.services.dag_status_service import DagStatusService

router = APIRouter(tags=["dag"])


@router.get("/api/knowledge/dag", response_model=KnowledgeDagStatusResponse)
def get_dag_status(
    request: Request,
    user_id: str = Query(min_length=1, max_length=64),
    course_name: str | None = Query(default=None, max_length=160),
) -> KnowledgeDagStatusResponse:
    service = DagStatusService(request.app.state.db)
    data = service.compute(user_id, course_name or "机器人与安全")
    return KnowledgeDagStatusResponse(data=data, trace_id=request.state.trace_id)
