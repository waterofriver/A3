from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "course"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _copy_tree(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            source_stat = path.stat()
            target_stat = target.stat()
            if (
                source_stat.st_size == target_stat.st_size
                and int(target_stat.st_mtime) >= int(source_stat.st_mtime)
            ):
                continue
        shutil.copy2(path, target)


def sync_knowledge_base(source_root: Path, course_root: Path) -> Path | None:
    source_root = source_root.resolve()
    dag_path = source_root / "knowledge_dag.json"
    if not dag_path.is_file():
        return None

    with dag_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    course_name = str(data.get("course_name", "")).strip()
    course_slug = str(data.get("course_slug", "")).strip() or slugify(course_name)
    if not course_name:
        raise ValueError("knowledge_dag.json 缺少 course_name")

    knowledge_points = data.get("knowledge_points")
    if not isinstance(knowledge_points, list) or not knowledge_points:
        raise ValueError("knowledge_dag.json 缺少 knowledge_points")

    materials_root = source_root / "materials"
    destination_root = course_root.resolve() / course_slug
    destination_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        destination_root / "course.json",
        {
            "name": course_name,
            "slug": course_slug,
        },
    )

    for point in knowledge_points:
        if not isinstance(point, dict):
            continue
        point_id = str(point.get("id", "")).strip()
        if not point_id:
            raise ValueError("knowledge_points 中存在空 id")
        source_dir = materials_root / point_id
        if not source_dir.is_dir():
            raise ValueError(f"缺少素材目录: materials/{point_id}")
        _copy_tree(source_dir, destination_root / point_id)

    return destination_root