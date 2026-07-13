# -*- coding: utf-8 -*-
"""
Quiz Agent 测试 —— 验证题目生成、题型分布、个性化、课件驱动和边界处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.quiz_agent.test_quiz_agent

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .quiz_agent import QuizAgent, QuizResult
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
    QuestionType,
)


class MockLLMClient:
    def __init__(self, content="", success=True, error=None):
        self.content = content
        self.success = success
        self.error = error
        self.last_call_kwargs = None

    def chat(self, **kwargs):
        self.last_call_kwargs = kwargs
        return LLMResponse(
            content=self.content, success=self.success,
            error=self.error, model="mock-model",
        )


def _make_kp():
    return KnowledgePoint(
        id="exp05_arp_poisoning",
        name="ARP 中毒攻击",
        description="认识链路层欺骗和中间人攻击的基础手法。",
        category="网络攻防",
        prerequisites=["network_environment_setup"],
        difficulty=3,
        estimated_minutes=60,
        tags=["ARP", "中间人", "网络攻击"],
    )


def _make_profile(**overrides):
    defaults = dict(
        major="机器人工程", grade="大三",
        knowledge_base=[
            KnowledgeBaseItem(knowledge_point_id="network_basics", knowledge_point_name="网络基础", mastery=MasteryLevel.PROFICIENT),
        ],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="掌握网络攻防实验技能",
        weak_points=[
            WeakPoint(knowledge_point_id="exp05_arp_poisoning", knowledge_point_name="ARP 中毒攻击", error_pattern="ARP 协议报文结构不熟", occurrence_count=2),
        ],
        learning_pace=LearningPace.DISTRIBUTED,
        interest_domains=["网络安全", "渗透测试"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_quiz_response():
    """构造标准题库 LLM 返回 JSON（8 道题，4 种题型混合）。"""
    data = {
        "items": [
            {
                "question_type": "single_choice",
                "stem": "ARP 协议的主要功能是什么？",
                "options": ["A. 将域名解析为IP地址", "B. 将IP地址解析为MAC地址", "C. 将MAC地址解析为端口号", "D. 将数据包路由到目标网络"],
                "correct_answer": "B",
                "explanation": "ARP（Address Resolution Protocol）的核心功能是将IP地址解析为MAC地址。A是DNS的功能，C是端口映射，D是路由器的功能。在局域网通信中，数据帧必须知道目标MAC地址才能发送。",
                "difficulty": 1,
                "knowledge_point_tags": ["ARP", "网络协议"],
            },
            {
                "question_type": "single_choice",
                "stem": "在 ARP 中毒攻击中，攻击者通常伪装成什么角色？",
                "options": ["A. DNS服务器", "B. DHCP服务器", "C. 网关", "D. 目标主机本身"],
                "correct_answer": "C",
                "explanation": "ARP中毒攻击中，攻击者通常伪装成网关。通过发送伪造的ARP应答，将网关IP绑定到攻击者的MAC地址，从而截获目标主机与网关之间的所有通信流量。",
                "difficulty": 2,
                "knowledge_point_tags": ["ARP中毒", "中间人"],
            },
            {
                "question_type": "single_choice",
                "stem": "使用 arpspoof 工具时，参数 -t 的作用是什么？",
                "options": ["A. 指定攻击持续时间", "B. 指定目标IP地址", "C. 指定使用的网络接口", "D. 指定伪造的MAC地址"],
                "correct_answer": "B",
                "explanation": "arpspoof 的 -t 参数用于指定目标IP地址（target），即要欺骗的主机。基本用法为: arpspoof -i eth0 -t 目标IP 伪装IP。",
                "difficulty": 2,
                "knowledge_point_tags": ["arpspoof", "工具使用"],
            },
            {
                "question_type": "multiple_choice",
                "stem": "以下哪些是 ARP 中毒攻击的常见防御措施？（多选）",
                "options": ["A. 静态ARP绑定", "B. 启用交换机DAI功能", "C. 使用更强的加密算法", "D. 部署ARP检测工具"],
                "correct_answer": "ABD",
                "explanation": "静态ARP绑定(A)、交换机DAI(Dynamic ARP Inspection)(B)和ARP检测工具如arpwatch(D)都是有效的防御措施。加密算法(C)对ARP层攻击无效，因为ARP工作在数据链路层。",
                "difficulty": 3,
                "knowledge_point_tags": ["ARP防御", "安全"],
            },
            {
                "question_type": "multiple_choice",
                "stem": "执行 ARP 欺骗攻击前必须完成的准备步骤有哪些？（多选）",
                "options": ["A. 开启IP转发", "B. 安装Scapy或dsniff工具", "C. 关闭目标主机防火墙", "D. 确认攻击机与目标机在同一局域网"],
                "correct_answer": "ABD",
                "explanation": "IP转发(A)必须开启否则目标断网；Scapy/dsniff(B)是攻击工具；同局域网(D)是ARP攻击的前提。关闭目标防火墙(C)不是必要步骤且可能引起警觉。",
                "difficulty": 3,
                "knowledge_point_tags": ["攻击准备", "实验"],
            },
            {
                "question_type": "true_false",
                "stem": "ARP 请求报文是广播发送的，而 ARP 应答报文是单播发送的。",
                "options": ["正确", "错误"],
                "correct_answer": "正确",
                "explanation": "这是ARP协议的基本工作机制：请求方不知道目标的MAC地址所以必须广播，而应答方知道请求方的MAC地址可以直接单播回复。",
                "difficulty": 1,
                "knowledge_point_tags": ["ARP协议", "基础概念"],
            },
            {
                "question_type": "true_false",
                "stem": "ARP 中毒攻击只需要发送一次伪造的ARP应答包就能永久生效。",
                "options": ["正确", "错误"],
                "correct_answer": "错误",
                "explanation": "ARP缓存表中的条目有老化时间（通常几分钟），过期后主机会重新发送ARP请求。因此ARP欺骗需要持续发送伪造应答包来维持欺骗状态。",
                "difficulty": 2,
                "knowledge_point_tags": ["ARP中毒", "常见误区"],
            },
            {
                "question_type": "short_answer",
                "stem": "请简述 ARP 中毒攻击的基本原理，并说明为什么 ARP 协议容易受到此类攻击。",
                "options": [],
                "correct_answer": "ARP中毒攻击通过发送伪造的ARP应答包，将攻击者的MAC地址与合法IP（通常是网关）绑定，使目标主机的流量经过攻击者。ARP协议容易受攻击的根本原因是它缺乏认证机制——任何主机都可以发送ARP应答，接收方无条件信任并更新缓存表。",
                "explanation": "答题要点应包括：(1)伪造ARP应答 → (2)IP-MAC绑定被篡改 → (3)流量重定向 → (4)ARP缺乏认证。重点在于解释'为什么'——ARP设计于信任网络时代，没有考虑恶意节点。",
                "difficulty": 3,
                "knowledge_point_tags": ["ARP中毒", "安全分析", "原理"],
            },
        ],
        "total_count": 8,
        "suggested_duration_minutes": 20,
    }
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return f"```json\n{json_str}\n```"


# ═══════════════════════════════════════════════════════════════
# 测试 1：正常题库生成
# ═══════════════════════════════════════════════════════════════

def test_basic_quiz_generation():
    """正常输入应生成包含多种题型的完整题库。"""
    print("=" * 60)
    print("测试 1：正常题库生成")
    print("=" * 60)

    client = MockLLMClient(content=_make_quiz_response())
    agent = QuizAgent(client=client)

    result = agent.generate(_make_kp(), _make_profile())

    assert result.success, f"生成应该成功: {result.error}"
    resource = result.resource
    assert resource.metadata.resource_type == ResourceType.QUIZ
    assert resource.generated_by == "QuizAgent"

    content = resource.content
    assert len(content.items) == 8
    assert content.total_count == 8
    assert content.suggested_duration_minutes == 20

    # 题型分布
    types = {}
    for item in content.items:
        types[item.question_type] = types.get(item.question_type, 0) + 1
    assert QuestionType.SINGLE_CHOICE in types
    assert QuestionType.MULTIPLE_CHOICE in types
    assert QuestionType.TRUE_FALSE in types
    assert QuestionType.SHORT_ANSWER in types

    # 每道题关键字段非空
    for item in content.items:
        assert item.stem
        assert item.correct_answer
        assert 1 <= item.difficulty <= 5

    print(f"  题目数: {len(content.items)} | 建议时长: {content.suggested_duration_minutes}min")
    print(f"  题型分布: { {k.value: v for k, v in types.items()} }")
    print("[PASS] 正常题库生成通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：LLM 调用失败 / 空 items / JSON 失败 / 空 KP
# ═══════════════════════════════════════════════════════════════

def test_llm_failure():
    client = MockLLMClient(success=False, error="Timeout")
    r = QuizAgent(client=client).generate(_make_kp())
    assert r.success is False and "Timeout" in (r.error or "")
    print("  测试 2：LLM 失败 [PASS]")

def test_empty_items():
    r = QuizAgent(client=MockLLMClient(content='```json\n{"items":[],"total_count":0,"suggested_duration_minutes":0}\n```')).generate(_make_kp())
    assert r.success is False and "空" in (r.error or "").lower()
    print("  测试 3：空 items [PASS]")

def test_json_failure():
    r = QuizAgent(client=MockLLMClient(content="不是JSON")).generate(_make_kp())
    assert r.success is False and "JSON" in (r.error or "").upper()
    print("  测试 4：JSON 失败 [PASS]")

def test_empty_kp():
    r = QuizAgent(client=MockLLMClient()).generate(KnowledgePoint(id="x", name="", description="", category="", prerequisites=[], difficulty=1))
    assert r.success is False and "空" in (r.error or "")
    print("  测试 5：空知识点 [PASS]")


# ═══════════════════════════════════════════════════════════════
# 测试 6：部分题目无效（题干空、题型错、缺答案）
# ═══════════════════════════════════════════════════════════════

def test_partial_invalid_items():
    """部分题目无效时跳过并警告，保留有效题。"""
    print("=" * 60)
    print("测试 6：部分题目无效")
    print("=" * 60)

    data = {
        "items": [
            {"question_type": "single_choice", "stem": "有效题", "options": ["A. x", "B. y"], "correct_answer": "A", "explanation": "解析", "difficulty": 1, "knowledge_point_tags": []},
            {"question_type": "invalid_type", "stem": "无效题型", "options": [], "correct_answer": "x", "explanation": "", "difficulty": 1, "knowledge_point_tags": []},
            {"question_type": "single_choice", "stem": "", "options": [], "correct_answer": "A", "explanation": "", "difficulty": 1, "knowledge_point_tags": []},
            {"question_type": "multiple_choice", "stem": "另一有效题", "options": ["A. a", "B. b", "C. c"], "correct_answer": "AB", "explanation": "解析2", "difficulty": 2, "knowledge_point_tags": []},
            {"question_type": "single_choice", "stem": "缺答案", "options": ["A. x"], "correct_answer": "", "explanation": "", "difficulty": 1, "knowledge_point_tags": []},
        ],
        "total_count": 5, "suggested_duration_minutes": 10,
    }
    js = json.dumps(data, ensure_ascii=False, indent=2)
    client = MockLLMClient(content=f"```json\n{js}\n```")
    r = QuizAgent(client=client).generate(_make_kp())

    assert r.success, f"应成功: {r.error}"
    assert len(r.resource.content.items) == 2, f"应保留2道有效题: {len(r.resource.content.items)}"
    assert len(r.warnings) >= 3, f"应有 ≥3 个警告: {r.warnings}"

    print(f"  有效题: {len(r.resource.content.items)} | 警告: {len(r.warnings)}")
    print(f"  警告内容: {r.warnings[:3]}")
    print("[PASS] 部分无效题目处理正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：无画像通用生成 / 个性化 / 薄弱点
# ═══════════════════════════════════════════════════════════════

def test_without_profile():
    r = QuizAgent(client=MockLLMClient(content=_make_quiz_response())).generate(_make_kp())
    assert r.success and r.resource.metadata.student_profile_snapshot == ""
    print("  测试 7：无画像 [PASS]")

def test_practice_personalization():
    client = MockLLMClient(content=_make_quiz_response())
    r = QuizAgent(client=client).generate(_make_kp(), _make_profile(cognitive_style=CognitiveStyle.PRACTICE_ORIENTED))
    assert r.success
    msg = client.last_call_kwargs.get("user_message", "")
    assert "实践" in msg or "操作" in msg
    print("  测试 8：实践型个性化 [PASS]")

def test_weak_point_personalization():
    client = MockLLMClient(content=_make_quiz_response())
    r = QuizAgent(client=client).generate(_make_kp(), _make_profile())
    assert r.success
    msg = client.last_call_kwargs.get("user_message", "")
    assert "薄弱" in msg or "基础" in msg
    print("  测试 9：薄弱点个性化 [PASS]")


# ═══════════════════════════════════════════════════════════════
# 测试 10：System Prompt / ResourceOutput 结构 / 题型单一警告
# ═══════════════════════════════════════════════════════════════

def test_system_prompt_contains_context():
    client = MockLLMClient(content=_make_quiz_response())
    r = QuizAgent(client=client).generate(_make_kp(), _make_profile(), material_context="课件: ARP协议详解")
    assert r.success
    sp = client.last_call_kwargs.get("system_prompt", "")
    assert "ARP 中毒攻击" in sp and "课件: ARP协议详解" in sp and "机器人工程" in sp
    print("  测试 10：System Prompt上下文 [PASS]")

def test_resource_structure():
    from ..models import QuizContent
    r = QuizAgent(client=MockLLMClient(content=_make_quiz_response())).generate(_make_kp(), _make_profile())
    assert r.success
    res = r.resource
    assert isinstance(res.content, QuizContent)
    assert res.metadata.resource_type == ResourceType.QUIZ
    assert res.metadata.title
    assert res.status == "generated"
    js = res.model_dump_json(indent=2)
    assert len(js) > 0
    print(f"  测试 11：ResourceOutput 结构 [PASS] ({len(js)} chars JSON)")

def test_single_type_warning():
    """只有一种题型时应有警告。"""
    data = {
        "items": [
            {"question_type": "single_choice", "stem": f"题{i}", "options": ["A. a", "B. b"], "correct_answer": "A", "explanation": "...", "difficulty": 1, "knowledge_point_tags": []}
            for i in range(5)
        ],
        "total_count": 5, "suggested_duration_minutes": 10,
    }
    js = json.dumps(data, ensure_ascii=False, indent=2)
    r = QuizAgent(client=MockLLMClient(content=f"```json\n{js}\n```")).generate(_make_kp())
    assert r.success and len(r.warnings) >= 1
    assert any("单一" in w or "仅" in w for w in r.warnings), f"应有题型单一警告: {r.warnings}"
    print(f"  测试 12：题型单一警告 [PASS] ({r.warnings})")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Quiz Agent (quiz_agent.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_basic_quiz_generation,
        test_llm_failure,
        test_empty_items,
        test_json_failure,
        test_empty_kp,
        test_partial_invalid_items,
        test_without_profile,
        test_practice_personalization,
        test_weak_point_personalization,
        test_system_prompt_contains_context,
        test_resource_structure,
        test_single_type_warning,
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
    print(f"  {'全部通过！Quiz Agent 可以放心使用。' if failed == 0 else f'{failed} 个测试失败，请检查。'}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
