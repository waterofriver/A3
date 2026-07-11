from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import EvaluationReport, LearningEvent, QuizAttempt, Resource
from app.schemas.evaluation import EvaluationDraft


class EvaluationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, report_id: str) -> EvaluationReport:
        report = self.session.get(EvaluationReport, report_id)
        if report is None:
            raise LookupError(report_id)
        return report

    def find_by_evidence(
        self, user_id: str, course_name: str, evidence_hash: str
    ) -> EvaluationReport | None:
        return self.session.scalar(
            select(EvaluationReport).where(
                EvaluationReport.user_id == user_id,
                EvaluationReport.course_name == course_name,
                EvaluationReport.evidence_hash == evidence_hash,
            )
        )

    def create(
        self,
        *,
        user_id: str,
        course_name: str,
        source_path_id: str,
        evidence_hash: str,
        draft: EvaluationDraft,
    ) -> EvaluationReport:
        report = EvaluationReport(
            user_id=user_id,
            course_name=course_name,
            source_path_id=source_path_id,
            evidence_hash=evidence_hash,
            theory_score=draft.theory_score,
            practice_score=draft.practice_score,
            weak_points=[item.model_dump(mode="json") for item in draft.weak_points],
            recommended_changes=[
                item.model_dump(mode="json") for item in draft.recommended_changes
            ],
        )
        self.session.add(report)
        self.session.flush()
        return report

    def list_quiz_attempts(
        self, user_id: str, course_name: str
    ) -> list[tuple[QuizAttempt, Resource]]:
        statement = (
            select(QuizAttempt, Resource)
            .join(Resource, Resource.id == QuizAttempt.resource_id)
            .where(
                QuizAttempt.user_id == user_id,
                Resource.course_name == course_name,
            )
            .order_by(QuizAttempt.created_at, QuizAttempt.id)
        )
        return [(row.QuizAttempt, row.Resource) for row in self.session.execute(statement)]

    def list_question_events(
        self, user_id: str, course_name: str
    ) -> list[LearningEvent]:
        statement = (
            select(LearningEvent)
            .where(
                LearningEvent.user_id == user_id,
                LearningEvent.event_type == "question_asked",
                or_(
                    LearningEvent.course_name == course_name,
                    LearningEvent.course_name == "全局答疑",
                ),
            )
            .order_by(LearningEvent.created_at, LearningEvent.id)
        )
        return list(self.session.scalars(statement))
