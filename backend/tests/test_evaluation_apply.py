from sqlalchemy import func, select

from app.db.models import LearningPath


def test_applying_a_report_twice_creates_one_new_path(client, evaluation_records):
    report_response = client.get(
        "/api/eval/report",
        params={
            "user_id": evaluation_records["user_id"],
            "course_name": evaluation_records["course_name"],
        },
    )
    report_id = report_response.json()["data"]["id"]

    first = client.post("/api/eval/apply", json={"report_id": report_id})
    second = client.post("/api/eval/apply", json={"report_id": report_id})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert first.json()["data"]["version"] == 2
    assert any(
        node["stage_name"].endswith("专项练习")
        for node in first.json()["data"]["nodes"]
    )

    from app.db.models import EvaluationReport

    with client.app.state.db.session() as session:
        assert session.scalar(select(func.count(LearningPath.id))) == 2
        assert (
            session.scalar(
                select(func.count(LearningPath.id)).where(
                    LearningPath.status == "active"
                )
            )
            == 1
        )
        report = session.get(EvaluationReport, report_id)
        assert report is not None
        assert report.applied_path_id == first.json()["data"]["id"]
