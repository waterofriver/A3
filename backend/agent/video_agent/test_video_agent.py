# -*- coding: utf-8 -*-
"""
Video Agent 测试 —— 验证视频发现、导览脚本生成、个性化推送和边界处理。

运行方式：
    cd D:/Study/中国软件杯
    python -m agent.video_agent.test_video_agent

所有测试使用 MockLLMClient，无需 API Key。
"""

import sys
import io
import json
import tempfile
import os

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .video_agent import VideoAgent, VideoResult, _find_mp4, _get_video_duration
from ..utils import LLMResponse
from ..models import (
    StudentProfile, KnowledgePoint,
    KnowledgeBaseItem, WeakPoint, MasteryLevel,
    CognitiveStyle, LearningPace, ResourceType,
)


class MockLLMClient:
    def __init__(self, content="", success=True, error=None):
        self.content = content; self.success = success; self.error = error
        self.last_call_kwargs = None

    def chat(self, **kwargs):
        self.last_call_kwargs = kwargs
        return LLMResponse(content=self.content, success=self.success,
                           error=self.error, model="mock-model")


def _make_kp():
    return KnowledgePoint(
        id="exp05_arp_poisoning", name="ARP 中毒攻击",
        description="认识链路层欺骗和中间人攻击的基础手法。",
        category="网络攻防", prerequisites=["network_environment_setup"],
        difficulty=3, estimated_minutes=60,
        tags=["ARP", "中间人", "网络攻击"],
    )


