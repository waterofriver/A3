def test_unknown_user_returns_exists_false(client):
    response = client.get("/api/user/info", params={"user_id": "new-student"})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "exists": False,
        "user_id": "new-student",
        "display_name": None,
        "profile": None,
        "profile_confirmed": False,
    }


def test_confirm_without_profile_returns_validation_error(client):
    response = client.post(
        "/api/profile/confirm", json={"user_id": "missing-profile"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
