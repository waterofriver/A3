def test_mock_mode_lists_an_explicit_demo_course(client):
    response = client.get("/api/course/list")

    assert response.status_code == 200
    assert response.json()["data"] == [
        {
            "name": "机器人操作系统（演示）",
            "slug": "robotics-demo",
            "content_ready": False,
            "is_demo": True,
        }
    ]
