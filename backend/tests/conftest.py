from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.agents.mock import MockAgentProvider
from app.core.config import Settings
from app.main import create_app
from app.repositories.learning import LearningRepository
from app.repositories.resources import ResourceRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        agent_mode="mock",
        mock_event_delay_ms=0,
        course_root=tmp_path / "courses",
    )


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def mock_provider(settings: Settings) -> MockAgentProvider:
    return MockAgentProvider(settings)


@pytest.fixture
def evaluation_records(client):
    user_id = "student-001"
    course_name = "机器人操作系统"
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create(user_id)
        task = TaskRepository(session).create(
            user_id=user.id,
            task_type="resource",
            request_snapshot={"course_name": course_name},
        )
        quiz_id = str(uuid4())
        ResourceRepository(session).create(
            resource_id=quiz_id,
            task_id=task.id,
            user_id=user.id,
            course_name=course_name,
            resource_type="quiz",
            title="ROS2 通信题库",
            payload={
                "questions": [
                    {
                        "id": "q1",
                        "question_type": "choice",
                        "prompt": "ROS2 服务通信",
                        "options": ["A", "B"],
                        "answer": "B",
                        "explanation": "服务采用请求响应模型。",
                    },
                    {
                        "id": "q2",
                        "question_type": "blank",
                        "prompt": "ROS2 主题通信",
                        "options": [],
                        "answer": "发布订阅",
                        "explanation": "主题采用发布订阅模型。",
                    },
                ]
            },
            media_url=None,
        )
        learning = LearningRepository(session)
        learning.record_quiz_attempt(
            user_id=user.id,
            resource_id=quiz_id,
            answers={"q1": "A", "q2": "发布订阅"},
            results=[
                {"question_id": "q1", "correct": False},
                {"question_id": "q2", "correct": True},
            ],
            score=60,
        )
        learning.record_quiz_attempt(
            user_id=user.id,
            resource_id=quiz_id,
            answers={"q1": "B", "q2": "发布订阅"},
            results=[
                {"question_id": "q1", "correct": True},
                {"question_id": "q2", "correct": True},
            ],
            score=100,
        )
        path = learning.create_path(user.id, course_name)
        nodes = learning.replace_nodes(
            path.id,
            [
                {
                    "stage_name": "代码实操一",
                    "difficulty": "实操",
                    "resource_id": None,
                },
                {
                    "stage_name": "代码实操二",
                    "difficulty": "实操",
                    "resource_id": None,
                },
            ],
        )
        learning.complete_path_node(nodes[0].id)
        learning.record_learning_event(
            user_id=user.id,
            course_name=course_name,
            event_type="question_asked",
            resource_id=None,
            path_node_id=None,
            client_started_at=None,
            client_ended_at=None,
            duration_seconds=0,
            event_metadata={"weak_point": "ROS2 服务通信"},
        )
        return {
            "user_id": user.id,
            "course_name": course_name,
            "source_path_id": path.id,
        }
