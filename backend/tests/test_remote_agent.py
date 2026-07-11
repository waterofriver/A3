import importlib
import json
from datetime import datetime, timezone

import httpx
import pytest

from app.schemas.evaluation import (
    EvaluationEvidence,
    EvaluationPracticeNodeEvidence,
    EvaluationQuizAttemptEvidence,
)
from app.schemas.profile import StudentProfileData
from app.schemas.resource import ResourceSummary


VALID_PROFILE = {
    "knowledge_foundation": "入门基础",
    "cognitive_style": "案例驱动",
    "weak_points": ["ROS2 通信"],
    "learning_pace": "分阶段",
    "content_preferences": ["代码案例"],
    "short_term_goal": "完成通信强化",
}


def sse_response(events: list[dict]) -> httpx.Response:
    body = "".join(f"data: {json.dumps(event, ensure_ascii=False)}\n\n" for event in events)
    return httpx.Response(
        200,
        content=body.encode(),
        headers={"content-type": "text/event-stream"},
    )


def remote_settings(settings):
    return settings.model_copy(
        update={
            "agent_mode": "remote",
            "remote_agent_base_url": "https://agents.example",
            "remote_agent_api_key": "secret-token",
        }
    )


@pytest.mark.asyncio
async def test_remote_profile_events_map_to_gateway_contract(settings):
    module = importlib.import_module("app.agents.remote")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/profile/stream"
        assert request.headers["authorization"] == "Bearer secret-token"
        return sse_response(
            [
                {"type": "agent", "name": "画像抽取Agent", "progress": 10},
                {"type": "delta", "text": "正在提取画像", "progress": 45},
                {"type": "profile", "profile": VALID_PROFILE, "progress": 85},
                {"type": "done"},
            ]
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agents.example"
    ) as client:
        provider = module.RemoteAgentProvider(remote_settings(settings), client=client)
        events = [
            event
            async for event in provider.stream_profile(
                task_id="task-1",
                trace_id="trace-1",
                user_id="student-001",
                chat_text="我想加强 ROS2 通信",
                current_profile=None,
            )
        ]

    assert [event.event for event in events] == [
        "agent.started",
        "content.delta",
        "profile.patch",
        "task.completed",
    ]
    assert events[2].profile_patch == VALID_PROFILE
    assert all(event.demo_mode is False for event in events)


@pytest.mark.asyncio
async def test_remote_resource_events_validate_fixed_resource_draft(settings):
    module = importlib.import_module("app.agents.remote")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/resources/stream"
        return sse_response(
            [
                {
                    "type": "agent",
                    "name": "讲义Agent",
                    "progress": 10,
                    "resource_type": "handout",
                },
                {
                    "type": "delta",
                    "name": "讲义Agent",
                    "progress": 45,
                    "resource_type": "handout",
                    "text": "# 通信模型",
                },
                {
                    "type": "resource",
                    "name": "讲义Agent",
                    "progress": 95,
                    "resource_type": "handout",
                    "resource": {
                        "resource_type": "handout",
                        "title": "通信讲义",
                        "payload": {"markdown": "# 通信模型"},
                        "media_url": None,
                    },
                },
                {"type": "done"},
            ]
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agents.example"
    ) as client:
        provider = module.RemoteAgentProvider(remote_settings(settings), client=client)
        events = [
            event
            async for event in provider.stream_resources(
                task_id="task-1",
                trace_id="trace-1",
                user_id="student-001",
                course_name="机器人操作系统",
                weak_point="服务通信",
                resource_types=["handout"],
            )
        ]

    assert [event.event for event in events] == [
        "agent.started",
        "content.delta",
        "resource.ready",
    ]
    assert events[-1].resource is not None
    assert events[-1].resource.payload["markdown"] == "# 通信模型"


@pytest.mark.asyncio
async def test_remote_qa_maps_text_and_truthful_empty_media(settings):
    module = importlib.import_module("app.agents.remote")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/qa/stream"
        return sse_response(
            [
                {"type": "agent", "name": "答疑Agent", "progress": 10},
                {"type": "delta", "text": "发布者发送消息。", "progress": 50},
                {"type": "media", "kind": "video", "url": None, "progress": 88},
                {"type": "done"},
            ]
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agents.example"
    ) as client:
        provider = module.RemoteAgentProvider(remote_settings(settings), client=client)
        events = [
            event
            async for event in provider.stream_qa(
                task_id="task-1",
                trace_id="trace-1",
                user_id="student-001",
                question="什么是发布订阅？",
                answer_mode="video",
                profile=StudentProfileData.model_validate(VALID_PROFILE),
            )
        ]

    assert [event.event for event in events] == [
        "agent.started",
        "content.delta",
        "media.ready",
        "task.completed",
    ]
    assert events[2].media_url is None


@pytest.mark.asyncio
async def test_remote_json_endpoints_map_path_and_evaluation_drafts(settings):
    module = importlib.import_module("app.agents.remote")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/path":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "nodes": [
                            {
                                "stage_name": name,
                                "difficulty": difficulty,
                                "resource_id": None,
                            }
                            for name, difficulty in [
                                ("基础补全", "基础"),
                                ("知识点学习", "进阶"),
                                ("习题训练", "巩固"),
                                ("代码实操", "实操"),
                                ("拓展视频", "拓展"),
                            ]
                        ]
                    }
                },
            )
        if request.url.path == "/evaluation":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "theory_score": 80,
                        "practice_score": 50,
                        "weak_points": [
                            {"name": "ROS2 服务通信", "frequency": 2}
                        ],
                        "recommended_changes": [
                            {
                                "stage_name": "ROS2 服务通信专项练习",
                                "difficulty": "巩固",
                                "reason": "错题频次较高。",
                                "resource_id": None,
                            }
                        ],
                    }
                },
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://agents.example"
    ) as client:
        provider = module.RemoteAgentProvider(remote_settings(settings), client=client)
        path = await provider.build_learning_path(
            user_id="student-001",
            course_name="机器人操作系统",
            profile=StudentProfileData.model_validate(VALID_PROFILE),
            resources=[
                ResourceSummary(
                    id="resource-1",
                    task_id="task-1",
                    course_name="机器人操作系统",
                    resource_type="handout",
                    title="讲义",
                    media_url=None,
                    created_at=datetime.now(timezone.utc),
                )
            ],
        )
        evaluation = await provider.build_evaluation(
            user_id="student-001",
            course_name="机器人操作系统",
            evidence=EvaluationEvidence(
                attempts=[
                    EvaluationQuizAttemptEvidence(
                        score=80, incorrect_points=["ROS2 服务通信"]
                    )
                ],
                practice_nodes=[
                    EvaluationPracticeNodeEvidence(
                        stage_name="代码实操", completed=False
                    )
                ],
            ),
        )

    assert len(path.nodes) == 5
    assert path.nodes[3].stage_name == "代码实操"
    assert evaluation.theory_score == 80
    assert evaluation.weak_points[0].name == "ROS2 服务通信"
