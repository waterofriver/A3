from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".docx",
    ".jpg",
    ".jpeg",
    ".md",
    ".mp4",
    ".pdf",
    ".png",
    ".pptx",
    ".txt",
    ".webp",
}

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_errors(root: Path) -> list[str]:
    errors: list[str] = []
    dag_path = root / "knowledge_dag.json"
    materials_root = root / "materials"

    if not dag_path.is_file():
        return [f"缺少文件: {dag_path.name}"]

    try:
        data = load_json(dag_path)
    except json.JSONDecodeError as error:
        return [f"JSON 格式错误: {error.msg} (line {error.lineno}, column {error.colno})"]

    course_name = str(data.get("course_name", "")).strip()
    course_slug = str(data.get("course_slug", "")).strip()
    points = data.get("knowledge_points")

    if not course_name:
        errors.append("course_name 不能为空")
    if not course_slug:
        errors.append("course_slug 不能为空")
    elif not SLUG_PATTERN.fullmatch(course_slug):
        errors.append("course_slug 只能包含小写字母、数字和连字符")
    if not isinstance(points, list) or not points:
        errors.append("knowledge_points 必须是非空数组")
        return errors

    ids: list[str] = []
    point_by_id: dict[str, dict] = {}
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            errors.append(f"knowledge_points[{index}] 不是对象")
            continue
        point_id = str(point.get("id", "")).strip()
        if not point_id:
            errors.append(f"knowledge_points[{index}].id 不能为空")
            continue
        if point_id in point_by_id:
            errors.append(f"知识点 ID 重复: {point_id}")
            continue
        ids.append(point_id)
        point_by_id[point_id] = point

        for field in ("name", "description", "category"):
            if not str(point.get(field, "")).strip():
                errors.append(f"{point_id} 的 {field} 不能为空")

        prerequisites = point.get("prerequisites", [])
        if not isinstance(prerequisites, list):
            errors.append(f"{point_id} 的 prerequisites 必须是数组")

        difficulty = point.get("difficulty")
        if not isinstance(difficulty, int) or not 1 <= difficulty <= 5:
            errors.append(f"{point_id} 的 difficulty 必须是 1-5 的整数")

        estimated_minutes = point.get("estimated_minutes")
        if not isinstance(estimated_minutes, int) or estimated_minutes <= 0:
            errors.append(f"{point_id} 的 estimated_minutes 必须是正整数")

        tags = point.get("tags")
        if not isinstance(tags, list) or not tags:
            errors.append(f"{point_id} 的 tags 必须是非空数组")

        material_dir = materials_root / point_id
        if not material_dir.is_dir():
            errors.append(f"缺少素材目录: materials/{point_id}")
            continue
        has_supported_file = any(
            file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS
            for file in material_dir.rglob("*")
        )
        if not has_supported_file:
            errors.append(f"materials/{point_id} 中至少需要一份受支持的素材文件")

    for point_id, point in point_by_id.items():
        prerequisites = point.get("prerequisites", [])
        if isinstance(prerequisites, list):
            for prerequisite in prerequisites:
                if prerequisite not in point_by_id:
                    errors.append(f"{point_id} 引用了不存在的前置知识点: {prerequisite}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node_id: str, path: list[str]) -> None:
        if node_id in visiting:
            cycle = " -> ".join(path + [node_id])
            errors.append(f"检测到循环依赖: {cycle}")
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        path.append(node_id)
        prerequisites = point_by_id[node_id].get("prerequisites", [])
        if isinstance(prerequisites, list):
            for prerequisite in prerequisites:
                if prerequisite in point_by_id:
                    dfs(prerequisite, path)
        path.pop()
        visiting.remove(node_id)
        visited.add(node_id)

    for point_id in ids:
        dfs(point_id, [])

    if not any(
        isinstance(point_by_id[point_id].get("prerequisites", []), list)
        and not point_by_id[point_id].get("prerequisites", [])
        for point_id in ids
    ):
        errors.append("至少需要一个入口知识点（prerequisites 为空数组）")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent
    errors = collect_errors(root)
    if errors:
        print("校验失败:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())