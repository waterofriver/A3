from dataclasses import dataclass

from app.core.errors import AppError
from app.db.database import Database
from app.db.models import LearningPath, LearningPathNode, Resource
from app.repositories.learning import LearningRepository
from app.repositories.users import UserRepository
from app.schemas.learning import LearningEventBatchData, LearningEventBatchRequest

MAX_EVENT_SECONDS = 4 * 60 * 60


@dataclass(frozen=True)
class ValidatedEvent:
    event: object
    duration_seconds: int


class LearningEventService:
    def __init__(self, db: Database):
        self.db = db

    def record(self, payload: LearningEventBatchRequest) -> LearningEventBatchData:
        with self.db.session() as session:
            UserRepository(session).get_or_create(payload.user_id)
            validated: list[ValidatedEvent] = []
            for event in payload.events:
                if (
                    event.client_started_at
                    and event.client_ended_at
                    and event.client_ended_at < event.client_started_at
                ):
                    raise AppError(
                        status_code=400,
                        code="VALIDATION_ERROR",
                        message="学习事件结束时间不能早于开始时间。",
                        retryable=False,
                    )

                if event.resource_id:
                    resource = session.get(Resource, event.resource_id)
                    if resource is None or resource.user_id != payload.user_id:
                        raise AppError(
                            status_code=400,
                            code="VALIDATION_ERROR",
                            message="学习事件引用了无效资源。",
                            retryable=False,
                        )

                if event.path_node_id:
                    node = session.get(LearningPathNode, event.path_node_id)
                    path = session.get(LearningPath, node.path_id) if node else None
                    if node is None or path is None or path.user_id != payload.user_id:
                        raise AppError(
                            status_code=400,
                            code="VALIDATION_ERROR",
                            message="学习事件引用了无效路径节点。",
                            retryable=False,
                        )
                elif event.event_type == "path_node_completed":
                    raise AppError(
                        status_code=400,
                        code="VALIDATION_ERROR",
                        message="完成路径节点时必须提供 path_node_id。",
                        retryable=False,
                    )

                duration = 0
                if event.client_started_at and event.client_ended_at:
                    duration = min(
                        MAX_EVENT_SECONDS,
                        max(
                            0,
                            int(
                                (
                                    event.client_ended_at
                                    - event.client_started_at
                                ).total_seconds()
                            ),
                        ),
                    )
                validated.append(
                    ValidatedEvent(event=event, duration_seconds=duration)
                )

            repository = LearningRepository(session)
            for item in validated:
                event = item.event
                if event.event_type == "path_node_completed":
                    repository.complete_path_node(event.path_node_id)
                repository.record_learning_event(
                    user_id=payload.user_id,
                    course_name=payload.course_name,
                    event_type=event.event_type,
                    resource_id=event.resource_id,
                    path_node_id=event.path_node_id,
                    client_started_at=event.client_started_at,
                    client_ended_at=event.client_ended_at,
                    duration_seconds=item.duration_seconds,
                    event_metadata=event.metadata,
                )

        return LearningEventBatchData(accepted=len(validated))
