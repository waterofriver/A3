def test_profile_stream_persists_profile_and_can_be_confirmed(client):
    with client.stream(
        "POST",
        "/api/chat/profile",
        json={"user_id": "student-001", "chat_text": "我想加强 ROS2 通信"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-task-id"]
    assert "event: profile.patch" in body
    assert "event: task.completed" in body
    assert '"seq":5' in body
    assert '"seq":6' in body

    info = client.get("/api/user/info", params={"user_id": "student-001"})
    profile = info.json()["data"]["profile"]
    assert set(profile) == {
        "knowledge_foundation",
        "cognitive_style",
        "weak_points",
        "learning_pace",
        "content_preferences",
        "short_term_goal",
    }
    assert info.json()["data"]["profile_confirmed"] is False

    confirm = client.post("/api/profile/confirm", json={"user_id": "student-001"})
    assert confirm.status_code == 200
    assert confirm.json()["data"]["profile_confirmed"] is True
