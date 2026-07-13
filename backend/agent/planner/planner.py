# -*- coding: utf-8 -*-
"""
学习路径规划 Agent (Planner Agent)
=================================
根据学生画像和知识 DAG 生成个性化学习路径。

设计原则：
- 混合算法：Kahn 拓扑排序保证前置依赖 + LLM 负责个性化标注
- 无状态：每次 plan() 调用独立，返回 PlannerResult
- 支持增量更新：可基于已有 LearningPath 调整
- 同步和异步两套 API

用法示例::

    from planner import PlannerAgent
    from utils.dag_loader import load_knowledge_dag

    agent = PlannerAgent()
    dag = load_knowledge_dag("path/to/knowledge_dag.json")
    result = agent.plan(student_profile, dag)
    if result.success:
        for node in result.learning_path.nodes:
            print(f"{node.order}. {node.knowledge_point_name} [depth={node.depth}]")
"""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..config import Config
from ..utils import LLMClient, LLMResponse, get_client
from ..utils.json_parser import extract_json
from ..models import (
    StudentProfile,
    KnowledgeDAG,
    KnowledgePoint,
    LearningPath,
    LearningPathNode,
    ResourceType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════


@dataclass
class PlannerResult:
    """每次规划调用返回的结果。

    调用方根据 success 判断是否成功，从 learning_path 获取路径。
    """

    learning_path: Optional[LearningPath] = None
    """生成的个性化学习路径；失败时可能为 None"""

    success: bool = True
    """LLM 调用和 JSON 解析是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""

    reasoning_content: Optional[str] = None
    """deepseek-reasoner 思维链，用于调试"""

    warnings: list[str] = field(default_factory=list)
    """非致命警告信息（部分节点未个性化、循环依赖等）"""


# ═══════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """
你是一个学习路径规划助手。你的任务是根据学生的画像和课程知识体系，为每个知识点标注学习参数，生成个性化学习路径。

## 标注规则

对每个知识点，你需要标注以下字段：

### 1. depth（学习深度，1-3）
- **3（精通）**: 学生的薄弱环节，或对其长期目标至关重要的核心知识点
- **2（掌握）**: 课程核心知识点，但不是薄弱环节
- **1（了解）**: 边缘/辅助知识点，学生可能已掌握或兴趣不大

### 2. recommended_resource_types（推荐资源类型列表）
可选值: doc, mindmap, quiz, code, video_script
- 偏理论学生: 优先 doc, mindmap
- 偏实践学生: 优先 code, quiz
- 薄弱环节: 增加 quiz（自测检验）
- 一般知识点: doc, mindmap 作为基础
- 所有节点至少包含一种资源类型

### 3. rationale（推荐理由，20-50字）
结合学生画像说明为什么设定此深度和资源类型。必须具体，不能泛泛而谈。

### 4. is_weak_point（是否薄弱环节）
检查该知识点 ID 是否在学生"薄弱环节 ID 列表"中。如果是则设为 true。

### 5. estimated_time_minutes（预计学习时长，分钟）
- depth=3: 原始估计时长 × 1.5
- depth=2: 原始估计时长 × 1.0
- depth=1: 原始估计时长 × 0.6
取整到最近的 5 分钟，最小不低于 10 分钟。

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块，不要输出任何其他文字。

```json
{
  "nodes": [
    {
      "knowledge_point_id": "course_orientation",
      "depth": 1,
      "recommended_resource_types": ["doc", "mindmap"],
      "rationale": "示例理由：你的基础较好，此导论知识点仅需快速了解即可进入后续实验。",
      "is_weak_point": false,
      "estimated_time_minutes": 20
    }
  ],
  "overall_rationale": "整体路径设计思路的一两句话说明（30-80字）"
}
```

## 重要约束

- nodes 数组中的顺序必须与输入中给出的知识点列表顺序**完全一致**
- 每个知识点的 knowledge_point_id 必须与输入完全匹配，不得遗漏或添加
- 不要跳过任何知识点，输入列表有多少个就输出多少个
""".strip()


# ═══════════════════════════════════════════════════════════════
# PlannerAgent
# ═══════════════════════════════════════════════════════════════


class PlannerAgent:
    """个性化学习路径规划 Agent。

    混合算法：Kahn 拓扑排序（保证前置依赖正确）+ LLM（个性化标注）。

    用法::

        from planner import PlannerAgent
        from utils.dag_loader import load_knowledge_dag

        agent = PlannerAgent()
        dag = load_knowledge_dag("path/to/knowledge_dag.json")
        result = agent.plan(student_profile, dag)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认 deepseek-reasoner 模型
        temperature: LLM 温度，默认 0.2（低温度保证 JSON 稳定性）
        max_tokens: 最大输出 token 数，默认 4096
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        self._client = client or get_client()
        self._model = model or Config.DEEPSEEK_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens

    # ── 公开 API ──────────────────────────────────────────

    def plan(
        self,
        student_profile: StudentProfile,
        knowledge_dag: KnowledgeDAG,
        existing_path: Optional[LearningPath] = None,
    ) -> PlannerResult:
        """同步生成个性化学习路径。

        参数:
            student_profile: 学生画像（Snapshot 会注入 System Prompt）
            knowledge_dag: 知识体系 DAG（用于拓扑排序和节点信息）
            existing_path: 已有学习路径（增量更新场景）

        返回:
            PlannerResult: 包含生成的 LearningPath
        """
        return self._plan_impl(student_profile, knowledge_dag, existing_path)

    async def plan_async(
        self,
        student_profile: StudentProfile,
        knowledge_dag: KnowledgeDAG,
        existing_path: Optional[LearningPath] = None,
    ) -> PlannerResult:
        """异步生成个性化学习路径。签名与 plan 一致。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        return await self._plan_impl_async(
            client, student_profile, knowledge_dag, existing_path
        )

    # ── 内部实现 ──────────────────────────────────────────

    def _plan_impl(
        self,
        student_profile: StudentProfile,
        knowledge_dag: KnowledgeDAG,
        existing_path: Optional[LearningPath],
    ) -> PlannerResult:
        """同步规划的核心实现。"""

        # 0. 空 DAG 校验
        if not knowledge_dag.knowledge_points:
            return PlannerResult(
                success=False,
                error="知识 DAG 中没有知识点",
            )

        # 1. 拓扑排序
        try:
            sorted_kps = self._topological_sort(knowledge_dag)
        except ValueError as e:
            logger.error(f"拓扑排序失败（循环依赖）: {e}")
            return PlannerResult(
                success=False,
                error=str(e),
                warnings=[str(e)],
            )

        logger.info(
            f"PlannerAgent.plan | model={self._model} | "
            f"kp_count={len(sorted_kps)} | "
            f"has_existing_path={existing_path is not None}"
        )

        # 2. 构建消息
        system_prompt = self._build_system_prompt(
            student_profile, sorted_kps, knowledge_dag, existing_path
        )
        user_message = self._build_user_message(student_profile)

        # 3. 调用 LLM
        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        # 4. 处理响应
        return self._handle_response(response, sorted_kps, student_profile, knowledge_dag, existing_path)

    async def _plan_impl_async(
        self,
        client,
        student_profile: StudentProfile,
        knowledge_dag: KnowledgeDAG,
        existing_path: Optional[LearningPath],
    ) -> PlannerResult:
        """异步规划的核心实现。"""

        if not knowledge_dag.knowledge_points:
            return PlannerResult(
                success=False,
                error="知识 DAG 中没有知识点",
            )

        sorted_kps = self._topological_sort(knowledge_dag)

        logger.info(
            f"PlannerAgent.plan_async | model={self._model} | "
            f"kp_count={len(sorted_kps)}"
        )

        system_prompt = self._build_system_prompt(
            student_profile, sorted_kps, knowledge_dag, existing_path
        )
        user_message = self._build_user_message(student_profile)

        response = await client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(response, sorted_kps, student_profile, knowledge_dag, existing_path)

    def _handle_response(
        self,
        response: LLMResponse,
        sorted_kps: list[KnowledgePoint],
        student_profile: StudentProfile,
        knowledge_dag: KnowledgeDAG,
        existing_path: Optional[LearningPath],
    ) -> PlannerResult:
        """统一处理 LLM 响应：解析 JSON → 构建 LearningPathNode 列表 → 组装 LearningPath。"""

        # LLM 调用失败
        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return PlannerResult(
                success=False,
                error=response.error or "LLM 调用失败",
            )

        # 解析 JSON
        parsed, json_error = extract_json(response.content)

        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return PlannerResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                reasoning_content=response.reasoning_content,
            )

        # 构建 LearningPathNode 列表
        llm_nodes = parsed.get("nodes") or []
        overall_rationale = parsed.get("overall_rationale") or ""

        # ── 空输出检测：LLM 完全没返回节点 ──
        if not llm_nodes:
            logger.warning("LLM 返回了空的 nodes 列表，全部节点将使用默认值")
            return PlannerResult(
                success=False,
                error="LLM 未返回任何个性化标注（nodes 为空），请重试",
                reasoning_content=response.reasoning_content,
            )

        # 建立 KP ID → KnowledgePoint 的快速查找表
        kp_map = {kp.id: kp for kp in sorted_kps}

        nodes: list[LearningPathNode] = []
        total_time = 0
        invalid_kp_ids: list[str] = []

        for i, node_data in enumerate(llm_nodes):
            kp_id = node_data.get("knowledge_point_id", "")
            kp = kp_map.get(kp_id)

            if kp is None:
                if kp_id:
                    invalid_kp_ids.append(kp_id)
                logger.warning(f"LLM 返回了未知知识点 ID: {kp_id}，跳过")
                continue

            # 解析资源类型
            resource_types: list[ResourceType] = []
            for rt_str in node_data.get("recommended_resource_types", []):
                try:
                    resource_types.append(ResourceType(rt_str))
                except ValueError:
                    logger.warning(f"未知资源类型: {rt_str}")

            # 确保至少有一种资源类型
            if not resource_types:
                resource_types = [ResourceType.DOC, ResourceType.MINDMAP]

            node = LearningPathNode(
                order=i + 1,
                knowledge_point_id=kp_id,
                knowledge_point_name=kp.name,
                depth=max(1, min(3, node_data.get("depth", 2))),
                recommended_resource_types=resource_types,
                rationale=node_data.get("rationale", ""),
                estimated_time_minutes=node_data.get("estimated_time_minutes", kp.estimated_minutes),
                is_weak_point=node_data.get("is_weak_point", False),
            )
            nodes.append(node)
            total_time += node.estimated_time_minutes

        # ── 收集警告 ──
        warnings: list[str] = []

        if invalid_kp_ids:
            warnings.append(
                f"LLM 返回了 {len(invalid_kp_ids)} 个未知知识点 ID，已跳过: "
                f"{', '.join(invalid_kp_ids[:5])}"
            )

        # 如果 LLM 返回的节点数不足，用拓扑排序的结果补充未标注的节点
        llm_kp_ids = {n.knowledge_point_id for n in nodes}
        auto_filled_count = 0
        for i, kp in enumerate(sorted_kps):
            if kp.id not in llm_kp_ids:
                logger.info(f"补充未标注节点: {kp.id}")
                nodes.append(LearningPathNode(
                    order=len(nodes) + 1,
                    knowledge_point_id=kp.id,
                    knowledge_point_name=kp.name,
                    depth=2,
                    recommended_resource_types=[ResourceType.DOC, ResourceType.MINDMAP],
                    rationale="自动补充：LLM 未返回此节点标注",
                    estimated_time_minutes=kp.estimated_minutes,
                    is_weak_point=False,
                ))
                total_time += kp.estimated_minutes
                auto_filled_count += 1

        # ── 过多自动填充警告 ──
        total_kp_count = len(sorted_kps)
        if auto_filled_count > 0:
            if auto_filled_count >= total_kp_count * 0.5:
                warnings.append(
                    f"LLM 个性化覆盖率不足：仅 {total_kp_count - auto_filled_count}/{total_kp_count} "
                    f"个节点有个性化标注，{auto_filled_count} 个节点使用了默认值。"
                    f"建议检查 LLM 输出质量或重试。"
                )
            else:
                logger.info(
                    f"自动补充了 {auto_filled_count}/{total_kp_count} 个未标注节点"
                )

        # 按 order 排序
        nodes.sort(key=lambda n: n.order)
        for i, node in enumerate(nodes):
            node.order = i + 1

        # 构建 LearningPath
        version = 1
        if existing_path is not None:
            version = existing_path.version + 1

        path = LearningPath(
            student_profile_snapshot=student_profile.snapshot(),
            course_name=knowledge_dag.course_name,
            nodes=nodes,
            total_estimated_minutes=total_time,
            version=version,
        )

        logger.info(
            f"PlannerAgent 结果 | nodes={len(nodes)} | "
            f"total_time={total_time}min | "
            f"version={version} | "
            f"auto_filled={auto_filled_count} | "
            f"warnings={len(warnings)}"
        )

        return PlannerResult(
            learning_path=path,
            success=True,
            reasoning_content=response.reasoning_content,
            warnings=warnings,
        )

    # ── 拓扑排序 ──────────────────────────────────────────

    @staticmethod
    def _topological_sort(dag: KnowledgeDAG) -> list[KnowledgePoint]:
        """Kahn 算法拓扑排序。

        对知识 DAG 做拓扑排序，保证前置依赖知识点排在前面。
        当同时有多个入度为 0 的节点时，按 difficulty 升序、id 字典序决定。

        参数:
            dag: 知识 DAG

        返回:
            按学习顺序排列的知识点列表

        异常:
            ValueError: DAG 中存在循环依赖，无法完成拓扑排序
        """
        # 构建入度表和邻接表
        in_degree: dict[str, int] = {kp.id: 0 for kp in dag.knowledge_points}
        adjacency: dict[str, list[str]] = {kp.id: [] for kp in dag.knowledge_points}

        for kp in dag.knowledge_points:
            for prereq in kp.prerequisites:
                if prereq in adjacency:
                    adjacency[prereq].append(kp.id)
                    in_degree[kp.id] += 1

        # 入度为 0 的节点入队
        queue = deque([
            kp for kp in dag.knowledge_points
            if in_degree[kp.id] == 0
        ])

        result: list[KnowledgePoint] = []

        while queue:
            # 按 difficulty → id 排序，保证确定性
            sorted_queue = sorted(queue, key=lambda kp: (kp.difficulty, kp.id))
            current = sorted_queue[0]
            queue = deque(sorted_queue[1:])

            result.append(current)

            for neighbor_id in adjacency.get(current.id, []):
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    neighbor = dag.get_by_id(neighbor_id)
                    if neighbor:
                        queue.append(neighbor)

        # 检测循环依赖：直接抛出异常，不允许静默丢数据
        if len(result) != len(dag.knowledge_points):
            missing = sorted(set(kp.id for kp in dag.knowledge_points) - set(kp.id for kp in result))
            cycle_nodes = sorted(
                kp_id for kp_id, deg in in_degree.items() if deg > 0
            )
            raise ValueError(
                f"DAG 中存在循环依赖，涉及 {len(cycle_nodes)} 个知识点: "
                f"{', '.join(cycle_nodes[:5])}{'...' if len(cycle_nodes) > 5 else ''}。"
                f"请检查这些知识点的 prerequisites 是否形成了 A→B→A 的环路。"
            )

        return result

    # ── System Prompt 构建 ────────────────────────────────

    def _build_system_prompt(
        self,
        profile: StudentProfile,
        sorted_kps: list[KnowledgePoint],
        dag: KnowledgeDAG,
        existing_path: Optional[LearningPath],
    ) -> str:
        """构建 System Prompt，包含学生画像和拓扑排序后的知识点列表。"""
        prompt = _SYSTEM_PROMPT

        # 注入学生画像
        profile_text = profile.snapshot()
        if profile_text:
            prompt += f"\n\n## 学生画像\n\n{profile_text}"

        # 注入薄弱环节 ID 列表
        if profile.weak_points:
            wp_lines = []
            for wp in profile.weak_points:
                wp_lines.append(f"- {wp.knowledge_point_id}: {wp.knowledge_point_name}（{wp.error_pattern}）")
            prompt += "\n\n## 学生薄弱环节 ID 列表\n\n" + "\n".join(wp_lines)

        # 注入拓扑排序后的知识点列表
        kp_lines = []
        for i, kp in enumerate(sorted_kps):
            kp_lines.append(
                f"{i + 1}. id={kp.id} | name={kp.name} | "
                f"difficulty={kp.difficulty} | "
                f"estimated={kp.estimated_minutes}min | "
                f"category={kp.category}"
            )
        prompt += "\n\n## 知识点列表（已按学习顺序排列，共 {} 个）\n\n".format(len(sorted_kps))
        prompt += "\n".join(kp_lines)

        # 增量更新场景：注入已有路径
        if existing_path is not None and existing_path.nodes:
            existing_lines = []
            for node in existing_path.nodes:
                existing_lines.append(
                    f"{node.order}. {node.knowledge_point_name} "
                    f"[depth={node.depth}, time={node.estimated_time_minutes}min, "
                    f"weak={node.is_weak_point}]"
                )
            prompt += "\n\n## 已有学习路径（请基于此做增量调整）\n\n"
            prompt += "\n".join(existing_lines)
            prompt += "\n\n如需调整，在输出中给出修改后的完整 nodes 列表。"

        return prompt

    # ── User Message 构建 ─────────────────────────────────

    def _build_user_message(self, profile: StudentProfile) -> str:
        """构建发送给 LLM 的 user message。"""
        parts = ["请为以下学生规划个性化学习路径。"]
        if profile.major:
            parts.append(f"专业: {profile.major}")
        if profile.grade:
            parts.append(f"年级: {profile.grade}")
        parts.append(f"认知风格: {profile.cognitive_style}")
        parts.append(f"学习节奏: {profile.learning_pace}")
        if profile.learning_goal_short:
            parts.append(f"短期目标: {profile.learning_goal_short}")
        if profile.learning_goal_long:
            parts.append(f"长期目标: {profile.learning_goal_long}")
        if profile.interest_domains:
            parts.append(f"兴趣方向: {', '.join(profile.interest_domains)}")
        return "，".join(parts) + "。"
