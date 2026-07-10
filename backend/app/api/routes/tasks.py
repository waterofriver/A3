from fastapi import APIRouter, Request

from app.core.errors import AppError
from app.repositories.tasks import TaskRepository

router = APIRouter(prefix="/api/task", tags=["tasks"])


@router.get("/{task_id}")
def get_task(task_id: str, request: Request) -> dict:
    with request.app.state.db.session() as session:
        try:
            task = TaskRepository(session).get(task_id)
        except LookupError as error:
            raise AppError(
                status_code=404,
                code="TASK_NOT_FOUND",
                message="任务不存在或已被清理。",
                retryable=False,
            ) from error

        data = {
            "task_id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "current_agent": task.current_agent,
            "result": task.result_snapshot,
            "error": task.error,
        }
    return {"data": data, "trace_id": request.state.trace_id}
