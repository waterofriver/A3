from fastapi import APIRouter, Query, Request

from app.schemas.memory import MemoryReportResponse
from app.services.memory_service import MemoryService

router = APIRouter(tags=["memory"])


@router.get("/api/memory/report", response_model=MemoryReportResponse)
def get_memory_report(
    request: Request,
    user_id: str = Query(min_length=1, max_length=64),
    course_name: str = Query(default="机器人与安全", min_length=1, max_length=160),
) -> MemoryReportResponse:
    data = MemoryService(request.app.state.db).compute(user_id, course_name)
    return MemoryReportResponse(data=data, trace_id=request.state.trace_id)
