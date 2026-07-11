from uuid import uuid4

from pydantic import TypeAdapter

from app.agents.base import AgentProvider, ResourceDraft
from app.core.errors import AppError
from app.db.database import Database
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.resource import (
    ResourceDetail,
    ResourceGenerateRequest,
    ResourceSummary,
    ResourceType,
    TaskAcceptedData,
)
from app.schemas.task import GatewayEvent
from app.tasks.manager import TaskManager
from app.services.agent_errors import gateway_error_from_exception

resource_detail_adapter = TypeAdapter(ResourceDetail)


def resource_to_detail(resource) -> ResourceDetail:
    return resource_detail_adapter.validate_python(
        {
            "id": resource.id,
            "task_id": resource.task_id,
            "course_name": resource.course_name,
            "resource_type": resource.resource_type,
            "title": resource.title,
            "payload": resource.payload,
            "media_url": resource.media_url,
            "created_at": resource.created_at,
        }
    )


class ResourceService:
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

    def submit(
        self,
        payload: ResourceGenerateRequest,
        *,
        idempotency_key: str | None,
        trace_id: str,
    ) -> TaskAcceptedData:
        with self.db.session() as session:
            user = UserRepository(session).get_or_create(payload.user_id)
            repository = TaskRepository(session)
            if idempotency_key:
                existing = repository.find_idempotent(user.id, idempotency_key)
                if existing is not None:
                    return TaskAcceptedData(
                        task_id=existing.id,
                        status=existing.status,
                        deduplicated=True,
                        retry_of_task_id=existing.request_snapshot.get(
                            "retry_of_task_id"
                        ),
                    )
            task = repository.create(
                user_id=user.id,
                task_type="resource",
                request_snapshot=payload.model_dump(mode="json"),
                idempotency_key=idempotency_key,
            )
            task_id = task.id

        self.task_manager.start(
            task_id,
            self.run(task_id=task_id, trace_id=trace_id, payload=payload),
        )
        return TaskAcceptedData(task_id=task_id)

    def retry(self, task_id: str, *, trace_id: str) -> TaskAcceptedData:
        with self.db.session() as session:
            repository = TaskRepository(session)
            try:
                source = repository.get(task_id)
            except LookupError as error:
                raise AppError(
                    status_code=404,
                    code="TASK_NOT_FOUND",
                    message="任务不存在或已被清理。",
                    retryable=False,
                ) from error
            if (
                source.task_type != "resource"
                or source.status not in {"failed", "partial_success"}
                or not (source.error or {}).get("retryable")
            ):
                raise AppError(
                    status_code=400,
                    code="VALIDATION_ERROR",
                    message="当前任务不支持重试。",
                    retryable=False,
                )

            snapshot = dict(source.request_snapshot)
            snapshot["retry_of_task_id"] = source.id
            payload = ResourceGenerateRequest.model_validate(snapshot)
            retried = repository.create(
                user_id=source.user_id,
                task_type="resource",
                request_snapshot=snapshot,
            )
            retried_id = retried.id

        self.task_manager.start(
            retried_id,
            self.run(task_id=retried_id, trace_id=trace_id, payload=payload),
        )
        return TaskAcceptedData(
            task_id=retried_id,
            retry_of_task_id=task_id,
        )

    def list_for_course(self, user_id: str, course_name: str) -> list[ResourceSummary]:
        with self.db.session() as session:
            resources = ResourceRepository(session).list_for_course(
                user_id, course_name
            )
            return [ResourceSummary.model_validate(resource) for resource in resources]

    def get_detail(self, resource_id: str) -> ResourceDetail:
        with self.db.session() as session:
            try:
                resource = ResourceRepository(session).get(resource_id)
            except LookupError as error:
                raise AppError(
                    status_code=404,
                    code="RESOURCE_NOT_FOUND",
                    message="学习资源不存在或已被清理。",
                    retryable=False,
                ) from error
            return resource_to_detail(resource)

    async def run(
        self,
        *,
        task_id: str,
        trace_id: str,
        payload: ResourceGenerateRequest,
    ) -> None:
        resource_ids: list[str] = []
        current_agent = "主管Agent"
        current_resource_type: ResourceType | None = None
        demo_mode = self.demo_mode
        try:
            self._persist_event(
                GatewayEvent(
                    event="task.started",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=0,
                    demo_mode=self.demo_mode,
                )
            )
            async for internal in self.provider.stream_resources(
                task_id=task_id,
                trace_id=trace_id,
                user_id=payload.user_id,
                course_name=payload.course_name,
                weak_point=payload.weak_point,
                resource_types=payload.resource_type_list,
            ):
                current_agent = internal.current_agent
                current_resource_type = internal.resource_type
                demo_mode = demo_mode or internal.demo_mode
                resource_id = None
                draft = internal.resource
                if internal.event == "resource.ready":
                    if draft is None:
                        raise ValueError("resource.ready event is missing its draft")
                    resource_id = str(uuid4())
                    resource_detail_adapter.validate_python(
                        {
                            "id": resource_id,
                            "resource_type": draft.resource_type,
                            "title": draft.title,
                            "payload": draft.payload,
                            "media_url": draft.media_url,
                        }
                    )
                    resource_ids.append(resource_id)

                gateway = GatewayEvent(
                    event=internal.event,
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=internal.current_agent,
                    progress=internal.progress,
                    resource_type=internal.resource_type,
                    content=internal.content,
                    media_url=draft.media_url if draft else None,
                    resource_ids=[resource_id] if resource_id else [],
                    demo_mode=demo_mode,
                )
                self._persist_event(
                    gateway,
                    draft=draft if resource_id else None,
                    resource_id=resource_id,
                    request=payload,
                )

            self._persist_event(
                GatewayEvent(
                    event="task.completed",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=100,
                    finish_flag=True,
                    resource_ids=resource_ids,
                    demo_mode=demo_mode,
                ),
                status="succeeded",
                result_snapshot={
                    "course_name": payload.course_name,
                    "resource_ids": resource_ids,
                },
            )
        except Exception as error:
            gateway_error = gateway_error_from_exception(
                error,
                default_code="RESOURCE_GENERATION_FAILED",
                default_prefix="资源生成失败",
            )
            failed_status = "partial_success" if resource_ids else "failed"
            self._persist_event(
                GatewayEvent(
                    event="task.failed",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=0,
                    resource_type=current_resource_type,
                    finish_flag=True,
                    resource_ids=resource_ids,
                    error=gateway_error,
                    demo_mode=demo_mode,
                ),
                status=failed_status,
                result_snapshot={"resource_ids": resource_ids},
            )

    def _persist_event(
        self,
        event: GatewayEvent,
        *,
        draft: ResourceDraft | None = None,
        resource_id: str | None = None,
        request: ResourceGenerateRequest | None = None,
        status: str = "running",
        result_snapshot: dict | None = None,
    ) -> None:
        with self.db.session() as session:
            if draft is not None and resource_id is not None and request is not None:
                ResourceRepository(session).create(
                    resource_id=resource_id,
                    task_id=event.task_id,
                    user_id=request.user_id,
                    course_name=request.course_name,
                    resource_type=draft.resource_type,
                    title=draft.title,
                    payload=draft.payload,
                    media_url=draft.media_url,
                )

            repository = TaskRepository(session)
            stored = repository.append_event(
                event.task_id,
                event.event,
                event.model_dump(mode="json"),
            )
            event.seq = stored.seq
            stored.payload = event.model_dump(mode="json")
            repository.update_state(
                event.task_id,
                status=status,
                progress=event.progress,
                current_agent=event.current_agent,
                result_snapshot=result_snapshot,
                error=event.error.model_dump() if event.error else None,
            )
