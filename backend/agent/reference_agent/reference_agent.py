# -*- coding: utf-8 -*-
"""
拓展阅读推荐 Agent (Reference Agent)
====================================
根据学生画像、当前学习进度和课件知识结构，从课程拓展阅读库和外部资源中
推荐最匹配的阅读材料。

设计原则：
- 库内优先：优先推荐 shared_references 中已有的材料，再补充外部推荐
- 个性化匹配：根据学生薄弱环节、认知风格、兴趣方向和学习目标匹配读物
- 理由明确：每本推荐书都附有详细的推荐理由和阅读建议
- 同步和异步两套 API

用法示例::

    from reference_agent import ReferenceAgent
    from utils.material_loader import MaterialLoader

    loader = MaterialLoader("A3/knowledge_base")
    agent = ReferenceAgent()
    result = agent.recommend(knowledge_point, student_profile, loader)
    for rec in result.recommendations:
        print(f"{rec['title']} - {rec['relevance_reason'][:50]}")
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
    ResourceMetadata,
    ResourceOutput,
    ResourceType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class ReferenceResult:
    """拓展阅读推荐的返回结果。

    推荐数据主要存储在 library_recommendations 和 external_recommendations 中。
    resource 字段保留用于 API 兼容，但其 content 为简化版（避免 Pydantic dict 强制转换问题）。
    """

    resource: Optional[ResourceOutput] = None
    """兼容性 ResourceOutput（content 为简化版 dict）"""

    success: bool = True
    """推荐是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""

    library_recommendations: list[dict] = field(default_factory=list)
    """来自课程拓展阅读库的推荐（每项含 title, file_path, relevance_reason 等）"""

    external_recommendations: list[dict] = field(default_factory=list)
    """来自外部的推荐（每项含 title, author, relevance_reason 等）"""

    reading_path: str = ""
    """建议的阅读顺序和组合策略"""

    total_estimated_hours: int = 0
    """预估总阅读时长"""

    library_count: int = 0
    """库内推荐数"""

    external_count: int = 0
    """外部推荐数"""

    reasoning_content: Optional[str] = None
    """deepseek-reasoner 思维链"""

    warnings: list[str] = field(default_factory=list)
    """非致命警告"""


# ═══════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """
你是一位学习顾问，擅长为学生推荐最适合他们当前阶段的拓展阅读材料。你的任务是根据学生的画像、当前学习的知识点和课程提供的课外阅读库，给出个性化的阅读推荐。

## 推荐原则

### 1. 匹配度优先

根据学生情况，按以下优先级排序推荐：
- **薄弱环节优先**：如果学生在某方面薄弱，优先推荐能帮助巩固基础的材料
- **兴趣驱动**：如果材料与学生兴趣方向匹配，即使难度稍高也可以推荐
- **目标导向**：紧扣学生的短期和长期学习目标
- **难度匹配**：不要给初学者推荐太高深的书，也不要给进阶者推荐太基础的

### 2. 库内 + 库外结合

- 优先从「课程拓展阅读库」中挑选最匹配的 2-5 本
- 如果库内材料不能完全覆盖学生需求，可以补充 1-3 本外部经典读物
- 外部推荐必须是在该领域公认的经典书籍/论文/在线资源

### 3. 阅读建议具体化

每本推荐必须包含：
- 为什么推荐（结合学生的具体情况）
- 建议重点阅读哪些章节
- 预估阅读难度（1-5）

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。

```json
{
    "library_recommendations": [
        {
            "title": "书名（从课程拓展阅读库中选取）",
            "relevance_reason": "结合学生画像的推荐理由（40-80字）",
            "suggested_focus": "建议重点阅读的章节或部分",
            "priority": 5,
            "difficulty_level": 3,
            "tags": ["标签1", "标签2"]
        }
    ],
    "external_recommendations": [
        {
            "title": "书名（外部经典读物）",
            "author": "作者",
            "relevance_reason": "推荐理由（40-80字）",
            "suggested_focus": "建议重点阅读的章节",
            "priority": 3,
            "difficulty_level": 4,
            "tags": ["标签1"]
        }
    ],
    "reading_path": "建议的阅读顺序和组合策略（50-100字）",
    "total_estimated_hours": 20
}
```

## 注意事项

