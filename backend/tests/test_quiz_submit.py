import pytest

from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


@pytest.fixture
def seeded_quiz_resource(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("quiz-student")
        task = TaskRepository(session).create(user.id, "resource", {})
        return ResourceRepository(session).create(
            resource_id="quiz-resource",
            task_id=task.id,
            user_id=user.id,
            course_name="机器人操作系统",
            resource_type="quiz",
            title="ROS2 演示题库",
            payload={
                "questions": [
                    {
                        "id": "q1",
                        "question_type": "choice",
                        "prompt": "选择正确选项",
                        "options": ["A", "B"],
                        "answer": "B",
                        "explanation": "B 是正确选项。",
                    },
                    {
                        "id": "q2",
                        "question_type": "blank",
                        "prompt": "填写节点名称",
                        "options": [],
                        "answer": "节点",
                        "explanation": "节点是基本运行单元。",
                    },
                ]
            },
            media_url=None,
        )


def test_quiz_submit_returns_per_question_results(client, seeded_quiz_resource):
    response = client.post(
        "/api/quiz/submit",
        json={
            "user_id": "quiz-student",
            "resource_id": seeded_quiz_resource.id,
            "answers": {"q1": "B", "q2": " 节点 "},
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["score"] == 100
    assert all(item["correct"] for item in response.json()["data"]["results"])
