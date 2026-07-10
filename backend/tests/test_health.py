def test_health_reports_database_and_agent_mode(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "agent_mode": "mock",
    }
