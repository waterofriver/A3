# -*- coding: utf-8 -*-
"""
MindMap Agent 测试 —— 验证思维导图生成的结构正确性、Mermaid 语法和边界处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.mindmap_agent.test_mindmap_agent

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
import io
import json
from copy import deepcopy

# 修复 Windows 控制台 GBK 编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .mindmap_agent import MindMapAgent, MindMapResult
from ..utils import LLMResponse
from ..models import (
    StudentProfile,
    KnowledgePoint,
    KnowledgeBaseItem,
    WeakPoint,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
    ResourceType,
)


# ═══════════════════════════════════════════════════════════════
# Mock LLM 客户端
# ═══════════════════════════════════════════════════════════════

class MockLLMClient:
    """可注入的 Mock LLM 客户端。"""

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
# 测试 Fixture
# ═══════════════════════════════════════════════════════════════

def _make_kp():
    """构造一个标准知识点。"""
    return KnowledgePoint(
        id="exp03_slam_mapping_navigation",
        name="SLAM 地图构建与导航",
        description="通过地图构建与导航流程理解机器人定位、建图和路径规划的核心机制。",
        category="移动与导航",
        prerequisites=["exp02_robot_remote_control"],
        difficulty=3,
        estimated_minutes=90,
        tags=["SLAM", "导航", "路径规划"],
    )


def _make_profile(**overrides):
    """快速构造 StudentProfile。"""
    defaults = dict(
        major="机器人工程",
        grade="大三",
        knowledge_base=[
            KnowledgeBaseItem(
                knowledge_point_id="ros_basics",
                knowledge_point_name="ROS 基础",
                mastery=MasteryLevel.FAMILIAR,
            ),
            KnowledgeBaseItem(
                knowledge_point_id="python",
                knowledge_point_name="Python 编程",
                mastery=MasteryLevel.PROFICIENT,
            ),
        ],
        cognitive_style=CognitiveStyle.THEORY_ORIENTED,
        learning_goal_short="掌握机器人自主导航技术",
        weak_points=[
            WeakPoint(
                knowledge_point_id="exp03_slam_mapping_navigation",
                knowledge_point_name="SLAM 地图构建与导航",
                error_pattern="粒子滤波的数学推导理解困难",
                occurrence_count=1,
            ),
        ],
        learning_pace=LearningPace.INTENSIVE,
        interest_domains=["机器人", "自动驾驶"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_mindmap_response():
    """构造标准的思维导图 LLM 返回 JSON。"""
    return """```json
{
    "root_topic": "SLAM 地图构建与导航",
    "mermaid_code": "mindmap\\n  root((SLAM 地图构建与导航))\\n    核心概念\\n      SLAM 问题定义\\n      定位与建图耦合\\n      概率模型\\n    关键算法\\n      粒子滤波\\n      扩展卡尔曼滤波\\n      图优化\\n    传感器模型\\n      激光雷达\\n      里程计\\n      IMU\\n    地图表示\\n      栅格地图\\n      特征地图\\n      拓扑地图\\n    实践操作\\n      ROS Navigation Stack\\n      gmapping 配置\\n      导航参数调优\\n    常见问题\\n      粒子发散\\n      回环检测失败\\n      计算资源不足",
    "nodes": [
        {"id": "root", "label": "SLAM 地图构建与导航", "parent_id": null, "children": ["n1", "n2", "n3", "n4", "n5", "n6"]},
        {"id": "n1", "label": "核心概念", "parent_id": "root", "children": ["n1a", "n1b", "n1c"]},
        {"id": "n1a", "label": "SLAM 问题定义", "parent_id": "n1", "children": []},
        {"id": "n1b", "label": "定位与建图耦合", "parent_id": "n1", "children": []},
        {"id": "n1c", "label": "概率模型", "parent_id": "n1", "children": []},
        {"id": "n2", "label": "关键算法", "parent_id": "root", "children": ["n2a", "n2b", "n2c"]},
        {"id": "n2a", "label": "粒子滤波", "parent_id": "n2", "children": []},
        {"id": "n2b", "label": "扩展卡尔曼滤波", "parent_id": "n2", "children": []},
        {"id": "n2c", "label": "图优化", "parent_id": "n2", "children": []},
        {"id": "n3", "label": "传感器模型", "parent_id": "root", "children": ["n3a", "n3b", "n3c"]},
        {"id": "n3a", "label": "激光雷达", "parent_id": "n3", "children": []},
        {"id": "n3b", "label": "里程计", "parent_id": "n3", "children": []},
        {"id": "n3c", "label": "IMU", "parent_id": "n3", "children": []},
        {"id": "n4", "label": "地图表示", "parent_id": "root", "children": ["n4a", "n4b", "n4c"]},
        {"id": "n4a", "label": "栅格地图", "parent_id": "n4", "children": []},
        {"id": "n4b", "label": "特征地图", "parent_id": "n4", "children": []},
        {"id": "n4c", "label": "拓扑地图", "parent_id": "n4", "children": []},
        {"id": "n5", "label": "实践操作", "parent_id": "root", "children": ["n5a", "n5b", "n5c"]},
        {"id": "n5a", "label": "ROS Navigation Stack", "parent_id": "n5", "children": []},
        {"id": "n5b", "label": "gmapping 配置", "parent_id": "n5", "children": []},
        {"id": "n5c", "label": "导航参数调优", "parent_id": "n5", "children": []},
        {"id": "n6", "label": "常见问题（薄弱环节）", "parent_id": "root", "children": ["n6a", "n6b", "n6c"]},
        {"id": "n6a", "label": "粒子发散", "parent_id": "n6", "children": []},
        {"id": "n6b", "label": "回环检测失败", "parent_id": "n6", "children": []},
        {"id": "n6c", "label": "计算资源不足", "parent_id": "n6", "children": []}
    ]
}
```"""


# ═══════════════════════════════════════════════════════════════
# 测试 1：正常思维导图生成
# ═══════════════════════════════════════════════════════════════

def test_basic_mindmap_generation():
    """正常输入应生成结构完整的思维导图（含 Mermaid 代码）。"""
    print("=" * 60)
    print("测试 1：正常思维导图生成")
    print("=" * 60)

    client = MockLLMClient(content=_make_mindmap_response())
    agent = MindMapAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)

    assert result.success, f"生成应该成功: {result.error}"

    resource = result.resource
    assert resource is not None
    assert resource.metadata.resource_type == ResourceType.MINDMAP
    assert resource.metadata.knowledge_point_id == kp.id
    assert resource.generated_by == "MindMapAgent"

    # 验证内容
    content = resource.content
    assert content.root_topic == "SLAM 地图构建与导航"
    assert len(content.mermaid_code) > 0, "应有 Mermaid 代码"
    assert "mindmap" in content.mermaid_code.lower(), "Mermaid 应以 mindmap 开头"
    assert len(content.nodes) >= 4, f"节点数不应过少: {len(content.nodes)}"

    # 验证节点结构
    for node in content.nodes:
        assert "id" in node, f"节点缺少 id: {node}"
        assert "label" in node, f"节点缺少 label: {node}"
        assert "parent_id" in node, f"节点缺少 parent_id: {node}"
        assert "children" in node, f"节点缺少 children: {node}"

    # 验证根节点
    root_nodes = [n for n in content.nodes if n["parent_id"] is None]
    assert len(root_nodes) == 1, f"应有且仅有一个根节点: {len(root_nodes)}"

    print(f"  根主题: {content.root_topic}")
    print(f"  节点数: {len(content.nodes)}")
    print(f"  Mermaid 代码行数: {len(content.mermaid_code.split(chr(10)))}")
    print(f"  主分支数: {len(root_nodes[0]['children'])}")
    print("[PASS] 正常思维导图生成通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：LLM 调用失败
# ═══════════════════════════════════════════════════════════════

def test_llm_failure():
    """LLM 调用失败时应返回 success=False。"""
    print("=" * 60)
    print("测试 2：LLM 调用失败")
    print("=" * 60)

    client = MockLLMClient(success=False, error="Connection timeout")
    agent = MindMapAgent(client=client)
    kp = _make_kp()

    result = agent.generate(kp)

    assert result.success is False
    assert "timeout" in (result.error or "").lower()

    print(f"  错误信息: {result.error}")
    print("[PASS] LLM 失败处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 3：空知识点名称
# ═══════════════════════════════════════════════════════════════

def test_empty_knowledge_point():
    """知识点名称为空时应返回失败。"""
    print("=" * 60)
    print("测试 3：空知识点名称")
    print("=" * 60)

    agent = MindMapAgent(client=MockLLMClient())
    empty_kp = KnowledgePoint(
        id="test", name="", description="",
        category="", prerequisites=[], difficulty=1,
    )

    result = agent.generate(empty_kp)

    assert result.success is False
    assert "名称为空" in (result.error or "")

    print(f"  错误信息: {result.error}")
    print("[PASS] 空知识点正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 4：空 nodes 检测
# ═══════════════════════════════════════════════════════════════

def test_empty_nodes():
    """LLM 返回空 nodes 时应失败。"""
    print("=" * 60)
    print("测试 4：空 nodes 检测")
    print("=" * 60)

    mock_response = """```json
{"root_topic": "测试", "mermaid_code": "", "nodes": []}
```"""
    client = MockLLMClient(content=mock_response)
    agent = MindMapAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success is False
    assert "nodes 为空" in (result.error or "").lower() or "未生成" in (result.error or "")

    print(f"  错误信息: {result.error}")
    print("[PASS] 空 nodes 正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 5：JSON 解析失败
# ═══════════════════════════════════════════════════════════════

def test_json_parse_failure():
    """LLM 返回非 JSON 内容时应失败。"""
    print("=" * 60)
    print("测试 5：JSON 解析失败")
    print("=" * 60)

    client = MockLLMClient(content="这不是 JSON 格式的回复")
    agent = MindMapAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success is False
    assert "JSON" in (result.error or "").upper()

    print(f"  错误信息: {result.error}")
    print("[PASS] JSON 解析失败正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 6：Mermaid 代码缺失警告
# ═══════════════════════════════════════════════════════════════

def test_mermaid_missing_warning():
    """Mermaid 代码为空时应产生警告但依然成功。"""
    print("=" * 60)
    print("测试 6：Mermaid 代码缺失警告")
    print("=" * 60)

    mock_response = """```json
{
    "root_topic": "测试知识点",
    "mermaid_code": "",
    "nodes": [
        {"id": "root", "label": "测试知识点", "parent_id": null, "children": ["n1"]},
        {"id": "n1", "label": "主分支", "parent_id": "root", "children": []}
    ]
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = MindMapAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success, f"应成功（节点有效）: {result.error}"
    assert len(result.warnings) >= 1
    assert any("mermaid" in w.lower() for w in result.warnings), \
        f"应有 Mermaid 代码缺失警告: {result.warnings}"

    print(f"  警告: {result.warnings}")
    print("[PASS] Mermaid 缺失警告正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：节点数过少警告
# ═══════════════════════════════════════════════════════════════

def test_few_nodes_warning():
    """节点数不足时应产生警告。"""
    print("=" * 60)
    print("测试 7：节点数过少警告")
    print("=" * 60)

    mock_response = """```json
{
    "root_topic": "简单知识点",
    "mermaid_code": "mindmap\\n  root((简单知识点))\\n    概念",
    "nodes": [
        {"id": "root", "label": "简单知识点", "parent_id": null, "children": ["n1"]},
        {"id": "n1", "label": "概念", "parent_id": "root", "children": []}
    ]
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = MindMapAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success, f"应成功但带警告: {result.error}"
    assert len(result.warnings) >= 1
    assert any("节点" in w or "简略" in w for w in result.warnings), \
        f"应有节点数过少警告: {result.warnings}"

    print(f"  节点数: {len(result.resource.content.nodes)}")
    print(f"  警告: {result.warnings}")
    print("[PASS] 节点数过少警告正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 8：无学生画像的通用生成
# ═══════════════════════════════════════════════════════════════

def test_generation_without_profile():
    """不提供学生画像时应使用通用风格。"""
    print("=" * 60)
    print("测试 8：无画像的通用生成")
    print("=" * 60)

    client = MockLLMClient(content=_make_mindmap_response())
    agent = MindMapAgent(client=client)
    kp = _make_kp()

    result = agent.generate(kp)  # 不传 profile

    assert result.success, f"应该成功: {result.error}"
    assert result.resource is not None
    assert result.resource.metadata.student_profile_snapshot == ""

    print(f"  生成成功（无画像模式）")
    print("[PASS] 无画像通用生成正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 9：System Prompt 包含知识点和学生画像
# ═══════════════════════════════════════════════════════════════

def test_system_prompt_contains_context():
    """System Prompt 应包含知识点信息和学生画像。"""
    print("=" * 60)
    print("测试 9：System Prompt 包含上下文")
    print("=" * 60)

    client = MockLLMClient(content=_make_mindmap_response())
    agent = MindMapAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)

    assert result.success
    last_kwargs = client.last_call_kwargs
    assert last_kwargs is not None

    system_prompt = last_kwargs.get("system_prompt", "")

    # 检查知识点信息
    assert kp.name in system_prompt
    assert kp.category in system_prompt
    assert str(kp.difficulty) in system_prompt

    # 检查学生画像
    assert "机器人工程" in system_prompt
    assert "自动驾驶" in system_prompt
    assert "SLAM" in system_prompt  # 薄弱环节

    print(f"  System Prompt 长度: {len(system_prompt)} 字符")
    print(f"  包含知识点信息: [OK]")
    print(f"  包含学生画像: [OK]")
    print("[PASS] System Prompt 构建正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 10：ResourceOutput 结构完整性
# ═══════════════════════════════════════════════════════════════

def test_resource_output_structure():
    """验证生成的 ResourceOutput 符合 schema 定义。"""
    print("=" * 60)
    print("测试 10：ResourceOutput 结构完整性")
    print("=" * 60)

    client = MockLLMClient(content=_make_mindmap_response())
    agent = MindMapAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)
    assert result.success

    resource = result.resource

    # 验证 metadata
    assert resource.metadata.resource_type == ResourceType.MINDMAP
    assert resource.metadata.knowledge_point_id == kp.id
    assert resource.metadata.title != ""
    assert 1 <= resource.metadata.difficulty <= 5
    assert resource.metadata.estimated_read_time_minutes > 0

    # 验证 status 和 generated_by
    assert resource.status == "generated"
    assert resource.generated_by == "MindMapAgent"

    # 验证 content 类型
    from ..models import MindMapContent
    assert isinstance(resource.content, MindMapContent), \
        f"content 应为 MindMapContent 类型: {type(resource.content)}"

    # 验证 content 字段
    assert len(resource.content.root_topic) > 0
    assert isinstance(resource.content.mermaid_code, str)
    assert len(resource.content.nodes) > 0

    # 验证 Mermaid 代码以 mindmap 开头
    assert "mindmap" in resource.content.mermaid_code.lower(), \
        "Mermaid 代码应以 mindmap 开头"

    # 验证可序列化
    try:
        json_str = resource.model_dump_json(indent=2)
        assert len(json_str) > 0
        print(f"  JSON 序列化: OK, {len(json_str)} 字符")
    except Exception as e:
        assert False, f"序列化失败: {e}"

    print(f"  资源类型: {resource.metadata.resource_type.value}")
    print(f"  根主题: {resource.content.root_topic}")
    print(f"  节点数: {len(resource.content.nodes)}")
    print(f"  状态: {resource.status}")
    print("[PASS] ResourceOutput 结构完整\n")


# ═══════════════════════════════════════════════════════════════
# 测试 11：作为薄弱知识点的个性化
# ═══════════════════════════════════════════════════════════════

def test_weak_point_personalization():
    """当前知识点是薄弱环节时 user_message 应体现。"""
    print("=" * 60)
    print("测试 11：薄弱知识点个性化")
    print("=" * 60)

    client = MockLLMClient(content=_make_mindmap_response())
    agent = MindMapAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()  # SLAM 在 weak_points 中

    result = agent.generate(kp, profile)

    assert result.success
    last_kwargs = client.last_call_kwargs
    user_message = last_kwargs.get("user_message", "")

    assert "薄弱" in user_message or "常见错误" in user_message or "避坑" in user_message, \
        f"薄弱知识点的提示应体现: '{user_message[:200]}'"

    print(f"  User Message 包含薄弱提示: [OK]")
    print("[PASS] 薄弱知识点个性化正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 12：部分节点 label 为空
# ═══════════════════════════════════════════════════════════════

def test_nodes_with_empty_label():
    """部分节点 label 为空时应跳过，保留有效节点。"""
    print("=" * 60)
    print("测试 12：部分节点 label 为空")
    print("=" * 60)

    mock_response = """```json
{
    "root_topic": "测试",
    "mermaid_code": "mindmap\\n  root((测试))",
    "nodes": [
        {"id": "root", "label": "有效节点", "parent_id": null, "children": []},
        {"id": "n1", "label": "", "parent_id": "root", "children": []},
        {"id": "n2", "label": "另一有效节点", "parent_id": "root", "children": []}
    ]
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = MindMapAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success, f"应成功: {result.error}"
    content = result.resource.content
    assert len(content.nodes) == 2, f"应保留 2 个有效节点: {len(content.nodes)}"

    labels = [n["label"] for n in content.nodes]
    assert "" not in labels, "不应有空 label 节点"

    print(f"  有效节点数: {len(content.nodes)} (过滤掉空 label)")
    print(f"  节点标签: {labels}")
    print("[PASS] 空 label 过滤正确\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    """运行所有测试并统计结果。"""
    print("=" * 60)
    print("  MindMap Agent (mindmap_agent.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_basic_mindmap_generation,
        test_llm_failure,
        test_empty_knowledge_point,
        test_empty_nodes,
        test_json_parse_failure,
        test_mermaid_missing_warning,
        test_few_nodes_warning,
        test_generation_without_profile,
        test_system_prompt_contains_context,
        test_resource_output_structure,
        test_weak_point_personalization,
        test_nodes_with_empty_label,
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
        print("  全部通过！MindMap Agent 可以放心使用。")
    else:
        print(f"  {failed} 个测试失败，请检查。")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
