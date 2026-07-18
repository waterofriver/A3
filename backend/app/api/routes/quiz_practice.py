"""题库练习 & 错题本 API"""

from fastapi import APIRouter, Depends, Header, Request, status

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.schemas.quiz_practice import (
    ErrorNotebookResponse,
    QuizGenerateRequest,
    QuizTaskResponse,
)
from app.services.quiz_practice_service import QuizPracticeService

router = APIRouter(prefix="/api/quiz", tags=["quiz-practice"])


def _service(request: Request, provider: AgentProvider) -> QuizPracticeService:
    return QuizPracticeService(
        request.app.state.db,
        provider,
        request.app.state.task_manager,
        demo_mode=request.app.state.settings.agent_mode == "mock",
    )


@router.get("/errors", response_model=ErrorNotebookResponse)
def get_error_notebook(
    request: Request,
    user_id: str,
    provider: AgentProvider = Depends(get_agent_provider),
) -> ErrorNotebookResponse:
    data = _service(request, provider).get_errors(user_id)
    return ErrorNotebookResponse(data=data, trace_id=request.state.trace_id)


@router.post(
    "/generate",
    response_model=QuizTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_quiz(
    payload: QuizGenerateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    provider: AgentProvider = Depends(get_agent_provider),
) -> QuizTaskResponse:
    data = _service(request, provider).generate(
        payload,
        idempotency_key=idempotency_key,
        trace_id=request.state.trace_id,
    )
    return QuizTaskResponse(data=data, trace_id=request.state.trace_id)
