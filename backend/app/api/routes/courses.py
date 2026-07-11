from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.core.errors import AppError
from app.repositories.courses import CourseRepository
from app.schemas.course import CourseBaseResponse, CourseListResponse
from app.services.course_catalog import CourseCatalogService
from app.services.course_indexer import resolve_under

router = APIRouter(prefix="/api/course", tags=["courses"])
media_router = APIRouter(tags=["course-media"])


@router.get("/list", response_model=CourseListResponse)
def list_courses(request: Request) -> CourseListResponse:
    courses = CourseCatalogService(
        request.app.state.settings, request.app.state.db
    ).list_courses()
    return CourseListResponse(data=courses, trace_id=request.state.trace_id)


@router.get("/base", response_model=CourseBaseResponse)
def get_course_base(course_name: str, request: Request) -> CourseBaseResponse:
    course = CourseCatalogService(
        request.app.state.settings, request.app.state.db
    ).get_course(course_name)
    return CourseBaseResponse(data=course, trace_id=request.state.trace_id)


@media_router.get(
    "/media/courses/{course_slug}/{relative_path:path}",
    include_in_schema=False,
)
def get_course_media(
    course_slug: str, relative_path: str, request: Request
) -> FileResponse:
    with request.app.state.db.session() as session:
        repository = CourseRepository(session)
        course = repository.get_by_slug(course_slug)
        document = repository.get_document_by_path(course_slug, relative_path)
        if course is None or document is None:
            raise AppError(
                status_code=404,
                code="COURSE_DOCUMENT_NOT_FOUND",
                message="课程文档不存在或已被移除。",
                retryable=False,
            )
        try:
            path = resolve_under(Path(course.root_path), Path(document.relative_path))
        except ValueError as error:
            raise AppError(
                status_code=404,
                code="COURSE_DOCUMENT_NOT_FOUND",
                message="课程文档路径无效。",
                retryable=False,
            ) from error
        if not path.is_file():
            raise AppError(
                status_code=404,
                code="COURSE_DOCUMENT_NOT_FOUND",
                message="课程文档不存在或已被移除。",
                retryable=False,
            )
    return FileResponse(
        path,
        filename=document.filename,
        content_disposition_type="inline",
    )
