from app.agents.mock import MockAgentProvider
from app.api.dependencies import create_agent_provider
from app.core.config import Settings


def test_mock_mode_does_not_require_local_agent_dependencies():
    provider = create_agent_provider(Settings(agent_mode="mock"))

    assert isinstance(provider, MockAgentProvider)
