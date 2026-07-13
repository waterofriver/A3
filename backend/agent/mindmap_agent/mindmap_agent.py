# -*- coding: utf-8 -*-
"""
思维导图生成 Agent (MindMap Agent)
==================================
根据知识点信息和学生画像，生成结构化思维导图（含 Mermaid 语法）。

设计原则：
- 无状态：每次 generate() 调用独立
- 个性化：根据学生画像调整导图的展开深度和侧重点
- 双重输出：Mermaid mindmap 代码 + 结构化节点树
- 同步和异步两套 API

用法示例::

    from mindmap_agent import MindMapAgent

    agent = MindMapAgent()
    result = agent.generate(knowledge_point, student_profile)
    if result.success:
        print(result.resource.content.mermaid_code)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..config import Config
from ..utils import LLMClient, LLMResponse, get_client
from ..utils.json_parser import extract_json
from ..models import (
    StudentProfile,
    KnowledgePoint,
    MindMapContent,
    ResourceMetadata,
    ResourceOutput,
    ResourceType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════


@dataclass
class MindMapResult:
    """思维导图生成的返回结果。"""

    resource: Optional[ResourceOutput] = None
    """生成的资源（含 metadata 和 MindMapContent）；失败时为 None"""

    success: bool = True
    """生成是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""

    reasoning_content: Optional[str] = None
    """deepseek-reasoner 思维链，用于调试"""

    warnings: list[str] = field(default_factory=list)
    """非致命警告"""


# ═══════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """
你是一位知识体系架构师，擅长将复杂的知识点拆解为层次分明、逻辑清晰的思维导图。你的任务是根据给定的知识点，生成一份结构化思维导图。

## 核心原则

1. **层次分明**：根节点 → 主分支（3-6个）→ 子分支（每主分支 2-4 个），最多 3 层
2. **逻辑清晰**：同一主分支下的子分支应属于同一维度（如概念、原理、应用、实验、注意点）
3. **Mermaid 语法**：必须生成有效的 Mermaid mindmap 代码，可直接渲染
4. **适应画像**：
   - 偏理论型学生：侧重"原理推导"、"数学模型"、"公式体系"分支
   - 偏实践型学生：侧重"操作步骤"、"代码示例"、"实验验证"分支
   - 薄弱知识点：增加"常见错误"、"避坑指南"分支

## 导图结构建议

建议按以下维度组织主分支（选择 3-5 个最相关的）：

1. **核心概念**（必选）：知识点最核心的定义和组成要素
2. **工作原理**（必选）：机制、流程、算法步骤
3. **关键要素**（可选）：组成部件、重要参数、核心数据结构
4. **操作实践**（推荐）：实验步骤、代码接口、配置方法
5. **常见问题**（推荐）：易错点、注意事项、调试技巧
6. **应用场景**（可选）：工程案例、关联知识点

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块，不要输出任何其他文字。

```json
{
    "root_topic": "知识点名称",
    "mermaid_code": "mindmap\\n  root((知识点名称))\\n    主分支1\\n      子分支1a\\n      子分支1b\\n    主分支2\\n      子分支2a\\n      子分支2b",
    "nodes": [
        {
            "id": "root",
            "label": "知识点名称",
            "parent_id": null,
            "children": ["n1", "n2", "n3"]
        },
        {
            "id": "n1",
            "label": "主分支1：核心概念",
            "parent_id": "root",
            "children": ["n1a", "n1b"]
        },
        {
            "id": "n1a",
            "label": "子分支：概念要素A",
            "parent_id": "n1",
            "children": []
        }
    ]
}
```

## Mermaid 语法要求

- 使用 `mindmap` 关键字开头（非 `graph`）
- 缩进表示层级关系，每级缩进 2-4 个空格
- 根节点用 `root((文本))` 格式
- 节点文本如果包含括号或特殊字符，用 `"` 包裹
- 确保代码可以被 Mermaid 渲染器正确解析

示例：
```mermaid
mindmap
  root((二叉树))
    基本概念
      节点与边
      根/叶/父/子
    遍历方式
      前序遍历
      中序遍历
      后序遍历
      层序遍历
    特殊类型
      满二叉树
      完全二叉树
      二叉搜索树
```

## 质量要求

- 根节点 label 与 root_topic 一致
- nodes 数组必须形成一棵完整的树：每个非根节点有 parent_id，children 数组列出直接子节点
- Mermaid 代码中的节点标签与 nodes 中的 label 保持一致
- 总节点数建议 8-25 个（根+主分支+子分支）
- 节点标签简洁（10 字以内），不要堆砌长句

## 课件参考材料

