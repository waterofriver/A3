"""仪表盘聚合服务 —— 从多个表取数拼装 DashboardData。"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text

from app.db.database import Database
from app.db.models import (
    LearningEvent,
    LearningPath,
    LearningPathNode,
    QuizAttempt,
    Resource,
)
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas.dashboard import (
    DashboardActivitySummary,
    DashboardData,
    DashboardPathProgress,
    DashboardProfileSummary,
    DashboardQuizSummary,
    DashboardRecentResource,
    DashboardWeakPoint,
)


def _empty(user_id: str) -> DashboardData:
    return DashboardData(user_id=user_id)


class DashboardService:
    def __init__(self, db: Database):
        self.db = db

    def build(self, user_id: str, course_name: str | None = None) -> DashboardData:
        with self.db.session() as session:
            user = UserRepository(session).get(user_id)
            if user is None:
                return _empty(user_id)

            # ── 画像摘要 ──
            profile_record = ProfileRepository(session).get(user_id)
            profile = DashboardProfileSummary()
            if profile_record:
                pd = profile_record.profile_data or {}
                profile.cognitive_style = str(pd.get("cognitive_style", ""))
                profile.learning_pace = str(pd.get("learning_pace", ""))
                profile.short_term_goal = str(pd.get("short_term_goal", ""))
                parts = [p for p in [
                    profile.cognitive_style,
                    profile.learning_pace,
                    f"目标：{profile.short_term_goal}" if profile.short_term_goal else "",
                ] if p]
                profile.profile_text = " · ".join(parts) if parts else "画像待采集"

            # ── 课程名兜底 ──
            resolved_course = course_name or "机器人与安全"

            # ── 学习路径进度 ──
            path_progress = DashboardPathProgress(course_name=resolved_course)
            active_path = session.scalar(
                select(LearningPath).where(
                    LearningPath.user_id == user_id,
                    LearningPath.course_name == resolved_course,
                    LearningPath.status == "active",
                ).order_by(LearningPath.version.desc())
            )
            if active_path is not None:
                nodes = list(session.scalars(
                    select(LearningPathNode)
                    .where(LearningPathNode.path_id == active_path.id)
                ))
                path_progress.total_nodes = len(nodes)
                path_progress.completed_nodes = sum(1 for n in nodes if n.completed_at is not None)
                if path_progress.total_nodes > 0:
                    path_progress.percent = round(
                        100 * path_progress.completed_nodes / path_progress.total_nodes
                    )

            # ── 题库表现 ──
            quiz = DashboardQuizSummary()
            quiz_rows = list(session.scalars(
                select(QuizAttempt.score).where(QuizAttempt.user_id == user_id)
            ))
            if quiz_rows:
                quiz.total_attempts = len(quiz_rows)
                quiz.avg_score = round(sum(quiz_rows) / len(quiz_rows))

            # ── 最近资源 ──
            resource_rows = list(session.scalars(
                select(Resource)
                .where(Resource.user_id == user_id)
                .order_by(Resource.created_at.desc())
                .limit(5)
            ))
            recent_resources = [
                DashboardRecentResource(
                    id=r.id,
                    title=r.title,
                    resource_type=r.resource_type,
                    created_at=r.created_at.isoformat(),
                )
                for r in resource_rows
            ]

            # ── 活跃度 ──
            activity = DashboardActivitySummary()
            total_events = session.scalar(
                select(func.count(LearningEvent.id)).where(
                    LearningEvent.user_id == user_id,
                )
            )
            activity.total_events = int(total_events or 0)

            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            week_events = session.scalar(
                select(func.count(LearningEvent.id)).where(
                    LearningEvent.user_id == user_id,
                    LearningEvent.created_at >= week_ago,
                )
            )
            activity.this_week_events = int(week_events or 0)

            # 简单 streak：从今天往前数连续有学习事件的天数
            activity.streak_days = _compute_streak(session, user_id)

            # ── 薄弱点（基于评估报告 latest） ──
            from app.repositories.evaluations import EvaluationRepository
            weak_points = []
            eval_repo = EvaluationRepository(session)
            # 用 raw SQL 简单取最近一份报告
            latest_report = session.execute(
                text(
                    "SELECT weak_points FROM evaluation_reports "
                    "WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1"
                ),
                {"uid": user_id},
            ).scalar_one_or_none()
            if latest_report:
                import json
                raw_list = json.loads(latest_report) if isinstance(latest_report, str) else latest_report
                if isinstance(raw_list, list):
                    weak_points = [
                        DashboardWeakPoint(
                            name=item.get("name", ""),
                            frequency=item.get("frequency", 1),
                        )
                        for item in raw_list[:5]
                    ]

            return DashboardData(
                user_id=user_id,
                display_name=user.display_name or user_id,
                profile=profile,
                path=path_progress,
                quiz=quiz,
                recent_resources=recent_resources,
                activity=activity,
                weak_points=weak_points,
            )


def _compute_streak(session, user_id: str) -> int:
    """统计从今天往前数连续有学习事件的天数。"""
    rows = session.execute(
        text(
            "SELECT DISTINCT DATE(created_at) AS d FROM learning_events "
            "WHERE user_id = :uid ORDER BY d DESC"
        ),
        {"uid": user_id},
    ).fetchall()

    if not rows:
        return 0

    # SQLite 的 DATE() 返回字符串，需要显式转换
    dates: list = []
    for row in rows:
        val = row[0]
        if isinstance(val, str):
            dates.append(datetime.strptime(val, "%Y-%m-%d").date())
        elif hasattr(val, "date"):
            dates.append(val.date())
        else:
            dates.append(val)
    today = datetime.now(timezone.utc).date()

    streak = 0
    expected = today
    for d in dates:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        elif d < expected:
            break  # gap — streak broken
    return streak
