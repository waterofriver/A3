# -*- coding: utf-8 -*-
"""
Planner Agent 测试 —— 验证拓扑排序、个性化标注、DAG 循环检测、空输出处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.planner.test_planner

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
import io
from copy import deepcopy

# 修复 Windows 控制台 GBK 编码导致的 UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .planner import PlannerAgent, PlannerResult
from ..utils import LLMResponse
from ..models import (
    StudentProfile,
    KnowledgePoint,
    KnowledgeDAG,
    LearningPath,
    LearningPathNode,
    WeakPoint,
    KnowledgeBaseItem,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
    ResourceType,
)


# ═══════════════════════════════════════════════════════════════
# Mock LLM 客户端
# ═══════════════════════════════════════════════════════════════

class MockLLMClient:
    """可注入的 Mock LLM 客户端，用于隔离测试 PlannerAgent 逻辑。"""

    def __init__(self, content="", success=True, error=None):
        self.content = content
        self.success = success
        self.error = error
        self.last_call_kwargs = None

    def chat(self, **kwargs):
        self.last_call_kwargs = kwargs
        return LLMResponse(
            content=self.content,
            success=self.success,
            error=self.error,
            model="mock-model",
        )


# ═══════════════════════════════════════════════════════════════
# 测试 Fixture：构建测试数据
# ═══════════════════════════════════════════════════════════════

def _make_profile(**overrides):
    """快速构造 StudentProfile 用于测试。"""
    defaults = dict(
        major="计算机科学与技术",
        grade="大三",
        knowledge_base=[
            KnowledgeBaseItem(
                knowledge_point_id="array",
                knowledge_point_name="数组",
                mastery=MasteryLevel.PROFICIENT,
            ),
        ],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="通过数据结构考试",
        weak_points=[
            WeakPoint(
                knowledge_point_id="linked_list",
                knowledge_point_name="链表",
                error_pattern="指针操作容易出错",
                occurrence_count=3,
            ),
        ],
        learning_pace=LearningPace.DISTRIBUTED,
        interest_domains=["游戏开发"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_dag(*, cyclic=False):
    """构建一个标准的 5 节点知识 DAG。

    结构:
        array → linked_list → stack
        array → linked_list → queue
        array → binary_tree

    如果 cyclic=True，在 linked_list ←→ stack 之间制造循环。
    """
    kps = [
        KnowledgePoint(
            id="array", name="数组基础",
            description="线性存储结构",
            category="线性结构",
            prerequisites=[],
            difficulty=1,
            estimated_minutes=20,
        ),
        KnowledgePoint(
            id="linked_list", name="链表",
            description="链式存储结构",
            category="线性结构",
            prerequisites=["array"],
            difficulty=2,
            estimated_minutes=30,
        ),
        KnowledgePoint(
            id="stack", name="栈",
            description="后进先出结构",
            category="线性结构",
            prerequisites=["linked_list"],
            difficulty=2,
            estimated_minutes=25,
        ),
        KnowledgePoint(
            id="queue", name="队列",
            description="先进先出结构",
            category="线性结构",
            prerequisites=["linked_list"],
            difficulty=2,
            estimated_minutes=25,
        ),
        KnowledgePoint(
            id="binary_tree", name="二叉树",
            description="树形结构基础",
            category="树结构",
            prerequisites=["linked_list"],
            difficulty=3,
            estimated_minutes=40,
        ),
    ]

    if cyclic:
        # 修改 stack 的 prerequisites 使其指向 linked_list，
        # 同时 linked_list 已经指向 stack... 等等，linked_list 不指向 stack。
        # 要制造循环，让 linked_list 的 prerequisites 添加 stack 的引用。
        # linked_list 依赖 array 和 stack，stack 依赖 linked_list → 循环
        for kp in kps:
            if kp.id == "linked_list":
                kp.prerequisites.append("stack")

    return KnowledgeDAG(
        course_name="数据结构与算法",
        course_description="计算机基础核心课程",
        knowledge_points=kps,
    )


def _make_llm_response(nodes=None, overall_rationale=""):
    """构造标准的 LLM 返回 JSON（5 个知识点的个性化标注）。"""
    if nodes is None:
        nodes = [
            {
                "knowledge_point_id": "array",
                "depth": 1,
                "recommended_resource_types": ["doc"],
                "rationale": "你已熟练掌握数组，快速了解即可。",
                "is_weak_point": False,
                "estimated_time_minutes": 15,
            },
            {
                "knowledge_point_id": "linked_list",
                "depth": 3,
                "recommended_resource_types": ["doc", "mindmap", "code", "quiz"],
                "rationale": "这是你的薄弱环节，需要重点攻克。",
                "is_weak_point": True,
                "estimated_time_minutes": 45,
            },
            {
                "knowledge_point_id": "stack",
                "depth": 2,
                "recommended_resource_types": ["doc", "code"],
                "rationale": "基于链表基础，掌握栈的核心操作。",
                "is_weak_point": False,
                "estimated_time_minutes": 25,
            },
            {
                "knowledge_point_id": "queue",
                "depth": 2,
                "recommended_resource_types": ["doc", "code"],
                "rationale": "与栈对比学习，加深理解。",
                "is_weak_point": False,
                "estimated_time_minutes": 25,
            },
            {
                "knowledge_point_id": "binary_tree",
                "depth": 3,
                "recommended_resource_types": ["doc", "mindmap", "code", "quiz"],
                "rationale": "树结构是后续算法的基础，需要精通。",
                "is_weak_point": False,
                "estimated_time_minutes": 40,
            },
        ]

    return """```json
{{
    "nodes": {nodes_json},
    "overall_rationale": "{rationale}"
}}
```""".format(
        nodes_json=__import__("json").dumps(nodes, ensure_ascii=False),
        rationale=overall_rationale or "根据你的薄弱环节，重点安排了链表和二叉树的深入学习。",
    )


# ═══════════════════════════════════════════════════════════════
# 测试 1：拓扑排序 - 正常 DAG
# ═══════════════════════════════════════════════════════════════

def test_topological_sort_normal():
    """拓扑排序应返回按前置依赖排列的知识点列表。"""
    print("=" * 60)
    print("测试 1：拓扑排序 - 正常 DAG")
    print("=" * 60)

    dag = _make_dag()
    result = PlannerAgent._topological_sort(dag)

    # 5 个节点全部排序
    assert len(result) == 5, f"应有 5 个节点: {len(result)}"

    # array 是入口，应该排第一
    assert result[0].id == "array", f"入口节点应该是 array: {result[0].id}"

    # linked_list 依赖 array，应在 array 之后
    array_idx = next(i for i, kp in enumerate(result) if kp.id == "array")
    ll_idx = next(i for i, kp in enumerate(result) if kp.id == "linked_list")
    assert array_idx < ll_idx, "array 应在 linked_list 之前"

    # binary_tree 依赖 linked_list
    bt_idx = next(i for i, kp in enumerate(result) if kp.id == "binary_tree")
    assert ll_idx < bt_idx, "linked_list 应在 binary_tree 之前"

    print(f"  排序结果: {' → '.join(kp.id for kp in result)}")
    print("[PASS] 拓扑排序正常\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：拓扑排序 - 循环 DAG 抛异常
# ═══════════════════════════════════════════════════════════════

def test_topological_sort_cycle_raises():
    """循环依赖应抛出 ValueError 异常。"""
    print("=" * 60)
    print("测试 2：拓扑排序 - 循环 DAG 抛异常")
    print("=" * 60)

    dag = _make_dag(cyclic=True)

    try:
        PlannerAgent._topological_sort(dag)
        assert False, "循环 DAG 应该抛出异常"
    except ValueError as e:
        msg = str(e)
        assert "循环依赖" in msg, f"异常信息应包含'循环依赖': {msg}"
        print(f"  异常信息: {msg}")
        print("[PASS] 循环依赖正确抛出异常\n")


# ═══════════════════════════════════════════════════════════════
# 测试 3：正常路径生成
# ═══════════════════════════════════════════════════════════════

def test_basic_path_generation():
    """正常输入应生成完整的个性化学习路径。"""
    print("=" * 60)
    print("测试 3：正常路径生成")
    print("=" * 60)

    mock_content = _make_llm_response()
    client = MockLLMClient(content=mock_content)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success, f"规划应该成功: {result.error}"
    assert result.learning_path is not None
    path = result.learning_path

    # 节点数
    assert len(path.nodes) == 5, f"应有 5 个节点: {len(path.nodes)}"

    # 薄弱环节标记
    weak_nodes = [n for n in path.nodes if n.is_weak_point]
    assert len(weak_nodes) == 1, f"应有 1 个薄弱环节节点: {len(weak_nodes)}"
    assert weak_nodes[0].knowledge_point_id == "linked_list"

    # 深度标记
    array_node = path.nodes[0]
    ll_node = path.nodes[1]
    assert array_node.depth == 1, f"array 深度应为 1（熟练）: {array_node.depth}"
    assert ll_node.depth == 3, f"linked_list 深度应为 3（薄弱环节）: {ll_node.depth}"

    # 资源类型
    assert len(ll_node.recommended_resource_types) >= 2, "薄弱环节应有更多资源类型"

    # 顺序正确
    assert path.nodes[0].order == 1
    assert path.nodes[-1].order == 5

    # 总时长
    assert path.total_estimated_minutes > 0

    # 版本号
    assert path.version == 1

    print(f"  路径节点数: {len(path.nodes)}")
    print(f"  薄弱环节: {[n.knowledge_point_name for n in weak_nodes]}")
    print(f"  总时长: {path.total_estimated_minutes} 分钟")
    print(f"  版本: {path.version}")
    print("[PASS] 正常路径生成通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 4：LLM 调用失败
# ═══════════════════════════════════════════════════════════════

def test_llm_failure():
    """LLM 调用失败时应返回 success=False。"""
    print("=" * 60)
    print("测试 4：LLM 调用失败")
    print("=" * 60)

    client = MockLLMClient(success=False, error="Connection timeout")
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success is False, "LLM 失败时 success 应为 False"
    assert result.error is not None
    assert "timeout" in result.error.lower() or "失败" in result.error

    print(f"  错误信息: {result.error}")
    print("[PASS] LLM 失败处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 5：空 DAG
# ═══════════════════════════════════════════════════════════════

def test_empty_dag():
    """空 DAG（无知识点）应返回失败。"""
    print("=" * 60)
    print("测试 5：空 DAG")
    print("=" * 60)

    agent = PlannerAgent(client=MockLLMClient())
    profile = _make_profile()
    empty_dag = KnowledgeDAG(
        course_name="空课程",
        knowledge_points=[],
    )

    result = agent.plan(profile, empty_dag)

    assert result.success is False
    assert "没有知识点" in result.error or "知识点" in result.error

    print(f"  错误信息: {result.error}")
    print("[PASS] 空 DAG 正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 6：DAG 循环依赖时 plan() 返回失败
# ═══════════════════════════════════════════════════════════════

def test_plan_with_cycle_returns_failure():
    """plan() 遇到循环 DAG 应返回 success=False 而不是静默成功。"""
    print("=" * 60)
    print("测试 6：plan() 循环依赖返回失败")
    print("=" * 60)

    agent = PlannerAgent(client=MockLLMClient())
    profile = _make_profile()
    dag = _make_dag(cyclic=True)

    result = agent.plan(profile, dag)

    assert result.success is False, "循环 DAG 的 plan() 应返回 False"
    assert "循环依赖" in (result.error or ""), f"错误信息应包含'循环依赖': {result.error}"
    assert len(result.warnings) >= 1, "应有警告信息"

    print(f"  错误信息: {result.error}")
    print(f"  警告数: {len(result.warnings)}")
    print("[PASS] plan() 循环依赖正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：LLM 返回空的 nodes 列表
# ═══════════════════════════════════════════════════════════════

def test_empty_llm_nodes():
    """LLM 返回空的 nodes 列表时应返回失败而不是全部默认填充。"""
    print("=" * 60)
    print("测试 7：LLM 返回空 nodes")
    print("=" * 60)

    mock_response = """```json
{
    "nodes": [],
    "overall_rationale": ""
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success is False, "空 nodes 应返回失败"
    assert "空" in (result.error or "").lower() or "未返回" in (result.error or "")

    print(f"  错误信息: {result.error}")
    print("[PASS] 空 nodes 正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 8：JSON 解析失败
# ═══════════════════════════════════════════════════════════════

def test_json_parse_failure():
    """LLM 返回非 JSON 内容时应返回失败。"""
    print("=" * 60)
    print("测试 8：JSON 解析失败")
    print("=" * 60)

    mock_response = "这是一段完全不是 JSON 的纯文本回复。"
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success is False, "JSON 解析失败应返回 success=False"
    assert "JSON" in (result.error or "").upper() or "解析" in (result.error or "")

    print(f"  错误信息: {result.error}")
    print("[PASS] JSON 解析失败正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 9：LLM 返回部分节点（部分标注缺失）
# ═══════════════════════════════════════════════════════════════

def test_partial_llm_nodes():
    """LLM 只返回部分节点时，缺失节点应自动补充，但有警告。"""
    print("=" * 60)
    print("测试 9：LLM 返回部分节点（自动补充）")
    print("=" * 60)

    # LLM 只返回了 3 个节点（共 5 个知识点）
    partial_nodes = [
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
            "depth": 3,
            "recommended_resource_types": ["doc", "mindmap", "code", "quiz"],
            "rationale": "薄弱环节，重点学习。",
            "is_weak_point": True,
            "estimated_time_minutes": 45,
        },
        {
            "knowledge_point_id": "stack",
            "depth": 2,
            "recommended_resource_types": ["doc", "code"],
            "rationale": "栈的基本操作。",
            "is_weak_point": False,
            "estimated_time_minutes": 25,
        },
    ]

    import json
    mock_response = f"""```json
{{
    "nodes": {json.dumps(partial_nodes, ensure_ascii=False)},
    "overall_rationale": "部分节点需要手动补充"
}}
```"""
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success, f"部分节点应成功: {result.error}"
    assert result.learning_path is not None
    path = result.learning_path

    # 总共 5 个节点
    assert len(path.nodes) == 5, f"应有 5 个节点: {len(path.nodes)}"

    # 自动补充的节点使用默认值
    auto_filled = [n for n in path.nodes if "自动补充" in n.rationale]
    assert len(auto_filled) == 2, f"应有 2 个自动补充节点: {len(auto_filled)}"
    for node in auto_filled:
        assert node.depth == 2
        assert ResourceType.DOC in node.recommended_resource_types

    # 部分节点缺失（≥50%）会产生警告
    # 3/5 = 60% 有个性化，2/5 = 40% 自动补充 → 40% < 50%，无警告
    # 但 warnings 可能包含其他信息
    print(f"  总节点数: {len(path.nodes)}")
    print(f"  LLM 标注: {3} | 自动补充: {2}")
    print(f"  警告数: {len(result.warnings)}")
    print("[PASS] 部分节点补充正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 10：大部分节点缺失（覆盖率 < 50%）
# ═══════════════════════════════════════════════════════════════

def test_majority_auto_filled():
    """LLM 返回不足 50% 节点时应有警告但路径仍成功生成。"""
    print("=" * 60)
    print("测试 10：大部分节点自动填充（低覆盖率）")
    print("=" * 60)

    # LLM 只返回 2 个节点（共 5 个，覆盖率 40%）
    sparse_nodes = [
        {
            "knowledge_point_id": "array",
            "depth": 1,
            "recommended_resource_types": ["doc"],
            "rationale": "已掌握。",
            "is_weak_point": False,
            "estimated_time_minutes": 15,
        },
        {
            "knowledge_point_id": "linked_list",
            "depth": 3,
            "recommended_resource_types": ["doc", "code"],
            "rationale": "薄弱环节。",
            "is_weak_point": True,
            "estimated_time_minutes": 45,
        },
    ]

    import json
    mock_response = f"""```json
{{
    "nodes": {json.dumps(sparse_nodes, ensure_ascii=False)},
    "overall_rationale": ""
}}
```"""
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    # 仍然成功（因为有兜底），但有警告
    assert result.success, f"应成功: {result.error}"
    assert len(result.warnings) >= 1, "覆盖率不足 50% 应有警告"
    assert any("覆盖率不足" in w for w in result.warnings), \
        f"应有覆盖率不足的警告: {result.warnings}"

    assert len(result.learning_path.nodes) == 5  # 全部 5 个节点

    print(f"  节点数: {len(result.learning_path.nodes)}")
    print(f"  警告: {result.warnings}")
    print("[PASS] 低覆盖率警告正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 11：含无效知识点 ID
# ═══════════════════════════════════════════════════════════════

def test_invalid_knowledge_point_ids():
    """LLM 返回无效知识点 ID 时应跳过并记录警告。"""
    print("=" * 60)
    print("测试 11：含无效知识点 ID")
    print("=" * 60)

    nodes_with_invalid = [
        {
            "knowledge_point_id": "array",
            "depth": 1,
            "recommended_resource_types": ["doc"],
            "rationale": "正常节点。",
            "is_weak_point": False,
            "estimated_time_minutes": 15,
        },
        {
            "knowledge_point_id": "nonexistent_kp_123",  # 不存在的 ID
            "depth": 3,
            "recommended_resource_types": ["doc", "code"],
            "rationale": "这个 ID 不存在。",
            "is_weak_point": True,
            "estimated_time_minutes": 30,
        },
        {
            "knowledge_point_id": "linked_list",
            "depth": 2,
            "recommended_resource_types": ["doc"],
            "rationale": "正常节点。",
            "is_weak_point": False,
            "estimated_time_minutes": 25,
        },
    ]

    import json
    mock_response = f"""```json
{{
    "nodes": {json.dumps(nodes_with_invalid, ensure_ascii=False)},
    "overall_rationale": ""
}}
```"""
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success, f"应成功: {result.error}"
    assert result.learning_path is not None
    path = result.learning_path

    # 无效节点被跳过，有效节点保留，缺失的自动补充
    assert len(path.nodes) == 5, f"应有 5 个节点: {len(path.nodes)}"

    # 应该有关于无效 ID 的警告
    assert len(result.warnings) >= 1, "应有无效 ID 的警告"
    assert any("未知知识点" in w for w in result.warnings), \
        f"应有未知知识点的警告: {result.warnings}"

    print(f"  节点数: {len(path.nodes)}")
    print(f"  警告: {result.warnings}")
    print("[PASS] 无效知识点 ID 正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 12：增量更新（existing_path → version 递增）
# ═══════════════════════════════════════════════════════════════

def test_incremental_update_version():
    """已有路径时，新路径的 version 应递增。"""
    print("=" * 60)
    print("测试 12：增量更新 version 递增")
    print("=" * 60)

    mock_content = _make_llm_response()
    client = MockLLMClient(content=mock_content)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    existing = LearningPath(
        course_name="数据结构与算法",
        nodes=[
            LearningPathNode(
                order=1,
                knowledge_point_id="array",
                knowledge_point_name="数组基础",
                depth=1,
                recommended_resource_types=[ResourceType.DOC],
                rationale="第一次规划",
                estimated_time_minutes=15,
            ),
        ],
        version=3,
    )

    result = agent.plan(profile, dag, existing_path=existing)

    assert result.success
    assert result.learning_path.version == 4, f"版本应从 3 递增到 4: {result.learning_path.version}"

    print(f"  旧版本: 3 → 新版本: {result.learning_path.version}")
    print("[PASS] 增量更新 version 正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 13：System Prompt 包含学生画像和知识点列表
# ═══════════════════════════════════════════════════════════════

def test_system_prompt_contains_profile_and_kps():
    """System Prompt 应包含学生画像快照和完整知识点列表。"""
    print("=" * 60)
    print("测试 13：System Prompt 包含画像和知识点")
    print("=" * 60)

    mock_content = _make_llm_response()
    client = MockLLMClient(content=mock_content)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success
    last_kwargs = client.last_call_kwargs
    assert last_kwargs is not None, "应该调用了 LLM"

    system_prompt = last_kwargs.get("system_prompt", "")

    # 检查画像信息
    assert "计算机科学与技术" in system_prompt
    assert "游戏开发" in system_prompt
    assert "linked_list" in system_prompt  # 薄弱环节 ID
    assert "指针操作" in system_prompt  # 薄弱环节错误模式

    # 检查知识点列表
    assert "array" in system_prompt
    assert "linked_list" in system_prompt
    assert "stack" in system_prompt
    assert "queue" in system_prompt
    assert "binary_tree" in system_prompt

    # 检查难度和时长
    assert "difficulty=" in system_prompt
    assert "estimated=" in system_prompt

    print(f"  System Prompt 长度: {len(system_prompt)} 字符")
    print(f"  包含画像: [OK]")
    print(f"  包含知识点列表: [OK]")
    print(f"  包含薄弱环节: [OK]")
    print("[PASS] System Prompt 构建正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 14：资源类型边界（空资源类型兜底）
# ═══════════════════════════════════════════════════════════════

def test_resource_type_fallback():
    """LLM 未返回资源类型时，应有 doc + mindmap 兜底。"""
    print("=" * 60)
    print("测试 14：资源类型兜底")
    print("=" * 60)

    # LLM 返回的节点没有 recommended_resource_types 字段
    nodes_no_resources = [
        {
            "knowledge_point_id": "array",
            "depth": 2,
            # 故意不写 recommended_resource_types
            "rationale": "测试空资源类型。",
            "is_weak_point": False,
            "estimated_time_minutes": 20,
        },
    ]

    import json
    mock_response = f"""```json
{{
    "nodes": {json.dumps(nodes_no_resources, ensure_ascii=False)},
    "overall_rationale": ""
}}
```"""
    client = MockLLMClient(content=mock_response)
    agent = PlannerAgent(client=client)
    profile = _make_profile()
    dag = _make_dag()

    result = agent.plan(profile, dag)

    assert result.success
    path = result.learning_path
    array_node = next(n for n in path.nodes if n.knowledge_point_id == "array")
    assert len(array_node.recommended_resource_types) >= 1, \
        f"应有兜底的资源类型: {array_node.recommended_resource_types}"
    assert ResourceType.DOC in array_node.recommended_resource_types

    print(f"  兜底资源类型: {[rt.value for rt in array_node.recommended_resource_types]}")
    print("[PASS] 资源类型兜底正确\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    """运行所有测试并统计结果。"""
    print("=" * 60)
    print("  Planner Agent (planner.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_topological_sort_normal,
        test_topological_sort_cycle_raises,
        test_basic_path_generation,
        test_llm_failure,
        test_empty_dag,
        test_plan_with_cycle_returns_failure,
        test_empty_llm_nodes,
        test_json_parse_failure,
        test_partial_llm_nodes,
        test_majority_auto_filled,
        test_invalid_knowledge_point_ids,
        test_incremental_update_version,
        test_system_prompt_contains_profile_and_kps,
        test_resource_type_fallback,
    ]

    passed = 0
    failed = 0

    for test in tests:
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

    print("=" * 60)
    print(f"  结果: {passed}/{len(tests)} 通过")
    if failed == 0:
        print("  全部通过！Planner Agent 可以放心使用。")
    else:
        print(f"  {failed} 个测试失败，请检查。")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
