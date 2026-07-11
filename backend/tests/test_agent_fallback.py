import importlib

import httpx
import pytest

from app.core.errors import AppError


def failing_client() -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("upstream timed out", request=request)

    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agents.example"
    )


@pytest.mark.asyncio
async def test_remote_timeout_never_silently_falls_back(settings):
    module = importlib.import_module("app.agents.remote")
    dependency = importlib.import_module("app.api.dependencies")
    remote = settings.model_copy(
        update={
            "agent_mode": "remote",
            "remote_agent_base_url": "https://agents.example",
            "allow_mock_fallback": False,
        }
    )
    async with failing_client() as client:
        provider = dependency.create_agent_provider(remote, client=client)
        with pytest.raises(AppError) as captured:
            _ = [
                event
                async for event in provider.stream_profile(
                    task_id="task-1",
                    trace_id="trace-1",
                    user_id="student-001",
                    chat_text="我想加强 ROS2 通信",
                    current_profile=None,
                )
            ]

    assert isinstance(provider, module.RemoteAgentProvider)
    assert captured.value.code == "UPSTREAM_TIMEOUT"
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_explicit_fallback_marks_mock_events_as_demo(settings):
    dependency = importlib.import_module("app.api.dependencies")
    remote = settings.model_copy(
        update={
            "agent_mode": "remote",
            "remote_agent_base_url": "https://agents.example",
            "allow_mock_fallback": True,
        }
    )
    async with failing_client() as client:
        provider = dependency.create_agent_provider(remote, client=client)
        events = [
            event
            async for event in provider.stream_profile(
                task_id="task-1",
                trace_id="trace-1",
                user_id="student-001",
                chat_text="我想加强 ROS2 通信",
                current_profile=None,
            )
        ]

    assert events
    assert all(event.demo_mode is True for event in events)


def test_remote_mode_requires_an_explicit_base_url(settings):
    dependency = importlib.import_module("app.api.dependencies")
    remote = settings.model_copy(
        update={"agent_mode": "remote", "remote_agent_base_url": ""}
    )

    with pytest.raises(AppError) as captured:
        dependency.create_agent_provider(remote)

    assert captured.value.code == "UPSTREAM_NOT_CONFIGURED"
