"""
统一数据模型定义
================
本文件定义项目中所有 Agent、工作流、前后端之间传递的核心数据结构。
所有 Agent 的输出格式、各模块之间的接口契约，均由本文件统一约束。

原则：
1. 所有结构使用 Pydantic v2，自带 JSON Schema 生成和字段校验
2. 字段命名使用 snake_case，序列化为 camelCase（通过 alias）
3. 每个结构都有明确的 docstring 说明用途
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict


# ═══════════════════════════════════════════════════════════════
# 枚举定义 —— 所有受控词汇表
# ═══════════════════════════════════════════════════════════════

class MasteryLevel(str, Enum):
    """知识点掌握程度"""
    PROFICIENT = "proficient"     # 熟练：能独立解决问题
    FAMILIAR = "familiar"         # 了解：有概念但需复习
    EXPOSED = "exposed"           # 接触过：学过但遗忘
    UNKNOWN = "unknown"           # 未接触：全新知识


class CognitiveStyle(str, Enum):
    """认知风格"""
    THEORY_ORIENTED = "theory_oriented"      # 偏理论：喜欢公式推导、原理解析
    PRACTICE_ORIENTED = "practice_oriented"  # 偏实践：喜欢代码实验、工程案例
    BALANCED = "balanced"                    # 均衡型


class LearningPace(str, Enum):
    """学习节奏偏好"""
    INTENSIVE = "intensive"        # 密集型：单次大量学习
    DISTRIBUTED = "distributed"    # 分散型：每天少量，长期坚持
    FLEXIBLE = "flexible"          # 灵活型：无固定偏好


class ResourceType(str, Enum):
    """资源类型 —— 与项目要求的 ≥5 类资源对应"""
    DOC = "doc"                    # 讲义文档
    MINDMAP = "mindmap"            # 思维导图
    QUIZ = "quiz"                  # 题库练习
    CODE = "code"                  # 代码案例
    VIDEO_SCRIPT = "video_script"  # 视频脚本


class QuestionType(str, Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class ReviewStatus(str, Enum):
    """审核结果"""
    PASSED = "passed"                # 通过
    NEEDS_REVISION = "needs_revision"  # 需修订（小问题）
    REJECTED = "rejected"            # 拒绝（大问题，需重新生成）


class Severity(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 严重：事实性错误、安全违规
    MAJOR = "major"          # 重要：内容缺失、逻辑矛盾
    MINOR = "minor"          # 轻微：格式问题、措辞可优化


# ═══════════════════════════════════════════════════════════════
# 1. 学生画像 —— 6 维度动态画像
# ═══════════════════════════════════════════════════════════════

class KnowledgeBaseItem(BaseModel):
    """画像中的单个知识点掌握状态"""
    knowledge_point_id: str = Field(..., description="知识点唯一标识，如 'binary_tree_traversal'")
    knowledge_point_name: str = Field(..., description="知识点名称，如 '二叉树遍历'")
    mastery: MasteryLevel = Field(default=MasteryLevel.UNKNOWN, description="掌握程度")
    last_updated: Optional[datetime] = Field(default=None, description="掌握程度上次更新时间")


class WeakPoint(BaseModel):
    """薄弱环节"""
    knowledge_point_id: str = Field(..., description="薄弱知识点 ID")
    knowledge_point_name: str = Field(..., description="薄弱知识点名称")
    error_pattern: str = Field(default="", description="错误模式描述，如 '递归终止条件常漏写'")
    occurrence_count: int = Field(default=0, description="出错的累计次数")


class StudentProfile(BaseModel):
    """
    学生画像 —— 6 维度动态画像。
    通过 Profile Agent 从对话中抽取，并随学习过程持续更新。
    """
    model_config = ConfigDict(use_enum_values=True)

    # ── 维度 1: 知识基础 ──
    knowledge_base: list[KnowledgeBaseItem] = Field(
        default_factory=list,
        description="已评估的知识点及掌握程度列表"
    )

    # ── 维度 2: 认知风格 ──
    cognitive_style: CognitiveStyle = Field(
        default=CognitiveStyle.BALANCED,
        description="认知风格：偏理论 / 偏实践 / 均衡"
    )

    # ── 维度 3: 学习目标 ──
    learning_goal_short: str = Field(
        default="",
        description="短期目标，如 '通过期末考试'、'完成课程设计'、'打蓝桥杯'"
    )
    learning_goal_long: str = Field(
        default="",
        description="长期目标，如 '掌握全栈开发'、'考研408高分'、'转行AI'"
    )

    # ── 维度 4: 薄弱环节 ──
    weak_points: list[WeakPoint] = Field(
        default_factory=list,
        description="常错知识点及错误模式"
    )

    # ── 维度 5: 学习节奏 ──
    learning_pace: LearningPace = Field(
        default=LearningPace.FLEXIBLE,
        description="学习节奏偏好：密集 / 分散 / 灵活"
    )

    # ── 维度 6: 兴趣偏好 ──
    interest_domains: list[str] = Field(
        default_factory=list,
        description="感兴趣的应用场景，如 ['游戏开发', 'AI推理', '嵌入式系统']"
    )

    # ── 基础信息 ──
    major: str = Field(default="", description="专业")
    grade: str = Field(default="", description="年级，如 '大三'")
    created_at: datetime = Field(default_factory=datetime.now, description="画像创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="画像最后更新时间")

    def snapshot(self) -> str:
        """生成画像的文本摘要，用于注入其他 Agent 的 System Prompt"""
        parts = []

        if self.major:
            parts.append(f"专业: {self.major}")
        if self.grade:
            parts.append(f"年级: {self.grade}")

        if self.knowledge_base:
            kb_summary = ", ".join(
                f"{k.knowledge_point_name}({k.mastery})" for k in self.knowledge_base[:10]
            )
            parts.append(f"已评估知识点: {kb_summary}")

        parts.append(f"认知风格: {self.cognitive_style}")
        parts.append(f"学习节奏: {self.learning_pace}")

        if self.learning_goal_short:
            parts.append(f"短期目标: {self.learning_goal_short}")

        if self.weak_points:
            wp_summary = ", ".join(w.knowledge_point_name for w in self.weak_points[:5])
            parts.append(f"薄弱环节: {wp_summary}")

        if self.interest_domains:
            parts.append(f"兴趣方向: {', '.join(self.interest_domains)}")

        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# 2. 知识点 DAG —— 知识体系骨架
# ═══════════════════════════════════════════════════════════════

class KnowledgePoint(BaseModel):
    """知识体系中单个知识点"""
    id: str = Field(..., description="唯一标识，如 'linked_list_basics'")
    name: str = Field(..., description="知识点名称，如 '链表基础'")
    description: str = Field(default="", description="知识点简介（1-2 句话）")
    category: str = Field(default="", description="所属分类/章节，如 '线性数据结构'")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="前置知识点 ID 列表，空列表表示该知识点无前置依赖"
    )
    difficulty: int = Field(
        default=1, ge=1, le=5,
        description="难度等级 1-5"
    )
    estimated_minutes: int = Field(
        default=30,
        description="建议学习时长（分钟）"
    )
    tags: list[str] = Field(default_factory=list, description="标签，用于分类检索")


class KnowledgeDAG(BaseModel):
    """知识点有向无环图 —— 一门课程/一个知识域的知识体系"""
    course_name: str = Field(..., description="课程名称，如 '数据结构与算法'")
    course_description: str = Field(default="", description="课程简介")
    knowledge_points: list[KnowledgePoint] = Field(
        default_factory=list,
        description="所有知识点节点"
    )

    def get_entry_points(self) -> list[KnowledgePoint]:
        """返回所有无前置依赖的入口知识点（可以最先学的）"""
        return [kp for kp in self.knowledge_points if not kp.prerequisites]

    def get_by_id(self, kp_id: str) -> Optional[KnowledgePoint]:
        """按 ID 查找知识点"""
        for kp in self.knowledge_points:
            if kp.id == kp_id:
                return kp
        return None

    def get_prerequisites_chain(self, kp_id: str) -> list[str]:
        """递归获取某个知识点所有前置依赖链（按学习顺序）"""
        result = []
        visited = set()

        def dfs(current_id: str):
            if current_id in visited:
                return
            visited.add(current_id)
            kp = self.get_by_id(current_id)
            if kp:
                for pre in kp.prerequisites:
                    dfs(pre)
                if current_id != kp_id:
                    result.append(current_id)

        dfs(kp_id)
        return result


# ═══════════════════════════════════════════════════════════════
# 3. 学习路径
# ═══════════════════════════════════════════════════════════════

class LearningPathNode(BaseModel):
    """学习路径中的一个节点"""
    order: int = Field(..., description="节点序号，从 1 开始")
    knowledge_point_id: str = Field(..., description="对应知识点 ID")
    knowledge_point_name: str = Field(..., description="知识点名称")
    depth: int = Field(default=1, description="学习深度 1-3（了解/掌握/精通）")
    recommended_resource_types: list[ResourceType] = Field(
        default_factory=list,
        description="该节点推荐生成的资源类型"
    )
    rationale: str = Field(
        default="",
        description="为什么推荐这个节点（结合画像的理由），如 '你的薄弱环节，需重点练习'"
    )
    estimated_time_minutes: int = Field(default=30, description="预计学习时长")
    is_weak_point: bool = Field(default=False, description="是否对应该学生的薄弱环节")


class LearningPath(BaseModel):
    """个性化学习路径 —— Planner Agent 输出"""
    student_profile_snapshot: str = Field(default="", description="生成路径时所用的画像快照（文本摘要）")
    course_name: str = Field(default="", description="课程名称")
    nodes: list[LearningPathNode] = Field(default_factory=list, description="路径节点序列")
    total_estimated_minutes: int = Field(default=0, description="总预计学习时长")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    version: int = Field(default=1, description="路径版本号，每次更新递增")


# ═══════════════════════════════════════════════════════════════
# 4. 资源输出 —— 5 类资源的统一外层结构
# ═══════════════════════════════════════════════════════════════

class ResourceMetadata(BaseModel):
    """资源元数据 —— 所有资源共用的外层信息"""
    resource_type: ResourceType = Field(..., description="资源类型")
    knowledge_point_id: str = Field(..., description="目标知识点 ID")
    knowledge_point_name: str = Field(..., description="目标知识点名称")
    title: str = Field(default="", description="资源标题，如 '二叉树遍历详解'")
    difficulty: int = Field(default=1, ge=1, le=5, description="内容难度 1-5")
    estimated_read_time_minutes: int = Field(default=15, description="预估阅读/学习时长")
    tags: list[str] = Field(default_factory=list, description="内容标签")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    student_profile_snapshot: str = Field(default="", description="生成时所用的学生画像快照")


# ── 具体资源内容 ──

class DocContent(BaseModel):
    """讲义文档内容"""
    sections: list[dict] = Field(
        default_factory=list,
        description="章节列表。每项为 {heading, body_markdown, key_points[]}"
    )
    summary: str = Field(default="", description="全文总结")
    further_reading: list[str] = Field(default_factory=list, description="延伸阅读推荐")


class MindMapContent(BaseModel):
    """思维导图内容 —— 结构化表述，可渲染为 Mermaid"""
    root_topic: str = Field(..., description="根主题（知识点名称）")
    mermaid_code: str = Field(default="", description="Mermaid mindmap 语法的完整代码块")
    nodes: list[dict] = Field(
        default_factory=list,
        description="结构化节点列表，每项为 {id, label, parent_id, children[]}"
    )


class QuizItem(BaseModel):
    """单道题目"""
    question_type: QuestionType = Field(..., description="题型")
    stem: str = Field(..., description="题干")
    options: list[str] = Field(
        default_factory=list,
        description="选项列表（选择题/判断题使用，简答题为空）"
    )
    correct_answer: str = Field(..., description="正确答案")
    explanation: str = Field(..., description="详细解析")
    difficulty: int = Field(default=1, ge=1, le=5, description="题目难度 1-5")
    knowledge_point_tags: list[str] = Field(default_factory=list, description="考察的知识点标签")


class QuizContent(BaseModel):
    """题库内容"""
    items: list[QuizItem] = Field(default_factory=list, description="题目列表")
    total_count: int = Field(default=0, description="题目总数")
    suggested_duration_minutes: int = Field(default=15, description="建议答题时长")


class CodeExample(BaseModel):
    """单个代码示例"""
    language: str = Field(..., description="编程语言，如 'python', 'verilog', 'c'")
    title: str = Field(..., description="示例标题")
    code: str = Field(..., description="代码内容")
    explanation: str = Field(..., description="逐行/逐段解释")
    expected_output: str = Field(default="", description="预期输出")


class CodeContent(BaseModel):
    """代码案例集合"""
    examples: list[CodeExample] = Field(default_factory=list, description="代码示例列表")
    prerequisites: str = Field(default="", description="前置知识要求")
    run_instructions: str = Field(default="", description="运行说明")


class VideoScene(BaseModel):
    """视频脚本的一个场景/分镜"""
    scene_number: int = Field(..., description="分镜序号")
    narration: str = Field(..., description="旁白/配音文本")
    visual_description: str = Field(..., description="画面描述（画什么、展示什么）")
    duration_seconds: int = Field(default=30, description="预估时长（秒）")


class VideoScriptContent(BaseModel):
    """视频脚本内容"""
    title: str = Field(..., description="视频标题")
    total_duration_seconds: int = Field(default=0, description="总时长（秒）")
    target_audience: str = Field(default="", description="目标受众")
    scenes: list[VideoScene] = Field(default_factory=list, description="分镜列表")


# ── 统一资源输出 ──

class ResourceOutput(BaseModel):
    """
    统一资源输出 —— 所有资源 Agent 必须按此结构返回。
    外层字段（metadata, status 等）由 Supervisor 填充，
    content 字段由各资源 Agent 填充对应子类型。
    """
    metadata: ResourceMetadata = Field(..., description="资源元数据")
    content: DocContent | MindMapContent | QuizContent | CodeContent | VideoScriptContent | dict = Field(
        ...,
        description="具体资源内容，类型由 metadata.resource_type 决定"
    )
    status: str = Field(default="generated", description="生成状态: generated / reviewing / reviewed / failed")
    generated_by: str = Field(default="", description="生成此资源的 Agent 名称")
    reviewer_feedback: Optional["ReviewerResult"] = Field(default=None, description="审核反馈")


# ═══════════════════════════════════════════════════════════════
# 5. Reviewer 审核结果
# ═══════════════════════════════════════════════════════════════

class ReviewIssue(BaseModel):
    """审核中发现的一个问题"""
    severity: Severity = Field(..., description="严重程度")
    category: str = Field(..., description="问题类别: factuality / safety / completeness / format")
    description: str = Field(..., description="问题描述")
    location: str = Field(default="", description="问题所在位置（章节/段落/行号）")
    suggestion: str = Field(default="", description="修改建议")


class ReviewerResult(BaseModel):
    """
    Reviewer Agent 输出 —— 对资源的质量审核结果。
    审核维度：事实性、安全性、完整性。
    """
    status: ReviewStatus = Field(..., description="审核结论: 通过 / 需修订 / 拒绝")
    factuality_score: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="事实性评分（1.0 = 无事实错误）"
    )
    safety_score: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="安全性评分（1.0 = 无安全问题）"
    )
    completeness_score: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="完整性评分（1.0 = 完全覆盖目标知识点）"
    )
    issues: list[ReviewIssue] = Field(default_factory=list, description="发现的问题列表")
    overall_comment: str = Field(default="", description="审核总评")
    needs_regeneration: bool = Field(default=False, description="是否需要回退到资源 Agent 重新生成")
    reviewed_at: datetime = Field(default_factory=datetime.now, description="审核时间")


# ═══════════════════════════════════════════════════════════════
# 6. Supervisor 任务调度
# ═══════════════════════════════════════════════════════════════

class TaskIntent(str, Enum):
    """Supervisor 识别的用户意图"""
    EXTRACT_PROFILE = "extract_profile"     # 画像抽取/更新
    PLAN_PATH = "plan_path"                 # 路径规划
    GENERATE_RESOURCE = "generate_resource" # 资源生成
    ANSWER_QUESTION = "answer_question"     # 答疑
    EVALUATE = "evaluate"                   # 学习评估
    CHITCHAT = "chitchat"                   # 闲聊


class Task(BaseModel):
    """Supervisor 下发的单个子任务"""
    task_id: str = Field(default="", description="任务唯一 ID")
    intent: TaskIntent = Field(..., description="任务意图")
    agent_name: str = Field(..., description="目标 Agent 名称")
    payload: dict = Field(default_factory=dict, description="传给 Agent 的输入参数")
    dependencies: list[str] = Field(default_factory=list, description="前置依赖的 task_id 列表")
    status: str = Field(default="pending", description="pending / running / completed / failed")


class SessionState(BaseModel):
    """
    会话全局状态 —— 由 Supervisor 维护，贯穿一次用户交互的完整生命周期。
    """
    session_id: str = Field(default="", description="会话 ID")
    student_profile: Optional[StudentProfile] = Field(default=None, description="当前学生画像")
    current_learning_path: Optional[LearningPath] = Field(default=None, description="当前学习路径")
    tasks: list[Task] = Field(default_factory=list, description="当前会话的任务列表")
    generated_resources: list[ResourceOutput] = Field(default_factory=list, description="本次生成的所有资源")
    conversation_history: list[dict] = Field(default_factory=list, description="对话历史")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
