from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse
from app.schemas.task import GatewayError


class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        details: Any | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    response = ErrorResponse(
        error=GatewayError(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            details=error.details,
        ),
        trace_id=request.state.trace_id,
    )
    return JSONResponse(status_code=error.status_code, content=response.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
