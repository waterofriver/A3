"""仪表盘聚合数据 Schema"""

from pydantic import BaseModel, Field


class DashboardProfileSummary(BaseModel):
    cognitive_style: str = ""
    learning_pace: str = ""
    short_term_goal: str = ""
    profile_text: str = ""  # 一句话摘要，如"偏实践·分散学习·短期目标：完成课程"


class DashboardPathProgress(BaseModel):
    total_nodes: int = 0
    completed_nodes: int = 0
    percent: int = 0  # 0-100
    course_name: str = ""


class DashboardQuizSummary(BaseModel):
    total_attempts: int = 0
    avg_score: int = 0


class DashboardRecentResource(BaseModel):
    id: str
    title: str
    resource_type: str  # handout / mindmap / quiz / code / video
    created_at: str  # ISO 字符串


class DashboardActivitySummary(BaseModel):
    total_events: int = 0
    this_week_events: int = 0
    # 简单"连续学习天数"：基于学习事件日期统计
    streak_days: int = 0


class DashboardWeakPoint(BaseModel):
    name: str
    frequency: int


class DashboardData(BaseModel):
    user_id: str
    display_name: str | None = None
    profile: DashboardProfileSummary = Field(default_factory=DashboardProfileSummary)
    path: DashboardPathProgress = Field(default_factory=DashboardPathProgress)
    quiz: DashboardQuizSummary = Field(default_factory=DashboardQuizSummary)
    recent_resources: list[DashboardRecentResource] = Field(default_factory=list)
    activity: DashboardActivitySummary = Field(default_factory=DashboardActivitySummary)
    weak_points: list[DashboardWeakPoint] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    data: DashboardData
    trace_id: str
