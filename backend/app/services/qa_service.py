from collections.abc import AsyncIterator

from app.agents.base import AgentProvider
from app.core.errors import AppError
from app.db.database import Database
from app.repositories.learning import LearningRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.profile import StudentProfileData
from app.schemas.qa import QaRequest
from app.schemas.task import GatewayError, GatewayEvent
from app.services.profile_service import encode_sse


class QaService:
    def __init__(self, db: Database, provider: AgentProvider):
        self.db = db
        self.provider = provider

    def create_task(self, payload: QaRequest) -> tuple[str, StudentProfileData]:
        with self.db.session() as session:
            user = UserRepository(session).get_or_create(payload.user_id)
            profile_record = ProfileRepository(session).get(user.id)
            if profile_record is None or profile_record.confirmed_at is None:
                raise AppError(
                    status_code=400,
                    code="VALIDATION_ERROR",
                    message="请先确认学生画像后再使用智能答疑。",
                    retryable=False,
                )
            profile = StudentProfileData.model_validate(profile_record.profile_data)
            task = TaskRepository(session).create(
                user_id=user.id,
                task_type="qa",
                request_snapshot=payload.model_dump(mode="json"),
            )
            LearningRepository(session).record_learning_event(
                user_id=user.id,
                course_name="全局答疑",
                event_type="question_asked",
                resource_id=None,
                path_node_id=None,
                client_started_at=None,
                client_ended_at=None,
                duration_seconds=0,
                event_metadata={"question": payload.question},
            )
            return task.id, profile

    async def stream(
        self,
        *,
        task_id: str,
        trace_id: str,
        payload: QaRequest,
        profile: StudentProfileData,
    ) -> AsyncIterator[str]:
        try:
            async for event in self.provider.stream_qa(
                task_id=task_id,
                trace_id=trace_id,
                user_id=payload.user_id,
                question=payload.question,
                answer_mode=payload.answer_mode,
                profile=profile,
            ):
                self._persist(event)
                yield encode_sse(event)
        except Exception as error:
            failed = GatewayEvent(
                event="task.failed",
                task_id=task_id,
                trace_id=trace_id,
                current_agent="智能答疑Agent",
                progress=0,
                finish_flag=True,
                error=GatewayError(
                    code="QA_GENERATION_FAILED",
                    message=f"答疑生成失败：{error}",
                    retryable=True,
                ),
            )
            self._persist(failed)
            yield encode_sse(failed)

    def _persist(self, event: GatewayEvent) -> None:
        with self.db.session() as session:
            repository = TaskRepository(session)
            stored = repository.append_event(
                event.task_id, event.event, event.model_dump(mode="json")
            )
            event.seq = stored.seq
            stored.payload = event.model_dump(mode="json")
            status = (
                "succeeded"
                if event.event == "task.completed"
                else "failed"
                if event.event == "task.failed"
                else "running"
            )
            repository.update_state(
                event.task_id,
                status=status,
                progress=event.progress,
                current_agent=event.current_agent,
                result_snapshot={"answer_complete": True}
                if event.event == "task.completed"
                else None,
                error=event.error.model_dump() if event.error else None,
            )
