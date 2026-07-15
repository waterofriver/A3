from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.core.config import Settings
from app.core.errors import AppError
from app.repositories.courses import CourseRepository
from app.schemas.course import CourseBaseResponse, CourseListResponse
from app.services.course_catalog import CourseCatalogService
from app.services.course_indexer import resolve_under

router = APIRouter(prefix="/api/course", tags=["courses"])
media_router = APIRouter(tags=["course-media"])

# 视频直连路由（不查 DB，直接从 data/courses 读取）
direct_media_router = APIRouter(tags=["direct-media"])


@direct_media_router.get(
    "/media/video/{kp_id}/{filename:path}",
    include_in_schema=False,
)
def get_video_direct(kp_id: str, filename: str, request: Request) -> FileResponse:
    """直接提供视频文件，不经过 DB 查询。"""
    settings: Settings = request.app.state.settings
    data_root = settings.course_root  # ./data/courses
    # 查找 robot-safety 目录（第一个课程目录）
    course_dir = None
    for entry in sorted(data_root.iterdir()):
        if entry.is_dir() and (entry / "course.json").exists():
            course_dir = entry
            break
    if course_dir is None:
        raise AppError(status_code=404, code="VIDEO_NOT_FOUND",
                       message="课程目录未找到。", retryable=False)

    video_path = course_dir / kp_id / filename
    if not video_path.is_file():
        # 回退：尝试直接读 knowledge_base 原始文件
        kb_root = settings.knowledge_base_root
        alt_path = kb_root / "materials" / kp_id / filename
        if alt_path.is_file():
            video_path = alt_path
        else:
            raise AppError(status_code=404, code="VIDEO_NOT_FOUND",
                           message="视频文件不存在。", retryable=False)

    return FileResponse(
        video_path,
        filename=filename,
        content_disposition_type="inline",
    )


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
