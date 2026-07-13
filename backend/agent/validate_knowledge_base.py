"""
知识库校验脚本
================
用 Pydantic v2 对 knowledge_dag.json 进行全面校验，包括：
1. JSON 结构是否符合 KnowledgeDAG schema
2. 知识点 ID 是否唯一
3. 所有 prerequisites 引用是否指向已存在的知识点
4. 是否存在循环依赖
5. 是否至少有一个入口知识点
6. 每个知识点是否都有对应的 materials 目录

用法：
    python validate_knowledge_base.py [json文件路径]
    
    默认校验  knowledge_base/knowledge_dag.json
"""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path
from collections import deque

# 修复 Windows 控制台 GBK 编码导致 UnicodeEncodeError 的问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 把 agent 所在目录（backend/）加入 sys.path，使 `from agent.models import ...` 可用
_AGENT_DIR = Path(__file__).resolve().parent  # agent/
_BACKEND_DIR = _AGENT_DIR.parent              # backend/
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from agent.models.schemas import KnowledgeDAG, KnowledgePoint


# ═══════════════════════════════════════════════════════════════
# 加载
# ═══════════════════════════════════════════════════════════════

def load_json(filepath: Path) -> dict | None:
    """加载 JSON 文件，失败则返回 None"""
    if not filepath.exists():
        print(f"[错误] 文件不存在: {filepath}")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 格式错误: {e}")
        return None
    except Exception as e:
        print(f"[错误] 无法读取文件: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# 校验函数（每个返回 (bool, 信息列表)）
# ═══════════════════════════════════════════════════════════════

def validate_schema(data: dict) -> tuple[bool, list[str]]:
    """校验 JSON 是否符合 KnowledgeDAG 的 Pydantic schema"""
    errors = []
    try:
        KnowledgeDAG(**data)
    except Exception as e:
        errors.append(f"Pydantic 校验失败: {e}")
    return len(errors) == 0, errors


def validate_unique_ids(kps: list[dict]) -> tuple[bool, list[str]]:
    """校验知识点 ID 是否唯一"""
    errors = []
    seen = {}
    for i, kp in enumerate(kps):
        kp_id = kp.get("id", "")
        if not kp_id:
            errors.append(f"第 {i+1} 个知识点缺少 'id' 字段")
        elif kp_id in seen:
            errors.append(
                f"知识点 ID '{kp_id}' 重复: 第 {seen[kp_id]+1} 个和第 {i+1} 个"
            )
        else:
            seen[kp_id] = i
    return len(errors) == 0, errors


def validate_prerequisites(kps: list[dict]) -> tuple[bool, list[str]]:
    """校验所有 prerequisites 引用的知识点 ID 是否真实存在"""
    errors = []
    all_ids = {kp.get("id", "") for kp in kps}
    for kp in kps:
        kp_id = kp.get("id", "?")
        for pre in kp.get("prerequisites", []):
            if pre not in all_ids:
                errors.append(
                    f"知识点 '{kp_id}' 的前置依赖 '{pre}' 不在知识点列表中"
                )
    return len(errors) == 0, errors


def validate_no_cycles(kps: list[dict]) -> tuple[bool, list[str]]:
    """用拓扑排序检测循环依赖（Kahn 算法）"""
    errors = []
    all_ids = {kp.get("id", "") for kp in kps}
    
    # 构建邻接表和入度表
    in_degree = {kp_id: 0 for kp_id in all_ids}
    adj = {kp_id: [] for kp_id in all_ids}
    
    for kp in kps:
        src = kp.get("id", "")
        for pre in kp.get("prerequisites", []):
            # pre → src（前置先学，再到当前知识点）
            if pre in adj:
                adj[pre].append(src)
                in_degree[src] = in_degree.get(src, 0) + 1
    
    # Kahn
    queue = deque([n for n, d in in_degree.items() if d == 0])
    sorted_count = 0
    
    while queue:
        node = queue.popleft()
        sorted_count += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if sorted_count != len(all_ids):
        # 找出环中的节点
        cycle_nodes = [n for n, d in in_degree.items() if d > 0]
        errors.append(
            f"检测到循环依赖，涉及知识点: {', '.join(cycle_nodes)}。"
            f"请检查这些知识点的 prerequisites 是否形成了 A→B→A 的环路。"
        )
    
    return len(errors) == 0, errors


def validate_entry_points(kps: list[dict]) -> tuple[bool, list[str]]:
    """校验是否至少有一个入口知识点（prerequisites 为空）"""
    errors = []
    entry_count = sum(1 for kp in kps if not kp.get("prerequisites", []))
    if entry_count == 0:
        errors.append(
            "没有找到入口知识点（prerequisites 为空的知识点）。"
            "至少需要一个无前置依赖的知识点作为学习起点。"
        )
    return len(errors) == 0, errors


def validate_materials(kps: list[dict], materials_dir: Path) -> tuple[bool, list[str]]:
    """校验每个知识点是否有对应的 materials 目录（非强制性，仅警告）"""
    warnings = []
    if not materials_dir.exists():
        warnings.append(f"[警告] materials 目录不存在: {materials_dir}")
        # 不是阻塞性错误，只警告
        return True, warnings
    
    for kp in kps:
        kp_id = kp.get("id", "")
        kp_dir = materials_dir / kp_id
        if not kp_dir.exists():
            warnings.append(
                f"[警告] 知识点 '{kp_id}' 对应的素材目录不存在: {kp_dir}。"
                f"建议创建该目录并放入至少一份素材文件。"
            )
        elif not any(kp_dir.iterdir()):
            warnings.append(
                f"[警告] 知识点 '{kp_id}' 的素材目录为空: {kp_dir}。"
                f"建议放入至少一份素材文件（.docx/.pptx/.pdf/.mp4 等）。"
            )
    
    return True, warnings  # 素材缺失不算错误，只警告


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    # 解析参数
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        # 默认路径：从 agent/validate_knowledge_base.py
        #   → agent/ → backend/ → A3/ → A3/knowledge_base/knowledge_dag.json
        json_path = _BACKEND_DIR.parent / "knowledge_base" / "knowledge_dag.json"
    
    materials_dir = json_path.parent / "materials"
    
    print("=" * 60)
    print(f"校验文件: {json_path}")
    print(f"素材目录: {materials_dir}")
    print("=" * 60)
    
    # 1. 加载 JSON
    data = load_json(json_path)
    if data is None:
        sys.exit(1)
    
    kps = data.get("knowledge_points", [])
    print(f"\n知识点总数: {len(kps)}")
    
    # 2. 逐项校验
    total_errors = 0
    total_warnings = 0
    
    checks = [
        ("JSON Schema 校验", validate_schema, [data]),
        ("ID 唯一性", validate_unique_ids, [kps]),
        ("前置依赖引用完整性", validate_prerequisites, [kps]),
        ("循环依赖检测", validate_no_cycles, [kps]),
        ("入口知识点检查", validate_entry_points, [kps]),
        ("素材目录检查", validate_materials, [kps, materials_dir]),
    ]
    
    print()
    for name, fn, args in checks:
        ok, msgs = fn(*args)
        icon = "[OK]" if ok else "[FAIL]"
        label = "校验通过" if ok else "发现问题"
        print(f"{icon} {name}: {label}")
        for msg in msgs:
            if msg.startswith("[警告]"):
                total_warnings += 1
            else:
                total_errors += 1
            print(f"    {msg}")
    
    # 3. 汇总
    print()
    print("=" * 60)
    if total_errors == 0:
        print(f"校验通过！ ({total_warnings} 个警告)")
        if total_warnings:
            print("警告不影响使用，但建议补充素材文件以获得更好的生成效果。")
    else:
        print(f"校验失败: {total_errors} 个错误, {total_warnings} 个警告")
        print("请修复以上错误后重新运行校验。")
        sys.exit(1)
    
    # 4. 额外提示
    print()
    print("小贴士:")
    entry_kps = [kp for kp in kps if not kp.get("prerequisites", [])]
    print(f"  - 入口知识点 ({len(entry_kps)} 个): {', '.join(k['name'] for k in entry_kps)}")
    max_depth_kps = sorted(kps, key=lambda k: len(k.get("prerequisites", [])), reverse=True)[:3]
    print(f"  - 最深知识点: {', '.join(k['name'] for k in max_depth_kps)}")
    print(f"  - 知识点总数: {len(kps)}")


if __name__ == "__main__":
    main()
