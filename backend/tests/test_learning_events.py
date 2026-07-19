import pytest

from app.repositories.learning import LearningRepository
from app.repositories.users import UserRepository


@pytest.fixture
def seeded_path_node(client):
    db = client.app.state.db
    with db.session() as session:
        UserRepository(session).get_or_create("event-student")
        repository = LearningRepository(session)
        path = repository.create_path("event-student", "机器人操作系统")
        return repository.replace_nodes(
            path.id,
            [
                {
                    "stage_name": "基础补全",
                    "difficulty": "基础",
                    "resource_id": None,
                }
            ],
        )[0]


def test_learning_events_complete_path_nodes_idempotently(client, seeded_path_node):
    payload = {
        "user_id": "event-student",
        "course_name": "机器人操作系统",
        "events": [
            {
                "event_type": "path_node_completed",
                "path_node_id": seeded_path_node.id,
                "client_started_at": "2026-07-10T08:00:00Z",
                "client_ended_at": "2026-07-10T08:10:00Z",
                "metadata": {},
            }
        ],
    }

    first = client.post("/api/learning/events", json=payload)
    second = client.post("/api/learning/events", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["accepted"] == 1
    assert second.json()["data"]["accepted"] == 1


def test_learning_events_reset_completed_path_nodes(client, seeded_path_node):
    complete = client.post(
        "/api/learning/events",
        json={
            "user_id": "event-student",
            "course_name": "机器人操作系统",
            "events": [
                {
                    "event_type": "path_node_completed",
                    "path_node_id": seeded_path_node.id,
                    "metadata": {},
                }
            ],
        },
    )
    reset = client.post(
        "/api/learning/events",
        json={
            "user_id": "event-student",
            "course_name": "机器人操作系统",
            "events": [
                {
                    "event_type": "path_node_reset",
                    "path_node_id": seeded_path_node.id,
                    "metadata": {},
                }
            ],
        },
    )

    assert complete.status_code == 200
    assert reset.status_code == 200
    with client.app.state.db.session() as session:
        node = LearningRepository(session).list_path_nodes(seeded_path_node.path_id)[0]
        assert node.completed_at is None


def test_learning_events_reject_end_before_start(client):
    response = client.post(
        "/api/learning/events",
        json={
            "user_id": "event-student",
            "course_name": "机器人操作系统",
            "events": [
                {
                    "event_type": "resource_closed",
                    "client_started_at": "2026-07-10T09:00:00Z",
                    "client_ended_at": "2026-07-10T08:00:00Z",
                    "metadata": {},
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
