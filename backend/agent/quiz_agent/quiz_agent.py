# -*- coding: utf-8 -*-
"""
题库生成 Agent (Quiz Agent)
===========================
根据知识点信息、学生画像和课件材料，生成个性化练习题。

设计原则：
- 无状态：每次 generate() 调用独立
- 个性化：根据学生画像调整题型分布、难度侧重和解析详细度
- 课件驱动：基于课件材料中的术语、步骤、参数出题
- 四类题型：单选、多选、判断、简答
- 同步和异步两套 API

用法示例::

    from quiz_agent import QuizAgent

    agent = QuizAgent()
    result = agent.generate(knowledge_point, student_profile)
    if result.success:
        for item in result.resource.content.items:
            print(item.stem)
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
    QuizItem,
    QuizContent,
    ResourceMetadata,
    ResourceOutput,
    ResourceType,
    QuestionType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class QuizResult:
    """题库生成的返回结果。"""

    resource: Optional[ResourceOutput] = None
    """生成的资源（含 metadata 和 QuizContent）；失败时为 None"""

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
你是一位资深课程命题专家，擅长根据教学内容设计高质量的练习题。你的任务是根据给定的知识点、学生画像和课件参考材料，生成一套个性化练习题。

## 核心原则

### 1. 题型设计

支持四种题型，按比例混合：

| 题型 | question_type | 占比 | 适用场景 |
|------|-------------|------|---------|
| 单选题 | single_choice | ~40% | 概念辨析、参数选择、步骤判断 |
| 多选题 | multiple_choice | ~30% | 多要素识别、综合理解 |
| 判断题 | true_false | ~15% | 关键细节确认、常见误区纠正 |
| 简答题 | short_answer | ~15% | 原理阐述、流程描述、实验分析 |

### 2. 难度适配

根据知识点难度和学生画像调整题目难度分布：
- 知识点难度 1-2（入门）: 70% 基础题 + 30% 进阶题
- 知识点难度 3（核心）: 40% 基础题 + 40% 进阶题 + 20% 挑战题
- 知识点难度 4-5（高阶）: 20% 基础题 + 40% 进阶题 + 40% 挑战题

对于学生的**薄弱环节**：增加基础题比例，解析要特别详细，帮助学生建立信心。

### 3. 个性化规则

- **偏理论型学生**: 增加概念辨析、原理阐述类题目
- **偏实践型学生**: 增加操作步骤、命令选择、故障排查类题目
- **学生已有基础**: 已掌握的知识点可以出高阶应用题，未接触的从基础开始

### 4. 课件依据

如果提供了"课件参考资料"，你必须：
- 题目中的术语、命令、参数名与课件保持一致
- 操作步骤题必须与课件中的实验步骤匹配
- 正确选项必须在课件中有明确依据
- 错误选项（干扰项）也应当是合理的常见错误，不能随意编造

### 5. 解析要求

每道题的 explanation 必须：
- 指出正确选项为什么对（引用课件中的依据或原理）
- 对于选择题，解释为什么其他选项是错的
- 对于错误选项，指出混淆点在哪里
- 解析长度建议 80-300 字

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。只输出 JSON 代码块。

```json
{
    "items": [
        {
            "question_type": "single_choice",
            "stem": "题干的完整描述，要清晰明确",
            "options": ["A. 选项A的描述", "B. 选项B的描述", "C. 选项C的描述", "D. 选项D的描述"],
            "correct_answer": "A",
            "explanation": "详细解析：A正确，因为...；B错误，因为...；C错误，因为...",
            "difficulty": 2,
            "knowledge_point_tags": ["ARP", "中间人攻击"]
        },
        {
            "question_type": "multiple_choice",
            "stem": "多选题的题干描述",
            "options": ["A. 正确项1", "B. 正确项2", "C. 错误项1", "D. 正确项3"],
            "correct_answer": "ABD",
            "explanation": "详细解析...",
            "difficulty": 3,
            "knowledge_point_tags": ["ARP", "网络协议"]
        },
        {
            "question_type": "true_false",
            "stem": "判断题的题干（陈述句）",
            "options": ["正确", "错误"],
            "correct_answer": "正确",
            "explanation": "为什么这个陈述是正确的...",
            "difficulty": 1,
            "knowledge_point_tags": ["ARP缓存"]
        },
        {
            "question_type": "short_answer",
            "stem": "简答题的题干",
            "options": [],
            "correct_answer": "参考答案要点：1. ... 2. ... 3. ...",
            "explanation": "答题要点说明...",
            "difficulty": 3,
            "knowledge_point_tags": ["ARP协议", "安全分析"]
        }
    ],
    "total_count": 8,
    "suggested_duration_minutes": 20
}
```

## 数量与时长

- items 中题目数量: 5-10 道（默认 8 道）
- total_count 必须等于 items 数组的实际长度
- suggested_duration_minutes: 按每道题 2-3 分钟估算（简答题 5 分钟）

## 选项格式

- 单选题和多选题的选项以 "A. " "B. " "C. " "D. " 开头
- 判断题的 options 固定为 ["正确", "错误"]
- 简答题的 options 为空数组 []
- 多选题的 correct_answer 是正确选项字母的拼接，如 "ABD"
""".strip()


