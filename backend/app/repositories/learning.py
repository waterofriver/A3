from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    LearningEvent,
    LearningPath,
    LearningPathNode,
    QuizAttempt,
    utcnow,
)


class LearningRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_path(self, user_id: str, course_name: str) -> LearningPath:
        active_paths = list(
            self.session.scalars(
                select(LearningPath).where(
                    LearningPath.user_id == user_id,
                    LearningPath.course_name == course_name,
                    LearningPath.status == "active",
                )
            )
        )
        for path in active_paths:
            path.status = "superseded"

        current_version = self.session.scalar(
            select(func.coalesce(func.max(LearningPath.version), 0)).where(
                LearningPath.user_id == user_id,
                LearningPath.course_name == course_name,
            )
        )
        path = LearningPath(
            user_id=user_id,
            course_name=course_name,
            version=int(current_version or 0) + 1,
        )
        self.session.add(path)
        self.session.flush()
        return path

    def get_active_path(self, user_id: str, course_name: str) -> LearningPath | None:
        return self.session.scalar(
            select(LearningPath).where(
                LearningPath.user_id == user_id,
                LearningPath.course_name == course_name,
                LearningPath.status == "active",
            )
        )

    def replace_nodes(self, path_id: str, nodes: list[dict]) -> list[LearningPathNode]:
        self.session.execute(
            delete(LearningPathNode).where(LearningPathNode.path_id == path_id)
        )
        stored = [
            LearningPathNode(path_id=path_id, position=position, **node)
            for position, node in enumerate(nodes)
        ]
        self.session.add_all(stored)
        self.session.flush()
        return stored

    def list_path_nodes(self, path_id: str) -> list[LearningPathNode]:
        return list(
            self.session.scalars(
                select(LearningPathNode)
                .where(LearningPathNode.path_id == path_id)
                .order_by(LearningPathNode.position)
            )
        )

    def complete_path_node(self, node_id: str) -> LearningPathNode:
        node = self.session.get(LearningPathNode, node_id)
        if node is None:
            raise LookupError(node_id)
        if node.completed_at is None:
            node.completed_at = utcnow()
            self.session.flush()
        return node

    def record_quiz_attempt(
        self,
        *,
        user_id: str,
        resource_id: str,
        answers: dict,
        results: list[dict],
        score: int,
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id,
            resource_id=resource_id,
            answers=answers,
            results=results,
            score=score,
        )
        self.session.add(attempt)
        self.session.flush()
        return attempt

    def record_learning_event(
        self,
        *,
        user_id: str,
        course_name: str,
        event_type: str,
        resource_id: str | None,
        path_node_id: str | None,
        client_started_at: datetime | None,
        client_ended_at: datetime | None,
        duration_seconds: int,
        event_metadata: dict,
    ) -> LearningEvent:
        event = LearningEvent(
            user_id=user_id,
            course_name=course_name,
            event_type=event_type,
            resource_id=resource_id,
            path_node_id=path_node_id,
            client_started_at=client_started_at,
            client_ended_at=client_ended_at,
            duration_seconds=duration_seconds,
            event_metadata=event_metadata,
        )
        self.session.add(event)
        self.session.flush()
        return event
