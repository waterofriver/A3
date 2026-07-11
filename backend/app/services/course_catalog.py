from app.core.config import Settings
from app.core.errors import AppError
from app.db.database import Database
from app.repositories.courses import CourseRepository
from app.schemas.course import CourseBaseData, CourseSummary
from app.services.course_indexer import course_data


class CourseCatalogService:
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db

    def list_courses(self) -> list[CourseSummary]:
        with self.db.session() as session:
            real_courses = [
                CourseSummary(
                    name=course.name,
                    slug=course.slug,
                    content_ready=course.content_ready,
                    is_demo=course.is_demo,
                )
                for course in CourseRepository(session).list_courses()
            ]
        by_slug = {course.slug: course for course in real_courses}
        if self.settings.agent_mode == "mock":
            by_slug.setdefault(
                "robotics-demo",
                CourseSummary(
                    name="机器人操作系统（演示）",
                    slug="robotics-demo",
                    content_ready=False,
                    is_demo=True,
                ),
            )
        return list(by_slug.values())

    def get_course(self, course_name: str) -> CourseBaseData:
        with self.db.session() as session:
            repository = CourseRepository(session)
            course = repository.get_by_name(course_name)
            if course is not None and course.content_ready:
                return course_data(course, repository.list_documents(course.slug))

        if course is not None or (
            self.settings.agent_mode == "mock"
            and course_name == "机器人操作系统（演示）"
        ):
            raise AppError(
                status_code=400,
                code="COURSE_NOT_READY",
                message="课程资料尚未同步，请挂载真实知识库文件后重试。",
                retryable=False,
            )
        raise AppError(
            status_code=404,
            code="COURSE_NOT_FOUND",
            message="课程不存在或已被移除。",
            retryable=False,
        )
