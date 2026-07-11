def test_evaluation_uses_quiz_and_learning_records(client, evaluation_records):
    response = client.get(
        "/api/eval/report",
        params={
            "user_id": evaluation_records["user_id"],
            "course_name": evaluation_records["course_name"],
        },
    )

    assert response.status_code == 200
    report = response.json()["data"]
    assert report["theory_score"] == 80
    assert report["practice_score"] == 50
    assert report["weak_points"][0] == {
        "name": "ROS2 服务通信",
        "frequency": 2,
    }
    assert report["recommended_changes"]
    assert report["source_path_id"] == evaluation_records["source_path_id"]
    assert report["applied_path_id"] is None


def test_evaluation_rejects_missing_evidence(client):
    response = client.get(
        "/api/eval/report",
        params={"user_id": "no-evidence", "course_name": "机器人操作系统"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EVALUATION_NOT_READY"
