from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.schemas.qa import QaRequest
from app.services.qa_service import QaService

router = APIRouter(tags=["qa"])


@router.post("/api/chat/qa")
def chat_qa(
    payload: QaRequest,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> StreamingResponse:
    service = QaService(request.app.state.db, provider)
    task_id, profile = service.create_task(payload)
    return StreamingResponse(
        service.stream(
            task_id=task_id,
            trace_id=request.state.trace_id,
            payload=payload,
            profile=profile,
        ),
        media_type="text/event-stream",
        headers={
            "X-Task-ID": task_id,
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