- library_recommendations 中的 title 必须与「课程拓展阅读库」中的材料名称一致
- external_recommendations 可以为空数组 [], 但 library_recommendations 至少应有 1 条
- priority 范围 1-5，5 表示最高优先级
- difficulty_level 范围 1-5，1=入门，5=专业
""".strip()


# ═══════════════════════════════════════════════════════════════
# ReferenceAgent
# ═══════════════════════════════════════════════════════════════

class ReferenceAgent:
    """拓展阅读推荐 Agent。

    根据学生画像和当前知识点，从课程拓展阅读库和外部资源中推荐阅读材料。

    用法::

        from reference_agent import ReferenceAgent
        from utils.material_loader import MaterialLoader

        loader = MaterialLoader("A3/knowledge_base")
        agent = ReferenceAgent()
        result = agent.recommend(knowledge_point, student_profile, loader)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认模型
        temperature: LLM 温度，默认 0.3
        max_tokens: 最大输出 token 数，默认 4096
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self._client = client or get_client()
        self._model = model or Config.DEEPSEEK_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens

    # ── 公开 API ──────────────────────────────────────────

    def recommend(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        shared_refs_summary: str = "",
        shared_refs_list: list[dict] | None = None,
    ) -> ReferenceResult:
        """同步生成拓展阅读推荐。

        参数:
            knowledge_point: 当前学习的知识点（用于匹配相关读物）
            student_profile: 学生画像
            shared_refs_summary: 课程拓展阅读库摘要（由 MaterialLoader.get_shared_references_summary() 提供）
            shared_refs_list: 课程拓展阅读库文件列表（用于回填 file_path）

        返回:
            ReferenceResult: 包含推荐列表的生成结果
        """
        return self._recommend_impl(
            knowledge_point, student_profile, shared_refs_summary, shared_refs_list
        )

    async def recommend_async(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        shared_refs_summary: str = "",
        shared_refs_list: list[dict] | None = None,
    ) -> ReferenceResult:
        """异步生成拓展阅读推荐。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        return await self._recommend_impl_async(
            client, knowledge_point, student_profile, shared_refs_summary, shared_refs_list
        )

    # ── 内部实现 ──────────────────────────────────────────

    def _recommend_impl(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        shared_refs_summary: str,
        shared_refs_list: list[dict] | None,
    ) -> ReferenceResult:
        if not knowledge_point.name:
            return ReferenceResult(success=False, error="知识点名称为空")

        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, shared_refs_summary
        )
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"ReferenceAgent.recommend | kp={knowledge_point.id} | "
            f"has_library={'yes' if shared_refs_summary else 'no'}"
        )

        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(
            response, knowledge_point, student_profile, shared_refs_list or []
        )

    async def _recommend_impl_async(
        self,
        client,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        shared_refs_summary: str,
        shared_refs_list: list[dict] | None,
    ) -> ReferenceResult:
        if not knowledge_point.name:
            return ReferenceResult(success=False, error="知识点名称为空")

        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, shared_refs_summary
        )
        user_message = self._build_user_message(knowledge_point, student_profile)

        response = await client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(
            response, knowledge_point, student_profile, shared_refs_list or []
        )

    def _handle_response(
        self,
        response: LLMResponse,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        shared_refs_list: list[dict],
    ) -> ReferenceResult:
        """处理 LLM 响应 → 回填 file_path → 组装 ResourceOutput。"""

        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return ReferenceResult(success=False, error=response.error or "LLM 调用失败")

        parsed, json_error = extract_json(response.content)
        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return ReferenceResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                reasoning_content=response.reasoning_content,
            )

        library_recs = parsed.get("library_recommendations") or []
        external_recs = parsed.get("external_recommendations") or []
        reading_path = parsed.get("reading_path", "")
        total_hours = parsed.get("total_estimated_hours", 0)

        warnings: list[str] = []

        if not library_recs and not external_recs:
            return ReferenceResult(
                success=False,
                error="LLM 未返回任何推荐（library 和 external 均为空）",
                reasoning_content=response.reasoning_content,
            )

        # ── 回填库内推荐的文件路径 ──
        enriched_library: list[dict] = []
        for rec in library_recs:
            title = str(rec.get("title", "")).strip()
            if not title:
                continue

            # 在 shared_refs_list 中按名称匹配
            matched = None
            for ref in shared_refs_list:
                ref_name = ref.get("name", "")
                if title in ref_name or ref_name in title:
                    matched = ref
                    break

            enriched = {
                "title": title,
                "source": "in_library",
                "file_name": matched.get("name", "") if matched else "",
                "file_path": matched.get("path", "") if matched else "",
                "file_type": matched.get("file_type", "") if matched else "",
                "relevance_reason": str(rec.get("relevance_reason", "")).strip(),
                "suggested_focus": str(rec.get("suggested_focus", "")).strip(),
                "priority": max(1, min(5, int(rec.get("priority", 3)))),
                "difficulty_level": max(1, min(5, int(rec.get("difficulty_level", knowledge_point.difficulty)))),
                "tags": rec.get("tags", []) if isinstance(rec.get("tags"), list) else [],
            }
            enriched_library.append(enriched)

            if matched is None:
                warnings.append(f"库内推荐「{title}」未在 shared_references 中找到匹配文件")

        # ── 整理外部推荐 ──
        enriched_external: list[dict] = []
        for rec in external_recs:
            title = str(rec.get("title", "")).strip()
            if not title:
                continue
            enriched_external.append({
                "title": title,
                "source": "external",
                "author": str(rec.get("author", "")).strip(),
                "relevance_reason": str(rec.get("relevance_reason", "")).strip(),
                "suggested_focus": str(rec.get("suggested_focus", "")).strip(),
                "priority": max(1, min(5, int(rec.get("priority", 2)))),
                "difficulty_level": max(1, min(5, int(rec.get("difficulty_level", 3)))),
                "tags": rec.get("tags", []) if isinstance(rec.get("tags"), list) else [],
            })

        if not enriched_library and not enriched_external:
            return ReferenceResult(
                success=False,
                error="所有推荐标题为空，无法生成有效推荐",
                warnings=warnings,
            )

        # ── 构建 content dict（简化版，避免 Pydantic dict→DocContent 强制转换）──
        content = {
            "recommendation_count": len(enriched_library) + len(enriched_external),
            "library_count": len(enriched_library),
            "external_count": len(enriched_external),
            "reading_path": reading_path,
            "total_estimated_hours": total_hours,
        }

        # ── 构建 ResourceMetadata ──
        profile_snapshot = ""
        if student_profile is not None:
            profile_snapshot = student_profile.snapshot()

        metadata = ResourceMetadata(
            resource_type=ResourceType.DOC,  # 拓展阅读最接近文档类型
            knowledge_point_id=knowledge_point.id,
            knowledge_point_name=knowledge_point.name,
            title=f"{knowledge_point.name} — 拓展阅读推荐",
            difficulty=knowledge_point.difficulty,
            estimated_read_time_minutes=total_hours * 60 if total_hours else 30,
            tags=knowledge_point.tags + ["拓展阅读"],
            student_profile_snapshot=profile_snapshot,
        )

        resource = ResourceOutput(
            metadata=metadata,
            content=content,
            status="generated",
            generated_by="ReferenceAgent",
        )

        logger.info(
            f"ReferenceAgent 结果 | library={len(enriched_library)} | "
            f"external={len(enriched_external)} | warnings={len(warnings)}"
        )

        return ReferenceResult(
            resource=resource,
            success=True,
            library_recommendations=enriched_library,
            external_recommendations=enriched_external,
            reading_path=reading_path,
            total_estimated_hours=total_hours,
            library_count=len(enriched_library),
            external_count=len(enriched_external),
            reasoning_content=response.reasoning_content,
            warnings=warnings,
        )

    # ── Prompt 构建 ──────────────────────────────────────

    def _build_system_prompt(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        shared_refs_summary: str,
    ) -> str:
        prompt = _SYSTEM_PROMPT

        prompt += f"""

