from fastapi.testclient import TestClient

from app.main import create_app


def test_cors_allows_a_configured_web_origin(settings):
    configured = settings.model_copy(
        update={"web_origins": "http://127.0.0.1:3000,http://localhost:3000"}
    )

    with TestClient(create_app(configured)) as client:
        response = client.options(
            "/api/user/info?user_id=cors-student",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_cors_does_not_allow_an_unconfigured_origin(settings):
    configured = settings.model_copy(
        update={"web_origins": "http://127.0.0.1:3000"}
    )

    with TestClient(create_app(configured)) as client:
        response = client.options(
            "/api/user/info?user_id=cors-student",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers
