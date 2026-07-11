from app.core.errors import AppError
from app.schemas.task import GatewayError


def gateway_error_from_exception(
    error: Exception,
    *,
    default_code: str,
    default_prefix: str,
) -> GatewayError:
    if isinstance(error, AppError):
        return GatewayError(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            details=error.details,
        )
    return GatewayError(
        code=default_code,
        message=f"{default_prefix}：{error}",
        retryable=True,
    )
