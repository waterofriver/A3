import pytest

from app.repositories.profiles import ProfileRepository
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


@pytest.fixture
def seeded_resource_set(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("path-student")
        ProfileRepository(session).upsert(
            user.id,
            {
                "knowledge_foundation": "入门基础",
                "cognitive_style": "案例驱动",
                "weak_points": ["ROS2 通信"],
                "learning_pace": "分阶段",
                "content_preferences": ["代码案例"],
                "short_term_goal": "完成 ROS2 强化",
            },
            revision=1,
        )
        task = TaskRepository(session).create(user.id, "resource", {})
        repository = ResourceRepository(session)
        for resource_type in ["handout", "mindmap", "quiz", "code", "video"]:
            repository.create(
                resource_id=f"path-{resource_type}",
                task_id=task.id,
                user_id=user.id,
                course_name="机器人操作系统",
                resource_type=resource_type,
                title=f"{resource_type} 资源",
                payload={},
                media_url=None,
            )
    return "path-student"


def test_path_orders_five_stages_and_binds_resources(client, seeded_resource_set):
    response = client.get(
        "/api/path/get",
        params={
            "user_id": seeded_resource_set,
            "course_name": "机器人操作系统",
        },
    )

    assert response.status_code == 200
    nodes = response.json()["data"]["nodes"]
    assert [node["stage_name"] for node in nodes] == [
        "基础补全",
        "知识点学习",
        "习题训练",
        "代码实操",
        "拓展视频",
    ]
    assert all("difficulty" in node for node in nodes)
    assert all(node["resource_id"] for node in nodes)
