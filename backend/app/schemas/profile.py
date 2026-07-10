from pydantic import BaseModel, Field


class StudentProfileData(BaseModel):
    knowledge_foundation: str = "待采集"
    cognitive_style: str = "待采集"
    weak_points: list[str] = Field(default_factory=list)
    learning_pace: str = "待采集"
    content_preferences: list[str] = Field(default_factory=list)
    short_term_goal: str = "待采集"


class ProfileChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    chat_text: str = Field(min_length=1, max_length=4000)


class ProfileConfirmRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)


class UserInfoData(BaseModel):
    exists: bool
    user_id: str
    display_name: str | None = None
    profile: StudentProfileData | None = None
    profile_confirmed: bool = False


class UserInfoResponse(BaseModel):
    data: UserInfoData
    trace_id: str
