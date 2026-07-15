"""
RealAgentProvider —— 将 FastAPI 网关桥接到本地 Agent 引擎。

当 AGENT_MODE=local 时使用。直接调用 agent/ 目录下的 8 个 Agent，
通过 DeepSeek API 生成真实的 AI 内容。

Agent 引擎是同步的，FastAPI 需要异步 → 用 asyncio.to_thread() 包装。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional

from app.agents.base import AgentProvider, ResourceAgentEvent, ResourceDraft
from app.schemas.learning import LearningPathDraft, LearningPathNodeDraft
from app.schemas.evaluation import (
    EvaluationDraft,
    EvaluationEvidence,
    EvaluationWeakPoint,
    EvaluationRecommendedChange,
)
from app.schemas.profile import StudentProfileData
from app.schemas.qa import AnswerMode
from app.schemas.resource import ResourceSummary, ResourceType
from app.schemas.task import GatewayEvent

from agent.config import Config
from agent.models import (
    StudentProfile,
    KnowledgeBaseItem,
    WeakPoint,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
)
from agent.utils.material_loader import MaterialLoader

logger = logging.getLogger(__name__)

# ── 路径常亮 ──────────────────────────────────────────────
# agent/ 目录在 backend/agent/，知识库在 A3/knowledge_base/
_AGENT_DIR = Path(__file__).resolve().parent.parent.parent / "agent"
_KB_DIR = _AGENT_DIR.parent.parent / "knowledge_base"  # A3/knowledge_base/
_MATERIALS_DIR = _KB_DIR / "materials"

# ── Agent 实例（每次调用新建，无状态共享）─────────────────

def _material_loader() -> MaterialLoader:
    return MaterialLoader(str(_KB_DIR.resolve()))


# ═══════════════════════════════════════════════════════════════
# 画像格式转换
# ═══════════════════════════════════════════════════════════════

def _api_to_agent_profile(api: StudentProfileData) -> StudentProfile:
    """API 画像 → Agent 画像（保留尽量多信息以便增量更新）。"""
    kb_items: list[KnowledgeBaseItem] = []
    if api.knowledge_foundation and api.knowledge_foundation != "待采集":
        for part in api.knowledge_foundation.split("\n"):
            part = part.strip()
            if part and ":" not in part and len(part) < 50:
                kb_items.append(KnowledgeBaseItem(
                    knowledge_point_id=part[:20].replace(" ", "_"),
                    knowledge_point_name=part[:30],
                    mastery=MasteryLevel.FAMILIAR,
                ))

    weak_points: list[WeakPoint] = []
    for wp_name in (api.weak_points or []):
        if wp_name.strip():
            weak_points.append(WeakPoint(
                knowledge_point_id=wp_name[:20].replace(" ", "_"),
                knowledge_point_name=wp_name.strip(),
                error_pattern="",
                occurrence_count=1,
            ))

    cognitive_map = {
        "偏理论": CognitiveStyle.THEORY_ORIENTED,
        "偏实践": CognitiveStyle.PRACTICE_ORIENTED,
    }
    pace_map = {
        "密集突击": LearningPace.INTENSIVE,
        "分散学习": LearningPace.DISTRIBUTED,
    }

    return StudentProfile(
        major="",
        grade="",
        cognitive_style=cognitive_map.get(api.cognitive_style or "", CognitiveStyle.BALANCED),
        learning_goal_short=api.short_term_goal or "",
        learning_goal_long="",
        weak_points=weak_points,
        learning_pace=pace_map.get(api.learning_pace or "", LearningPace.FLEXIBLE),
        interest_domains=list(set(api.content_preferences or [])),
        knowledge_base=kb_items,
    )


def _agent_to_api_profile(agent: StudentProfile) -> dict:
    """Agent 画像 → API profile_patch dict。"""
    cognitive_labels = {
        "theory_oriented": "偏理论",
        "practice_oriented": "偏实践",
        "balanced": "均衡型",
    }
    pace_labels = {
        "intensive": "密集突击",
        "distributed": "分散学习",
        "flexible": "灵活适应",
    }

    knowledge_text = agent.snapshot()

    return {
        "knowledge_foundation": knowledge_text or "待采集",
        "cognitive_style": cognitive_labels.get(agent.cognitive_style, "均衡型"),
        "weak_points": list({w.knowledge_point_name for w in agent.weak_points}),
        "learning_pace": pace_labels.get(agent.learning_pace, "灵活适应"),
        "content_preferences": list({d for d in agent.interest_domains if d}),
        "short_term_goal": agent.learning_goal_short or "待采集",
    }


def _profile_ready(profile) -> bool:
    """严格检验画像是否真的有足够维度（不信任 LLM 的 is_complete）。"""
    filled = 0
    # 1. 基础信息：major 和 grade 至少一个有非默认值
    if profile.major or profile.grade:
        filled += 1
    # 2. 知识基础：至少有一个知识点
    if profile.knowledge_base:
        filled += 1
    # 3. 认知风格：非默认 BALANCED
    if profile.cognitive_style and str(profile.cognitive_style) != "balanced":
        filled += 1
    # 4. 学习目标：短目标或长目标有实质内容（排除默认空字符串）
    if profile.learning_goal_short and profile.learning_goal_short.strip():
        filled += 1
    elif profile.learning_goal_long and profile.learning_goal_long.strip():
        filled += 1
    # 5. 薄弱环节：有列出的薄弱点
    if profile.weak_points:
        filled += 1
    # 6. 学习节奏与兴趣
    if profile.learning_pace and str(profile.learning_pace) != "flexible":
        filled += 1
    elif profile.interest_domains:
        filled += 1

    return filled >= 5


def _is_confirmation_message(text: str) -> bool:
    """检测用户输入是否为对画像完成的确认/接受（而非新的画像信息）。"""
    if not text or not text.strip():
        return False
    text = text.strip()
    # 短确认词
    confirm_words = ["好", "好的", "可以", "行", "嗯", "对", "是的", "没错", "ok", "yes", "确认"]
    if text in confirm_words:
        return True
    if len(text) <= 15 and any(w in text for w in confirm_words):
        return True
    # 包含规划/路径请求的短消息
    path_words = ["规划", "路径", "计划", "安排", "接下来", "下一步", "然后"]
    if any(w in text for w in path_words) and len(text) <= 30:
        return True
    return False


def _match_knowledge_point(weak_point: str, dag) -> Optional[object]:
    """用关键词分词匹配知识点，而非完整子串匹配。

    例如用户输入 "ARP攻击比较难" 可以匹配到 "实验五：ARP 中毒攻击"。
    """
    if not weak_point or not weak_point.strip():
        return None

    text = weak_point.strip().lower()
    # 提取文本中的英文关键词（如 ARP, ROS, SLAM, DOS 等）
    import re
    keywords = set(re.findall(r'[a-zA-Z0-9]{2,}', text))
    # 也加入中文关键词（2-4字符的片段）
    for i in range(len(text)):
        for j in range(i+2, min(i+5, len(text)+1)):
            keywords.add(text[i:j])

    best_kp = None
    best_score = 0

    for kp in dag.knowledge_points:
        search_text = (kp.name + " " + kp.description + " " + " ".join(kp.tags)).lower()
        score = 0
        for kw in keywords:
            if kw in search_text:
                score += len(kw) * 2  # 英文关键词权重更高
        if score > best_score:
            best_score = score
            best_kp = kp

    return best_kp if best_score > 0 else None


# ═══════════════════════════════════════════════════════════════
# RealAgentProvider
# ═══════════════════════════════════════════════════════════════

class RealAgentProvider(AgentProvider):
    """本地 Agent 引擎 Provider。"""

    def __init__(self, db=None):
        self._db = db

    # ── 画像采集 ──────────────────────────────────────────

    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        from agent.profile_agent import ProfileAgent
        from app.db.models import ProfileMessage

        existing = _api_to_agent_profile(current_profile) if current_profile else None

        # ── 加载历史对话 ──
        conversation_history: list[dict] = []
        if self._db is not None:
            try:
                with self._db.session() as session:
                    rows = (
                        session.query(ProfileMessage)
                        .filter(ProfileMessage.user_id == user_id)
                        .order_by(ProfileMessage.created_at)
                        .all()
                    )
                    conversation_history = [
                        {"role": row.role, "content": row.content}
                        for row in rows
                    ]
            except Exception:
                pass  # DB 不可用时忽略

        # ── 死循环检测：画像已基本完整 + 用户明显在确认 → 跳过ProfileAgent ──
        is_confirmation = _is_confirmation_message(chat_text)
        profile_is_rich = current_profile and (
            (current_profile.knowledge_foundation and current_profile.knowledge_foundation != "待采集") and
            (current_profile.cognitive_style and current_profile.cognitive_style != "待采集")
        )

        if is_confirmation and profile_is_rich:
            # 直接返回引导消息，不再调 ProfileAgent
            yield GatewayEvent(
                event="task.started", task_id=task_id, trace_id=trace_id,
                current_agent="画像Agent", progress=0, demo_mode=False,
            )
            yield GatewayEvent(
                event="content.delta", task_id=task_id, trace_id=trace_id,
                current_agent="画像Agent", progress=50,
                content="你的画像已经采集完成了！点击左侧导航栏的「学习路径」即可查看个性化学习路径，"
                        "或者去「资源工作台」选择薄弱知识点后生成专属学习资料。",
                demo_mode=False,
            )
            if current_profile:
                yield GatewayEvent(
                    event="profile.patch", task_id=task_id, trace_id=trace_id,
                    current_agent="画像Agent", progress=80,
                    profile_patch=current_profile.model_dump(), demo_mode=False,
                )
            yield GatewayEvent(
                event="task.completed", task_id=task_id, trace_id=trace_id,
                current_agent="画像Agent", progress=100, finish_flag=True, demo_mode=False,
            )
            return

        yield GatewayEvent(
            event="task.started", task_id=task_id, trace_id=trace_id,
            current_agent="主管Agent", progress=0, demo_mode=False,
        )

        yield GatewayEvent(
            event="agent.started", task_id=task_id, trace_id=trace_id,
            current_agent="画像Agent", progress=10, demo_mode=False,
        )

        # 在线程池执行同步 ProfileAgent（传入历史对话）
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: ProfileAgent().extract(
                chat_text,
                existing_profile=existing,
                conversation_history=conversation_history,
            ),
        )

        if not result.success:
            yield GatewayEvent(
                event="task.failed", task_id=task_id, trace_id=trace_id,
                current_agent="画像Agent", progress=0, finish_flag=True,
                error={"code": "PROFILE_FAILED", "message": result.error or "画像提取失败", "retryable": True},
                demo_mode=False,
            )
            return

        # 构造追问文本（模拟 content.delta）
        assistant_text = result.follow_up_question or result.rationale or "明白了，请继续。"

        # ── 严格检验：不信任 LLM 的 is_complete，自行数维度 ──
        profile = result.profile
        actually_complete = result.is_complete and profile is not None and _profile_ready(profile)

        if result.is_complete and not actually_complete:
            # LLM 说完成了但维度不够 → 强制继续
            assistant_text = result.follow_up_question or "请再详细说说你的学习情况和目标吧。"
        elif actually_complete:
            assistant_text = "好的，我已经对你的学习情况有了比较全面的了解。点击左侧导航栏的「学习路径」即可查看个性化学习路径，或者去「资源工作台」生成专属学习资料。"

        yield GatewayEvent(
            event="content.delta", task_id=task_id, trace_id=trace_id,
            current_agent="画像Agent", progress=45, content=assistant_text,
            demo_mode=False,
        )

        # 推送画像更新
        if result.profile:
            profile_patch = _agent_to_api_profile(result.profile)
            yield GatewayEvent(
                event="profile.patch", task_id=task_id, trace_id=trace_id,
                current_agent="画像Agent", progress=80,
                profile_patch=profile_patch, demo_mode=False,
            )

        if actually_complete and self._db is not None:
            try:
                from app.repositories.profiles import ProfileRepository
                with self._db.session() as session:
                    ProfileRepository(session).confirm(user_id)
            except Exception:
                pass

        yield GatewayEvent(
            event="task.completed", task_id=task_id, trace_id=trace_id,
            current_agent="画像Agent", progress=100, finish_flag=True,
            demo_mode=False,
        )

    # ── 资源生成 ──────────────────────────────────────────

    async def stream_resources(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        course_name: str,
        weak_point: str,
        resource_types: list[ResourceType],
    ) -> AsyncIterator[ResourceAgentEvent]:
        from agent.doc_agent import DocAgent
        from agent.mindmap_agent import MindMapAgent
        from agent.quiz_agent import QuizAgent
        from agent.video_agent import VideoAgent
        from agent.reference_agent import ReferenceAgent

        loader = _material_loader()
        dag = loader.load_dag()

        # 匹配知识点：用关键词分词匹配（而非整个字符串的子串匹配）
        target_kp = _match_knowledge_point(weak_point, dag)
        if target_kp is None:
            target_kp = dag.knowledge_points[0]

        profile = StudentProfile()
        total = len(resource_types)

        agent_registry = {
            "handout":  ("讲义Agent",    DocAgent),
            "mindmap":  ("思维导图Agent", MindMapAgent),
            "quiz":     ("题库Agent",    QuizAgent),
            "video":    ("视频Agent",    VideoAgent),
            "code":     ("拓展阅读Agent",  ReferenceAgent),
        }

        for idx, res_type in enumerate(resource_types):
            label, agent_cls = agent_registry.get(res_type, (res_type, None))
            progress = 10 + int(80 * idx / max(1, total))

            yield ResourceAgentEvent(
                event="agent.started", current_agent=label,
                progress=progress, resource_type=res_type, demo_mode=False,
            )

            if agent_cls is None:
                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=ResourceDraft(
                        resource_type=res_type,
                        title=f"{target_kp.name}",
                        payload={"markdown": f"# {target_kp.name}\n\n资源类型 `{res_type}` 暂未接入 Agent 引擎。"},
                    ),
                    demo_mode=False,
                )
                continue

            material_ctx = loader.get_context(target_kp.id, max_chars=8000, per_file_max=5000)
            loop = asyncio.get_running_loop()

            # ── handout ──
            if res_type == "handout":
                result = await loop.run_in_executor(
                    None,
                    lambda: agent_cls().generate(target_kp, profile, material_context=material_ctx),
                )
                if result.success:
                    from agent.models import DocContent
                    content = result.resource.content
                    markdown = _sections_to_markdown(content.sections) if hasattr(content, "sections") else str(content)
                    draft = ResourceDraft(resource_type="handout", title=result.resource.metadata.title, payload={"markdown": markdown})
                else:
                    draft = ResourceDraft(resource_type="handout", title=target_kp.name, payload={"markdown": f"讲义生成失败: {result.error}"})

                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=draft, demo_mode=False,
                )

            # ── mindmap ──
            elif res_type == "mindmap":
                result = await loop.run_in_executor(
                    None,
                    lambda: agent_cls().generate(target_kp, profile, material_context=material_ctx),
                )
                if result.success:
                    draft = ResourceDraft(
                        resource_type="mindmap",
                        title=result.resource.metadata.title,
                        payload={"nodes": result.resource.content.nodes},
                    )
                else:
                    draft = ResourceDraft(resource_type="mindmap", title=target_kp.name, payload={"nodes": []})

                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=draft, demo_mode=False,
                )

            # ── quiz ──
            elif res_type == "quiz":
                result = await loop.run_in_executor(
                    None,
                    lambda: agent_cls().generate(target_kp, profile, material_context=material_ctx),
                )
                if result.success:
                    questions = []
                    for item in result.resource.content.items:
                        questions.append({
                            "id": f"q_{len(questions) + 1}",
                            "question_type": _map_question_type(item.question_type.value),
                            "prompt": item.stem,
                            "options": item.options,
                            "answer": item.correct_answer,
                            "explanation": item.explanation,
                        })
                    draft = ResourceDraft(resource_type="quiz", title=result.resource.metadata.title, payload={"questions": questions})
                else:
                    draft = ResourceDraft(resource_type="quiz", title=target_kp.name, payload={"questions": []})

                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=draft, demo_mode=False,
                )

            # ── video ──
            elif res_type == "video":
                result = await loop.run_in_executor(
                    None,
                    lambda: agent_cls().generate(
                        target_kp, profile,
                        material_context=material_ctx,
                        materials_dir=str(_MATERIALS_DIR),
                    ),
                )
                if result.success and result.has_video:
                    media_url = _ensure_media_url(target_kp.id, result.video_path)
                    draft = ResourceDraft(
                        resource_type="video",
                        title=result.resource.metadata.title,
                        payload={
                            "summary": result.push_reason,
                            "poster_url": "",
                            "duration_seconds": result.video_duration_seconds,
                        },
                        media_url=media_url,
                    )
                else:
                    draft = ResourceDraft(
                        resource_type="video",
                        title=target_kp.name,
                        payload={"summary": "该知识点暂无演示视频", "poster_url": "", "duration_seconds": 0},
                        media_url=None,
                    )

                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=draft, demo_mode=False,
                )

            # ── code → 拓展阅读（ReferenceAgent）──
            elif res_type == "code":
                shared_list = loader.get_shared_references()
                shared_summary = loader.get_shared_references_summary()
                result = await loop.run_in_executor(
                    None,
                    lambda: agent_cls().recommend(target_kp, profile, shared_summary, shared_list),
                )
                if result.success:
                    # 把推荐内容序列化为 Markdown 格式（兼容 handout payload）
                    lines = [f"# {target_kp.name} — 拓展阅读推荐\n"]
                    if result.reading_path:
                        lines.append(f"> {result.reading_path}\n")
                    if result.library_recommendations:
                        lines.append("## 课程拓展阅读库\n")
                        for rec in result.library_recommendations:
                            lines.append(f"- **{rec['title']}** ⭐{rec['priority']}")
                            lines.append(f"  {rec['relevance_reason']}")
                            lines.append(f"  建议重点: {rec['suggested_focus']}\n")
                    if result.external_recommendations:
                        lines.append("## 外部经典推荐\n")
                        for rec in result.external_recommendations:
                            lines.append(f"- **{rec['title']}**（{rec.get('author', '')}）⭐{rec['priority']}")
                            lines.append(f"  {rec['relevance_reason']}\n")
                    draft = ResourceDraft(resource_type="handout", title=f"{target_kp.name} — 拓展阅读", payload={"markdown": "\n".join(lines)})
                else:
                    draft = ResourceDraft(resource_type="handout", title=target_kp.name, payload={"markdown": f"阅读推荐生成失败: {result.error}"})

                yield ResourceAgentEvent(
                    event="resource.ready", current_agent=label,
                    progress=progress + 5, resource_type=res_type,
                    resource=draft, demo_mode=False,
                )

    # ── 学习路径 ──────────────────────────────────────────

    async def build_learning_path(
        self,
        *,
        user_id: str,
        course_name: str,
        profile: StudentProfileData,
        resources: list[ResourceSummary],
    ) -> LearningPathDraft:
        from agent.planner import PlannerAgent

        agent_profile = _api_to_agent_profile(profile)
        loader = _material_loader()
        dag = loader.load_dag()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: PlannerAgent().plan(agent_profile, dag),
        )

        if not result.success or result.learning_path is None:
            return LearningPathDraft(nodes=[])

        nodes: list[LearningPathNodeDraft] = []
        for node in result.learning_path.nodes:
            # Agent 资源类型 → API 资源类型映射
            _AGENT_TO_API_TYPE = {
                "doc": "handout", "mindmap": "mindmap", "quiz": "quiz",
                "code": "code", "video_script": "video",
            }
            api_types = [_AGENT_TO_API_TYPE.get(rt.value, rt.value) for rt in node.recommended_resource_types]

            resource_id: Optional[str] = None
            for res in resources:
                if res.resource_type in api_types:
                    resource_id = res.id
                    break

            # 丰富阶段名称：包含学习建议
            depth_label = {1: "了解", 2: "掌握", 3: "精通"}.get(node.depth, "学习")
            time_info = f"约{node.estimated_time_minutes}分钟" if node.estimated_time_minutes else ""
            stage_name = f"{node.knowledge_point_name}（{depth_label}，{time_info}）"

            # 丰富难度字段：包含推荐理由
            difficulty_parts = [depth_label]
            if node.rationale:
                short_reason = node.rationale[:50] + ("..." if len(node.rationale) > 50 else "")
                difficulty_parts.append(short_reason)
            difficulty = " | ".join(difficulty_parts)

            nodes.append(LearningPathNodeDraft(
                stage_name=stage_name,
                difficulty=difficulty,
                resource_id=resource_id,
            ))

        return LearningPathDraft(nodes=nodes)

    # ── 答疑 ──────────────────────────────────────────────

    async def stream_qa(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        question: str,
        answer_mode: AnswerMode,
        profile: StudentProfileData,
    ) -> AsyncIterator[GatewayEvent]:
        from agent.utils.llm_client import get_client

        yield GatewayEvent(
            event="agent.started", task_id=task_id, trace_id=trace_id,
            current_agent="答疑Agent", progress=10, demo_mode=False,
        )

        system_prompt = "你是一位知识渊博的学习导师。请用中文回答学生的问题。解释清晰易懂，适当举例说明。"

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: get_client().chat(user_message=question, system_prompt=system_prompt, temperature=0.5),
        )

        if response.success:
            yield GatewayEvent(
                event="content.delta", task_id=task_id, trace_id=trace_id,
                current_agent="答疑Agent", progress=90, content=response.content,
                demo_mode=False,
            )
            yield GatewayEvent(
                event="task.completed", task_id=task_id, trace_id=trace_id,
                current_agent="答疑Agent", progress=100, finish_flag=True,
                demo_mode=False,
            )
        else:
            yield GatewayEvent(
                event="task.failed", task_id=task_id, trace_id=trace_id,
                current_agent="答疑Agent", progress=0, finish_flag=True,
                error={"code": "QA_FAILED", "message": response.error or "答疑失败", "retryable": True},
                demo_mode=False,
            )

    # ── 评估 ──────────────────────────────────────────────

    async def build_evaluation(
        self,
        *,
        user_id: str,
        course_name: str,
        evidence: EvaluationEvidence,
    ) -> EvaluationDraft:
        # ── 理论知识：题库答题平均分 ──
        theory_score = 0
        if evidence.attempts:
            scores = [a.score for a in evidence.attempts]
            theory_score = sum(scores) // len(scores) if scores else 0

        # ── 实操能力：学习路径节点完成率 × 100 ──
        practice_score = 0
        if evidence.practice_nodes:
            completed = sum(1 for n in evidence.practice_nodes if n.completed)
            total = len(evidence.practice_nodes)
            practice_score = int((completed / total) * 100) if total > 0 else 0

        # 无数据时显示初始状态
        if not evidence.attempts and not evidence.practice_nodes:
            theory_score = 50
            practice_score = 50

        # ── 汇总所有答题中的错误知识点 ──
        wp_freq: dict[str, int] = {}
        for attempt in evidence.attempts:
            for point in (attempt.incorrect_points or []):
                wp_freq[point] = wp_freq.get(point, 0) + 1
        for wp in (evidence.question_weak_points or []):
            wp_freq[wp] = wp_freq.get(wp, 0) + 1

        weak_points = [
            EvaluationWeakPoint(name=name, frequency=freq)
            for name, freq in sorted(wp_freq.items(), key=lambda x: -x[1])
        ]

        # ── 根据所有薄弱点生成路径调整建议 ──
        recommended_changes: list[EvaluationRecommendedChange] = []
        for wp in weak_points:
            if wp.frequency >= 5:
                level = "核心"
                advice = f"严重薄弱（错{wp.frequency}次），必须重新学习本知识点讲义和思维导图，完成配套题库后再测试"
            elif wp.frequency >= 3:
                level = "核心"
                advice = f"高频错误（错{wp.frequency}次），建议返回本知识点，重读讲义并完成专项练习"
            elif wp.frequency >= 2:
                level = "基础"
                advice = f"中频错误（错{wp.frequency}次），建议回顾思维导图，针对此薄弱点做巩固练习"
            else:
                level = "入门"
                advice = f"偶发错误（错{wp.frequency}次），建议快速浏览讲义中此知识点的常见误区"

            recommended_changes.append(
                EvaluationRecommendedChange(
                    stage_name=wp.name,
                    difficulty=level,
                    reason=advice,
                    resource_id=None,
                )
            )

        return EvaluationDraft(
            theory_score=theory_score,
            practice_score=practice_score,
            weak_points=weak_points,
            recommended_changes=recommended_changes,
        )


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _sections_to_markdown(sections: list[dict]) -> str:
    """DocContent.sections → 单个 Markdown 字符串。"""
    parts: list[str] = []
    for sec in sections:
        heading = sec.get("heading", "")
        body = sec.get("body_markdown", "")
        key_points = sec.get("key_points", [])
        if heading:
            parts.append(f"## {heading}\n")
        if body:
            parts.append(body)
        if key_points:
            parts.append("\n**要点：**\n")
            for kp in key_points:
                parts.append(f"- {kp}")
        parts.append("\n")
    return "\n".join(parts)


def _map_question_type(agent_type: str) -> str:
    """Agent 题型 → API 题型。"""
    mapping = {
        "single_choice": "choice",
        "multiple_choice": "choice",
        "true_false": "choice",
        "short_answer": "blank",
    }
    return mapping.get(agent_type, "choice")


def _ensure_media_url(kp_id: str, video_path: Optional[str]) -> Optional[str]:
    """返回前端可访问的视频 URL。

    视频文件在 knowledge_base_sync 时已复制到 data/courses/robot-safety/{kp_id}/，
    并由 CourseIndexer 索引到数据库。直接构造 media_url 即可，
    GET /media/courses/robot-safety/{kp_id}/{filename} 会由 courses.py 的路由处理。
    """
    if not video_path:
        return None

    video_file = Path(video_path)
    if not video_file.exists():
        logger.warning(f"视频文件不存在: {video_path}")
        return None

    from urllib.parse import quote
    return f"/media/video/{quote(kp_id)}/{quote(video_file.name)}"
