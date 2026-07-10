from fastapi import APIRouter, Depends, Request, status

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.core.errors import AppError
from app.repositories.tasks import TaskRepository
from app.schemas.resource import TaskAcceptedResponse
from app.services.resource_service import ResourceService

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
            "request": task.request_snapshot,
            "result": task.result_snapshot,
            "error": task.error,
        }
    return {"data": data, "trace_id": request.state.trace_id}


@router.post(
    "/{task_id}/retry",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_task(
    task_id: str,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> TaskAcceptedResponse:
    service = ResourceService(
        request.app.state.db,
        provider,
        request.app.state.task_manager,
        demo_mode=request.app.state.settings.agent_mode == "mock",
    )
    data = service.retry(task_id, trace_id=request.state.trace_id)
    return TaskAcceptedResponse(data=data, trace_id=request.state.trace_id)
