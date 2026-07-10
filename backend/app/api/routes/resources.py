from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import StreamingResponse

from app.core.errors import AppError
from app.repositories.tasks import TaskRepository
from app.services.task_event_stream import stream_persisted_task_events

router = APIRouter(prefix="/api/resource", tags=["resources"])


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
