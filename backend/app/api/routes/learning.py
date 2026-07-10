from fastapi import APIRouter, Request

from app.schemas.learning import (
    LearningEventBatchRequest,
    LearningEventBatchResponse,
)
from app.schemas.resource import QuizSubmitRequest, QuizSubmitResponse
from app.services.learning_event_service import LearningEventService
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
