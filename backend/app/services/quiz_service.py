from app.core.errors import AppError
from app.db.database import Database
from app.repositories.learning import LearningRepository
from app.repositories.resources import ResourceRepository
from app.schemas.resource import (
    QuizQuestion,
    QuizQuestionResult,
    QuizResourceDetail,
    QuizSubmitData,
    QuizSubmitRequest,
)
from app.services.resource_service import resource_to_detail


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def normalize_programming_output(value: str) -> str:
    return "".join(value.split()).casefold()


def is_correct(question: QuizQuestion, submitted: str) -> bool:
    if question.question_type == "choice":
        return submitted.strip() == question.answer
    if question.question_type == "blank":
        return normalize_text(submitted) == normalize_text(question.answer)
    return normalize_programming_output(submitted) == normalize_programming_output(
        question.answer
    )


class QuizService:
    def __init__(self, db: Database):
        self.db = db

    def submit(self, payload: QuizSubmitRequest) -> QuizSubmitData:
        with self.db.session() as session:
            try:
                resource = ResourceRepository(session).get(payload.resource_id)
            except LookupError as error:
                raise AppError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="题库资源不存在或已被清理。",
                    retryable=False,
                ) from error
            if resource.user_id != payload.user_id:
                raise AppError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="题库资源不存在或已被清理。",
                    retryable=False,
                )
            detail = resource_to_detail(resource)
            if not isinstance(detail, QuizResourceDetail):
                raise AppError(
                    status_code=400,
                    code="VALIDATION_ERROR",
                    message="指定资源不是题库。",
                    retryable=False,
                )

            results = [
                QuizQuestionResult(
                    question_id=question.id,
                    correct=is_correct(
                        question, payload.answers.get(question.id, "")
                    ),
                    submitted_answer=payload.answers.get(question.id, "").strip(),
                    expected_answer=question.answer,
                    explanation=question.explanation,
                )
                for question in detail.payload.questions
            ]
            correct_count = sum(result.correct for result in results)
            score = round(100 * correct_count / len(results)) if results else 0
            attempt = LearningRepository(session).record_quiz_attempt(
                user_id=payload.user_id,
                resource_id=payload.resource_id,
                answers=payload.answers,
                results=[result.model_dump(mode="json") for result in results],
                score=score,
            )
            return QuizSubmitData(
                attempt_id=attempt.id,
                score=score,
                results=results,
            )
