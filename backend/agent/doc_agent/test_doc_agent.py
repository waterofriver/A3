# -*- coding: utf-8 -*-
"""
Doc Agent 测试 —— 验证讲义文档生成的正确性、个性化和边界处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.doc_agent.test_doc_agent

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

from .doc_agent import DocAgent, DocResult
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
        id="exp05_arp_poisoning",
        name="ARP 中毒攻击",
        description="认识链路层欺骗和中间人攻击的基础手法，理解攻击面与实验环境中的风险点。",
        category="网络攻防",
        prerequisites=["network_environment_setup"],
        difficulty=3,
        estimated_minutes=60,
        tags=["ARP", "中间人", "网络攻击"],
    )


def _make_profile(**overrides):
    """快速构造 StudentProfile。"""
    defaults = dict(
        major="信息安全",
        grade="大三",
        knowledge_base=[
            KnowledgeBaseItem(
                knowledge_point_id="network_basics",
                knowledge_point_name="网络基础",
                mastery=MasteryLevel.PROFICIENT,
            ),
        ],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="掌握网络攻防实验技能",
        weak_points=[
            WeakPoint(
                knowledge_point_id="exp05_arp_poisoning",
                knowledge_point_name="ARP 中毒攻击",
                error_pattern="ARP 协议报文结构理解不透彻",
                occurrence_count=2,
            ),
        ],
        learning_pace=LearningPace.DISTRIBUTED,
        interest_domains=["网络安全", "渗透测试"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_doc_response():
    """构造标准的讲义 LLM 返回 JSON。

    注意：body_markdown 中使用缩进代码块（4空格）而非围栏代码块（```)，
    避免与 extract_json 的 code fence 剥离逻辑冲突。
    """
    data = {
        "sections": [
            {
                "heading": "一、概念导入：什么是 ARP 协议与 ARP 中毒",
                "body_markdown": (
                    "## 1.1 ARP 协议概述\n\n"
                    "ARP（Address Resolution Protocol，地址解析协议）是 TCP/IP 协议栈中的关键协议，"
                    "负责将 **IP 地址** 解析为 **MAC 地址**。\n\n"
                    "### 为什么需要 ARP？\n\n"
                    "在局域网中，数据帧的传输依赖于 MAC 地址，而应用层使用的却是 IP 地址。"
                    "ARP 充当了这两者之间的翻译官角色。\n\n"
                    "### ARP 工作流程\n\n"
                    "1. 主机 A 要向主机 B 发送数据，但只知道 B 的 IP 地址\n"
                    "2. A 在局域网内广播 ARP 请求\n"
                    "3. B 收到后单播回复自己的 MAC 地址\n"
                    "4. A 将 IP-MAC 映射存入 ARP 缓存表\n\n"
                    "> ARP 协议设计于网络信任时代，**缺乏认证机制**，这为 ARP 中毒攻击埋下了隐患。"
                ),
                "key_points": [
                    "ARP 负责 IP 到 MAC 的地址解析",
                    "ARP 请求是广播，ARP 回复是单播",
                    "ARP 协议缺乏认证机制，这是安全漏洞的根源",
                ],
            },
            {
                "heading": "二、核心原理：ARP 中毒攻击机制",
                "body_markdown": (
                    "## 2.1 攻击原理\n\n"
                    "ARP 中毒（ARP Poisoning / ARP Spoofing）通过发送**伪造的 ARP 应答报文**，"
                    "欺骗目标主机更新 ARP 缓存表，将攻击者的 MAC 地址与合法 IP 绑定。\n\n"
                    "### 攻击步骤\n\n"
                    "正常通信路径：\n"
                    "    主机A  <-->  网关\n"
                    "攻击后路径：\n"
                    "    主机A  <-->  攻击者  <-->  网关\n\n"
                    "### 关键代码示例\n\n"
                    "使用 Python Scapy 库构造 ARP 欺骗包：\n\n"
                    "    from scapy.all import *\n"
                    "    # 构造 ARP 应答包\n"
                    "    packet = ARP(\n"
                    "        op=2,                  # 2 = ARP 应答\n"
                    '        pdst="192.168.1.100",  # 目标 IP\n'
                    '        hwdst="aa:bb:cc:dd",   # 目标 MAC\n'
                    '        psrc="192.168.1.1",    # 伪装成网关 IP\n'
                    "    )\n"
                    "    send(packet, verbose=False)"
                ),
                "key_points": [
                    "ARP 中毒通过伪造 ARP 应答实现中间人位置",
                    "攻击者伪装成网关，截获所有流量",
                    "Scapy 是 ARP 中毒实验的核心工具",
                ],
            },
            {
                "heading": "三、实践案例：ARP 中毒实验操作",
                "body_markdown": (
                    "## 3.1 实验环境\n\n"
                    "- 攻击机: Kali Linux (IP: 192.168.1.50)\n"
                    "- 目标机: Ubuntu 20.04 (IP: 192.168.1.100)\n"
                    "- 网关: 192.168.1.1\n"
                    "- 工具: Scapy / Ettercap / arpspoof\n\n"
                    "## 3.2 实验步骤\n\n"
                    "### 步骤 1: 确认网络连通性\n\n"
                    "    ping 192.168.1.100\n\n"
                    "### 步骤 2: 开启 IP 转发\n\n"
                    "    echo 1 > /proc/sys/net/ipv4/ip_forward\n\n"
                    "### 步骤 3: 执行 ARP 欺骗\n\n"
                    "    arpspoof -i eth0 -t 192.168.1.100 192.168.1.1\n\n"
                    "### 步骤 4: 验证攻击效果\n\n"
                    "在目标机上查看 ARP 缓存表：\n\n"
                    "    arp -a\n\n"
                    "如果网关 IP 对应的 MAC 地址变成了攻击机的 MAC，说明攻击成功。"
                ),
                "key_points": [
                    "攻击前必须开启 IP 转发，否则目标机断网",
                    "arpspoof 是 dsniff 工具集中的 ARP 欺骗工具",
                    "通过 arp -a 验证攻击是否成功",
                ],
            },
            {
                "heading": "四、常见误区与注意事项",
                "body_markdown": (
                    "## 4.1 常见错误\n\n"
                    "1. **忘记开启 IP 转发**: 如果不开启，目标主机将无法上网，攻击容易被发现\n"
                    "2. **ARP 表缓存时间**: 大多数系统 ARP 缓存会定期刷新，需要持续发送欺骗包\n"
                    "3. **防火墙拦截**: 部分安全软件和交换机 DAI 功能可能拦截 ARP 攻击\n\n"
                    "## 4.2 防御措施\n\n"
                    "- 静态 ARP 绑定: 在关键设备上手动设置 IP-MAC 映射\n"
                    "- 使用 ARP 检测工具: 如 arpwatch、XArp\n"
                    "- 交换机启用 DAI 和 DHCP Snooping"
                ),
                "key_points": [
                    "IP 转发未开启是最常见的实验失败原因",
                    "ARP 欺骗需要持续发包维持，不是一次性的",
                    "理解攻击原理才能更好地实施防御",
                ],
            },
            {
                "heading": "五、本章总结",
                "body_markdown": (
                    "## 总结\n\n"
                    "ARP 中毒攻击利用了 ARP 协议缺乏认证的设计缺陷，通过伪造 ARP 应答实现中间人攻击。"
                    "理解 ARP 的工作机制（请求/应答、广播/单播、缓存表）是掌握此攻击的基础。\n\n"
                    "在实际安全工作中，ARP 中毒的防御需要从协议层（静态绑定）、设备层（DAI）"
                    "和监控层（arpwatch）三个维度综合施策。\n\n"
                    "### 下一步学习\n\n"
                    "掌握 ARP 中毒后，可以继续学习 MITM（中间人攻击）中的数据篡改和流量劫持技术（参见实验六）。"
                ),
                "key_points": [
                    "ARP 协议缺乏认证是其核心安全缺陷",
                    "ARP 中毒是中间人攻击的基础技术",
                    "防御需要多层次综合施策",
                ],
            },
        ],
        "summary": (
            "本讲义从 ARP 协议基础出发，系统讲解了 ARP 中毒攻击的原理、实操步骤和防御方法。"
            "通过 Scapy 代码示例和完整实验流程，帮助学习者从理论到实践全面掌握 ARP 安全知识。"
        ),
        "further_reading": [
            "《TCP/IP 详解 卷一》第4章 ARP — 深入理解 ARP 协议设计",
            "RFC 826 — ARP 协议的原始规范文档",
            "Scapy 官方文档 — 学习更多网络数据包构造技巧",
            "《Metasploit 渗透测试指南》— ARP 中毒在渗透中的应用",
        ],
    }
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return f"```json\n{json_str}\n```"


# ═══════════════════════════════════════════════════════════════
# 测试 1：正常讲义生成
# ═══════════════════════════════════════════════════════════════

def test_basic_doc_generation():
    """正常输入应生成包含多个章节的完整讲义。"""
    print("=" * 60)
    print("测试 1：正常讲义生成")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)

    assert result.success, f"生成应该成功: {result.error}"

    resource = result.resource
    assert resource is not None
    assert resource.metadata.resource_type == ResourceType.DOC
    assert resource.metadata.knowledge_point_id == kp.id
    assert resource.generated_by == "DocAgent"

    # 验证内容
    content = resource.content
    assert len(content.sections) == 5, f"应有 5 个章节: {len(content.sections)}"
    assert len(content.summary) > 0, "应有总结"
    assert len(content.further_reading) == 4, f"应有 4 条延伸阅读: {len(content.further_reading)}"

    # 验证章节结构
    for sec in content.sections:
        assert "heading" in sec, "每章应有 heading"
        assert "body_markdown" in sec, "每章应有 body_markdown"
        assert "key_points" in sec, "每章应有 key_points"
        assert len(sec["body_markdown"]) > 0, f"章节 '{sec['heading']}' 的 body 不能为空"

    # 验证元数据
    assert resource.metadata.difficulty == kp.difficulty
    assert resource.metadata.estimated_read_time_minutes > 0

    print(f"  章节数: {len(content.sections)}")
    print(f"  阅读时长: {resource.metadata.estimated_read_time_minutes} 分钟")
    print(f"  总结: {content.summary[:80]}...")
    print(f"  延伸阅读: {len(content.further_reading)} 条")
    print("[PASS] 正常讲义生成通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2：LLM 调用失败
# ═══════════════════════════════════════════════════════════════

def test_llm_failure():
    """LLM 调用失败时应返回 success=False。"""
    print("=" * 60)
    print("测试 2：LLM 调用失败")
    print("=" * 60)

    client = MockLLMClient(success=False, error="Connection timeout")
    agent = DocAgent(client=client)
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

    agent = DocAgent(client=MockLLMClient())
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
# 测试 4：空 sections 检测
# ═══════════════════════════════════════════════════════════════

def test_empty_sections():
    """LLM 返回空 sections 时应失败。"""
    print("=" * 60)
    print("测试 4：空 sections 检测")
    print("=" * 60)

    mock_response = """```json
{"sections": [], "summary": "", "further_reading": []}
```"""
    client = MockLLMClient(content=mock_response)
    agent = DocAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success is False
    assert "sections 为空" in (result.error or "").lower() or "未生成" in (result.error or "")

    print(f"  错误信息: {result.error}")
    print("[PASS] 空 sections 正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 5：JSON 解析失败
# ═══════════════════════════════════════════════════════════════

def test_json_parse_failure():
    """LLM 返回非 JSON 内容时应失败。"""
    print("=" * 60)
    print("测试 5：JSON 解析失败")
    print("=" * 60)

    client = MockLLMClient(content="这不是 JSON 格式的回复")
    agent = DocAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success is False
    assert "JSON" in (result.error or "").upper()

    print(f"  错误信息: {result.error}")
    print("[PASS] JSON 解析失败正确处理\n")


# ═══════════════════════════════════════════════════════════════
# 测试 6：部分章节 body 为空
# ═══════════════════════════════════════════════════════════════

def test_sections_with_empty_body():
    """部分章节 body_markdown 为空时应跳过，保留有效章节。"""
    print("=" * 60)
    print("测试 6：部分章节 body 为空")
    print("=" * 60)

    mock_response = """```json
{
    "sections": [
        {"heading": "有效章节", "body_markdown": "有内容", "key_points": ["要点1"]},
        {"heading": "空章节", "body_markdown": "", "key_points": []},
        {"heading": "另一有效章节", "body_markdown": "也有内容", "key_points": ["要点2"]}
    ],
    "summary": "测试总结",
    "further_reading": []
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = DocAgent(client=client)

    result = agent.generate(_make_kp())

    assert result.success, f"应成功: {result.error}"
    content = result.resource.content
    assert len(content.sections) == 2, f"应保留 2 个有效章节: {len(content.sections)}"

    headings = [s["heading"] for s in content.sections]
    assert "空章节" not in headings

    print(f"  有效章节数: {len(content.sections)} (过滤掉空章节)")
    print(f"  章节: {headings}")
    print("[PASS] 空 body 过滤正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 7：无学生画像的通用生成
# ═══════════════════════════════════════════════════════════════

def test_generation_without_profile():
    """不提供学生画像时应使用通用风格。"""
    print("=" * 60)
    print("测试 7：无画像的通用生成")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()

    result = agent.generate(kp)  # 不传 profile

    assert result.success, f"应该成功: {result.error}"
    assert result.resource is not None
    # metadata 中应无画像快照
    assert result.resource.metadata.student_profile_snapshot == ""

    print(f"  生成成功（无画像模式）")
    print(f"  画像快照: '(空)'")
    print("[PASS] 无画像通用生成正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 8：System Prompt 包含知识点和学生画像
# ═══════════════════════════════════════════════════════════════

def test_system_prompt_contains_context():
    """System Prompt 应包含知识点信息和学生画像。"""
    print("=" * 60)
    print("测试 8：System Prompt 包含上下文")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)

    assert result.success
    last_kwargs = client.last_call_kwargs
    assert last_kwargs is not None

    system_prompt = last_kwargs.get("system_prompt", "")

    # 检查知识点信息
    assert kp.name in system_prompt
    assert kp.description in system_prompt
    assert kp.category in system_prompt
    assert str(kp.difficulty) in system_prompt

    # 检查学生画像
    assert "信息安全" in system_prompt
    assert "渗透测试" in system_prompt
    assert "ARP 中毒攻击" in system_prompt  # 薄弱环节

    print(f"  System Prompt 长度: {len(system_prompt)} 字符")
    print(f"  包含知识点信息: [OK]")
    print(f"  包含学生画像: [OK]")
    print("[PASS] System Prompt 构建正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 9：低质量内容警告
# ═══════════════════════════════════════════════════════════════

def test_low_quality_warning():
    """讲义总长度不足时应产生警告但依然成功。"""
    print("=" * 60)
    print("测试 9：低质量内容警告")
    print("=" * 60)

    # 返回的 body 非常短
    mock_response = """```json
{
    "sections": [
        {"heading": "短章节", "body_markdown": "很短的内容。", "key_points": []}
    ],
    "summary": "",
    "further_reading": []
}
```"""
    client = MockLLMClient(content=mock_response)
    agent = DocAgent(client=client)

    result = agent.generate(_make_kp())

    # 应成功（因为毕竟有内容），但有警告
    assert result.success
    assert len(result.warnings) >= 1
    assert any("长度" in w or "不够充实" in w for w in result.warnings), \
        f"应有内容长度警告: {result.warnings}"

    print(f"  警告: {result.warnings}")
    print("[PASS] 低质量警告正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 10：ResourceOutput 结构完整性
# ═══════════════════════════════════════════════════════════════

def test_resource_output_structure():
    """验证生成的 ResourceOutput 符合 schema 定义。"""
    print("=" * 60)
    print("测试 10：ResourceOutput 结构完整性")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()

    result = agent.generate(kp, profile)
    assert result.success

    resource = result.resource

    # 验证 metadata
    assert resource.metadata.resource_type == ResourceType.DOC
    assert resource.metadata.knowledge_point_id == kp.id
    assert resource.metadata.knowledge_point_name == kp.name
    assert resource.metadata.title != ""
    assert 1 <= resource.metadata.difficulty <= 5
    assert resource.metadata.estimated_read_time_minutes > 0

    # 验证 status
    assert resource.status == "generated"
    assert resource.generated_by == "DocAgent"

    # 验证 content 类型
    from ..models import DocContent
    assert isinstance(resource.content, DocContent), \
        f"content 应为 DocContent 类型: {type(resource.content)}"

    # 验证 content 字段
    assert len(resource.content.sections) > 0
    assert isinstance(resource.content.summary, str)
    assert isinstance(resource.content.further_reading, list)

    # 验证可序列化
    try:
        json_str = resource.model_dump_json(indent=2)
        assert len(json_str) > 0
        print(f"  JSON 序列化: OK, {len(json_str)} 字符")
    except Exception as e:
        assert False, f"序列化失败: {e}"

    print(f"  资源类型: {resource.metadata.resource_type.value}")
    print(f"  知识点: {resource.metadata.knowledge_point_name}")
    print(f"  标题: {resource.metadata.title}")
    print(f"  状态: {resource.status}")
    print("[PASS] ResourceOutput 结构完整\n")


# ═══════════════════════════════════════════════════════════════
# 测试 11：实践型学生个性化
# ═══════════════════════════════════════════════════════════════

def test_practice_oriented_personalization():
    """偏实践型学生应在 user_message 中体现实践偏好。"""
    print("=" * 60)
    print("测试 11：实践型学生个性化")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()
    profile = _make_profile(cognitive_style=CognitiveStyle.PRACTICE_ORIENTED)

    result = agent.generate(kp, profile)

    assert result.success
    last_kwargs = client.last_call_kwargs
    user_message = last_kwargs.get("user_message", "")

    assert "实践" in user_message or "动手" in user_message or "操作" in user_message, \
        f"实践型学生的提示应包含实践关键词: '{user_message[:200]}'"

    print(f"  User Message 包含实践关键词: [OK]")
    print("[PASS] 实践型个性化正确\n")


# ═══════════════════════════════════════════════════════════════
# 测试 12：薄弱知识点个性化
# ═══════════════════════════════════════════════════════════════

def test_weak_point_personalization():
    """当前知识点是学生薄弱环节时应在提示中体现。"""
    print("=" * 60)
    print("测试 12：薄弱知识点个性化")
    print("=" * 60)

    client = MockLLMClient(content=_make_doc_response())
    agent = DocAgent(client=client)
    kp = _make_kp()
    profile = _make_profile()  # weak_points 中包含 exp05_arp_poisoning

    result = agent.generate(kp, profile)

    assert result.success
    last_kwargs = client.last_call_kwargs
    user_message = last_kwargs.get("user_message", "")

    assert "薄弱" in user_message or "重点" in user_message, \
        f"薄弱知识点的提示应体现: '{user_message[:200]}'"

    print(f"  User Message 包含薄弱知识点提示: [OK]")
    print("[PASS] 薄弱知识点个性化正确\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    """运行所有测试并统计结果。"""
    print("=" * 60)
    print("  Doc Agent (doc_agent.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_basic_doc_generation,
        test_llm_failure,
        test_empty_knowledge_point,
        test_empty_sections,
        test_json_parse_failure,
        test_sections_with_empty_body,
        test_generation_without_profile,
        test_system_prompt_contains_context,
        test_low_quality_warning,
        test_resource_output_structure,
        test_practice_oriented_personalization,
        test_weak_point_personalization,
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
        print("  全部通过！Doc Agent 可以放心使用。")
    else:
        print(f"  {failed} 个测试失败，请检查。")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
