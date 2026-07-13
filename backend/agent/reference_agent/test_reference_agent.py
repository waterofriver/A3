# -*- coding: utf-8 -*-
"""
Reference Agent 测试 — 验证推荐匹配、库内外推荐、个性化和边界处理。
运行: python -m agent.reference_agent.test_reference_agent
"""

import sys, io, json
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from .reference_agent import ReferenceAgent
from ..utils import LLMResponse
from ..models import (StudentProfile, KnowledgePoint, KnowledgeBaseItem,
    WeakPoint, MasteryLevel, CognitiveStyle, LearningPace)

class MockLLMClient:
    def __init__(self, content="", success=True, error=None):
        self.content = content; self.success = success; self.error = error
        self.last_call_kwargs = None
    def chat(self, **kwargs):
        self.last_call_kwargs = kwargs
        return LLMResponse(content=self.content, success=self.success, error=self.error, model="mock")

def _make_kp():
    return KnowledgePoint(id="exp01_ros_turtlesim", name="ROS 进阶与小乌龟",
        description="通过 turtlesim 认识 ROS 的基本通信和控制方式。",
        category="ROS 基础", prerequisites=["network_environment_setup"],
        difficulty=2, estimated_minutes=60, tags=["ROS", "turtlesim", "入门实验"])

def _make_profile(**o):
    d = dict(major="机器人工程", grade="大三",
        knowledge_base=[KnowledgeBaseItem(knowledge_point_id="linux", knowledge_point_name="Linux基础", mastery=MasteryLevel.FAMILIAR)],
        cognitive_style=CognitiveStyle.PRACTICE_ORIENTED,
        learning_goal_short="掌握ROS机器人开发", learning_goal_long="成为机器人安全工程师",
        weak_points=[WeakPoint(knowledge_point_id="ros_basics", knowledge_point_name="ROS基础", error_pattern="话题通信理解不深", occurrence_count=3)],
        learning_pace=LearningPace.DISTRIBUTED, interest_domains=["机器人", "ROS"])
    d.update(o); return StudentProfile(**d)

_SHARED_REFS = [
    {"name": "ROS基础（课外阅读）", "path": "/materials/shared/ROS基础.pdf", "file_type": "pdf", "size_bytes": 1000},
    {"name": "ROS机器人高效编程（原书第3版）", "path": "/materials/shared/ROS高效编程.pdf", "file_type": "pdf", "size_bytes": 2000},
    {"name": "Linux学习笔记", "path": "/materials/shared/Linux笔记.pdf", "file_type": "pdf", "size_bytes": 500},
    {"name": "机器人操作系统ROS原理与应用", "path": "/materials/shared/ROS原理.pdf", "file_type": "pdf", "size_bytes": 1500},
    {"name": "Turtlebot3京天用户手册", "path": "/materials/shared/turtlebot3.docx", "file_type": "docx", "size_bytes": 3000},
]

_SHARED_SUMMARY = "## 课程拓展阅读库\n\n### ROS基础（课外阅读）\n- 格式: pdf\n- 内容摘要: ROS核心概念、话题通信、服务调用...\n\n### ROS机器人高效编程\n- 格式: pdf\n- 内容摘要: ROS编程实践、调试技巧..."

def _make_response():
    data = {
        "library_recommendations": [
            {"title": "ROS基础（课外阅读）", "relevance_reason": "你的ROS基础薄弱，这本书从话题通信讲起，正好补齐你的短板", "suggested_focus": "第3-4章：话题通信与服务调用", "priority": 5, "difficulty_level": 2, "tags": ["ROS", "入门"]},
            {"title": "ROS机器人高效编程（原书第3版）", "relevance_reason": "你偏好动手实践，这本书有大量可直接运行的代码案例", "suggested_focus": "第5-8章：机器人控制与传感器", "priority": 4, "difficulty_level": 3, "tags": ["ROS", "编程"]},
            {"title": "机器人操作系统ROS原理与应用", "relevance_reason": "配合你的长期目标（机器人安全工程师），系统学习ROS原理", "suggested_focus": "第6-9章：ROS安全机制", "priority": 3, "difficulty_level": 3, "tags": ["ROS", "原理"]},
        ],
        "external_recommendations": [
            {"title": "Programming Robots with ROS", "author": "Morgan Quigley", "relevance_reason": "ROS官方推荐的实战指南，英文原版更适合深入理解术语", "suggested_focus": "Part II: ROS Core Concepts", "priority": 3, "difficulty_level": 3, "tags": ["ROS", "英文"]},
        ],
        "reading_path": "建议先读ROS基础（课外阅读）建立概念，再用ROS高效编程动手练习，最后阅读ROS原理与应用深入理解安全机制。",
        "total_estimated_hours": 25,
    }
    return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"


# ═══════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════