如果提供了"课件参考资料"（从课程原始 PDF/PPTX/DOCX 中提取），你必须：
- **以课件结构为主要依据**，导图的主分支应反映课件中的主要章节/主题
- 在课件内容的基础上进行细化和补充
- 不要编造课件中没有的核心概念
""".strip()


# ═══════════════════════════════════════════════════════════════
# MindMapAgent
# ═══════════════════════════════════════════════════════════════


class MindMapAgent:
    """思维导图生成 Agent。

    根据知识点和学生画像，生成结构化的思维导图（含 Mermaid 语法）。

    用法::

        from mindmap_agent import MindMapAgent

        agent = MindMapAgent()
        result = agent.generate(knowledge_point, student_profile)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认模型
        temperature: LLM 温度，默认 0.2（导图需要稳定结构）
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

    def generate(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
    ) -> MindMapResult:
        """同步生成思维导图。

        参数:
            knowledge_point: 目标知识点
            student_profile: 学生画像（None 则使用默认通用风格）
            material_context: 从课件材料中提取的参考文本（由 MaterialLoader 提供）

        返回:
            MindMapResult: 包含 ResourceOutput 的生成结果
        """
        return self._generate_impl(knowledge_point, student_profile, material_context)

    async def generate_async(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
    ) -> MindMapResult:
        """异步生成思维导图。签名与 generate 一致。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        return await self._generate_impl_async(
            client, knowledge_point, student_profile, material_context
        )

    # ── 内部实现 ──────────────────────────────────────────

    def _generate_impl(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str = "",
    ) -> MindMapResult:
        """同步生成的核心实现。"""

        # 0. 输入校验
        if not knowledge_point.name:
            return MindMapResult(
                success=False,
                error="知识点名称为空",
            )

        # 1. 构建消息
        system_prompt = self._build_system_prompt(knowledge_point, student_profile, material_context)
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"MindMapAgent.generate | model={self._model} | "
            f"kp={knowledge_point.id} | "
            f"difficulty={knowledge_point.difficulty}"
        )

        # 2. 调用 LLM
        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        # 3. 处理响应
        return self._handle_response(response, knowledge_point, student_profile)

    async def _generate_impl_async(
        self,
        client,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str = "",
    ) -> MindMapResult:
        """异步生成的核心实现。"""

        if not knowledge_point.name:
            return MindMapResult(
                success=False,
                error="知识点名称为空",
            )

        system_prompt = self._build_system_prompt(knowledge_point, student_profile, material_context)
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"MindMapAgent.generate_async | model={self._model} | "
            f"kp={knowledge_point.id}"
        )

        response = await client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(response, knowledge_point, student_profile)

    def _handle_response(
        self,
        response: LLMResponse,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
    ) -> MindMapResult:
        """统一处理 LLM 响应：解析 JSON → 构建 MindMapContent → 包装 ResourceOutput。"""

        # LLM 调用失败
        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return MindMapResult(
                success=False,
                error=response.error or "LLM 调用失败",
            )

        # 解析 JSON
        parsed, json_error = extract_json(response.content)

        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return MindMapResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                reasoning_content=response.reasoning_content,
            )

        # 提取字段
        root_topic = parsed.get("root_topic") or knowledge_point.name
        mermaid_code = parsed.get("mermaid_code") or ""
        nodes = parsed.get("nodes") or []

        # ── 空内容检测 ──
        if not nodes:
            logger.warning("LLM 返回了空的 nodes 列表")
            return MindMapResult(
                success=False,
                error="LLM 未生成任何导图节点（nodes 为空），请重试",
                reasoning_content=response.reasoning_content,
            )

        # ── 质量检测 ──
        warnings: list[str] = []

        # 节点数过少
        if len(nodes) < 4:
            warnings.append(
                f"导图仅包含 {len(nodes)} 个节点，内容可能过于简略"
            )

        # Mermaid 代码缺失
        if not mermaid_code:
            warnings.append("LLM 未返回 mermaid_code，前端可能无法渲染导图")

        # Mermaid 关键字检查
        if mermaid_code and "mindmap" not in mermaid_code.lower():
            warnings.append(
                "mermaid_code 中未找到 'mindmap' 关键字，"
                "请确认使用了正确的 Mermaid mindmap 语法"
            )

        # ── 校验并规范化 nodes ──
        node_ids: set[str] = set()
        parent_ids: set[str] = {""}  # 允许空 parent_id（root）

        for i, node in enumerate(nodes):
            nid = str(node.get("id", f"n{i}")).strip()
            if not nid:
                nid = f"n{i}"
            node["id"] = nid
            node_ids.add(nid)

            if "parent_id" in node and node["parent_id"] is not None:
                parent_ids.add(str(node["parent_id"]))

        # 检查是否有孤立节点（parent_id 不在 nodes 中）
        orphan_nodes = []
        for node in nodes:
            pid = node.get("parent_id")
            if pid is not None and str(pid) not in node_ids and str(pid) != "":
                orphan_nodes.append(node.get("label", node.get("id", "?")))

        if orphan_nodes:
            warnings.append(
                f"以下节点的 parent_id 指向不存在的节点: {', '.join(orphan_nodes[:5])}"
            )

        # ── 校验并规范化每个节点 ──
        validated_nodes: list[dict] = []
        for node in nodes:
            nid = str(node.get("id", "")).strip()
            label = str(node.get("label", "")).strip()
            parent_id = node.get("parent_id")
            children = node.get("children", [])

            if not label:
                logger.warning(f"节点 {nid} 的 label 为空，跳过")
                continue

            if isinstance(children, str):
                children = [children]
            if not isinstance(children, list):
                children = []

            validated_nodes.append({
                "id": nid,
                "label": label,
                "parent_id": parent_id,
                "children": [str(c).strip() for c in children if c],
            })

        if not validated_nodes:
            return MindMapResult(
                success=False,
                error="所有节点的 label 均为空，无法生成有效导图",
                reasoning_content=response.reasoning_content,
                warnings=warnings,
            )

        # ── 构建 MindMapContent ──
        mindmap_content = MindMapContent(
            root_topic=root_topic,
            mermaid_code=mermaid_code,
            nodes=validated_nodes,
        )

        # ── 构建 ResourceMetadata ──
        profile_snapshot = ""
        if student_profile is not None:
            profile_snapshot = student_profile.snapshot()

        metadata = ResourceMetadata(
            resource_type=ResourceType.MINDMAP,
            knowledge_point_id=knowledge_point.id,
            knowledge_point_name=knowledge_point.name,
            title=f"{knowledge_point.name} — 思维导图",
            difficulty=knowledge_point.difficulty,
            estimated_read_time_minutes=max(3, len(validated_nodes) // 3),
            tags=knowledge_point.tags,
            student_profile_snapshot=profile_snapshot,
        )

        # ── 组装 ResourceOutput ──
        resource = ResourceOutput(
            metadata=metadata,
            content=mindmap_content,
            status="generated",
            generated_by="MindMapAgent",
        )

        logger.info(
            f"MindMapAgent 结果 | nodes={len(validated_nodes)} | "
            f"has_mermaid={'yes' if mermaid_code else 'no'} | "
            f"warnings={len(warnings)}"
        )

        return MindMapResult(
            resource=resource,
            success=True,
            reasoning_content=response.reasoning_content,
            warnings=warnings,
        )

    # ── System Prompt 构建 ────────────────────────────────

    def _build_system_prompt(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str = "",
    ) -> str:
        """构建 System Prompt，注入知识点、学生画像和课件参考材料。"""
        prompt = _SYSTEM_PROMPT

        # 注入知识点信息
        prompt += f"""

