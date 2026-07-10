from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Resource


class ResourceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        resource_id: str,
        task_id: str,
        user_id: str,
        course_name: str,
        resource_type: str,
        title: str,
        payload: dict,
        media_url: str | None,
    ) -> Resource:
        resource = Resource(
            id=resource_id,
            task_id=task_id,
            user_id=user_id,
            course_name=course_name,
            resource_type=resource_type,
            title=title,
            payload=payload,
            media_url=media_url,
        )
        self.session.add(resource)
        self.session.flush()
        return resource

    def get(self, resource_id: str) -> Resource:
        resource = self.session.get(Resource, resource_id)
        if resource is None:
            raise LookupError(resource_id)
        return resource

    def list_for_course(self, user_id: str, course_name: str) -> list[Resource]:
        statement = (
            select(Resource)
            .where(
                Resource.user_id == user_id,
                Resource.course_name == course_name,
            )
            .order_by(Resource.created_at, Resource.id)
        )
        return list(self.session.scalars(statement))

    def list_by_task(self, task_id: str) -> list[Resource]:
        statement = (
            select(Resource)
            .where(Resource.task_id == task_id)
            .order_by(Resource.created_at, Resource.id)
        )
        return list(self.session.scalars(statement))
