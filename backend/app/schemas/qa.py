from typing import Literal

from pydantic import BaseModel, Field

AnswerMode = Literal["text", "image", "video"]


class QaRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=4000)
    answer_mode: AnswerMode = "text"