## 当前知识点

- 名称: {knowledge_point.name}
- 描述: {knowledge_point.description or '暂无描述'}
- 分类: {knowledge_point.category or '未分类'}
- 难度: {knowledge_point.difficulty}/5
- 标签: {', '.join(knowledge_point.tags) if knowledge_point.tags else '无'}
"""

        # 注入学生画像
        if student_profile is not None:
            snapshot = student_profile.snapshot()
            if snapshot.strip():
                prompt += f"""
## 学生画像

{snapshot}

请根据以上画像调整导图结构：
- 偏理论学生增加原理推导分支
- 偏实践学生增加操作步骤分支
- 薄弱知识点增加常见错误/避坑分支
"""
        else:
            prompt += """
## 学生画像

未提供学生画像，请使用通用的均衡风格组织导图结构。
"""

        # ── 注入课件参考材料 ──
        if material_context and material_context.strip():
            ctx = material_context.strip()
            if len(ctx) > 12000:
                ctx = ctx[:12000] + "\n\n...(课件内容过长，已截断)"
            prompt += f"\n\n{ctx}\n"

        return prompt

    # ── User Message 构建 ─────────────────────────────────

    def _build_user_message(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
    ) -> str:
        """构建发送给 LLM 的 user message。"""
        parts = [
            f"请为知识点「{knowledge_point.name}」生成一份思维导图。",
            f"该知识点属于「{knowledge_point.category}」分类，难度 {knowledge_point.difficulty}/5。",
            f"知识点描述: {knowledge_point.description or '暂无'}。",
        ]

        if student_profile is not None:
            if student_profile.weak_points:
                wp_names = [w.knowledge_point_name for w in student_profile.weak_points]
                if knowledge_point.name in wp_names or any(
                    w.knowledge_point_id == knowledge_point.id
                    for w in student_profile.weak_points
                ):
                    parts.append("这是学生的薄弱知识点，请增加「常见错误」和「避坑指南」分支。")

        parts.append("请确保 Mermaid 代码以 'mindmap' 开头，节点控制在 10-20 个。")
        return " ".join(parts)
