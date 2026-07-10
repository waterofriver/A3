import pytest


@pytest.mark.asyncio
async def test_mock_resource_stream_completes_selected_types(mock_provider):
    events = [
        event
        async for event in mock_provider.stream_resources(
            task_id="task-1",
            trace_id="trace-1",
            user_id="student-001",
            course_name="机器人操作系统",
            weak_point="ROS2 节点通信",
            resource_types=["handout", "mindmap", "quiz", "code", "video"],
        )
    ]

    ready_events = [event for event in events if event.event == "resource.ready"]
    assert [event.resource_type for event in ready_events] == [
        "handout",
        "mindmap",
        "quiz",
        "code",
        "video",
    ]
    assert all(event.resource is not None for event in ready_events)
    assert all("演示资源" in event.resource.title for event in ready_events)
    assert ready_events[-1].resource.media_url is None
    assert max(event.progress for event in events) < 100
