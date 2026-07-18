"""仪表盘聚合 API"""

from fastapi import APIRouter, Query, Request

from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    request: Request,
    user_id: str = Query(min_length=1, max_length=64),
    course_name: str | None = Query(default=None, max_length=160),
) -> DashboardResponse:
    service = DashboardService(request.app.state.db)
    data = service.build(user_id, course_name)
    return DashboardResponse(data=data, trace_id=request.state.trace_id)
