import importlib
import json


def test_course_base_returns_only_indexed_documents(client, settings):
    course = settings.course_root / "ros2"
    chapter = course / "01-basics"
    chapter.mkdir(parents=True)
    (course / "course.json").write_text(
        json.dumps({"name": "机器人操作系统", "slug": "ros2"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (chapter / "intro.md").write_text("# ROS2 基础", encoding="utf-8")
    module = importlib.import_module("app.services.course_indexer")
    module.CourseIndexer(client.app.state.db).index_root(settings.course_root)

    listing = client.get("/api/course/list")
    response = client.get(
        "/api/course/base", params={"course_name": "机器人操作系统"}
    )

    assert listing.status_code == 200
    assert any(course["slug"] == "ros2" for course in listing.json()["data"])
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_demo"] is False
    document = data["chapters"][0]["documents"][0]
    assert document["filename"] == "intro.md"
    assert "示例正文" not in response.text
    media = client.get(document["media_url"])
    assert media.status_code == 200
    assert media.content == "# ROS2 基础".encode()
    assert client.get("/media/courses/ros2/course.json").status_code == 404


def test_course_base_reports_not_ready_for_demo_catalog(client):
    response = client.get(
        "/api/course/base", params={"course_name": "机器人操作系统（演示）"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "COURSE_NOT_READY"
