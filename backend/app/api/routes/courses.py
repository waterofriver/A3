from fastapi import APIRouter, Request

from app.schemas.course import CourseListResponse
from app.services.course_catalog import CourseCatalogService

router = APIRouter(prefix="/api/course", tags=["courses"])


@router.get("/list", response_model=CourseListResponse)
def list_courses(request: Request) -> CourseListResponse:
    courses = CourseCatalogService(request.app.state.settings).list_courses()
    return CourseListResponse(data=courses, trace_id=request.state.trace_id)
