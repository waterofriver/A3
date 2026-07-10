from fastapi import Request

from app.agents.base import AgentProvider
from app.core.errors import AppError


def get_agent_provider(request: Request) -> AgentProvider:
    provider = request.app.state.agent_provider
    if provider is None:
        raise AppError(
            status_code=503,
            code="UPSTREAM_REJECTED",
            message="远程智能体服务尚未配置。",
            retryable=False,
        )
    return provider
