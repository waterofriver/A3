# -*- coding: utf-8 -*-
"""
讲义文档生成 Agent (Doc Agent)
==============================
根据知识点信息和学生画像，生成结构化讲义文档。

设计原则：
- 无状态：每次 generate() 调用独立
- 个性化：根据学生画像调整内容深度、示例风格和讲解方式
- 结构化输出：多章节 + 要点提炼 + 总结 + 延伸阅读
- 同步和异步两套 API

用法示例::

    from doc_agent import DocAgent

    agent = DocAgent()
    result = agent.generate(knowledge_point, student_profile)
    if result.success:
        for section in result.resource.content.sections:
            print(section["heading"])
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
    DocContent,
    ResourceMetadata,
    ResourceOutput,
    ResourceType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════


@dataclass
class DocResult:
    """讲义文档生成的返回结果。"""

    resource: Optional[ResourceOutput] = None
    """生成的资源（含 metadata 和 DocContent）；失败时为 None"""

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
你是一位经验丰富的课程讲师，擅长编写结构清晰、深入浅出的讲义文档。你的任务是根据给定的知识点和学生画像，生成一份个性化讲义。

## 核心原则

1. **因材施教**：根据学生的认知风格调整讲解方式
   - 偏理论型学生：多讲原理推导、数学模型、底层机制
   - 偏实践型学生：多给操作步骤、代码示例、实验演示
   - 均衡型学生：理论实践各半，穿插进行

2. **阶梯式讲解**：从直观概念 → 核心原理 → 深入细节 → 实践应用
   - 薄弱知识点应在相关章节增加详细解释和更多示例
   - 已有基础的知识点可以适当简化基础部分，深入高级内容

3. **Markdown 格式**：body_markdown 字段必须使用标准 Markdown 语法
   - 支持标题、列表、代码块、表格、加粗/斜体、链接
   - 代码块标注语言：```python、```bash、```cpp 等
   - 重要概念使用 **加粗** 强调
   - 公式可使用 $$ 或 $ 包裹（LaTeX）

4. **关键要点提炼**：每个章节末尾给出 3-5 个 key_points，便于复习

## 讲义结构要求

讲义必须包含 3-6 个 sections，建议结构如下：

1. **概念导入**（必选）：用生活化例子引入，让初学者建立直观认识
2. **核心原理**（必选）：深入讲解工作机制、关键算法或协议流程
3. **详细解析**（可选）：分点展开重难点，附带图解说明
4. **实践案例**（必选）：给出可操作的实验、代码或练习
5. **常见误区/注意事项**（可选）：针对学生薄弱点强调避坑指南
6. **本章总结**（必选）：归纳核心要点，连接前后知识点

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块，不要输出任何其他文字。

```json
{
    "sections": [
        {
            "heading": "章节标题（如：一、概念导入：什么是XXX）",
            "body_markdown": "章节正文，使用标准 Markdown 格式。支持标题、列表、代码块、加粗、表格等。\\n\\n可包含多个段落。",
            "key_points": [
                "关键要点1：一句话概括",
                "关键要点2：一句话概括",
                "关键要点3：一句话概括"
            ]
        }
    ],
    "summary": "全文总结，2-3句话概括本讲义的核心内容和学习目标",
    "further_reading": [
        "推荐阅读1：书名/文章名 + 一句话说明",
        "推荐阅读2：书名/文章名 + 一句话说明"
    ]
}
```

## 内容质量要求

- 每个 section 的 body_markdown 至少 200 字，内容丰富不空洞
- 实践案例部分必须给出可直接操作的步骤或可运行的代码
- 术语首次出现时给出简短解释
- 难度匹配知识点的 difficulty 等级（1=入门科普, 5=高阶专业）
- 总字数建议 1500-4000 字（含 Markdown 标记）
- key_points 不要简单重复正文标题，要提炼出"读完这一节应该记住什么"
## 课件参考材料

如果提供了"课件参考资料"（从课程原始 PDF/PPTX/DOCX 中提取），你必须：
- **以课件内容为主要依据**，确保知识点定义、术语、实验步骤与课件一致
- 在课件内容的基础上进行扩展讲解、补充背景和案例分析
- 不要编造与课件矛盾的概念或流程
- 如果课件中没有覆盖某方面，可以基于你的知识补充，但要标注「补充知识」

""".strip()


# ═══════════════════════════════════════════════════════════════
# DocAgent
# ═══════════════════════════════════════════════════════════════


