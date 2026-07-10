from app.core.config import Settings
from app.schemas.course import CourseSummary


class CourseCatalogService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def list_courses(self) -> list[CourseSummary]:
        if self.settings.agent_mode != "mock":
            return []
        return [
            CourseSummary(
                name="机器人操作系统（演示）",
                slug="robotics-demo",
                content_ready=False,
                is_demo=True,
            )
        ]
