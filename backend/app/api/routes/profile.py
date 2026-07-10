from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.core.errors import AppError
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas.profile import (
    ProfileChatRequest,
    ProfileConfirmRequest,
    StudentProfileData,
    UserInfoData,
    UserInfoResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter(tags=["profile"])


@router.post("/api/chat/profile")
def chat_profile(
    payload: ProfileChatRequest,
    request: Request,
    provider: AgentProvider = Depends(get_agent_provider),
) -> StreamingResponse:
    service = ProfileService(request.app.state.db, provider)
    task_id = service.create_task(payload.user_id, payload.chat_text)
    stream = service.stream_profile(
        task_id=task_id,
        trace_id=request.state.trace_id,
        user_id=payload.user_id,
        chat_text=payload.chat_text,
    )
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "X-Task-ID": task_id,
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/profile/confirm", response_model=UserInfoResponse)
def confirm_profile(
    payload: ProfileConfirmRequest, request: Request
) -> UserInfoResponse:
    with request.app.state.db.session() as session:
        try:
            profile = ProfileRepository(session).confirm(payload.user_id)
        except LookupError as error:
            raise AppError(
                status_code=400,
                code="VALIDATION_ERROR",
                message="尚未采集学生画像，无法确认。",
                retryable=False,
            ) from error
        user = UserRepository(session).get(payload.user_id)
        data = UserInfoData(
            exists=True,
            user_id=payload.user_id,
            display_name=user.display_name if user else None,
            profile=StudentProfileData.model_validate(profile.profile_data),
            profile_confirmed=True,
        )
    return UserInfoResponse(data=data, trace_id=request.state.trace_id)