def _make_profile(**overrides):
    defaults = dict(
        major="机器人工程", grade="大三",
        knowledge_base=[KnowledgeBaseItem(knowledge_point_id="network_basics", knowledge_point_name="网络基础", mastery=MasteryLevel.PROFICIENT)],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="掌握网络攻防实验",
        weak_points=[WeakPoint(knowledge_point_id="exp05_arp_poisoning", knowledge_point_name="ARP 中毒攻击", error_pattern="ARP协议不熟", occurrence_count=2)],
        learning_pace=LearningPace.DISTRIBUTED,
        interest_domains=["网络安全", "渗透测试"],
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _make_video_response():
    data = {
        "push_reason": "你在ARP协议理解上存在薄弱点，这个演示视频将直观展示ARP欺骗的完整攻击链路，帮助你从实际操作中理解协议漏洞。",
        "target_audience": "机器人工程大三学生，已掌握网络基础，正在学习网络攻防",
        "scenes": [
            {"scene_number": 1, "narration": "注意观察攻击前的网络拓扑和IP配置", "visual_description": "展示实验环境：攻击机Kali、目标机Ubuntu、网关的三方IP和MAC地址", "duration_seconds": 45},
            {"scene_number": 2, "narration": "重点关注ARP欺骗命令的参数含义", "visual_description": "攻击机执行arpspoof命令，同时开启IP转发", "duration_seconds": 60},
            {"scene_number": 3, "narration": "观察目标机ARP缓存表的变化——网关MAC已被替换为攻击机MAC", "visual_description": "目标机上用arp -a查看被污染的ARP表，网关IP对应攻击机MAC", "duration_seconds": 50},
            {"scene_number": 4, "narration": "理解攻击效果：所有流量经过攻击机中转", "visual_description": "Wireshark抓包展示流量劫持效果，攻击机可看到目标的所有通信", "duration_seconds": 55},
            {"scene_number": 5, "narration": "回顾攻击全过程，思考防御方法", "visual_description": "总结ARP中毒的攻击链路，展示静态绑定和DAI等防御配置", "duration_seconds": 50},
        ],
        "watch_focus": ["ARP请求/应答的广播与单播区别", "arpspoof命令的-t参数含义", "IP转发在攻击中的关键作用"],
        "after_watching": "看完视频后建议动手复现实验五的ARP中毒攻击，并完成配套练习题",
    }
    js = json.dumps(data, ensure_ascii=False, indent=2)
    return f"```json\n{js}\n```"


# ═══════════════════════════════════════════════════════════════
# 测试 1：正常视频推送（有 MP4）
# ═══════════════════════════════════════════════════════════════

def test_basic_video_push():
    """知识点有 MP4 时应返回完整的视频推送。"""
    print("=" * 60)
    print("测试 1：正常视频推送")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        mp4_path = os.path.join(kp_dir, "实验五 APR中毒演示视频.mp4")
        Path = __import__("pathlib").Path
        Path(mp4_path).write_bytes(b"fake mp4 content " * 10000)

        client = MockLLMClient(content=_make_video_response())
        agent = VideoAgent(client=client)

        result = agent.generate(_make_kp(), _make_profile(), materials_dir=tmpdir)

        assert result.success
        assert result.has_video
        assert "实验五" in str(result.video_path or "")
        assert len(result.push_reason) > 0

        resource = result.resource
        assert resource.metadata.resource_type == ResourceType.VIDEO_SCRIPT
        assert resource.generated_by == "VideoAgent"

        content = resource.content
        assert len(content.scenes) == 5
        assert content.title
        assert content.total_duration_seconds >= 0

        print(f"  视频路径: .../{Path(result.video_path).name}")
        print(f"  分镜数: {len(content.scenes)}")
        print(f"  推送理由: {result.push_reason[:80]}...")
        print("[PASS] 正常视频推送通过\n")


# ═══════════════════════════════════════════════════════════════
# 测试 2-5：无视频 / LLM 失败 / 空 KP / JSON 失败
# ═══════════════════════════════════════════════════════════════

def test_no_video():
    with tempfile.TemporaryDirectory() as tmpdir:
        r = VideoAgent(client=MockLLMClient()).generate(_make_kp(), materials_dir=tmpdir)
        assert r.success and not r.has_video
    print("  测试 2：无视频 [PASS]")

def test_llm_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        r = VideoAgent(client=MockLLMClient(success=False, error="Timeout")).generate(_make_kp(), materials_dir=tmpdir)
        assert r.success is False and r.has_video and "Timeout" in (r.error or "")
    print("  测试 3：LLM 失败 [PASS]")

def test_empty_kp():
    kp = KnowledgePoint(id="x", name="", description="", category="", prerequisites=[], difficulty=1)
    r = VideoAgent(client=MockLLMClient()).generate(kp)
    assert r.success is False and "空" in (r.error or "")
    print("  测试 4：空知识点 [PASS]")

def test_json_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        r = VideoAgent(client=MockLLMClient(content="不是JSON")).generate(_make_kp(), materials_dir=tmpdir)
        assert r.success and r.has_video, f"JSON失败应降级成功: {r.error}"
        assert len(r.warnings) >= 1 and any("降级" in w or "失败" in w for w in r.warnings)
    print("  测试 5：JSON 失败降级 [PASS]")


# ═══════════════════════════════════════════════════════════════
# 测试 6：无画像 / 个性化 / System Prompt
# ═══════════════════════════════════════════════════════════════

def test_without_profile():
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        r = VideoAgent(client=MockLLMClient(content=_make_video_response())).generate(_make_kp(), materials_dir=tmpdir)
        assert r.success and r.has_video and r.resource.metadata.student_profile_snapshot == ""
    print("  测试 6：无画像 [PASS]")

def test_personalization():
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        client = MockLLMClient(content=_make_video_response())
        r = VideoAgent(client=client).generate(_make_kp(), _make_profile(), materials_dir=tmpdir)
        assert r.success
        msg = client.last_call_kwargs.get("user_message", "")
        assert "薄弱" in msg
    print("  测试 7：个性化 [PASS]")

def test_system_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        client = MockLLMClient(content=_make_video_response())
        r = VideoAgent(client=client).generate(_make_kp(), _make_profile(), material_context="课件内容", materials_dir=tmpdir)
        assert r.success
        sp = client.last_call_kwargs.get("system_prompt", "")
        assert "ARP 中毒攻击" in sp and "课件内容" in sp and "机器人工程" in sp
    print("  测试 8：System Prompt [PASS]")


# ═══════════════════════════════════════════════════════════════
# 测试 9：ResourceOutput 结构 / _find_mp4 优先级
# ═══════════════════════════════════════════════════════════════

def test_resource_structure():
    from ..models import VideoScriptContent
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        r = VideoAgent(client=MockLLMClient(content=_make_video_response())).generate(_make_kp(), _make_profile(), materials_dir=tmpdir)
        assert r.success
        res = r.resource
        assert isinstance(res.content, VideoScriptContent)
        assert res.metadata.resource_type == ResourceType.VIDEO_SCRIPT
        assert res.metadata.title
        assert res.status == "generated"
        js = res.model_dump_json(indent=2)
        assert len(js) > 0
        print(f"  测试 9：结构完整 [PASS] ({len(js)} chars)")

def test_find_mp4_priority():
    """_find_mp4 应优先选非'新_'版本。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp02_robot_remote_control")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "新_实验二.mp4")).write_bytes(b"new")
        Path(os.path.join(kp_dir, "实验二.mp4")).write_bytes(b"stable")
        result = _find_mp4(Path(tmpdir), "exp02_robot_remote_control")
        assert result is not None and "新_" not in result.name
    print("  测试 10：MP4 优先级 [PASS]")


# ═══════════════════════════════════════════════════════════════
# 测试 11：分镜校验（无效分镜跳过）
# ═══════════════════════════════════════════════════════════════

def test_invalid_scene_filtered():
    """无效分镜（narration 和 visual_description 均为空）应被过滤。"""
    print("=" * 60)
    print("测试 11：无效分镜过滤")
    print("=" * 60)

    data = {
        "push_reason": "测试",
        "target_audience": "",
        "scenes": [
            {"scene_number": 1, "narration": "有效分镜", "visual_description": "有描述", "duration_seconds": 30},
            {"scene_number": 2, "narration": "", "visual_description": "", "duration_seconds": 30},
            {"scene_number": 3, "narration": "另一有效", "visual_description": "", "duration_seconds": 20},
        ],
        "watch_focus": [],
        "after_watching": "",
    }
    js = json.dumps(data, ensure_ascii=False, indent=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        kp_dir = os.path.join(tmpdir, "exp05_arp_poisoning")
        os.makedirs(kp_dir)
        Path = __import__("pathlib").Path
        Path(os.path.join(kp_dir, "v.mp4")).write_bytes(b"x" * 1000)
        r = VideoAgent(client=MockLLMClient(content=f"```json\n{js}\n```")).generate(_make_kp(), materials_dir=tmpdir)
        assert r.success
        scenes = r.resource.content.scenes
        assert len(scenes) == 2, f"应过滤掉空分镜: {len(scenes)}"

    print(f"  有效分镜: {len(scenes)}")
    print("[PASS] 无效分镜过滤通过\n")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Video Agent (video_agent.py) 测试")
    print("=" * 60)
    print()

    tests = [
        test_basic_video_push,
        test_no_video,
        test_llm_failure,
        test_empty_kp,
        test_json_failure,
        test_without_profile,
        test_personalization,
        test_system_prompt,
        test_resource_structure,
        test_find_mp4_priority,
        test_invalid_scene_filtered,
    ]

    passed = 0; failed = 0
    for test in tests:
        try:
            test(); passed += 1
        except AssertionError as e:
            failed += 1; print(f"[FAIL] {test.__name__}: {e}\n")
        except Exception as e:
            failed += 1
            import traceback; print(f"[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc(); print()

    print("=" * 60)
    print(f"  结果: {passed}/{len(tests)} 通过")
    print(f"  {'全部通过！Video Agent 可以放心使用。' if failed == 0 else f'{failed} 个测试失败，请检查。'}")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
