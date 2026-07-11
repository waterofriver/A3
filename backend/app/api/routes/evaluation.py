from fastapi import APIRouter, Depends, Request

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.schemas.evaluation import (
    EvaluationApplyRequest,
    EvaluationApplyResponse,
    EvaluationReportResponse,
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["evaluation"])


@router.get("/api/eval/report", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    user_id: str,
    course_name: str,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> EvaluationReportResponse:
    data = await EvaluationService(request.app.state.db, provider).get_report(
        user_id, course_name
    )
    return EvaluationReportResponse(data=data, trace_id=request.state.trace_id)


@router.post("/api/eval/apply", response_model=EvaluationApplyResponse)
def apply_evaluation_plan(
    payload: EvaluationApplyRequest,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> EvaluationApplyResponse:
    data = EvaluationService(request.app.state.db, provider).apply(payload.report_id)
    return EvaluationApplyResponse(data=data, trace_id=request.state.trace_id)
