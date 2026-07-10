from app.agents.base import AgentProvider
from app.core.errors import AppError
from app.db.database import Database
from app.repositories.learning import LearningRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.resources import ResourceRepository
from app.schemas.learning import (
    LearningPathData,
    LearningPathNodeData,
)
from app.schemas.profile import StudentProfileData
from app.schemas.resource import ResourceSummary


def path_data(path, nodes) -> LearningPathData:
    return LearningPathData(
        id=path.id,
        user_id=path.user_id,
        course_name=path.course_name,
        version=path.version,
        nodes=[
            LearningPathNodeData(
                id=node.id,
                position=node.position,
                stage_name=node.stage_name,
                difficulty=node.difficulty,
                resource_id=node.resource_id,
                completed_at=node.completed_at,
            )
            for node in nodes
        ],
    )


class LearningPathService:
    def __init__(self, db: Database, provider: AgentProvider):
        self.db = db
        self.provider = provider

    async def get_or_create(self, user_id: str, course_name: str) -> LearningPathData:
        with self.db.session() as session:
            learning = LearningRepository(session)
            current = learning.get_active_path(user_id, course_name)
            if current is not None:
                return path_data(current, learning.list_path_nodes(current.id))

            profile_record = ProfileRepository(session).get(user_id)
            if profile_record is None:
                raise AppError(
                    status_code=400,
                    code="VALIDATION_ERROR",
                    message="请先完成学生画像采集。",
                    retryable=False,
                )
            profile = StudentProfileData.model_validate(profile_record.profile_data)
            resources = [
                ResourceSummary.model_validate(resource)
                for resource in ResourceRepository(session).list_for_course(
                    user_id, course_name
                )
            ]

        draft = await self.provider.build_learning_path(
            user_id=user_id,
            course_name=course_name,
            profile=profile,
            resources=resources,
        )
        with self.db.session() as session:
            learning = LearningRepository(session)
            existing = learning.get_active_path(user_id, course_name)
            if existing is not None:
                return path_data(existing, learning.list_path_nodes(existing.id))
            path = learning.create_path(user_id, course_name)
            nodes = learning.replace_nodes(
                path.id,
                [node.model_dump() for node in draft.nodes],
            )
            return path_data(path, nodes)
