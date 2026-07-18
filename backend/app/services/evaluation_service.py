import hashlib

from app.agents.base import AgentProvider
from app.core.errors import AppError
from app.db.database import Database
from app.db.models import LearningPath
from app.repositories.evaluations import EvaluationRepository
from app.repositories.learning import LearningRepository
from app.schemas.evaluation import (
    EvaluationEvidence,
    EvaluationPracticeNodeEvidence,
    EvaluationQuizAttemptEvidence,
    EvaluationRecommendedChange,
    EvaluationReportData,
    EvaluationWeakPoint,
)
from app.schemas.learning import LearningPathData
from app.services.learning_path_service import path_data


def report_data(report) -> EvaluationReportData:
    return EvaluationReportData(
        id=report.id,
        user_id=report.user_id,
        course_name=report.course_name,
        theory_score=report.theory_score,
        practice_score=report.practice_score,
        weak_points=[
            EvaluationWeakPoint.model_validate(item) for item in report.weak_points
        ],
        recommended_changes=[
            EvaluationRecommendedChange.model_validate(item)
            for item in report.recommended_changes
        ],
        source_path_id=report.source_path_id,
        applied_path_id=report.applied_path_id,
        created_at=report.created_at,
    )


class EvaluationService:
    def __init__(self, db: Database, provider: AgentProvider):
        self.db = db
        self.provider = provider

    async def get_report(
        self, user_id: str, course_name: str
    ) -> EvaluationReportData:
        with self.db.session() as session:
            learning = LearningRepository(session)
            source_path = learning.get_active_path(user_id, course_name)
            if source_path is None:
                self._not_ready()
            nodes = learning.list_path_nodes(source_path.id)
            repository = EvaluationRepository(session)
            attempt_rows = repository.list_quiz_attempts(user_id, course_name)
            question_events = repository.list_question_events(user_id, course_name)

            attempts = []
            quiz_resource_id = None
            for attempt, resource in attempt_rows:
                quiz_resource_id = resource.id
                prompts = {
                    question.get("id"): question.get("prompt", question.get("id", ""))
                    for question in resource.payload.get("questions", [])
                }
                incorrect_points = [
                    prompts.get(result.get("question_id"), result.get("question_id", ""))
                    for result in attempt.results
                    if not result.get("correct", False)
                ]
                attempts.append(
                    EvaluationQuizAttemptEvidence(
                        score=attempt.score,
                        incorrect_points=[point for point in incorrect_points if point],
                    )
                )

            practice_nodes = [
                EvaluationPracticeNodeEvidence(
                    stage_name=node.stage_name,
                    completed=node.completed_at is not None,
                )
                for node in nodes
            ]
            question_weak_points = []
            for event in question_events:
                metadata = event.event_metadata or {}
                weak_point = metadata.get("weak_point") or metadata.get("question")
                if isinstance(weak_point, str) and weak_point.strip():
                    question_weak_points.append(weak_point.strip())

            evidence = EvaluationEvidence(
                attempts=attempts,
                practice_nodes=practice_nodes,
                question_weak_points=question_weak_points,
                quiz_resource_id=quiz_resource_id,
            )
            if not (
                evidence.attempts
                or evidence.question_weak_points
                or any(node.completed for node in evidence.practice_nodes)
            ):
                self._not_ready()
            evidence_hash = hashlib.sha256(
                evidence.model_dump_json().encode("utf-8")
            ).hexdigest()
            existing = repository.find_by_evidence(
                user_id, course_name, evidence_hash
            )
            if existing is not None:
                return report_data(existing)
            source_path_id = source_path.id

        draft = await self.provider.build_evaluation(
            user_id=user_id,
            course_name=course_name,
            evidence=evidence,
        )
        with self.db.session() as session:
            repository = EvaluationRepository(session)
            existing = repository.find_by_evidence(
                user_id, course_name, evidence_hash
            )
            if existing is not None:
                return report_data(existing)
            report = repository.create(
                user_id=user_id,
                course_name=course_name,
                source_path_id=source_path_id,
                evidence_hash=evidence_hash,
                draft=draft,
            )
            # 把评估出的薄弱点同步回学生画像
            self._sync_weak_points_to_profile(
                session, user_id, draft.weak_points
            )
            return report_data(report)

    def apply(self, report_id: str) -> LearningPathData:
        with self.db.session() as session:
            repository = EvaluationRepository(session)
            try:
                report = repository.get(report_id)
            except LookupError as error:
                raise AppError(
                    status_code=404,
                    code="EVALUATION_NOT_FOUND",
                    message="评估报告不存在或已被清理。",
                    retryable=False,
                ) from error
            learning = LearningRepository(session)
            if report.applied_path_id:
                applied = session.get(LearningPath, report.applied_path_id)
                if applied is not None:
                    return path_data(applied, learning.list_path_nodes(applied.id))

            active = learning.get_active_path(report.user_id, report.course_name)
            if active is None or active.id != report.source_path_id:
                raise AppError(
                    status_code=400,
                    code="EVALUATION_STALE",
                    message="学习路径已更新，请重新生成评估报告。",
                    retryable=False,
                )

            source_nodes = learning.list_path_nodes(active.id)
            node_drafts = [
                {
                    "stage_name": node.stage_name,
                    "difficulty": node.difficulty,
                    "resource_id": node.resource_id,
                    "completed_at": node.completed_at,
                }
                for node in source_nodes
            ]
            existing_names = {node["stage_name"] for node in node_drafts}
            insertion_index = next(
                (
                    index + 1
                    for index, node in reversed(list(enumerate(node_drafts)))
                    if "习题" in node["stage_name"]
                ),
                len(node_drafts),
            )
            for raw_change in report.recommended_changes:
                change = EvaluationRecommendedChange.model_validate(raw_change)
                if change.stage_name in existing_names:
                    continue
                node_drafts.insert(
                    insertion_index,
                    {
                        "stage_name": change.stage_name,
                        "difficulty": change.difficulty,
                        "resource_id": change.resource_id,
                        "completed_at": None,
                    },
                )
                existing_names.add(change.stage_name)
                insertion_index += 1

            updated = learning.create_path(report.user_id, report.course_name)
            updated_nodes = learning.replace_nodes(updated.id, node_drafts)
            report.applied_path_id = updated.id
            session.flush()
            return path_data(updated, updated_nodes)

    @staticmethod
    def _sync_weak_points_to_profile(
        session, user_id: str, eval_weak_points: list
    ) -> None:
        """把评估薄弱点名称合并到学生画像的 weak_points 字段。"""
        from app.repositories.profiles import ProfileRepository
        from app.schemas.profile import StudentProfileData

        profile_record = ProfileRepository(session).get(user_id)
        if profile_record is None:
            return

        profile_data = dict(profile_record.profile_data or {})
        existing: list[str] = list(profile_data.get("weak_points", []) or [])

        for wp in eval_weak_points:
            name = wp.name if hasattr(wp, "name") else str(wp)
            if name and name not in existing:
                existing.append(name)

        profile_data["weak_points"] = existing
        # 用 upsert 写回（不改变 confirmed_at）
        ProfileRepository(session).upsert(
            user_id,
            profile_data,
            revision=profile_record.revision + 1,
        )

    @staticmethod
    def _not_ready() -> None:
        raise AppError(
            status_code=400,
            code="EVALUATION_NOT_READY",
            message="评估数据不足，请先完成题库练习或学习路径节点。",
            retryable=False,
        )
