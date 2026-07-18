from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.repositories.learning import LearningRepository
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.memory import CurvePoint, MemoryAction, MemoryKnowledgePoint, MemoryReportData


def _record_attempt(client, user_id, course_name, title, scores, timestamps=None):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create(user_id)
        task = TaskRepository(session).create(
            user_id=user.id, task_type="resource", request_snapshot={"course_name": course_name}
        )
        resource_id = str(uuid4())
        ResourceRepository(session).create(
            resource_id=resource_id, task_id=task.id, user_id=user.id,
            course_name=course_name, resource_type="quiz", title=title,
            payload={"questions": []}, media_url=None,
        )
        learning = LearningRepository(session)
        attempts = [learning.record_quiz_attempt(
            user_id=user.id, resource_id=resource_id, answers={}, results=[], score=score
        ) for score in scores]
        for attempt, timestamp in zip(attempts, timestamps or []):
            attempt.created_at = timestamp
        return attempts


def test_memory_report_returns_explainable_snapshot_for_unknown_user(client):
    response = client.get(
        "/api/memory/report",
        params={"user_id": "demo-memory-user", "course_name": "机器人与安全"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"]
    assert 0 <= payload["data"]["memory_health"] <= 100
    assert payload["data"]["knowledge_points"]
    assert len(payload["data"]["today_actions"]) <= 3
    assert payload["data"]["has_personal_evidence"] is False
    assert "暂无个人学习记录" in payload["data"]["summary"]
    assert all("起步建议" in action["reason"] for action in payload["data"]["today_actions"])


def test_memory_report_keeps_curve_and_action_contract(client):
    response = client.get(
        "/api/memory/report",
        params={"user_id": "demo-memory-user", "course_name": "机器人与安全"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    point = data["knowledge_points"][0]
    assert [item["day"] for item in point["curve"]] == [0, 1, 3, 7]
    assert all(0 <= item["retention"] <= 100 for item in point["curve"])
    assert point["risk_level"] in {"stable", "review_soon", "urgent"}
    assert data["today_actions"]
    assert all(1 <= action["minutes"] <= 30 for action in data["today_actions"])
    assert all(action["action_type"] in {"recall", "quiz", "practice"} for action in data["today_actions"])


def test_unmapped_quiz_attempt_does_not_change_first_knowledge_point(client):
    user_id = "unmapped-quiz-user"
    course_name = "机器人与安全"
    before = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()
    baseline = before["data"]["knowledge_points"][0]["base_mastery"]

    _record_attempt(client, user_id, course_name, "未标注知识点的综合测验", [10])
    after = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()

    assert after["data"]["knowledge_points"][0]["base_mastery"] == baseline
    assert after["data"]["has_personal_evidence"] is False
    assert "暂无个人学习记录" in after["data"]["summary"]


def test_stable_prerequisite_is_not_reported_as_root_blockage(client):
    user_id = "blockage-user"
    course_name = "机器人与安全"
    initial = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]
    prerequisite, target = initial["knowledge_points"][:2]
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create(user_id)
        learning = LearningRepository(session)
        path = learning.create_path(user.id, course_name)
        node = learning.replace_nodes(path.id, [{
            "stage_name": prerequisite["name"], "difficulty": "基础", "resource_id": None
        }])[0]
        learning.complete_path_node(node.id)
    _record_attempt(client, user_id, course_name, target["name"], [20])

    report = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]
    target_after = next(point for point in report["knowledge_points"] if point["id"] == target["id"])
    assert target_after["risk_level"] == "urgent"
    assert target_after["blockage"] is None


def test_latest_low_score_triggers_urgent_risk_even_when_inserted_before_older_score(client):
    user_id = "ordered-score-user"
    course_name = "机器人与安全"
    point = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]["knowledge_points"][0]
    now = datetime.now(timezone.utc)
    _record_attempt(
        client, user_id, course_name, point["name"], [20, 95],
        timestamps=[now, now - timedelta(days=2)],
    )

    report = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]
    updated = next(item for item in report["knowledge_points"] if item["id"] == point["id"])
    assert updated["risk_level"] == "urgent"


def test_blockage_selects_the_weakest_of_multiple_prerequisites(client):
    user_id = "multiple-prerequisite-user"
    course_name = "机器人与安全"
    points = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]["knowledge_points"]
    by_id = {point["id"]: point for point in points}
    first = by_id["exp04_line_following"]
    second = by_id["exp10_brute_force_attack"]
    target = by_id["exp11_multi_robot_formation"]
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create(user_id)
        learning = LearningRepository(session)
        path = learning.create_path(user.id, course_name)
        node = learning.replace_nodes(path.id, [{
            "stage_name": first["name"], "difficulty": "基础", "resource_id": None
        }])[0]
        learning.complete_path_node(node.id)
    _record_attempt(client, user_id, course_name, second["name"], [20])
    _record_attempt(client, user_id, course_name, target["name"], [20])

    report = client.get("/api/memory/report", params={"user_id": user_id, "course_name": course_name}).json()["data"]
    target_after = next(point for point in report["knowledge_points"] if point["id"] == target["id"])
    assert target_after["blockage"]["knowledge_point_id"] == second["id"]


def test_memory_schema_rejects_unfixed_curve_days_and_more_than_three_actions():
    with pytest.raises(ValidationError):
        MemoryKnowledgePoint(
            id="kp", name="知识点", retention=80, base_mastery=80, days_since_review=0,
            risk_level="stable", curve=[CurvePoint(day=0, retention=80)] * 4,
            recommendation="建议回顾。",
        )
    point = MemoryKnowledgePoint(
        id="kp", name="知识点", retention=80, base_mastery=80, days_since_review=0,
        risk_level="stable", curve=[CurvePoint(day=0, retention=80), CurvePoint(day=1, retention=75), CurvePoint(day=3, retention=65), CurvePoint(day=7, retention=50)],
        recommendation="建议回顾。",
    )
    action = MemoryAction(
        knowledge_point_id="kp", title="复习", minutes=5, action_type="recall", reason="起步建议"
    )
    with pytest.raises(ValidationError):
        MemoryReportData(
            memory_health=80, summary="摘要", knowledge_points=[point], today_actions=[action] * 4
        )
