import importlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest


def test_course_indexer_builds_chapter_tree_from_real_files(client, tmp_path):
    module = importlib.import_module("app.services.course_indexer")
    course_root = tmp_path / "catalog"
    course = course_root / "ros2"
    chapter = course / "01-basics"
    chapter.mkdir(parents=True)
    (course / "course.json").write_text(
        json.dumps({"name": "机器人操作系统", "slug": "ros2"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (chapter / "intro.md").write_text("# ROS2 基础", encoding="utf-8")

    result = module.CourseIndexer(client.app.state.db).index_root(course_root)

    assert result[0].name == "机器人操作系统"
    assert result[0].content_ready is True
    assert result[0].chapters[0].documents[0].filename == "intro.md"
    assert result[0].chapters[0].documents[0].preview_text == "# ROS2 基础"


def test_course_indexer_uses_metadata_name_and_hides_metadata_file(client, tmp_path):
    module = importlib.import_module("app.services.course_indexer")
    course_root = tmp_path / "catalog"
    chapter = course_root / "robot-safety" / "exp02_robot_remote_control"
    chapter.mkdir(parents=True)
    (course_root / "robot-safety" / "course.json").write_text(
        json.dumps({"name": "机器人与安全", "slug": "robot-safety"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (chapter / "metadata.json").write_text(
        json.dumps({"name": "实验二 机器人远程控制"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (chapter / "guide.md").write_text("# 实验二", encoding="utf-8")

    result = module.CourseIndexer(client.app.state.db).index_root(course_root)

    chapter_data = result[0].chapters[0]
    assert chapter_data.name == "实验二 机器人远程控制"
    assert [document.filename for document in chapter_data.documents] == ["guide.md"]


def test_resolve_under_rejects_path_traversal(tmp_path):
    module = importlib.import_module("app.services.course_indexer")
    root = tmp_path / "course"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError, match="课程根目录"):
        module.resolve_under(root, Path("..") / "secret.txt")


def test_pptx_preview_uses_text_layer_without_image_dependencies(tmp_path):
    module = importlib.import_module("app.services.course_indexer")
    presentation = tmp_path / "lesson.pptx"
    slide_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
      <p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>ROS2 通信模型</a:t></a:r></a:p>
      </p:txBody></p:sp></p:spTree></p:cSld>
    </p:sld>"""
    with ZipFile(presentation, "w", ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)

    assert module.extract_preview(presentation, ".pptx") == "ROS2 通信模型"


def test_broken_pdf_keeps_real_file_without_fabricating_preview(client, tmp_path):
    module = importlib.import_module("app.services.course_indexer")
    course_root = tmp_path / "catalog"
    course = course_root / "systems"
    course.mkdir(parents=True)
    (course / "course.json").write_text(
        json.dumps({"name": "系统课程", "slug": "systems"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (course / "broken.pdf").write_bytes(b"not-a-pdf")

    result = module.CourseIndexer(client.app.state.db).index_root(course_root)

    document = result[0].chapters[0].documents[0]
    assert document.filename == "broken.pdf"
    assert document.preview_text is None
    assert document.media_url == "/media/courses/systems/broken.pdf"
