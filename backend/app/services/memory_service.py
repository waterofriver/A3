"""Build an explainable, evidence-based memory estimate without external calls."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.db.database import Database
from app.db.models import LearningEvent, LearningPath, LearningPathNode, QuizAttempt, Resource
from app.schemas.memory import (
    CurvePoint,
    MemoryAction,
    MemoryBlockage,
    MemoryKnowledgePoint,
    MemoryReportData,
)


def _load_dag() -> list[dict]:
    dag_path = Path(__file__).resolve().parents[3] / "knowledge_base" / "knowledge_dag.json"
    with dag_path.open(encoding="utf-8") as file:
        return json.load(file).get("knowledge_points", [])


def _days_since(when: datetime | None) -> int:
    if when is None:
        return 3
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - when).days)


class MemoryService:
    def __init__(self, db: Database):
        self.db = db

    def compute(self, user_id: str, course_name: str) -> MemoryReportData:
        dag = _load_dag()
        by_id = {item["id"]: item for item in dag}
        evidence: dict[str, dict] = {
            item["id"]: {"scores": [], "reviewed_at": None, "completed": False}
            for item in dag
        }
        has_mapped_path_evidence = False
        has_mapped_event_evidence = False
        has_mapped_attempt_evidence = False

        with self.db.session() as session:
            paths = list(session.scalars(select(LearningPath).where(
                LearningPath.user_id == user_id, LearningPath.course_name == course_name
            )))
            nodes = list(session.scalars(select(LearningPathNode).where(
                LearningPathNode.path_id.in_([path.id for path in paths])
            ))) if paths else []
            events = list(session.scalars(select(LearningEvent).where(
                LearningEvent.user_id == user_id, LearningEvent.course_name == course_name
            )))
            attempts = list(session.execute(
                select(QuizAttempt, Resource).join(Resource, Resource.id == QuizAttempt.resource_id).where(
                    QuizAttempt.user_id == user_id, Resource.course_name == course_name
                ).order_by(QuizAttempt.created_at.asc(), QuizAttempt.id.asc())
            ))

        for node in nodes:
            for item in dag:
                if item["name"] in node.stage_name or item["id"] in node.stage_name:
                    has_mapped_path_evidence = True
                    item_evidence = evidence[item["id"]]
                    item_evidence["completed"] |= node.completed_at is not None
                    if node.completed_at is not None:
                        item_evidence["reviewed_at"] = max(
                            filter(None, [item_evidence["reviewed_at"], node.completed_at]), default=node.completed_at
                        )

        for event in events:
            metadata = event.event_metadata or {}
            kp_id = metadata.get("knowledge_point_id") or metadata.get("kp_id")
            if kp_id in evidence:
                has_mapped_event_evidence = True
                item_evidence = evidence[kp_id]
                item_evidence["reviewed_at"] = max(
                    filter(None, [item_evidence["reviewed_at"], event.created_at]), default=event.created_at
                )

        for attempt, resource in attempts:
            searchable = f"{resource.title} {resource.payload}".lower()
            matches = [item for item in dag if item["id"].lower() in searchable or item["name"].lower() in searchable]
            # Only point-labelled quizzes may influence an individual point estimate.
            for item in matches[:1]:
                has_mapped_attempt_evidence = True
                item_evidence = evidence[item["id"]]
                item_evidence["scores"].append(attempt.score)
                item_evidence["reviewed_at"] = max(
                    filter(None, [item_evidence["reviewed_at"], attempt.created_at]), default=attempt.created_at
                )

        points: list[MemoryKnowledgePoint] = []
        for item in dag:
            item_evidence = evidence[item["id"]]
            scores = item_evidence["scores"]
            base = round(sum(scores) / len(scores)) if scores else (82 if item_evidence["completed"] else 76)
            days = _days_since(item_evidence["reviewed_at"])
            recent_low_score = bool(scores and scores[-1] < 70)
            decay = 0.15 if recent_low_score else 0.09
            retention = max(0, min(100, round(base * math.exp(-decay * days))))
            risk = "urgent" if recent_low_score or retention < 55 else "review_soon" if retention < 70 else "stable"
            prereqs = item.get("prerequisites", [])
            blockage = None
            prerequisite_name = ""
            prerequisite_points = [point for point in points if point.id in prereqs]
            if prerequisite_points:
                prerequisite_name = prerequisite_points[0].name
                risky_prerequisites = [point for point in prerequisite_points if point.risk_level != "stable"]
                if risk == "urgent" and risky_prerequisites:
                    chosen = min(
                        risky_prerequisites,
                        key=lambda point: ({"urgent": 0, "review_soon": 1}[point.risk_level], point.retention),
                    )
                    blockage = MemoryBlockage(
                        knowledge_point_id=chosen.id,
                        name=chosen.name,
                        reason="该前置知识点也处于复习风险中，可能影响当前内容的理解。",
                    )
            recommendation = (
                "建议优先完成一次回忆题和一题变式练习。" if risk == "urgent"
                else "建议在下一次学习前用几分钟回顾关键步骤。" if risk == "review_soon"
                else "当前为稳定估计，建议按学习节奏做一次简短回忆。"
            )
            if risk == "urgent" and prerequisite_name and blockage is None:
                recommendation += f" 建议同时回顾前置内容“{prerequisite_name}”。"
            points.append(MemoryKnowledgePoint(
                id=item["id"], name=item["name"], retention=retention, base_mastery=base,
                days_since_review=days, risk_level=risk,
                curve=[CurvePoint(day=day, retention=max(0, min(100, round(base * math.exp(-decay * day))))) for day in (0, 1, 3, 7)],
                recommendation=recommendation, blockage=blockage,
            ))

        priority = sorted(points, key=lambda point: ({"urgent": 0, "review_soon": 1, "stable": 2}[point.risk_level], point.retention))[:3]
        action_types = ("recall", "quiz", "practice")
        has_personal_evidence = (
            has_mapped_path_evidence or has_mapped_event_evidence or has_mapped_attempt_evidence
        )
        actions = [MemoryAction(
            knowledge_point_id=point.id,
            title=f"复习：{point.name}",
            minutes=(8, 10, 15)[index], action_type=action_types[index],
            reason=(
                f"基于当前学习记录的记忆保持估计，{point.recommendation}"
                if has_personal_evidence else f"课程起步建议：{point.recommendation}"
            ),
        ) for index, point in enumerate(priority)]
        health = round(sum(point.retention for point in points) / len(points)) if points else 70
        summary = (
            "这是基于学习记录和课程知识图谱的记忆保持估计，建议优先处理今日复习任务。"
            if has_personal_evidence else "暂无个人学习记录，以下为课程起步建议。"
        )
        return MemoryReportData(
            memory_health=health, summary=summary, has_personal_evidence=has_personal_evidence,
            knowledge_points=points, today_actions=actions,
        )
