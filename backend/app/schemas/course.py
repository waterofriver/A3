from pydantic import BaseModel


class CourseSummary(BaseModel):
    name: str
    slug: str
    content_ready: bool
    is_demo: bool


class CourseListResponse(BaseModel):
    data: list[CourseSummary]
    trace_id: str
