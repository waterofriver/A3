import httpx
from fastapi import Request

from app.agents.base import AgentProvider
from app.agents.mock import MockAgentProvider
from app.agents.remote import FallbackAgentProvider, RemoteAgentProvider
from app.core.config import Settings
from app.core.errors import AppError


def create_agent_provider(
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
    db=None,
) -> AgentProvider:
    if settings.agent_mode == "local":
        from app.agents.real import RealAgentProvider

        return RealAgentProvider(db=db)
    if settings.agent_mode == "mock":
        return MockAgentProvider(settings)
    if not settings.remote_agent_base_url.strip():
        raise AppError(
            status_code=503,
            code="UPSTREAM_NOT_CONFIGURED",
            message="远程 Agent 服务地址尚未配置。",
            retryable=False,
        )
    remote = RemoteAgentProvider(settings, client=client)
    if settings.allow_mock_fallback:
        return FallbackAgentProvider(remote, MockAgentProvider(settings))
    return remote


def get_agent_provider(request: Request) -> AgentProvider:
    provider = request.app.state.agent_provider
    if provider is None:
        provider = create_agent_provider(
            request.app.state.settings,
            db=request.app.state.db,
        )
        request.app.state.agent_provider = provider
    return provider
