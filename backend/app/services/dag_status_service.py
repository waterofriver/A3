"""知识 DAG 着色状态服务 —— 结合学习数据计算每个知识点的掌握状态。"""

from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import select

from app.agents.mock import _conceptualize_weak_point as _to_concept
from app.db.database import Database
from app.db.models import EvaluationReport, LearningPath, LearningPathNode
from app.repositories.learning import LearningRepository
from app.schemas.dag import KnowledgeDagNodeStatus


def _load_kp_list() -> list[dict]:
    """从 knowledge_dag.json 读取知识点原始数据。"""
    dag_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "knowledge_base"
        / "knowledge_dag.json"
    )
    import json

    with dag_path.open("r", encoding="utf-8") as f:
        dag = json.load(f)
    return dag.get("knowledge_points", [])


class DagStatusService:
    def __init__(self, db: Database):
        self.db = db

    def compute(
        self, user_id: str, course_name: str = "机器人与安全"
    ) -> list[KnowledgeDagNodeStatus]:
        kp_list = _load_kp_list()

        with self.db.session() as session:
            learning = LearningRepository(session)

            # ── 活跃学习路径的节点 ──
            path: LearningPath | None = learning.get_active_path(user_id, course_name)
            path_stage_names: set[str] = set()
            completed_stage_names: set[str] = set()
            if path is not None:
                nodes: Iterable[LearningPathNode] = learning.list_path_nodes(path.id)
                for node in nodes:
                    path_stage_names.add(node.stage_name)
                    if node.completed_at is not None:
                        completed_stage_names.add(node.stage_name)

            # ── 最近评估报告的薄弱点 → 转为概念名 ──
            weak_concepts: set[str] = set()
            eval_rows = list(
                session.scalars(
                    select(EvaluationReport)
                    .where(
                        EvaluationReport.user_id == user_id,
                        EvaluationReport.course_name == course_name,
                    )
                    .order_by(EvaluationReport.created_at.desc())
                    .limit(1)
                )
            )
            if eval_rows:
                latest = eval_rows[0]
                for wp in latest.weak_points or []:
                    name = wp.get("name", "") if isinstance(wp, dict) else str(wp)
                    if name:
                        concept, _ = _to_concept(name)
                        weak_concepts.add(concept)

        # ── 逐节点判定状态 ──
        results: list[KnowledgeDagNodeStatus] = []
        for kp in kp_list:
            kp_name = kp.get("name", "")
            kp_id = kp.get("id", "")

            # 将 DAG 节点名也转为概念，与薄弱点概念做精确匹配
            kp_concept, _ = _to_concept(kp_name)

            # 检查路径阶段是否包含此知识点名
            in_path = any(kp_name in sn for sn in path_stage_names)
            is_completed = any(kp_name in sn for sn in completed_stage_names)
            is_weak = kp_concept in weak_concepts

            # 状态判定优先级：weak > mastered > learning > untouched
            if is_weak:
                status = "weak"
            elif is_completed:
                status = "mastered"
            elif in_path:
                status = "learning"
            else:
                status = "untouched"

            results.append(
                KnowledgeDagNodeStatus(
                    kp_id=kp_id,
                    kp_name=kp_name,
                    difficulty=kp.get("difficulty", 1),
                    category=kp.get("category", ""),
                    prerequisites=kp.get("prerequisites", []),
                    status=status,
                )
            )

        return results