# ═══════════════════════════════════════════════════════════════
# QuizAgent
# ═══════════════════════════════════════════════════════════════

class QuizAgent:
    """题库生成 Agent。

    根据知识点、学生画像和课件材料，生成个性化练习题。

    用法::

        from quiz_agent import QuizAgent

        agent = QuizAgent()
        result = agent.generate(knowledge_point, student_profile)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认模型
        temperature: LLM 温度，默认 0.3
        max_tokens: 最大输出 token 数，默认 8192
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
        question_count: int = 8,
    ) -> QuizResult:
        """同步生成题库。

        参数:
            knowledge_point: 目标知识点
            student_profile: 学生画像（None 则使用默认通用风格）
            material_context: 从课件材料中提取的参考文本（由 MaterialLoader 提供）
            question_count: 期望生成的题目数量（5-10）

        返回:
            QuizResult: 包含 ResourceOutput 的生成结果
        """
        count = max(5, min(10, question_count))
        return self._generate_impl(knowledge_point, student_profile, material_context, count)

    async def generate_async(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
        question_count: int = 8,
    ) -> QuizResult:
        """异步生成题库。签名与 generate 一致。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        count = max(5, min(10, question_count))
        return await self._generate_impl_async(
            client, knowledge_point, student_profile, material_context, count
        )

    # ── 内部实现 ──────────────────────────────────────────

    def _generate_impl(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str,
        question_count: int,
    ) -> QuizResult:
        """同步生成的核心实现。"""

        if not knowledge_point.name:
            return QuizResult(success=False, error="知识点名称为空")

        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, material_context, question_count
        )
        user_message = self._build_user_message(knowledge_point, student_profile, question_count)

        logger.info(
            f"QuizAgent.generate | model={self._model} | "
            f"kp={knowledge_point.id} | difficulty={knowledge_point.difficulty} | "
            f"target_count={question_count}"
        )

        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(response, knowledge_point, student_profile)

    async def _generate_impl_async(
        self,
        client,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str,
        question_count: int,
    ) -> QuizResult:
        """异步生成的核心实现。"""

        if not knowledge_point.name:
            return QuizResult(success=False, error="知识点名称为空")

        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, material_context, question_count
        )
        user_message = self._build_user_message(knowledge_point, student_profile, question_count)

        logger.info(
            f"QuizAgent.generate_async | model={self._model} | kp={knowledge_point.id}"
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
    ) -> QuizResult:
        """统一处理 LLM 响应：解析 JSON → 校验题目 → 构建 QuizContent → 包装 ResourceOutput。"""

        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return QuizResult(success=False, error=response.error or "LLM 调用失败")

        parsed, json_error = extract_json(response.content)
        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            return QuizResult(
                success=False,
                error=f"JSON 解析失败: {json_error}",
                reasoning_content=response.reasoning_content,
            )

        raw_items = parsed.get("items") or []
        total_count = parsed.get("total_count", len(raw_items))
        suggested_minutes = parsed.get("suggested_duration_minutes", 15)

        # ── 空内容检测 ──
        if not raw_items:
            logger.warning("LLM 返回了空的 items 列表")
            return QuizResult(
                success=False,
                error="LLM 未生成任何题目（items 为空），请重试",
                reasoning_content=response.reasoning_content,
            )

        # ── 逐题校验 ──
        warnings: list[str] = []
        validated_items: list[QuizItem] = []
        type_counts: dict[str, int] = {}

        for i, item_data in enumerate(raw_items):
            # 题型
            q_type_str = item_data.get("question_type", "")
            try:
                q_type = QuestionType(q_type_str)
            except ValueError:
                warnings.append(f"第{i+1}题题型无效 '{q_type_str}'，跳过")
                continue

            # 题干
            stem = str(item_data.get("stem", "")).strip()
            if not stem:
                warnings.append(f"第{i+1}题题干为空，跳过")
                continue

            # 选项
            options = item_data.get("options", [])
            if isinstance(options, str):
                options = [options]
            options = [str(o).strip() for o in options if o]

            # 正确答案
            correct_answer = str(item_data.get("correct_answer", "")).strip()
            if not correct_answer:
                warnings.append(f"第{i+1}题缺少正确答案，跳过")
                continue

            # 解析
            explanation = str(item_data.get("explanation", "")).strip()

            # 难度
            difficulty = int(item_data.get("difficulty", knowledge_point.difficulty))
            difficulty = max(1, min(5, difficulty))

            # 标签
            tags = item_data.get("knowledge_point_tags", [])
            if isinstance(tags, str):
                tags = [tags]
            tags = [str(t).strip() for t in tags if t]

            try:
                item = QuizItem(
                    question_type=q_type,
                    stem=stem,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    difficulty=difficulty,
                    knowledge_point_tags=tags,
                )
                validated_items.append(item)
                type_counts[q_type_str] = type_counts.get(q_type_str, 0) + 1
            except Exception as e:
                warnings.append(f"第{i+1}题校验失败: {e}")
                continue

        # ── 全部无效 → 失败 ──
        if not validated_items:
            return QuizResult(
                success=False,
                error="所有题目均校验失败，无法生成有效题库",
                reasoning_content=response.reasoning_content,
                warnings=warnings,
            )

        # ── 质量检测 ──
        if len(validated_items) < 5:
            warnings.append(f"有效题目仅 {len(validated_items)} 道（预期 ≥5），建议重试")

        no_explanation = sum(1 for item in validated_items if not item.explanation)
        if no_explanation > 0:
            warnings.append(f"{no_explanation} 道题目缺少解析")

        # 题型分布
        valid_types = set(item.question_type.value for item in validated_items)
        if len(valid_types) < 2:
            warnings.append(f"题型过于单一（仅 {valid_types}），建议混合多种题型")

        # ── 构建 QuizContent ──
        quiz_content = QuizContent(
            items=validated_items,
            total_count=len(validated_items),
            suggested_duration_minutes=max(5, suggested_minutes),
        )

        # ── 构建 ResourceMetadata ──
        profile_snapshot = ""
        if student_profile is not None:
            profile_snapshot = student_profile.snapshot()

        metadata = ResourceMetadata(
            resource_type=ResourceType.QUIZ,
            knowledge_point_id=knowledge_point.id,
            knowledge_point_name=knowledge_point.name,
            title=f"{knowledge_point.name} — 练习题",
            difficulty=knowledge_point.difficulty,
            estimated_read_time_minutes=quiz_content.suggested_duration_minutes,
            tags=knowledge_point.tags,
            student_profile_snapshot=profile_snapshot,
        )

        resource = ResourceOutput(
            metadata=metadata,
            content=quiz_content,
            status="generated",
            generated_by="QuizAgent",
        )

        logger.info(
            f"QuizAgent 结果 | items={len(validated_items)} | "
            f"types={dict(type_counts)} | "
            f"duration={quiz_content.suggested_duration_minutes}min | "
            f"warnings={len(warnings)}"
        )

        return QuizResult(
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
        material_context: str,
        question_count: int,
    ) -> str:
        """构建 System Prompt。"""
        prompt = _SYSTEM_PROMPT

        # 知识点
        prompt += f"""

## 当前知识点

- 名称: {knowledge_point.name}
- 描述: {knowledge_point.description or '暂无描述'}
- 分类: {knowledge_point.category or '未分类'}
- 难度: {knowledge_point.difficulty}/5
- 标签: {', '.join(knowledge_point.tags) if knowledge_point.tags else '无'}
- 期望题目数: {question_count} 道
"""

        # 学生画像
        if student_profile is not None:
            snapshot = student_profile.snapshot()
            if snapshot.strip():
                prompt += f"""
## 学生画像

{snapshot}

请根据以上画像调整：
- 题型分布（理论型→增加概念辨析，实践型→增加操作步骤题）
- 难度侧重（薄弱环节→增加基础题，详细解析）
- 示例场景（结合学生兴趣方向）
"""
        else:
            prompt += "\n## 学生画像\n\n未提供，请使用通用均衡风格。\n"

        # 课件材料
        if material_context and material_context.strip():
            ctx = material_context.strip()
            if len(ctx) > 12000:
                ctx = ctx[:12000] + "\n\n...(截断)"
            prompt += f"\n{ctx}\n"

        return prompt

    # ── User Message 构建 ─────────────────────────────────

    def _build_user_message(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        question_count: int,
    ) -> str:
        """构建 user message。"""
        parts = [
            f"请为知识点「{knowledge_point.name}」生成 {question_count} 道练习题。",
            f"知识点分类: {knowledge_point.category}，难度 {knowledge_point.difficulty}/5。",
        ]

        if student_profile is not None:
            if student_profile.weak_points:
                wp_names = [w.knowledge_point_name for w in student_profile.weak_points]
                if knowledge_point.name in wp_names or any(
                    w.knowledge_point_id == knowledge_point.id
                    for w in student_profile.weak_points
                ):
                    parts.append("这是学生的薄弱环节，请增加基础题比例，解析要特别详细。")
            if student_profile.cognitive_style == "theory_oriented":
                parts.append("学生偏理论型，请侧重概念辨析和原理阐述。")
            elif student_profile.cognitive_style == "practice_oriented":
                parts.append("学生偏实践型，请侧重操作步骤和故障排查。")

        parts.append("请确保题型混合：约40%单选 + 30%多选 + 15%判断 + 15%简答。")
        return " ".join(parts)
