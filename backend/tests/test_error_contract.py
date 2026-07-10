import pytest
from pydantic import ValidationError

from app.schemas.task import GatewayEvent


def test_unknown_task_returns_normalized_error(client):
    response = client.get("/api/task/missing")

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == {
        "code": "TASK_NOT_FOUND",
        "message": "任务不存在或已被清理。",
        "retryable": False,
        "details": None,
    }
    assert body["trace_id"]
    assert response.headers["x-trace-id"] == body["trace_id"]


def test_trace_id_header_is_forwarded(client):
    response = client.get(
        "/api/task/missing", headers={"X-Trace-ID": "trace-from-client"}
    )

    assert response.json()["trace_id"] == "trace-from-client"
    assert response.headers["x-trace-id"] == "trace-from-client"


def test_gateway_event_rejects_progress_above_one_hundred():
    with pytest.raises(ValidationError):
        GatewayEvent(
            event="task.progress",
            task_id="task-1",
            trace_id="trace-1",
            progress=101,
        )
