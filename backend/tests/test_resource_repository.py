from datetime import datetime, timezone

from app.repositories.learning import LearningRepository
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


def seed_task(session, user_id: str = "student-001"):
    user = UserRepository(session).get_or_create(user_id)
    return TaskRepository(session).create(
        user_id=user.id,
        task_type="resource",
        request_snapshot={"course_name": "机器人操作系统"},
    )


def test_resource_repository_lists_course_history(client):
    db = client.app.state.db
    with db.session() as session:
        task = seed_task(session)
        repository = ResourceRepository(session)
        repository.create(
            resource_id="res-1",
            task_id=task.id,
            user_id="student-001",
            course_name="机器人操作系统",
            resource_type="handout",
            title="ROS2 节点通信讲义",
            payload={"markdown": "# ROS2"},
            media_url=None,
        )

        resources = repository.list_for_course("student-001", "机器人操作系统")
        stored = repository.get("res-1")

    assert [resource.id for resource in resources] == ["res-1"]
    assert resources[0].payload == {"markdown": "# ROS2"}
    assert stored.id == "res-1"


def test_learning_repository_versions_paths_and_records_learning(client):
    db = client.app.state.db
    with db.session() as session:
        task = seed_task(session, "student-002")
        resource = ResourceRepository(session).create(
            resource_id="res-quiz",
            task_id=task.id,
            user_id="student-002",
            course_name="机器人操作系统",
            resource_type="quiz",
            title="ROS2 题库",
            payload={"questions": []},
            media_url=None,
        )
        repository = LearningRepository(session)
        first_path = repository.create_path("student-002", "机器人操作系统")
        second_path = repository.create_path("student-002", "机器人操作系统")
        nodes = repository.replace_nodes(
            second_path.id,
            [
                {
                    "stage_name": "习题训练",
                    "difficulty": "基础",
                    "resource_id": resource.id,
                }
            ],
        )
        first_completion = repository.complete_path_node(nodes[0].id)
        second_completion = repository.complete_path_node(nodes[0].id)
        attempt = repository.record_quiz_attempt(
            user_id="student-002",
            resource_id=resource.id,
            answers={"q1": "B"},
            results=[{"question_id": "q1", "correct": True}],
            score=100,
        )
        started_at = datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc)
        event = repository.record_learning_event(
            user_id="student-002",
            course_name="机器人操作系统",
            event_type="resource_opened",
            resource_id=resource.id,
            path_node_id=nodes[0].id,
            client_started_at=started_at,
            client_ended_at=None,
            duration_seconds=0,
            event_metadata={"source": "test"},
        )

    assert first_path.version == 1
    assert first_path.status == "superseded"
    assert second_path.version == 2
    assert nodes[0].position == 0
    assert first_completion.completed_at == second_completion.completed_at
    assert attempt.score == 100
    assert event.event_metadata == {"source": "test"}