## 当前知识点

- 名称: {knowledge_point.name}
- 描述: {knowledge_point.description or '暂无'}
- 分类: {knowledge_point.category or '未分类'}
- 难度: {knowledge_point.difficulty}/5
- 标签: {', '.join(knowledge_point.tags) if knowledge_point.tags else '无'}
"""

        if student_profile is not None:
            snapshot = student_profile.snapshot()
            if snapshot.strip():
                prompt += f"""
## 学生画像

{snapshot}
"""
        else:
            prompt += "\n## 学生画像\n\n未提供，请使用通用推荐策略。\n"

        if shared_refs_summary and shared_refs_summary.strip():
            prompt += f"\n{shared_refs_summary}\n"
        else:
            prompt += "\n## 课程拓展阅读库\n\n未提供课外阅读库，请全部使用外部推荐。\n"

        return prompt

    def _build_user_message(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
    ) -> str:
        parts = [
            f"请为正在学习「{knowledge_point.name}」的学生推荐拓展阅读材料。",
            f"先从课程拓展阅读库中挑选最匹配的 2-5 本，必要时补充 1-3 本外部经典。",
        ]

        if student_profile is not None:
            if student_profile.weak_points:
                wp_names = [w.knowledge_point_name for w in student_profile.weak_points]
                parts.append(f"学生薄弱环节: {', '.join(wp_names)}，请优先推荐能帮助克服这些薄弱点的材料。")
            if student_profile.interest_domains:
                parts.append(f"学生兴趣方向: {', '.join(student_profile.interest_domains)}。")
            if student_profile.learning_goal_long:
                parts.append(f"长期目标: {student_profile.learning_goal_long}。")

        return " ".join(parts)
