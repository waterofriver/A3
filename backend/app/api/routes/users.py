from fastapi import APIRouter, Query, Request

from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas.profile import StudentProfileData, UserInfoData, UserInfoResponse

router = APIRouter(prefix="/api/user", tags=["users"])


@router.get("/info", response_model=UserInfoResponse)
def get_user_info(
    request: Request,
    user_id: str = Query(min_length=1, max_length=64),
) -> UserInfoResponse:
    with request.app.state.db.session() as session:
        user = UserRepository(session).get(user_id)
        if user is None:
            data = UserInfoData(exists=False, user_id=user_id)
        else:
            profile_record = ProfileRepository(session).get(user_id)
            data = UserInfoData(
                exists=True,
                user_id=user.id,
                display_name=user.display_name,
                profile=StudentProfileData.model_validate(profile_record.profile_data)
                if profile_record
                else None,
                profile_confirmed=bool(
                    profile_record and profile_record.confirmed_at is not None
                ),
            )
    return UserInfoResponse(data=data, trace_id=request.state.trace_id)
