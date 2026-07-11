import time

from app.agents.base import ResourceAgentEvent
from app.agents.mock import MockAgentProvider
from app.core.errors import AppError
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


def generation_payload(user_id: str = "resource-student") -> dict:
    return {
        "user_id": user_id,
        "course_name": "机器人操作系统（演示）",
        "weak_point": "ROS2 通信",
        "resource_type_list": ["handout", "video"],
    }


def wait_for_task(client, task_id: str) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        response = client.get(f"/api/task/{task_id}")
        assert response.status_code == 200
        task = response.json()["data"]
        if task["status"] in {"succeeded", "failed", "partial_success"}:
            return task
        time.sleep(0.01)
    raise AssertionError(f"task {task_id} did not finish")


def test_resource_generation_is_idempotent(client):
    payload = generation_payload("idempotent-student")

    first = client.post(
        "/api/resource/generate",
        json=payload,
        headers={"Idempotency-Key": "same-request"},
    )
    second = client.post(
        "/api/resource/generate",
        json=payload,
        headers={"Idempotency-Key": "same-request"},
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["data"]["task_id"] == second.json()["data"]["task_id"]
    assert second.json()["data"]["deduplicated"] is True


def test_resource_generation_persists_selected_types_and_detail(client):
    payload = generation_payload()
    accepted = client.post("/api/resource/generate", json=payload)
    assert accepted.status_code == 202
    task_id = accepted.json()["data"]["task_id"]

    task = wait_for_task(client, task_id)
    assert task["status"] == "succeeded"
    assert task["request"]["resource_type_list"] == ["handout", "video"]

    history = client.get(
        "/api/resource/list",
        params={
            "user_id": payload["user_id"],
            "course_name": payload["course_name"],
        },
    )
    assert history.status_code == 200
    resources = history.json()["data"]["resources"]
    assert [resource["resource_type"] for resource in resources] == [
        "handout",
        "video",
    ]

    video = next(item for item in resources if item["resource_type"] == "video")
    detail = client.get(f"/api/resource/detail/{video['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["payload"]["summary"]
    assert detail.json()["data"]["media_url"] is None


def test_retry_creates_a_new_task_with_source_snapshot(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("retry-student")
        repository = TaskRepository(session)
        failed = repository.create(
            user_id=user.id,
            task_type="resource",
            request_snapshot=generation_payload(user.id),
        )
        repository.update_state(
            failed.id,
            status="failed",
            progress=45,
            error={
                "code": "UPSTREAM_TIMEOUT",
                "message": "上游超时",
                "retryable": True,
            },
        )

    response = client.post(f"/api/task/{failed.id}/retry")

    assert response.status_code == 202
    retried_id = response.json()["data"]["task_id"]
    assert retried_id != failed.id
    with db.session() as session:
        snapshot = TaskRepository(session).get_request_snapshot(retried_id)
    assert snapshot["retry_of_task_id"] == failed.id


def test_partial_success_keeps_completed_resources_and_retry_contract(
    client, settings
):
    class PartialProvider(MockAgentProvider):
        async def stream_resources(self, **kwargs):
            yield ResourceAgentEvent(
                event="resource.ready",
                current_agent="讲义Agent",
                progress=45,
                resource_type="handout",
                resource=self._resource_draft(
                    resource_type="handout",
                    course_name=kwargs["course_name"],
                    weak_point=kwargs["weak_point"],
                ),
            )
            yield ResourceAgentEvent(
                event="agent.started",
                current_agent="题库Agent",
                progress=55,
                resource_type="quiz",
            )
            raise AppError(
                status_code=503,
                code="UPSTREAM_TIMEOUT",
                message="题库 Agent 响应超时。",
                retryable=True,
            )

    client.app.state.agent_provider = PartialProvider(settings)
    payload = {
        **generation_payload("partial-student"),
        "resource_type_list": ["handout", "quiz"],
    }
    accepted = client.post("/api/resource/generate", json=payload)
    task_id = accepted.json()["data"]["task_id"]

    task = wait_for_task(client, task_id)

    assert task["status"] == "partial_success"
    assert task["error"]["code"] == "UPSTREAM_TIMEOUT"
    history = client.get(
        "/api/resource/list",
        params={"user_id": payload["user_id"], "course_name": payload["course_name"]},
    ).json()["data"]["resources"]
    assert [resource["resource_type"] for resource in history] == ["handout"]
    with client.app.state.db.session() as session:
        failed_event = TaskRepository(session).list_events(task_id)[-1]
        assert failed_event.event_type == "task.failed"
        assert failed_event.payload["resource_type"] == "quiz"
        assert failed_event.payload["error"]["code"] == "UPSTREAM_TIMEOUT"

    retry = client.post(f"/api/task/{task_id}/retry")
    assert retry.status_code == 202
