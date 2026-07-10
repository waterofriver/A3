import pytest

from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.task import GatewayEvent


@pytest.fixture
def seeded_resource_task(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("resource-sse-student")
        repository = TaskRepository(session)
        task = repository.create(
            user_id=user.id,
            task_type="resource",
            request_snapshot={"course_name": "机器人操作系统"},
        )
        for seq, event_type in enumerate(
            ["task.started", "task.progress", "task.completed"], start=1
        ):
            event = GatewayEvent(
                event=event_type,
                task_id=task.id,
                seq=seq,
                trace_id="trace-sse",
                progress=100 if event_type == "task.completed" else seq * 20,
                finish_flag=event_type == "task.completed",
                demo_mode=True,
            )
            repository.append_event(task.id, event_type, event.model_dump(mode="json"))
        repository.update_state(task.id, status="succeeded", progress=100)
        return task


def test_resource_sse_replays_events_after_last_event_id(
    client, seeded_resource_task
):
    response = client.get(
        f"/api/resource/progress/{seeded_resource_task.id}",
        headers={"Last-Event-ID": "2"},
    )

    assert response.status_code == 200
    assert "id: 1\n" not in response.text
    assert "id: 2\n" not in response.text
    assert "id: 3\n" in response.text
    assert "event: task.completed" in response.text


def test_resource_sse_supports_after_seq_query(client, seeded_resource_task):
    response = client.get(
        f"/api/resource/progress/{seeded_resource_task.id}?after_seq=1"
    )

    assert "id: 1\n" not in response.text
    assert "id: 2\n" in response.text
    assert "id: 3\n" in response.text
