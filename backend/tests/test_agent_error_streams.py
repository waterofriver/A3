from app.agents.mock import MockAgentProvider
from app.core.errors import AppError
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository


class TimeoutProvider(MockAgentProvider):
    @staticmethod
    def _timeout():
        return AppError(
            status_code=503,
            code="UPSTREAM_TIMEOUT",
            message="远程 Agent 服务响应超时。",
            retryable=True,
        )

    async def stream_profile(self, **kwargs):
        raise self._timeout()
        yield

    async def stream_qa(self, **kwargs):
        raise self._timeout()
        yield


def test_profile_stream_preserves_structured_agent_failure(client, settings):
    client.app.state.agent_provider = TimeoutProvider(settings)

    with client.stream(
        "POST",
        "/api/chat/profile",
        json={"user_id": "timeout-profile", "chat_text": "学习 ROS2"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: task.failed" in body
    assert '"code":"UPSTREAM_TIMEOUT"' in body
    assert '"retryable":true' in body


def test_qa_stream_preserves_structured_agent_failure(client, settings):
    with client.app.state.db.session() as session:
        user = UserRepository(session).get_or_create("timeout-qa")
        ProfileRepository(session).upsert(
            user.id,
            {
                "knowledge_foundation": "入门基础",
                "cognitive_style": "案例驱动",
                "weak_points": ["ROS2 通信"],
                "learning_pace": "分阶段",
                "content_preferences": ["代码案例"],
                "short_term_goal": "完成通信强化",
            },
            revision=1,
        )
        ProfileRepository(session).confirm(user.id)
    client.app.state.agent_provider = TimeoutProvider(settings)

    with client.stream(
        "POST",
        "/api/chat/qa",
        json={
            "user_id": "timeout-qa",
            "question": "什么是发布订阅？",
            "answer_mode": "text",
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: task.failed" in body
    assert '"code":"UPSTREAM_TIMEOUT"' in body
    assert '"retryable":true' in body
