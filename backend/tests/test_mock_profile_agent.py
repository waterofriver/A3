import pytest

from app.agents.mock import MockAgentProvider


@pytest.mark.asyncio
async def test_mock_profile_stream_emits_fixed_profile_schema(settings):
    provider = MockAgentProvider(settings)
    events = [
        event
        async for event in provider.stream_profile(
            task_id="task-1",
            trace_id="trace-1",
            user_id="student-001",
            chat_text="我在 ROS2 节点通信方面基础薄弱，喜欢代码案例。",
            current_profile=None,
        )
    ]

    assert events[0].event == "task.started"
    patch = next(
        event.profile_patch for event in events if event.event == "profile.patch"
    )
    assert set(patch) == {
        "knowledge_foundation",
        "cognitive_style",
        "weak_points",
        "learning_pace",
        "content_preferences",
        "short_term_goal",
    }
    assert [event.seq for event in events] == [0, 0, 0, 0, 0, 0]
    assert all(event.demo_mode for event in events)
    assert events[-1].event == "task.completed"
    assert events[-1].finish_flag is True
