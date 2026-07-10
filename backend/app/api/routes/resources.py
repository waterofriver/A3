from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import StreamingResponse

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.core.errors import AppError
from app.repositories.tasks import TaskRepository
from app.schemas.resource import (
    ResourceDetailResponse,
    ResourceGenerateRequest,
    ResourceListData,
    ResourceListResponse,
    TaskAcceptedResponse,
)
from app.services.resource_service import ResourceService
from app.services.task_event_stream import stream_persisted_task_events

router = APIRouter(prefix="/api/resource", tags=["resources"])


def get_resource_service(request: Request, provider: AgentProvider) -> ResourceService:
    return ResourceService(
        request.app.state.db,
        provider,
        request.app.state.task_manager,
        demo_mode=request.app.state.settings.agent_mode == "mock",
    )


@router.post(
    "/generate",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_resources(
    payload: ResourceGenerateRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    provider: AgentProvider = Depends(get_agent_provider),
) -> TaskAcceptedResponse:
    data = get_resource_service(request, provider).submit(
        payload,
        idempotency_key=idempotency_key,
        trace_id=request.state.trace_id,
    )
    return TaskAcceptedResponse(data=data, trace_id=request.state.trace_id)


@router.get("/list", response_model=ResourceListResponse)
def list_resources(
    user_id: str,
    course_name: str,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> ResourceListResponse:
    resources = get_resource_service(request, provider).list_for_course(
        user_id, course_name
    )
    return ResourceListResponse(
        data=ResourceListData(resources=resources),
        trace_id=request.state.trace_id,
    )


@router.get("/detail/{resource_id}", response_model=ResourceDetailResponse)
def resource_detail(
    resource_id: str,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> ResourceDetailResponse:
    detail = get_resource_service(request, provider).get_detail(resource_id)
    return ResourceDetailResponse(data=detail, trace_id=request.state.trace_id)


@router.get("/progress/{task_id}")
def resource_progress(
    task_id: str,
    request: Request,
    after_seq: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    try:
        header_seq = int(last_event_id) if last_event_id else 0
    except ValueError as error:
        raise AppError(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Last-Event-ID 必须是非负整数。",
            retryable=False,
        ) from error

    with request.app.state.db.session() as session:
        try:
            task = TaskRepository(session).get(task_id)
        except LookupError as error:
            raise AppError(
                status_code=404,
                code="TASK_NOT_FOUND",
                message="资源任务不存在或已被清理。",
                retryable=False,
            ) from error
        if task.task_type != "resource":
            raise AppError(
                status_code=404,
                code="TASK_NOT_FOUND",
                message="资源任务不存在或已被清理。",
                retryable=False,
            )

    settings = request.app.state.settings
    stream = stream_persisted_task_events(
        db=request.app.state.db,
        task_id=task_id,
        after_seq=max(after_seq, header_seq),
        poll_interval_ms=settings.sse_poll_interval_ms,
        heartbeat_seconds=settings.sse_heartbeat_seconds,
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
