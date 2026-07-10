from fastapi import APIRouter, Depends, Request

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.schemas.learning import (
    LearningEventBatchRequest,
    LearningEventBatchResponse,
    LearningPathResponse,
)
from app.schemas.resource import QuizSubmitRequest, QuizSubmitResponse
from app.services.learning_event_service import LearningEventService
from app.services.learning_path_service import LearningPathService
from app.services.quiz_service import QuizService

router = APIRouter(tags=["learning"])


@router.post("/api/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest, request: Request
) -> QuizSubmitResponse:
    result = QuizService(request.app.state.db).submit(payload)
    return QuizSubmitResponse(data=result, trace_id=request.state.trace_id)


@router.post("/api/learning/events", response_model=LearningEventBatchResponse)
def record_learning_events(
    payload: LearningEventBatchRequest, request: Request
) -> LearningEventBatchResponse:
    result = LearningEventService(request.app.state.db).record(payload)
    return LearningEventBatchResponse(data=result, trace_id=request.state.trace_id)


@router.get("/api/path/get", response_model=LearningPathResponse)
async def get_learning_path(
    user_id: str,
    course_name: str,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> LearningPathResponse:
    data = await LearningPathService(request.app.state.db, provider).get_or_create(
        user_id, course_name
    )
    return LearningPathResponse(data=data, trace_id=request.state.trace_id)
