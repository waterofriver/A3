import pytest

from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository


@pytest.fixture
def confirmed_user(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("qa-student")
        ProfileRepository(session).upsert(
            user.id,
            {
                "knowledge_foundation": "入门基础",
                "cognitive_style": "案例驱动",
                "weak_points": ["ROS2 通信"],
                "learning_pace": "分阶段",
                "content_preferences": ["图解", "代码案例"],
                "short_term_goal": "理解发布订阅模型",
            },
            revision=1,
        )
        profile = ProfileRepository(session).confirm(user.id)
        return user, profile


def test_video_qa_stream_uses_profile_without_fabricating_media(
    client, confirmed_user
):
    user, _ = confirmed_user
    with client.stream(
        "POST",
        "/api/chat/qa",
        json={
            "user_id": user.id,
            "question": "请解释 ROS2 发布订阅模型",
            "answer_mode": "video",
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert body.count("event: content.delta") >= 3
    assert "案例驱动" in body
    assert "event: media.ready" in body
    assert '"media_url":null' in body
    assert "event: task.completed" in body


def test_qa_requires_a_confirmed_profile_with_readable_error(client):
    response = client.post(
        "/api/chat/qa",
        json={
            "user_id": "qa-without-profile",
            "question": "请解释发布订阅模型",
            "answer_mode": "text",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "请先确认学生画像后再使用智能答疑。"
