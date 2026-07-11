from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Course, CourseDocument, utcnow


class CourseRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_course(
        self,
        *,
        slug: str,
        name: str,
        root_path: str,
        content_ready: bool,
        is_demo: bool = False,
    ) -> Course:
        course = self.session.get(Course, slug)
        if course is None:
            course = Course(slug=slug)
            self.session.add(course)
        course.name = name
        course.root_path = root_path
        course.content_ready = content_ready
        course.is_demo = is_demo
        course.indexed_at = utcnow()
        self.session.flush()
        return course

    def replace_documents(
        self, course_slug: str, documents: list[dict]
    ) -> list[CourseDocument]:
        self.session.execute(
            delete(CourseDocument).where(CourseDocument.course_slug == course_slug)
        )
        stored = [
            CourseDocument(course_slug=course_slug, **document)
            for document in documents
        ]
        self.session.add_all(stored)
        self.session.flush()
        return stored

    def remove_courses_not_in(self, slugs: set[str]) -> None:
        stale = list(
            self.session.scalars(select(Course).where(Course.slug.not_in(slugs)))
        )
        for course in stale:
            self.session.execute(
                delete(CourseDocument).where(
                    CourseDocument.course_slug == course.slug
                )
            )
            self.session.delete(course)
        self.session.flush()

    def list_courses(self) -> list[Course]:
        return list(self.session.scalars(select(Course).order_by(Course.name)))

    def get_by_name(self, name: str) -> Course | None:
        return self.session.scalar(select(Course).where(Course.name == name))

    def get_by_slug(self, slug: str) -> Course | None:
        return self.session.get(Course, slug)

    def list_documents(self, course_slug: str) -> list[CourseDocument]:
        return list(
            self.session.scalars(
                select(CourseDocument)
                .where(CourseDocument.course_slug == course_slug)
                .order_by(
                    CourseDocument.chapter_path,
                    CourseDocument.relative_path,
                )
            )
        )

    def get_document_by_path(
        self, course_slug: str, relative_path: str
    ) -> CourseDocument | None:
        return self.session.scalar(
            select(CourseDocument).where(
                CourseDocument.course_slug == course_slug,
                CourseDocument.relative_path == relative_path,
            )
        )
