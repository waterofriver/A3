# -*- coding: utf-8 -*-
"""
Supervisor Agent 测试 —— 验证意图分类、Agent 分发、SessionState 管理、异步支持。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.supervisor.test_supervisor

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
import io
import asyncio
import os
import tempfile
import json
from datetime import datetime
from copy import deepcopy

# 修复 Windows 控制台 GBK 编码导致的 UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .supervisor import Supervisor, SupervisorResult
from ..utils import LLMResponse
from ..models import (
    StudentProfile,
    KnowledgeBaseItem,
    WeakPoint,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
    KnowledgePoint,
    KnowledgeDAG,
    LearningPath,
    LearningPathNode,
    SessionState,
    TaskIntent,
    ResourceType,
)


# ═══════════════════════════════════════════════════════════════
# Mock LLM 客户端
# ═══════════════════════════════════════════════════════════════

class MockLLMClient:
    """可注入的 Mock LLM 客户端。

    支持通过 call_sequence 控制多次调用的返回序列。
    """

    def __init__(self, content="", success=True, error=None, call_sequence=None):
        """
        参数:
            content: 默认返回内容
            success: 默认是否成功
            error: 默认错误信息
            call_sequence: list of (content, success, error) 按调用顺序返回
        """
        self.content = content
        self.success = success
        self.error = error
        self.call_sequence = call_sequence or []
        self.call_count = 0
        self.last_call_kwargs = None
        self.all_calls = []  # 所有调用的 kwargs 记录

    def chat(self, **kwargs):
        self.last_call_kwargs = kwargs
        self.all_calls.append(kwargs)

        if self.call_count < len(self.call_sequence):
            content, success, error = self.call_sequence[self.call_count]
            self.call_count += 1
            return LLMResponse(
                content=content,
                success=success,
                error=error,
                model="mock-model",
            )

        self.call_count += 1
        return LLMResponse(
            content=self.content,
            success=self.success,
            error=self.error,
            model="mock-model",
        )


# ═══════════════════════════════════════════════════════════════
# 测试 Fixture
# ═══════════════════════════════════════════════════════════════

def _make_profile(**overrides):
    """快速构造 StudentProfile。"""
    defaults = dict(
        major="计算机科学",
        grade="大三",
        knowledge_base=[
            KnowledgeBaseItem(
                knowledge_point_id="python",
                knowledge_point_name="Python",
                mastery=MasteryLevel.PROFICIENT,
            ),
        ],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="通过期末考试",
        weak_points=[
            WeakPoint(
                knowledge_point_id="recursion",
                knowledge_point_name="递归",
                error_pattern="递归终止条件错误",
                occurrence_count=2,
            ),
        ],
        learning_pace=LearningPace.DISTRIBUTED,
        interest_domains=["Web开发"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_session(*, with_profile=False, with_path=False):
    """快速构造 SessionState。"""
    return SessionState(
        session_id="test-session-001",
        student_profile=_make_profile() if with_profile else None,
        current_learning_path=(
            LearningPath(
                course_name="数据结构",
                nodes=[
                    LearningPathNode(
                        order=1,
                        knowledge_point_id="array",
                        knowledge_point_name="数组",
                        depth=1,
                        recommended_resource_types=[ResourceType.DOC],
                        rationale="测试路径",
                        estimated_time_minutes=20,
                    ),
                ],
                version=1,
            )
            if with_path
            else None
        ),
    )


def _make_dag_json():
    """创建临时知识 DAG JSON 文件，返回路径。"""
    dag_data = {
        "course_name": "数据结构与算法",
        "course_description": "计算机核心基础课程",
        "knowledge_points": [
            {
                "id": "array",
                "name": "数组基础",
                "description": "线性存储结构",
                "category": "线性结构",
                "prerequisites": [],
                "difficulty": 1,
                "estimated_minutes": 20,
                "tags": ["数组"],
            },
            {
                "id": "linked_list",
                "name": "链表",
                "description": "链式存储结构",
                "category": "线性结构",
                "prerequisites": ["array"],
                "difficulty": 2,
                "estimated_minutes": 30,
                "tags": ["链表"],
            },
            {
                "id": "stack",
                "name": "栈",
                "description": "后进先出",
                "category": "线性结构",
                "prerequisites": ["linked_list"],
                "difficulty": 2,
                "estimated_minutes": 25,
                "tags": ["栈"],
            },
        ],
    }
    fd, path = tempfile.mkstemp(suffix=".json", prefix="test_dag_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(dag_data, f, ensure_ascii=False)
    return path


def _make_intent_response(intent="extract_profile", confidence=0.95, rationale=""):
    """构造意图分类的 LLM 返回 JSON。"""
    return f"""```json
{{
    "intent": "{intent}",
    "confidence": {confidence},
    "rationale": "{rationale or '测试意图分类'}"
}}
```"""


def _make_profile_extraction_json(
    major="计算机科学",
    grade="大三",
    is_complete=False,
    follow_up="你的学习目标是什么？",
):
    """构造 ProfileAgent 的 LLM 返回 JSON。"""
    import json as _json
    return f"""```json
{{
    "extracted_fields": {{
        "major": "{major}",
        "grade": "{grade}",
        "cognitive_style": "practice_oriented"
    }},
    "follow_up_question": "{follow_up}",
    "is_complete": {_json.dumps(is_complete)},
    "rationale": "测试画像抽取"
}}
```"""


def _make_planner_json():
    """构造 Planner 的 LLM 返回 JSON。"""
    import json as _json
    nodes = [
        {
            "knowledge_point_id": "array",
            "depth": 1,
            "recommended_resource_types": ["doc"],
            "rationale": "已掌握，快速复习。",
            "is_weak_point": False,
            "estimated_time_minutes": 15,
        },
        {
            "knowledge_point_id": "linked_list",
            "depth": 2,
            "recommended_resource_types": ["doc", "code"],
            "rationale": "正常学习。",
            "is_weak_point": False,
            "estimated_time_minutes": 30,
        },
        {
            "knowledge_point_id": "stack",
            "depth": 2,
            "recommended_resource_types": ["doc", "code"],
            "rationale": "正常学习。",
            "is_weak_point": False,
            "estimated_time_minutes": 25,
        },
    ]
    return f"""```json
{{
    "nodes": {_json.dumps(nodes, ensure_ascii=False)},
    "overall_rationale": "全部节点已标注"
}}
```"""


# ═══════════════════════════════════════════════════════════════
# 测试 1：意图分类 - extract_profile
# ═══════════════════════════════════════════════════════════════

def test_intent_extract_profile():
    """用户自我介绍应分类为 extract_profile。"""
    print("=" * 60)
    print("测试 1：意图分类 - extract_profile")
    print("=" * 60)

    client = MockLLMClient(content=_make_intent_response("extract_profile"))
    sup = Supervisor(client=client)
    session = _make_session()

    intent, confidence, rationale = sup.classify_intent(
        "大家好，我是计算机大三的学生", session
    )

    assert intent == TaskIntent.EXTRACT_PROFILE
    assert confidence > 0.5

    print(f"  意图: {intent.value} | 置信度: {confidence:.2f}")
    print("[PASS] 意图分类 extract_profile 正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：意图分类 - plan_path
# ═══════════════════════════════════════════════════════════════

def test_intent_plan_path():
    """用户请求学习规划应分类为 plan_path。"""
    print("=" * 60)
    print("测试 2：意图分类 - plan_path")
    print("=" * 60)

    client = MockLLMClient(content=_make_intent_response("plan_path"))
    sup = Supervisor(client=client)
    session = _make_session(with_profile=True)

    intent, confidence, rationale = sup.classify_intent(
        "帮我规划一下接下来学什么", session
    )

    assert intent == TaskIntent.PLAN_PATH

    print(f"  意图: {intent.value} | 置信度: {confidence:.2f}")
    print("[PASS] 意图分类 plan_path 正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 3：意图分类 - answer_question
# ═══════════════════════════════════════════════════════════════

def test_intent_answer_question():
    """知识提问应分类为 answer_question。"""
    print("=" * 60)
    print("测试 3：意图分类 - answer_question")
    print("=" * 60)

    client = MockLLMClient(content=_make_intent_response("answer_question"))
    sup = Supervisor(client=client)
    session = _make_session(with_profile=True, with_path=True)

    intent, confidence, rationale = sup.classify_intent(
        "什么是二叉树的中序遍历", session
    )

    assert intent == TaskIntent.ANSWER_QUESTION

    print(f"  意图: {intent.value} | 置信度: {confidence:.2f}")
    print("[PASS] 意图分类 answer_question 正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 4：意图分类 - chitchat
# ═══════════════════════════════════════════════════════════════

def test_intent_chitchat():
    """问候应分类为 chitchat。"""
    print("=" * 60)
    print("测试 4：意图分类 - chitchat")
    print("=" * 60)

    client = MockLLMClient(content=_make_intent_response("chitchat"))
    sup = Supervisor(client=client)
    session = _make_session()

    intent, confidence, rationale = sup.classify_intent("你好啊", session)

    assert intent == TaskIntent.CHITCHAT

    print(f"  意图: {intent.value} | 置信度: {confidence:.2f}")
    print("[PASS] 意图分类 chitchat 正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 5：意图分类 LLM 失败时的兜底
# ═══════════════════════════════════════════════════════════════

def test_intent_fallback_llm_failure():
    """LLM 调用失败时应有合理的兜底分类。"""
    print("=" * 60)
    print("测试 5：意图分类 LLM 失败兜底")
    print("=" * 60)

    # LLM 调用失败
    client = MockLLMClient(success=False, error="Network error")

    # 场景 1：无画像 → 应兜底为 extract_profile
    sup = Supervisor(client=client)
    session = _make_session()  # 无画像
    intent, confidence, _ = sup.classify_intent("随便说点什么", session)
    assert intent == TaskIntent.EXTRACT_PROFILE, \
        f"无画像时应兜底 extract_profile: {intent.value}"
    print(f"  无画像兜底: {intent.value}")

    # 场景 2：有画像无路径 → 应兜底为 plan_path
    session2 = _make_session(with_profile=True)
    intent2, confidence2, _ = sup.classify_intent("随便说点什么", session2)
    assert intent2 == TaskIntent.PLAN_PATH, \
        f"有画像无路径时应兜底 plan_path: {intent2.value}"
    print(f"  有画像无路径兜底: {intent2.value}")

    # 场景 3：有画像有路径 → 应兜底为 chitchat
    session3 = _make_session(with_profile=True, with_path=True)
    intent3, confidence3, _ = sup.classify_intent("随便说点什么", session3)
    assert intent3 == TaskIntent.CHITCHAT, \
        f"有画像有路径时应兜底 chitchat: {intent3.value}"
    print(f"  有画像有路径兜底: {intent3.value}")

    print("[PASS] 意图分类兜底逻辑正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 6：意图分类 JSON 解析失败时的兜底
# ═══════════════════════════════════════════════════════════════

def test_intent_fallback_json_failure():
    """LLM 返回非 JSON 内容时应有兜底。"""
    print("=" * 60)
    print("测试 6：意图分类 JSON 解析失败兜底")
    print("=" * 60)

    client = MockLLMClient(content="这不是 JSON 格式的回复")
    sup = Supervisor(client=client)

    # 无画像 → 兜底 extract_profile
    session = _make_session()
    intent, _, _ = sup.classify_intent("你好", session)
    assert intent == TaskIntent.EXTRACT_PROFILE
    print(f"  无画像: {intent.value}")

    # 有画像 → 兜底 answer_question
    session2 = _make_session(with_profile=True)
    intent2, _, _ = sup.classify_intent("你好", session2)
    assert intent2 == TaskIntent.ANSWER_QUESTION
    print(f"  有画像: {intent2.value}")

    print("[PASS] JSON 解析失败兜底正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：空输入处理
# ═══════════════════════════════════════════════════════════════

def test_empty_input():
    """空输入应返回友好提示而不是崩溃。"""
    print("=" * 60)
    print("测试 7：空输入处理")
    print("=" * 60)

    sup = Supervisor(client=MockLLMClient())
    session = _make_session()

    # 空字符串
    result = sup.handle("", session)
    assert result.success
    assert len(result.reply) > 0
    assert result.intent == TaskIntent.CHITCHAT

    # 纯空格
    result2 = sup.handle("   ", session)
    assert result2.success
    assert len(result2.reply) > 0

    print(f"  空输入回复: '{result.reply}'")
    print("[PASS] 空输入正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 8：画像抽取流程（happy path）
# ═══════════════════════════════════════════════════════════════

def test_handle_extract_profile():
    """Supervisor.handle() 处理画像抽取的完整流程。"""
    print("=" * 60)
    print("测试 8：画像抽取完整流程")
    print("=" * 60)

    # 第一次调用：意图分类 → extract_profile
    # 第二次调用：ProfileAgent.extract → 调用 LLM
    client = MockLLMClient(call_sequence=[
        (_make_intent_response("extract_profile"), True, None),  # 意图分类
        (_make_profile_extraction_json(is_complete=False), True, None),  # 画像抽取
    ])
    sup = Supervisor(client=client)
    session = _make_session()

    result = sup.handle("我是计算机大三学生", session)

    assert result.success, f"应该成功: {result.error}"
    assert result.intent == TaskIntent.EXTRACT_PROFILE
    assert result.session is not None

    # Session 应该被更新
    updated_session = result.session
    assert updated_session is not session  # deep copy，不是同一个对象
    assert updated_session.student_profile is not None
    assert updated_session.student_profile.major == "计算机科学"
    assert updated_session.student_profile.grade == "大三"

    # 对话历史增加
    assert len(updated_session.conversation_history) >= 2

    # 追问问题应该在回复中
    assert len(result.reply) > 0

    print(f"  回复: '{result.reply}'")
    print(f"  画像专业: {updated_session.student_profile.major}")
    print(f"  画像年级: {updated_session.student_profile.grade}")
    print(f"  对话轮次: {len(updated_session.conversation_history) // 2}")
    print("[PASS] 画像抽取完整流程正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 9：画像抽取完成时的过渡引导
# ═══════════════════════════════════════════════════════════════

def test_handle_extract_profile_complete():
    """画像收集完成时，回复应引导用户进入路径规划。"""
    print("=" * 60)
    print("测试 9：画像完成时的引导")
    print("=" * 60)

    client = MockLLMClient(call_sequence=[
        (_make_intent_response("extract_profile"), True, None),
        (_make_profile_extraction_json(is_complete=True, follow_up=""), True, None),
    ])
    sup = Supervisor(client=client)
    session = _make_session()

    result = sup.handle("我的所有信息都在这里了", session)

    assert result.success
    assert result.session.student_profile is not None
    # 回复应包含路径规划引导
    assert "学习路径" in result.reply or "规划" in result.reply, \
        f"回复应引导到路径规划: '{result.reply[:100]}'"

    print(f"  回复: '{result.reply[:150]}...'")
    print("[PASS] 画像完成引导正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 10：路径规划流程（happy path）
# ═══════════════════════════════════════════════════════════════

def test_handle_plan_path():
    """Supervisor 处理路径规划的完整流程。"""
    print("=" * 60)
    print("测试 10：路径规划完整流程")
    print("=" * 60)

    dag_path = _make_dag_json()

    try:
        client = MockLLMClient(call_sequence=[
            (_make_intent_response("plan_path"), True, None),  # 意图分类
            (_make_planner_json(), True, None),  # Planner LLM 调用
        ])
        sup = Supervisor(client=client, dag_path=dag_path)
        session = _make_session(with_profile=True)

        result = sup.handle("帮我规划学习路径", session)

        assert result.success, f"应该成功: {result.error}"
        assert result.intent == TaskIntent.PLAN_PATH
        assert result.session is not None
        assert result.session.current_learning_path is not None

        path = result.session.current_learning_path
        assert len(path.nodes) == 3
        assert path.course_name == "数据结构与算法"

        # 回复应包含路径信息
        assert "数组" in result.reply
        assert "学习路径" in result.reply

        print(f"  路径节点数: {len(path.nodes)}")
        print(f"  总时长: {path.total_estimated_minutes} 分钟")
        print(f"  回复前 200 字符: '{result.reply[:200]}'")
        print("[PASS] 路径规划完整流程正确\n")

    finally:
        os.unlink(dag_path)


# ═══════════════════════════════════════════════════════════════
# 测试 11：路径规划 - 无画像时引导先采集
# ═══════════════════════════════════════════════════════════════

def test_plan_path_without_profile():
    """没有画像时请求路径规划，应引导用户先完善画像。"""
    print("=" * 60)
    print("测试 11：路径规划 - 无画像引导")
    print("=" * 60)

    client = MockLLMClient(content=_make_intent_response("plan_path"))
    sup = Supervisor(client=client)
    session = _make_session()  # 无画像

    result = sup.handle("帮我规划学习", session)

    assert result.success
    assert result.intent == TaskIntent.PLAN_PATH
    # 应该引导用户先提供画像
    assert "画像" in result.reply or "了解" in result.reply or "介绍" in result.reply, \
        f"应引导用户先完善画像: '{result.reply[:100]}'"

    print(f"  回复: '{result.reply[:150]}...'")
    print("[PASS] 无画像引导正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 12：闲聊处理
# ═══════════════════════════════════════════════════════════════

def test_handle_chitchat():
    """闲聊意图应返回简短友好回复。"""
    print("=" * 60)
    print("测试 12：闲聊处理")
    print("=" * 60)

    client = MockLLMClient(call_sequence=[
        (_make_intent_response("chitchat"), True, None),  # 意图分类
        ("你好！有什么可以帮你的吗？", True, None),  # 闲聊回复
    ])
    sup = Supervisor(client=client)
    session = _make_session()

    result = sup.handle("你好", session)

    assert result.success
    assert result.intent == TaskIntent.CHITCHAT
    assert len(result.reply) > 0

    # 对话历史应增加
    assert len(result.session.conversation_history) >= 2

    print(f"  回复: '{result.reply}'")
    print("[PASS] 闲聊处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 13：答疑处理
# ═══════════════════════════════════════════════════════════════

def test_handle_answer_question():
    """答疑意图应返回 LLM 的直接回答。"""
    print("=" * 60)
    print("测试 13：答疑处理")
    print("=" * 60)

    client = MockLLMClient(call_sequence=[
        (_make_intent_response("answer_question"), True, None),  # 意图分类
        ("二叉树的中序遍历是指：先遍历左子树，然后访问根节点，最后遍历右子树。这种遍历方式常用于表达式树的计算。", True, None),  # 答疑回复
    ])
    sup = Supervisor(client=client)
    session = _make_session(with_profile=True)

    result = sup.handle("什么是中序遍历", session)

    assert result.success
    assert result.intent == TaskIntent.ANSWER_QUESTION
    assert "中序遍历" in result.reply or "二叉树" in result.reply

    print(f"  回复: '{result.reply[:120]}...'")
    print("[PASS] 答疑处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 14：占位意图（generate_resource / evaluate）
# ═══════════════════════════════════════════════════════════════

def test_handle_placeholder_intents():
    """未实现功能应返回状态提示和替代建议。"""
    print("=" * 60)
    print("测试 14：占位意图处理")
    print("=" * 60)

    # generate_resource
    client1 = MockLLMClient(content=_make_intent_response("generate_resource"))
    sup1 = Supervisor(client=client1)
    session1 = _make_session(with_profile=True, with_path=True)

    result1 = sup1.handle("帮我生成一份讲义的资料", session1)
    assert result1.success
    assert result1.intent == TaskIntent.GENERATE_RESOURCE
    assert "开发中" in result1.reply or "资源" in result1.reply
    print(f"  generate_resource 回复: '{result1.reply[:120]}...'")

    # evaluate
    client2 = MockLLMClient(content=_make_intent_response("evaluate"))
    sup2 = Supervisor(client=client2)
    session2 = _make_session(with_profile=True, with_path=True)

    result2 = sup2.handle("帮我评估一下学习效果", session2)
    assert result2.success
    assert result2.intent == TaskIntent.EVALUATE
    assert "开发中" in result2.reply or "评估" in result2.reply
    print(f"  evaluate 回复: '{result2.reply[:120]}...'")

    print("[PASS] 占位意图处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 15：SessionState 不可变性（deep copy）
# ═══════════════════════════════════════════════════════════════

def test_session_immutability():
    """每次 handle 应返回新的 SessionState 对象，不修改原 session。"""
    print("=" * 60)
    print("测试 15：SessionState 不可变性")
    print("=" * 60)

    client = MockLLMClient(call_sequence=[
        (_make_intent_response("extract_profile"), True, None),
        (_make_profile_extraction_json(is_complete=False), True, None),
    ])
    sup = Supervisor(client=client)
    original_session = _make_session()
    original_id = id(original_session)

    result = sup.handle("我是计算机学生", original_session)

    # 返回的 session 应该是新对象
    assert result.session is not None
    assert id(result.session) != original_id, "handle 应返回新的 SessionState"

    # 原始 session 不应被修改
    assert original_session.student_profile is None, \
        "原始 session 的 student_profile 不应被修改"
    assert len(original_session.conversation_history) == 0, \
        "原始 session 的对话历史不应被修改"

    print(f"  原始 session ID: {original_id}")
    print(f"  返回 session ID: {id(result.session)}")
    print(f"  原始 profile 保持 None: [OK]")
    print(f"  返回 profile 已填充: [OK]")
    print("[PASS] SessionState 不可变性正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 16：Intent 分类时 state_summary 包含对话历史
# ═══════════════════════════════════════════════════════════════

def test_state_summary_includes_history():
    """_build_state_summary 应包含最近的对话上下文。"""
    print("=" * 60)
    print("测试 16：State Summary 包含对话历史")
    print("=" * 60)

    session = _make_session()
    session.conversation_history = [
        {"role": "assistant", "content": "你的专业是什么？"},
        {"role": "user", "content": "计算机科学"},
        {"role": "assistant", "content": "你的年级呢？"},
        {"role": "user", "content": "大三"},
    ]

    summary = Supervisor._build_state_summary(session)

    assert "计算机科学" in summary, f"应包含最近对话内容: {summary}"
    assert "大三" in summary
    assert "最近对话" in summary

    print(f"  Summary 长度: {len(summary)} 字符")
    print(f"  包含对话内容: [OK]")
    print("[PASS] State Summary 包含对话历史\n")


# ═══════════════════════════════════════════════════════════════
# 测试 17：未知意图处理
# ═══════════════════════════════════════════════════════════════

def test_unknown_intent():
    """LLM 返回未知意图时应返回友好提示。"""
    print("=" * 60)
    print("测试 17：未知意图处理")
    print("=" * 60)

    client = MockLLMClient(
        content=_make_intent_response("unknown_intent_type")
    )
    sup = Supervisor(client=client)
    session = _make_session()

    # classify_intent 对未知意图应兜底为 chitchat
    intent, confidence, _ = sup.classify_intent("奇怪的问题...", session)
    assert intent == TaskIntent.CHITCHAT, f"未知意图应兜底 chitchat: {intent.value}"

    print(f"  未知意图兜底为: {intent.value}")
    print("[PASS] 未知意图处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 18：异步 handle_async 不阻塞事件循环
# ═══════════════════════════════════════════════════════════════

async def _test_handle_async_basic():
    """handle_async 应正确返回结果（在线程池中执行同步逻辑）。"""
    print("=" * 60)
    print("测试 18：handle_async 异步支持")
    print("=" * 60)

    client = MockLLMClient(call_sequence=[
        (_make_intent_response("extract_profile"), True, None),
        (_make_profile_extraction_json(is_complete=False), True, None),
    ])
    sup = Supervisor(client=client)
    session = _make_session()

    result = await sup.handle_async("我是计算机大三学生", session)

    assert result is not None
    assert result.success
    assert result.intent == TaskIntent.EXTRACT_PROFILE
    assert result.session is not None
    assert result.session.student_profile is not None

    print(f"  handle_async 返回: intent={result.intent.value}")
    print(f"  画像专业: {result.session.student_profile.major}")
    print("[PASS] handle_async 异步支持正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 19：异步并发调用
# ═══════════════════════════════════════════════════════════════

async def _test_handle_async_concurrent():
    """多个 handle_async 调用应能并发执行。"""
    print("=" * 60)
    print("测试 19：异步并发调用")
    print("=" * 60)

    async def make_supervisor_and_call(user_text):
        client = MockLLMClient(call_sequence=[
            (_make_intent_response("chitchat"), True, None),
            (f"回复: {user_text}", True, None),
        ])
        sup = Supervisor(client=client)
        return await sup.handle_async(user_text, _make_session())

    tasks = [
        make_supervisor_and_call("你好"),
        make_supervisor_and_call("早上好"),
        make_supervisor_and_call("晚上好"),
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    for i, result in enumerate(results):
        assert result.success, f"任务 {i} 应成功: {result.error}"
        assert len(result.reply) > 0

    print(f"  并发调用数: {len(results)}")
    for i, r in enumerate(results):
        print(f"    任务 {i}: intent={r.intent.value} reply='{r.reply[:40]}...'")
    print("[PASS] 异步并发调用正确\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    """运行所有测试并统计结果。"""
    print("=" * 60)
    print("  Supervisor Agent (supervisor.py) 测试")
    print("=" * 60)
    print()

    sync_tests = [
        test_intent_extract_profile,
        test_intent_plan_path,
        test_intent_answer_question,
        test_intent_chitchat,
        test_intent_fallback_llm_failure,
        test_intent_fallback_json_failure,
        test_empty_input,
        test_handle_extract_profile,
        test_handle_extract_profile_complete,
        test_handle_plan_path,
        test_plan_path_without_profile,
        test_handle_chitchat,
        test_handle_answer_question,
        test_handle_placeholder_intents,
        test_session_immutability,
        test_state_summary_includes_history,
        test_unknown_intent,
    ]

    async_tests = [
        _test_handle_async_basic,
        _test_handle_async_concurrent,
    ]

    passed = 0
    failed = 0

    # 运行同步测试
    for test in sync_tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {test.__name__}: {e}\n")
        except Exception as e:
            failed += 1
            import traceback
            print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
            print()

    # 运行异步测试
    async def run_async_tests():
        nonlocal passed, failed
        for test in async_tests:
            try:
                await test()
                passed += 1
            except AssertionError as e:
                failed += 1
                print(f"[FAIL] {test.__name__}: {e}\n")
            except Exception as e:
                failed += 1
                import traceback
                print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
                traceback.print_exc()
                print()

    asyncio.run(run_async_tests())

    total = len(sync_tests) + len(async_tests)
    print("=" * 60)
    print(f"  结果: {passed}/{total} 通过")
    if failed == 0:
        print("  全部通过！Supervisor Agent 可以放心使用。")
    else:
        print(f"  {failed} 个测试失败，请检查。")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
