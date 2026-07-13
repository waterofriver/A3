# -*- coding: utf-8 -*-
"""
Profile Agent 测试 —— 验证画像提取、增量更新、JSON 解析、边界处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.profile_agent.test_profile_agent

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
from copy import deepcopy

from .profile_agent import ProfileAgent, ProfileExtractionResult
from ..utils import LLMResponse
from ..models import (
    StudentProfile,
    KnowledgeBaseItem,
    WeakPoint,
    MasteryLevel,
    CognitiveStyle,
    LearningPace,
)


# ═══════════════════════════════════════════════════════════════
# Mock LLM 客户端
# ═══════════════════════════════════════════════════════════════

class MockLLMClient:
    """可注入的 Mock LLM 客户端，用于隔离测试 ProfileAgent 逻辑。"""

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
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _make_profile(**overrides):
    """快速构造 StudentProfile 用于测试。"""
    defaults = dict(
        major="",
        grade="",
        knowledge_base=[],
        cognitive_style=CognitiveStyle.BALANCED,
        learning_goal_short="",
        learning_goal_long="",
        weak_points=[],
        learning_pace=LearningPace.FLEXIBLE,
        interest_domains=[],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_kb_item(kp_id, name, mastery=MasteryLevel.FAMILIAR):
    """快速构造 KnowledgeBaseItem。"""
    return KnowledgeBaseItem(
        knowledge_point_id=kp_id,
        knowledge_point_name=name,
        mastery=mastery,
    )


def _make_weak_point(kp_id, name, pattern, count=1):
    """快速构造 WeakPoint。"""
    return WeakPoint(
        knowledge_point_id=kp_id,
        knowledge_point_name=name,
        error_pattern=pattern,
        occurrence_count=count,
    )


# ═══════════════════════════════════════════════════════════════
# 测试 1：ProfileExtractionResult 数据类
# ═══════════════════════════════════════════════════════════════

def test_extraction_result_dataclass():
    """验证 ProfileExtractionResult 数据类各字段的默认值和赋值。"""
    print("=" * 60)
    print("测试 1：ProfileExtractionResult 数据类")
    print("=" * 60)

    # 默认值
    r = ProfileExtractionResult()
    assert r.profile is None
    assert r.follow_up_question == ""
    assert r.is_complete is False
    assert r.rationale == ""
    assert r.success is True
    assert r.error is None
    assert r.reasoning_content is None

    # 成功场景
    profile = _make_profile(major="计算机科学")
    r = ProfileExtractionResult(
        profile=profile,
        follow_up_question="还有什么要补充的吗？",
        is_complete=True,
        rationale="采集了基础信息",
        reasoning_content="推理链内容",
    )
    assert r.profile is profile
    assert r.follow_up_question == "还有什么要补充的吗？"
    assert r.is_complete is True

    # 失败场景
    r = ProfileExtractionResult(
        success=False,
        error="API 超时",
        rationale="调用失败",
    )
    assert r.success is False
    assert r.error == "API 超时"

    print("  [OK] 成功/失败状态均正确")
    print("[PASS] 数据类字段验证通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：完整文本提取
# ═══════════════════════════════════════════════════════════════

def test_basic_extraction():
    """验证从完整中文文本中提取 6 维度信息。"""
    print("=" * 60)
    print("测试 2：完整文本提取")
    print("=" * 60)

    mock_response = """```json
{
    "extracted_fields": {
        "major": "计算机科学与技术",
        "grade": "大二",
        "knowledge_base": [
            {"knowledge_point_id": "python", "knowledge_point_name": "Python", "mastery": "proficient"},
            {"knowledge_point_id": "cpp", "knowledge_point_name": "C++", "mastery": "familiar"}
        ],
        "cognitive_style": "practice_oriented",
        "learning_goal_short": "通过数据结构和算法考试",
        "learning_goal_long": "",
        "weak_points": [
            {"knowledge_point_id": "recursion", "knowledge_point_name": "递归",
             "error_pattern": "递归终止条件错误", "occurrence_count": 5}
        ],
        "learning_pace": "distributed",
        "interest_domains": ["游戏开发", "Web 开发"]
    },
    "follow_up_question": "你的长期目标是什么？",
    "is_complete": false,
    "rationale": "已提取基础信息和知识背景，薄弱环节和学习目标还需细化。"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("我是计算机大二学生，Python 很熟，C++ 也不错，喜欢做游戏")

    assert result.success, f"提取应该成功: {result.error}"
    assert result.profile is not None
    assert result.profile.major == "计算机科学与技术"
    assert result.profile.grade == "大二"
    assert len(result.profile.knowledge_base) == 2
    assert result.profile.cognitive_style == CognitiveStyle.PRACTICE_ORIENTED
    assert "游戏开发" in result.profile.interest_domains
    assert len(result.profile.weak_points) == 1
    assert result.profile.weak_points[0].occurrence_count == 5
    assert result.is_complete is False
    assert result.follow_up_question != ""

    print(f"  专业: {result.profile.major} | 年级: {result.profile.grade}")
    print(f"  知识基础: {len(result.profile.knowledge_base)} 个 | 认知风格: {result.profile.cognitive_style}")
    print(f"  弱项: {len(result.profile.weak_points)} 个 | 兴趣: {result.profile.interest_domains}")
    print("[PASS] 完整文本提取通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 3：增量更新 - 保留旧字段
# ═══════════════════════════════════════════════════════════════

def test_incremental_update_preserves():
    """增量更新时，extracted 中没出现但 existing 中有的字段应保留。"""
    print("=" * 60)
    print("测试 3：增量更新 - 保留旧字段")
    print("=" * 60)

    existing = _make_profile(
        major="软件工程",
        grade="大三",
        knowledge_base=[_make_kb_item("java", "Java", MasteryLevel.PROFICIENT)],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_long="成为架构师",
    )

    # 第二轮：只更新了年级和弱项
    mock_response = """```json
{
    "extracted_fields": {
        "major": "软件工程",
        "grade": "大四",
        "weak_points": [
            {"knowledge_point_id": "design_patterns", "knowledge_point_name": "设计模式",
             "error_pattern": "无法选择合适模式", "occurrence_count": 2}
        ],
        "learning_goal_short": "准备毕业设计"
    },
    "follow_up_question": "你的知识基础有哪些？",
    "is_complete": false,
    "rationale": "更新了年级和学习目标"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("我现在大四了", existing_profile=existing)

    assert result.success, f"提取应该成功: {result.error}"
    p = result.profile
    assert p is not None

    # 旧值保留
    assert p.major == "软件工程", f"major 应该保留: {p.major}"
    assert p.cognitive_style == CognitiveStyle.PRACTICE_ORIENTED
    assert p.learning_goal_long == "成为架构师"

    # 新值生效
    assert p.grade == "大四"
    assert len(p.knowledge_base) == 1  # 仅 java（design_patterns 是弱项不是知识基础）
    assert len(p.weak_points) == 1

    print(f"  major 保留: {p.major} | grade 更新: {p.grade}")
    print(f"  知识基础合并后: {len(p.knowledge_base)} 个")
    print(f"  长期目标保留: {p.learning_goal_long}")
    print("[PASS] 增量更新保留测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 4：增量更新 - 覆盖旧值
# ═══════════════════════════════════════════════════════════════

def test_incremental_update_overwrites():
    """extracted 中有新值时，应覆盖 existing 中的同名标量字段。"""
    print("=" * 60)
    print("测试 4：增量更新 - 覆盖旧值")
    print("=" * 60)

    existing = _make_profile(
        major="计算机科学",
        grade="大二",
        cognitive_style=CognitiveStyle.BALANCED,
        learning_goal_short="考过四级",
    )

    # 第三轮：更新了专业和认知风格
    mock_response = """```json
{
    "extracted_fields": {
        "major": "人工智能",
        "cognitive_style": "theory_oriented",
        "learning_goal_long": "从事 AI 研究"
    },
    "follow_up_question": "你在哪些方向有薄弱？",
    "is_complete": false,
    "rationale": "修正了专业方向，明确了认知偏好"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("我其实想转 AI 方向", existing_profile=existing)

    assert result.success
    p = result.profile
    assert p.major == "人工智能", f"major 应该被覆盖: {p.major}"
    assert p.cognitive_style == CognitiveStyle.THEORY_ORIENTED, f"cognitive_style 应该被覆盖: {p.cognitive_style}"
    assert p.learning_goal_short == "考过四级"  # 旧值保留

    print(f"  major: 计算机科学 → 人工智能")
    print(f"  cognitive_style: balanced → theory_oriented")
    print("[PASS] 增量更新覆盖测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 5：occurrence_count 累加
# ═══════════════════════════════════════════════════════════════

def test_weak_point_accumulation():
    """同一个知识点的 weak_point，occurrence_count 应累加。"""
    print("=" * 60)
    print("测试 5：弱项 occurrence_count 累加")
    print("=" * 60)

    existing = _make_profile(
        weak_points=[
            _make_weak_point("recursion", "递归", "栈溢出", count=3),
        ],
    )

    # 第二轮又提到递归的错误
    mock_response = """```json
{
    "extracted_fields": {
        "weak_points": [
            {"knowledge_point_id": "recursion", "knowledge_point_name": "递归",
             "error_pattern": "递归深度控制不当", "occurrence_count": 2}
        ]
    },
    "follow_up_question": "还有什么困难？",
    "is_complete": false,
    "rationale": "补充了递归弱项信息"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("递归又出错了", existing_profile=existing)

    assert result.success
    p = result.profile
    wp = p.weak_points[0]
    assert wp.occurrence_count == 5, f"occurrence_count 应该是 3+2=5: {wp.occurrence_count}"
    assert wp.error_pattern == "递归深度控制不当"  # 用最新错误模式

    print(f"  occurrence_count: 3 + 2 = {wp.occurrence_count}")
    print(f"  error_pattern 已更新: {wp.error_pattern}")
    print("[PASS] 弱项累加测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 6：畸形 JSON 恢复（末尾逗号）
# ═══════════════════════════════════════════════════════════════

def test_malformed_json_recovery():
    """带末尾逗号的畸形 JSON 应通过 json_parser 恢复。"""
    print("=" * 60)
    print("测试 6：畸形 JSON 恢复（末尾逗号）")
    print("=" * 60)

    # JSON 末尾有逗号
    mock_response = """```json
{
    "extracted_fields": {
        "major": "信息安全",
        "grade": "大四",
    },
    "follow_up_question": "你的学习目标是什么？",
    "is_complete": false,
    "rationale": "已提取基础信息，",
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("信息安全大四")

    assert result.success, f"应该成功恢复: {result.error}"
    assert result.profile.major == "信息安全"
    assert result.profile.grade == "大四"

    print(f"  专业: {result.profile.major} | 目标: {result.profile.grade}")
    print("[PASS] 畸形 JSON 恢复测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：code fence 包裹的 JSON
# ═══════════════════════════════════════════════════════════════

def test_json_in_code_block():
    """```json``` 包裹的 JSON 应正确提取。"""
    print("=" * 60)
    print("测试 7：code fence 包裹的 JSON")
    print("=" * 60)

    mock_response = """好的，我来提取你的画像信息：

```json
{
    "extracted_fields": {
        "major": "数学",
        "grade": "大一",
        "cognitive_style": "theory_oriented"
    },
    "follow_up_question": "你有编程基础吗？",
    "is_complete": false,
    "rationale": "提取了基本信息"
}
```

以上是根据你的回答构建的画像。"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("我是数学大一新生")

    assert result.success, f"应该提取成功: {result.error}"
    assert result.profile.major == "数学"
    assert result.profile.grade == "大一"

    print(f"  专业: {result.profile.major} | 年级: {result.profile.grade}")
    print("[PASS] code fence JSON 测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 8：含无关文字的 JSON 提取
# ═══════════════════════════════════════════════════════════════

def test_json_with_stray_text():
    """JSON 前后有解释文字的应正确提取。"""
    print("=" * 60)
    print("测试 8：含无关文字的 JSON 提取")
    print("=" * 60)

    mock_response = """根据你的介绍，我构建了以下画像：

{
    "extracted_fields": {
        "major": "电子工程",
        "interest_domains": ["嵌入式系统"]
    },
    "follow_up_question": "你常用哪些开发工具？",
    "is_complete": false,
    "rationale": "提取了专业和兴趣方向"
}

如果还有其他信息，请告诉我。"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("电子工程专业，对嵌入式感兴趣")

    assert result.success, f"应该成功: {result.error}"
    assert result.profile.major == "电子工程"
    assert "嵌入式系统" in result.profile.interest_domains

    print(f"  专业: {result.profile.major} | 兴趣: {result.profile.interest_domains}")
    print("[PASS] 含无关文字的 JSON 测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 9：LLM 调用失败处理
# ═══════════════════════════════════════════════════════════════

def test_llm_failure():
    """LLM 调用失败时，应返回 ProfileExtractionResult 的失败状态。"""
    print("=" * 60)
    print("测试 9：LLM 调用失败处理")
    print("=" * 60)

    client = MockLLMClient(success=False, error="Connection timeout")
    agent = ProfileAgent(client=client)

    result = agent.extract("什么内容都行")

    assert result.success is False
    assert result.error is not None
    assert result.profile is None
    assert "timeout" in result.error.lower() or "失败" in result.rationale

    print(f"  错误信息: {result.error}")
    print("[PASS] LLM 失败处理测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 10：完成度检测
# ═══════════════════════════════════════════════════════════════

def test_completeness_detection():
    """is_complete 标志应正确传递。"""
    print("=" * 60)
    print("测试 10：完成度检测")
    print("=" * 60)

    mock_response = """```json
{
    "extracted_fields": {
        "major": "计算机科学",
        "grade": "大三",
        "knowledge_base": [
            {"knowledge_point_id": "python", "knowledge_point_name": "Python", "mastery": "proficient"}
        ],
        "cognitive_style": "practice_oriented",
        "learning_goal_short": "考试",
        "learning_goal_long": "工程师",
        "weak_points": [
            {"knowledge_point_id": "algo", "knowledge_point_name": "算法", "error_pattern": "DP", "occurrence_count": 2}
        ],
        "learning_pace": "distributed",
        "interest_domains": ["Web"]
    },
    "follow_up_question": "",
    "is_complete": true,
    "rationale": "全部6个维度已采集"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("完整信息")

    assert result.success
    assert result.is_complete is True
    assert result.follow_up_question == ""

    print(f"  is_complete: {result.is_complete}")
    print(f"  follow_up_question: '{result.follow_up_question}'")
    print("[PASS] 完成度检测测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 11：完成度覆盖（维度不足）
# ═══════════════════════════════════════════════════════════════

def test_completeness_override():
    """LLM 误判完成但维度不足时，Agent 应覆盖为 false。"""
    print("=" * 60)
    print("测试 11：完成度覆盖（维度不足）")
    print("=" * 60)

    # LLM 说完成了但只提供了 1 个维度
    mock_response = """```json
{
    "extracted_fields": {
        "major": "测试专业"
    },
    "follow_up_question": "",
    "is_complete": true,
    "rationale": "完成了"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("测试")

    assert result.success
    assert result.is_complete is False, f"应该被覆盖为 false: {result.is_complete}"

    print(f"  LLM 判定: true → Agent 覆盖: {result.is_complete}")
    print("[PASS] 完成度覆盖测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 12：空输入边界处理
# ═══════════════════════════════════════════════════════════════

def test_empty_user_text():
    """空输入应返回失败结果而不是崩溃。"""
    print("=" * 60)
    print("测试 12：空输入边界处理")
    print("=" * 60)

    agent = ProfileAgent(client=MockLLMClient())

    # 空字符串
    result = agent.extract("")
    assert result.success is False
    assert "空" in result.error or "空" in result.rationale

    # 纯空格
    result = agent.extract("   ")
    assert result.success is False

    print(f"  空字符串处理: {result.rationale}")
    print("[PASS] 空输入边界测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 13：空已有画像的增量更新
# ═══════════════════════════════════════════════════════════════

def test_empty_existing_profile():
    """从空画像开始的增量更新应正常工作（等同于首次提取）。"""
    print("=" * 60)
    print("测试 13：空已有画像的增量更新")
    print("=" * 60)

    mock_response = """```json
{
    "extracted_fields": {
        "major": "计算机科学与技术",
        "knowledge_base": [
            {"knowledge_point_id": "python", "knowledge_point_name": "Python", "mastery": "proficient"},
            {"knowledge_point_id": "cpp", "knowledge_point_name": "C++", "mastery": "familiar"}
        ]
    },
    "follow_up_question": "你的年级是什么？",
    "is_complete": false,
    "rationale": "提取了专业和知识基础"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    empty_profile = StudentProfile()
    result = agent.extract("计算机专业，会 Python 和 C++", existing_profile=empty_profile)

    assert result.success
    assert result.profile.major == "计算机科学与技术"
    assert len(result.profile.knowledge_base) == 2

    print(f"  从空画像构建: major={result.profile.major}, kb={len(result.profile.knowledge_base)}个")
    print("[PASS] 空已有画像增量更新测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 14：已有画像的 snapshot 注入 System Prompt
# ═══════════════════════════════════════════════════════════════

def test_snapshot_injection():
    """当存在已有画像时，snapshot 应该被注入到 System Prompt。"""
    print("=" * 60)
    print("测试 14：Snapshot 注入 System Prompt")
    print("=" * 60)

    existing = _make_profile(
        major="网络安全",
        knowledge_base=[_make_kb_item("cissp", "CISSP", MasteryLevel.PROFICIENT)],
        interest_domains=["渗透测试"],
    )

    # 不设置 content（让 LLM 调用在这里无关紧要，但为了测试不崩给一个最小响应）
    mock_response = """```json
{
    "extracted_fields": {},
    "follow_up_question": "继续",
    "is_complete": false,
    "rationale": "测试"
}
```"""

    client = MockLLMClient(content=mock_response)
    agent = ProfileAgent(client=client)

    result = agent.extract("继续学习", existing_profile=existing)

    assert result.success, f"提取应该成功: {result.error}"

    # 关键：验证调用 LLM 时 System Prompt 包含 snapshot
    last_kwargs = client.last_call_kwargs
    assert last_kwargs is not None, "应该调用了 LLM"

    system_prompt = last_kwargs.get("system_prompt", "")
    assert "网络安全" in system_prompt, f"System Prompt 应包含网络安全: {system_prompt[:200]}"
    assert "CISSP" in system_prompt
    assert "渗透测试" in system_prompt

    # 同时检查 user_message 也包含已有画像
    user_message = last_kwargs.get("user_message", "")
    assert "已有画像" in user_message or "existing" in user_message.lower()
    assert "网络安全" in user_message

    print(f"  System Prompt 长度: {len(system_prompt)} 字符")
    print(f"  包含 snapshot: 网络安全 [OK] | CISSP [OK] | 渗透测试 [OK]")
    print("[PASS] Snapshot 注入测试通过\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    """运行所有测试并统计结果。"""
    print("=" * 60)
    print("  Profile Agent (profile_agent.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_extraction_result_dataclass,
        test_basic_extraction,
        test_incremental_update_preserves,
        test_incremental_update_overwrites,
        test_weak_point_accumulation,
        test_malformed_json_recovery,
        test_json_in_code_block,
        test_json_with_stray_text,
        test_llm_failure,
        test_completeness_detection,
        test_completeness_override,
        test_empty_user_text,
        test_empty_existing_profile,
        test_snapshot_injection,
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
            print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}\n")

    print("=" * 60)
    print(f"  结果: {passed}/{len(tests)} 通过")
    if failed == 0:
        print("  全部通过！Profile Agent 可以放心使用。")
    else:
        print(f"  {failed} 个测试失败，请检查。")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
