from pydantic import BaseModel


class CourseSummary(BaseModel):
    name: str
    slug: str
    content_ready: bool
    is_demo: bool


class CourseDocumentData(BaseModel):
    id: str
    chapter_path: str
    filename: str
    file_type: str
    sha256: str
    size_bytes: int
    preview_text: str | None = None
    media_url: str | None = None


class CourseChapterData(BaseModel):
    path: str
    name: str
    documents: list[CourseDocumentData]


class CourseBaseData(CourseSummary):
    chapters: list[CourseChapterData]


class CourseListResponse(BaseModel):
    data: list[CourseSummary]
    trace_id: str


class CourseBaseResponse(BaseModel):
    data: CourseBaseData
    trace_id: str
