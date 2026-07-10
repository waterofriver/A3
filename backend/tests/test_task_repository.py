from app.repositories.profiles import ProfileRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


def test_user_creation_and_task_event_sequence(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("student-001")
        task = TaskRepository(session).create(
            user_id=user.id,
            task_type="profile",
            request_snapshot={"chat_text": "我想学习 ROS2"},
        )
        first = TaskRepository(session).append_event(
            task.id, "task.started", {"progress": 0}
        )
        second = TaskRepository(session).append_event(
            task.id, "content.delta", {"content": "你好"}
        )

        assert first.seq == 1
        assert second.seq == 2
        assert TaskRepository(session).get(task.id).status == "queued"


def test_profile_upsert_reuses_record_and_can_be_confirmed(client):
    db = client.app.state.db
    with db.session() as session:
        UserRepository(session).get_or_create("student-002")
        repository = ProfileRepository(session)
        first = repository.upsert(
            "student-002", {"knowledge_foundation": "待采集"}, revision=1
        )
        second = repository.upsert(
            "student-002", {"knowledge_foundation": "入门基础"}, revision=2
        )
        confirmed = repository.confirm("student-002")

        assert second.id == first.id
        assert confirmed.revision == 2
        assert confirmed.confirmed_at is not None


def test_task_state_update_persists_result_and_agent(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("student-003")
        repository = TaskRepository(session)
        task = repository.create(user.id, "profile", {})
        updated = repository.update_state(
            task.id,
            status="succeeded",
            progress=100,
            current_agent="画像抽取Agent",
            result_snapshot={"revision": 1},
        )

        assert updated.status == "succeeded"
        assert updated.progress == 100
        assert updated.current_agent == "画像抽取Agent"
        assert updated.result_snapshot == {"revision": 1}
