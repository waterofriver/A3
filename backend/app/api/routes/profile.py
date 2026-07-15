from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.base import AgentProvider
from app.api.dependencies import get_agent_provider
from app.core.errors import AppError
from app.db.models import ProfileMessage
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas.profile import (
    ProfileChatRequest,
    ProfileConfirmRequest,
    StudentProfileData,
    UserInfoData,
    UserInfoResponse,
)
from app.schemas.task import GatewayEvent
from app.services.profile_service import ProfileService

router = APIRouter(tags=["profile"])


class ProfileMessageData(BaseModel):
    id: str
    role: str
    content: str


class ProfileHistoryData(BaseModel):
    messages: list[ProfileMessageData]


class ProfileHistoryResponse(BaseModel):
    data: ProfileHistoryData
    trace_id: str


@router.get("/api/chat/profile/history", response_model=ProfileHistoryResponse)
def get_profile_history(
    user_id: str = Query(min_length=1, max_length=64),
    request: Request = None,  # type: ignore
) -> ProfileHistoryResponse:
    """获取用户的历史对话消息。"""
    with request.app.state.db.session() as session:
        rows = (
            session.query(ProfileMessage)
            .filter(ProfileMessage.user_id == user_id)
            .order_by(ProfileMessage.created_at)
            .all()
        )
        messages = [
            ProfileMessageData(id=row.id, role=row.role, content=row.content)
            for row in rows
        ]
    return ProfileHistoryResponse(
        data=ProfileHistoryData(messages=messages),
        trace_id=request.state.trace_id,
    )


@router.post(
    "/api/chat/profile",
    responses={
        200: {
            "model": GatewayEvent,
            "description": "GatewayEvent SSE 流",
            "content": {"text/event-stream": {}},
        }
    },
)
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