def test_basic_recommend():
    print("=" * 60)
    print("测试 1：正常推荐")
    print("=" * 60)
    r = ReferenceAgent(client=MockLLMClient(content=_make_response())).recommend(_make_kp(), _make_profile(), _SHARED_SUMMARY, _SHARED_REFS)
    assert r.success, f"应该成功: {r.error}"
    assert r.library_count == 3 and r.external_count == 1
    for rec in r.library_recommendations:
        assert rec["source"] == "in_library"
        assert rec["file_path"], f"库内推荐应有 file_path: {rec['title']}"
        assert rec["priority"] >= 1
    for rec in r.external_recommendations:
        assert rec["source"] == "external"
        assert rec["author"]
    assert r.reading_path
    print(f"  库内: {r.library_count} | 外部: {r.external_count}")
    print(f"  阅读路径: {r.reading_path[:80]}...")
    print("[PASS]\n")

def test_llm_failure():
    r = ReferenceAgent(client=MockLLMClient(success=False, error="Timeout")).recommend(_make_kp())
    assert r.success is False and "Timeout" in (r.error or "")
    print("  测试 2：LLM 失败 [PASS]")

def test_empty_kp():
    kp = KnowledgePoint(id="x", name="", description="", category="", prerequisites=[], difficulty=1)
    r = ReferenceAgent(client=MockLLMClient()).recommend(kp)
    assert r.success is False and "空" in (r.error or "")
    print("  测试 3：空知识点 [PASS]")

def test_json_failure():
    r = ReferenceAgent(client=MockLLMClient(content="不是JSON")).recommend(_make_kp())
    assert r.success is False and "JSON" in (r.error or "").upper()
    print("  测试 4：JSON 失败 [PASS]")

def test_empty_recs():
    r = ReferenceAgent(client=MockLLMClient(content='```json\n{"library_recommendations":[],"external_recommendations":[],"reading_path":"","total_estimated_hours":0}\n```')).recommend(_make_kp())
    assert r.success is False and "空" in (r.error or "").lower()
    print("  测试 5：空推荐 [PASS]")

def test_without_profile():
    r = ReferenceAgent(client=MockLLMClient(content=_make_response())).recommend(_make_kp(), shared_refs_summary=_SHARED_SUMMARY, shared_refs_list=_SHARED_REFS)
    assert r.success and r.resource.metadata.student_profile_snapshot == ""
    print("  测试 6：无画像 [PASS]")

def test_personalization():
    client = MockLLMClient(content=_make_response())
    r = ReferenceAgent(client=client).recommend(_make_kp(), _make_profile(), _SHARED_SUMMARY, _SHARED_REFS)
    assert r.success
    sp = client.last_call_kwargs.get("system_prompt", "")
    assert "机器人工程" in sp and "ROS基础" in sp and "拓展阅读库" in sp
    print("  测试 7：System Prompt 上下文 [PASS]")

def test_file_path_backfill():
    """库内推荐的 title 匹配到 shared_refs_list 中时应回填 file_path。"""
    r = ReferenceAgent(client=MockLLMClient(content=_make_response())).recommend(_make_kp(), _make_profile(), _SHARED_SUMMARY, _SHARED_REFS)
    assert r.success
    with_path = [rec for rec in r.library_recommendations if rec["file_path"]]
    assert len(with_path) == 3, f"3 本库内推荐都应有 file_path: {len(with_path)}"
    print(f"  测试 8：file_path 回填 [PASS] ({len(with_path)}/3)")

def test_no_library():
    """无共享库时全用外部推荐也能成功。"""
    data = {"library_recommendations": [], "external_recommendations": [{"title": "ROS: The Complete Reference", "author": "A. Koubaa", "relevance_reason": "综合参考", "suggested_focus": "Part I", "priority": 2, "difficulty_level": 4, "tags": ["ROS"]}], "reading_path": "只有外部推荐", "total_estimated_hours": 10}
    r = ReferenceAgent(client=MockLLMClient(content=f"```json\n{json.dumps(data, ensure_ascii=False)}\n```")).recommend(_make_kp(), _make_profile())
    assert r.success and r.external_count == 1 and r.library_count == 0
    print("  测试 9：纯外部推荐 [PASS]")

def test_resource_structure():
    r = ReferenceAgent(client=MockLLMClient(content=_make_response())).recommend(_make_kp(), _make_profile(), _SHARED_SUMMARY, _SHARED_REFS)
    assert r.success
    res = r.resource
    assert res.metadata.title
    assert res.generated_by == "ReferenceAgent"
    assert res.status == "generated"
    js = res.model_dump_json(indent=2)
    assert len(js) > 0
    print(f"  测试 10：ResourceOutput 结构 [PASS] ({len(js)} chars)")


def main():
    print("=" * 60)
    print("  Reference Agent (reference_agent.py) 测试")
    print("=" * 60 + "\n")
    tests = [test_basic_recommend, test_llm_failure, test_empty_kp, test_json_failure,
             test_empty_recs, test_without_profile, test_personalization,
             test_file_path_backfill, test_no_library, test_resource_structure]
    p = f = 0
    for t in tests:
        try: t(); p += 1
        except AssertionError as e: f += 1; print(f"[FAIL] {t.__name__}: {e}\n")
        except Exception as e: f += 1; import traceback; print(f"[ERROR] {t.__name__}: {e}"); traceback.print_exc(); print()
    print("=" * 60)
    print(f"  结果: {p}/{len(tests)} 通过")
    print(f"  {'全部通过！' if f == 0 else f'{f} 个失败'}")
    print("=" * 60)
    return f == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
