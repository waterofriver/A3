"""题库练习服务 —— 错题本查询 + 独立出题"""

from app.agents.base import AgentProvider
from app.agents.mock import _conceptualize_weak_point
from app.db.database import Database
from app.db.models import QuizAttempt, Resource
from app.repositories.learning import LearningRepository
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.quiz_practice import (
    ErrorNotebookData,
    ErrorQuestionItem,
    QuizGenerateRequest,
    QuizTaskAcceptedData,
)
from app.schemas.resource import ResourceGenerateRequest, ResourceType
from app.services.resource_service import ResourceService
from app.tasks.manager import TaskManager


class QuizPracticeService:
    def __init__(
        self,
        db: Database,
        provider: AgentProvider,
        task_manager: TaskManager,
        *,
        demo_mode: bool,
    ):
        self.db = db
        self.provider = provider
        self.task_manager = task_manager
        self.demo_mode = demo_mode

    def get_errors(self, user_id: str) -> ErrorNotebookData:
        """获取用户错题，每题只保留最近一次作答结果（做对了就移除）。"""
        with self.db.session() as session:
            attempts = list(
                session.query(QuizAttempt)
                .filter(QuizAttempt.user_id == user_id)
                .order_by(QuizAttempt.created_at.asc())  # 升序，后面覆盖前面的
                .all()
            )

            # key = hashlib.md5(prompt).hexdigest() → 同题去重
            import hashlib

            # 每题只保留最新一次答题结果
            latest_by_prompt: dict[str, dict] = {}
            for attempt in attempts:
                resource = session.get(Resource, attempt.resource_id)
                if resource is None:
                    continue
                questions = resource.payload.get("questions", [])
                if not questions:
                    continue

                question_map = {q.get("id", ""): q for q in questions}
                results = attempt.results or []

                for result in results:
                    qid = result.get("question_id", "")
                    question = question_map.get(qid, {})
                    prompt = question.get("prompt", qid)
                    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()

                    latest_by_prompt[prompt_hash] = {
                        "attempt_id": attempt.id,
                        "quiz_title": resource.title,
                        "prompt": prompt,
                        "question_type": question.get("question_type", "choice"),
                        "options": question.get("options", []),
                        "correct": result.get("correct", True),
                        "user_answer": result.get("submitted_answer", ""),
                        "correct_answer": result.get(
                            "expected_answer", question.get("answer", "")
                        ),
                        "explanation": result.get(
                            "explanation", question.get("explanation", "")
                        ),
                        "created_at": attempt.created_at.isoformat(),
                    }

            # 只保留最近一次仍答错的题
            error_items: list[ErrorQuestionItem] = []
            for entry in latest_by_prompt.values():
                if entry["correct"]:
                    continue  # 最近一次做对了 → 移除
                concept, _ = _conceptualize_weak_point(entry["prompt"])
                error_items.append(
                    ErrorQuestionItem(
                        question_id=entry["prompt"][:36],
                        attempt_id=entry["attempt_id"],
                        quiz_title=entry["quiz_title"],
                        prompt=entry["prompt"],
                        question_type=entry["question_type"],
                        options=entry["options"],
                        user_answer=entry["user_answer"],
                        correct_answer=entry["correct_answer"],
                        explanation=entry["explanation"],
                        concept=concept,
                        created_at=entry["created_at"],
                    )
                )

        unique_concepts = len({item.concept for item in error_items})
        return ErrorNotebookData(
            questions=error_items,
            total_errors=len(error_items),
            unique_concepts=unique_concepts,
        )

    def generate(
        self,
        payload: QuizGenerateRequest,
        *,
        idempotency_key: str | None,
        trace_id: str,
    ) -> QuizTaskAcceptedData:
        """发起独立出题任务，内部复用 ResourceService。"""
        resource_svc = ResourceService(
            self.db, self.provider, self.task_manager, demo_mode=self.demo_mode,
        )
        resource_payload = ResourceGenerateRequest(
            user_id=payload.user_id,
            course_name=payload.course_name,
            weak_point=payload.weak_point,
            resource_type_list=["quiz"],
        )
        accepted = resource_svc.submit(
            resource_payload,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
        )
        return QuizTaskAcceptedData(
            task_id=accepted.task_id,
            status=accepted.status,
        )
