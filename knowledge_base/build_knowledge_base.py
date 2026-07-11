from __future__ import annotations

import json
import mimetypes
from pathlib import Path


SUPPORTED_PREVIEWABLE_EXTENSIONS = {
    ".docx",
    ".md",
    ".pdf",
    ".pptx",
    ".txt",
    ".py",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def classify_resource(file_path: Path) -> str:
    extension = file_path.suffix.lower()
    if extension in {".docx", ".md", ".pdf", ".pptx", ".txt"}:
        return "lecture"
    if extension in {".py", ".sh", ".ps1", ".js", ".ts"}:
        return "code"
    if extension in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    if extension in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        return "image"
    if extension in {".zip", ".rar", ".7z"}:
        return "archive"
    guessed_type, _ = mimetypes.guess_type(file_path.name)
    if guessed_type and guessed_type.startswith("image/"):
        return "image"
    if guessed_type and guessed_type.startswith("video/"):
        return "video"
    return "supplementary"


def build_metadata(root: Path) -> list[dict]:
    dag = load_json(root / "knowledge_dag.json")
    points = dag.get("knowledge_points", [])
    materials_root = root / "materials"
    resource_index: list[dict] = []

    for point in points:
        if not isinstance(point, dict):
            continue
        point_id = str(point.get("id", "")).strip()
        if not point_id:
            continue

        point_dir = materials_root / point_id
        if not point_dir.is_dir():
            continue

        file_entries: list[dict] = []
        for file_path in sorted(p for p in point_dir.rglob("*") if p.is_file()):
            relative_path = file_path.relative_to(point_dir).as_posix()
            extension = file_path.suffix.lower()
            previewable = extension in SUPPORTED_PREVIEWABLE_EXTENSIONS
            file_entry = {
                "name": file_path.name,
                "path": relative_path,
                "file_type": extension.removeprefix("."),
                "resource_type": classify_resource(file_path),
                "previewable": previewable,
                "retrievable": True,
                "size_bytes": file_path.stat().st_size,
            }
            file_entries.append(file_entry)
            resource_index.append(
                {
                    "resource_id": f"{point_id}:{relative_path}",
                    "title": file_path.stem,
                    "path": f"materials/{point_id}/{relative_path}",
                    "file_type": extension.removeprefix("."),
                    "resource_type": classify_resource(file_path),
                    "knowledge_point_id": point_id,
                    "retrievable": True,
                    "previewable": previewable,
                    "is_core": point_id != "shared_references",
                }
            )

        metadata = {
            "id": point_id,
            "name": point.get("name", point_id),
            "description": point.get("description", ""),
            "category": point.get("category", ""),
            "keywords": point.get("tags", []),
            "files": file_entries,
        }
        dump_json(point_dir / "metadata.json", metadata)

    dump_json(root / "resource_index.json", resource_index)
    return resource_index


def main() -> int:
    root = Path(__file__).resolve().parent
    build_metadata(root)
    print("知识库元数据已生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())