class DocAgent:
    """讲义文档生成 Agent。

    根据知识点和学生画像，生成结构化的个性化讲义。

    用法::

        from doc_agent import DocAgent

        agent = DocAgent()
        result = agent.generate(knowledge_point, student_profile)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认模型
        temperature: LLM 温度，默认 0.3（保证质量的同时有一定创造性）
        max_tokens: 最大输出 token 数，默认 8192（讲义较长）
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 8192,
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
    ) -> DocResult:
        """同步生成讲义文档。

        参数:
            knowledge_point: 目标知识点
            student_profile: 学生画像（None 则使用默认通用风格）
            material_context: 从课件材料中提取的参考文本（由 MaterialLoader 提供），
                              注入 System Prompt 以确保内容与课件一致

        返回:
            DocResult: 包含 ResourceOutput 的生成结果
        """
        return self._generate_impl(knowledge_point, student_profile, material_context)

    async def generate_async(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
    ) -> DocResult:
        """异步生成讲义文档。签名与 generate 一致。"""
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
    ) -> DocResult:
        """同步生成的核心实现。"""

        # 0. 输入校验
        if not knowledge_point.name:
            return DocResult(
                success=False,
                error="知识点名称为空",
            )

        # 1. 构建消息
        system_prompt = self._build_system_prompt(knowledge_point, student_profile, material_context)
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"DocAgent.generate | model={self._model} | "
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
    ) -> DocResult:
        """异步生成的核心实现。"""

        if not knowledge_point.name:
            return DocResult(
                success=False,
                error="知识点名称为空",
            )

        system_prompt = self._build_system_prompt(knowledge_point, student_profile, material_context)
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"DocAgent.generate_async | model={self._model} | "
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
    ) -> DocResult:
        """统一处理 LLM 响应：解析 JSON → 构建 DocContent → 包装 ResourceOutput。"""

        # LLM 调用失败
        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return DocResult(
                success=False,
                error=response.error or "LLM 调用失败",
            )

        # 解析 JSON
        parsed, json_error = extract_json(response.content)

        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return DocResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                reasoning_content=response.reasoning_content,
            )

        # 提取字段
        sections = parsed.get("sections") or []
        summary = parsed.get("summary") or ""
        further_reading = parsed.get("further_reading") or []

        # ── 空内容检测 ──
        if not sections:
            logger.warning("LLM 返回了空的 sections 列表")
            return DocResult(
                success=False,
                error="LLM 未生成任何讲义章节（sections 为空），请重试",
                reasoning_content=response.reasoning_content,
            )

        # ── 质量检测 ──
        warnings: list[str] = []

        total_length = sum(
            len(s.get("body_markdown", "")) for s in sections
        )
        if total_length < 500:
            warnings.append(
                f"讲义总长度仅 {total_length} 字符，内容可能不够充实，建议重试"
            )

        sections_without_key_points = [
            s.get("heading", "?") for s in sections
            if not s.get("key_points")
        ]
        if sections_without_key_points:
            warnings.append(
                f"以下章节缺少 key_points: {', '.join(sections_without_key_points[:3])}"
            )

        # ── 校验并规范化每个 section ──
        validated_sections: list[dict] = []
        for i, sec in enumerate(sections):
            heading = str(sec.get("heading", f"第{i+1}节")).strip()
            body = str(sec.get("body_markdown", "")).strip()
            key_points = sec.get("key_points", [])

            if not body:
                logger.warning(f"章节 '{heading}' 的 body_markdown 为空，跳过")
                continue

            if isinstance(key_points, str):
                key_points = [key_points]
            key_points = [str(kp).strip() for kp in key_points if kp]

            validated_sections.append({
                "heading": heading,
                "body_markdown": body,
                "key_points": key_points,
            })

        if not validated_sections:
            return DocResult(
                success=False,
                error="所有章节的 body_markdown 均为空，无法生成有效讲义",
                reasoning_content=response.reasoning_content,
                warnings=warnings,
            )

        # ── 估算阅读时长 ──
        estimated_minutes = max(5, total_length // 400)  # 约 400 字/分钟

        # ── 构建 DocContent ──
        doc_content = DocContent(
            sections=validated_sections,
            summary=summary,
            further_reading=further_reading,
        )

        # ── 构建 ResourceMetadata ──
        profile_snapshot = ""
        if student_profile is not None:
            profile_snapshot = student_profile.snapshot()

        metadata = ResourceMetadata(
            resource_type=ResourceType.DOC,
            knowledge_point_id=knowledge_point.id,
            knowledge_point_name=knowledge_point.name,
            title=f"{knowledge_point.name} — 学习讲义",
            difficulty=knowledge_point.difficulty,
            estimated_read_time_minutes=estimated_minutes,
            tags=knowledge_point.tags,
            student_profile_snapshot=profile_snapshot,
        )

        # ── 组装 ResourceOutput ──
        resource = ResourceOutput(
            metadata=metadata,
            content=doc_content,
            status="generated",
            generated_by="DocAgent",
        )

        logger.info(
            f"DocAgent 结果 | sections={len(validated_sections)} | "
            f"total_length={total_length} | "
            f"estimated_minutes={estimated_minutes} | "
            f"warnings={len(warnings)}"
        )

        return DocResult(
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
- 前置知识: {', '.join(knowledge_point.prerequisites) if knowledge_point.prerequisites else '无（入口知识点）'}
"""

        # 注入学生画像
        if student_profile is not None:
            snapshot = student_profile.snapshot()
            if snapshot.strip():
                prompt += f"""
## 学生画像

{snapshot}

请根据以上画像调整讲义的内容深度、示例风格和讲解方式。
"""
        else:
            prompt += """
## 学生画像

未提供学生画像，请使用通用的入门级讲解风格，兼顾理论和实践。
"""

        # ── 注入课件参考材料 ──
        if material_context and material_context.strip():
            # 限制材料上下文不超过 15000 字符，避免超出 token 限制
            ctx = material_context.strip()
            if len(ctx) > 15000:
                ctx = ctx[:15000] + "\n\n...(课件内容过长，已截断)"
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
            f"请为知识点「{knowledge_point.name}」编写一份完整的讲义文档。",
            f"该知识点属于「{knowledge_point.category}」分类，难度 {knowledge_point.difficulty}/5。",
        ]

        if student_profile is not None:
            if student_profile.weak_points:
                wp_names = [w.knowledge_point_name for w in student_profile.weak_points]
                parts.append(f"学生薄弱环节: {', '.join(wp_names)}，相关章节请重点展开。")
            if student_profile.cognitive_style == "theory_oriented":
                parts.append("学生偏好理论推导，请侧重原理和数学建模。")
            elif student_profile.cognitive_style == "practice_oriented":
                parts.append("学生偏好动手实践，请侧重操作步骤和代码示例。")

        return " ".join(parts)
