from pathlib import Path

from app.core.config import Settings


def test_health_reports_database_and_agent_mode(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "agent_mode": "mock",
    }


def test_settings_resolve_relative_knowledge_base_from_workspace_root():
    settings = Settings(knowledge_base_root=Path("knowledge_base"))

    assert settings.knowledge_base_root == (
        Path(__file__).resolve().parents[2] / "knowledge_base"
    )
