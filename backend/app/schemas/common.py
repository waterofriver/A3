from typing import Any

from pydantic import BaseModel

from app.schemas.task import GatewayError


class DataResponse(BaseModel):
    data: Any
    trace_id: str


class ErrorResponse(BaseModel):
    error: GatewayError
    trace_id: str
