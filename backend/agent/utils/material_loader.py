# -*- coding: utf-8 -*-
"""
课件材料加载器 (Material Loader)
================================
从 A3/knowledge_base/materials/ 中读取课件文件（PDF/DOCX/PPTX/TXT），
提取文本内容作为 Agent 生成讲义和思维导图的参考素材。

用法::

    from utils.material_loader import MaterialLoader

    loader = MaterialLoader("A3/knowledge_base")
    dag = loader.load_dag()
    context = loader.get_context("exp05_arp_poisoning", max_chars=8000)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from ..models import KnowledgeDAG, KnowledgePoint

logger = logging.getLogger(__name__)

# ── 支持的文本文件扩展名 ──
_TEXT_EXTENSIONS = {".txt", ".md", ".py", ".cpp", ".c", ".h", ".sh", ".yaml", ".yml", ".json", ".xml"}


class MaterialLoader:
    """课件材料加载器。

    负责：
    1. 加载 A3 知识库 DAG
    2. 根据知识点 ID 读取 metadata.json，获取素材文件列表
    3. 从 PDF/DOCX/PPTX/TXT 中提取文本内容
    4. 拼接为 LLM 可用的参考上下文

    参数:
        knowledge_base_dir: A3/knowledge_base 目录的路径
    """

    def __init__(self, knowledge_base_dir: str | Path):
        self._root = Path(knowledge_base_dir).resolve()
        self._dag_path = self._root / "knowledge_dag.json"
        self._materials_dir = self._root / "materials"

        if not self._dag_path.exists():
            raise FileNotFoundError(f"知识 DAG 文件不存在: {self._dag_path}")
        if not self._materials_dir.exists():
            raise FileNotFoundError(f"素材目录不存在: {self._materials_dir}")

    # ── DAG 加载 ──────────────────────────────────────────

    def load_dag(self) -> KnowledgeDAG:
        """加载 A3 知识库的 DAG。

        与 agent/utils/dag_loader.py 不同，此方法直接处理 A3 格式的 DAG：
        - A3 的 DAG 包含 course_slug 字段（agent 的 DAG 不含）
        - 自动兼容两种格式
        """
        with open(self._dag_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return KnowledgeDAG.model_validate(data)

    # ── 素材获取 ──────────────────────────────────────────

    def get_materials(self, kp_id: str) -> list[dict]:
        """获取指定知识点的素材文件列表。

        返回: [{"name": ..., "path": ..., "file_type": ..., "resource_type": ...}, ...]
        """
        metadata_path = self._materials_dir / kp_id / "metadata.json"
        if not metadata_path.exists():
            logger.warning(f"知识点 {kp_id} 缺少 metadata.json")
            return []

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            return meta.get("files", [])
        except Exception as e:
            logger.warning(f"读取 metadata.json 失败 ({kp_id}): {e}")
            return []

    def _get_retrievable_files(self, kp_id: str) -> list[Path]:
        """获取可提取文本的素材文件绝对路径（排除 metadata.json 和视频）。"""
        materials = self.get_materials(kp_id)
        files = []
        for m in materials:
            if not m.get("retrievable", True):
                continue
            file_type = m.get("file_type", "")
            if file_type in ("mp4", "json", "png", "jpg", "jpeg", "gif"):
                continue
            file_path = self._materials_dir / kp_id / m.get("path", "")
            if file_path.exists():
                files.append(file_path)
        return files

    # ── 文本提取 ──────────────────────────────────────────

    def extract_text(self, file_path: Path, max_chars: int = 16000) -> str:
        """从单个文件中提取文本，超过 max_chars 则截断。

        支持: PDF (PyMuPDF), DOCX (python-docx), PPTX (python-pptx), TXT/MD/PY 等纯文本
        """
        suffix = file_path.suffix.lower()

        try:
            if suffix == ".pdf":
                return self._extract_pdf(file_path, max_chars)
            elif suffix == ".docx":
                return self._extract_docx(file_path, max_chars)
            elif suffix == ".pptx":
                return self._extract_pptx(file_path, max_chars)
            elif suffix in _TEXT_EXTENSIONS:
                return self._extract_text_file(file_path, max_chars)
            else:
                logger.info(f"不支持的文件类型: {suffix} ({file_path.name})")
                return ""
        except Exception as e:
            logger.warning(f"提取文本失败 ({file_path.name}): {e}")
            return ""

    def _extract_pdf(self, path: Path, max_chars: int) -> str:
        """用 PyMuPDF 提取 PDF 文本，不可用时回退到 pypdf。"""
        # 优先 PyMuPDF（速度最快）
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            parts = []
            total = 0
            for page in doc:
                text = page.get_text()
                if total + len(text) > max_chars:
                    remaining = max_chars - total
                    if remaining > 0:
                        parts.append(text[:remaining])
                    break
                parts.append(text)
                total += len(text)
            doc.close()
            return "\n\n".join(parts).strip()
        except ImportError:
            pass

        # 回退到 pypdf（纯 Python，不依赖系统库）
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            parts = []
            total = 0
            for page in reader.pages[:50]:  # 最多 50 页
                text = page.extract_text() or ""
                if total + len(text) > max_chars:
                    remaining = max_chars - total
                    if remaining > 0:
                        parts.append(text[:remaining])
                    break
                parts.append(text)
                total += len(text)
            return "\n\n".join(parts).strip()
        except ImportError:
            logger.warning("未安装 PDF 提取库（PyMuPDF 或 pypdf），无法提取 PDF 文本")
            return ""

    def _extract_docx(self, path: Path, max_chars: int) -> str:
        """用 python-docx 提取 DOCX 文本。"""
        from docx import Document
        doc = Document(str(path))
        parts = []
        total = 0
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                parts.append("")  # 保留段落分隔
                continue
            if total + len(text) > max_chars:
                remaining = max_chars - total
                if remaining > 0:
                    parts.append(text[:remaining])
                break
            parts.append(text)
            total += len(text)
        return "\n".join(parts).strip()

    def _extract_pptx(self, path: Path, max_chars: int) -> str:
        """用 python-pptx 提取 PPTX 文本（幻灯片标题+内容）。"""
        from pptx import Presentation
        prs = Presentation(str(path))
        parts = []
        total = 0
        for i, slide in enumerate(prs.slides):
            slide_parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            slide_parts.append(text)
            if slide_parts:
                slide_text = f"【幻灯片 {i+1}】\n" + "\n".join(slide_parts)
                if total + len(slide_text) > max_chars:
                    remaining = max_chars - total
                    if remaining > 100:
                        parts.append(slide_text[:remaining] + "\n...(截断)")
                    break
                parts.append(slide_text)
                total += len(slide_text)
        return "\n\n".join(parts).strip()

    def _extract_text_file(self, path: Path, max_chars: int) -> str:
        """读取纯文本文件（自动检测编码）。"""
        text = ""
        # 按优先级尝试常见编码
        for encoding in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                text = path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if not text:
            text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + "\n...(截断)"
        return text.strip()

    # ── 上下文构建 ────────────────────────────────────────

    def get_context(
        self,
        kp_id: str,
        max_chars: int = 12000,
        per_file_max: int = 8000,
    ) -> str:
        """获取知识点所有素材的文本拼接，作为 LLM 生成的参考上下文。

        参数:
            kp_id: 知识点 ID
            max_chars: 总上下文最大字符数
            per_file_max: 每个文件最多提取的字符数

        返回:
            拼接后的参考文本（Markdown 格式），供注入 System Prompt
        """
        files = self._get_retrievable_files(kp_id)
        if not files:
            logger.info(f"知识点 {kp_id} 无可提取文本的素材文件")
            return ""

        parts = []
        total = 0

        for file_path in files:
            file_name = file_path.name
            # 跳过 metadata.json
            if file_path.name == "metadata.json":
                continue

            text = self.extract_text(file_path, max_chars=per_file_max)
            if not text.strip():
                continue

            if total + len(text) > max_chars:
                remaining = max_chars - total
                if remaining > 200:
                    parts.append(
                        f"### 📄 {file_name}\n\n{text[:remaining]}\n\n...(内容截断)"
                    )
                break

            parts.append(f"### 📄 {file_name}\n\n{text}")
            total += len(text)

        if not parts:
            return ""

        header = "## 课件参考资料\n\n以下内容提取自课程原始课件，请基于这些材料生成内容，确保知识点和术语与课件一致：\n\n"
        return header + "\n\n".join(parts)

    def list_knowledge_points(self) -> list[dict]:
        """列出所有知识点的基本信息（id, name, category, has_materials）。"""
        dag = self.load_dag()
        result = []
        for kp in dag.knowledge_points:
            mat_count = len(self._get_retrievable_files(kp.id))
            result.append({
                "id": kp.id,
                "name": kp.name,
                "category": kp.category,
                "difficulty": kp.difficulty,
                "material_count": mat_count,
            })
        return result

    # ── 拓展阅读（shared_references）──────────────────────

    def get_shared_references(self) -> list[dict]:
        """获取 shared_references 中的所有课外阅读材料信息。

        返回: [{"name": "书名", "path": "文件路径", "file_type": "pdf/docx", "size_bytes": 123}, ...]
        """
        refs = self._get_retrievable_files("shared_references")
        result = []
        for file_path in refs:
            result.append({
                "name": file_path.stem,
                "path": str(file_path),
                "file_type": file_path.suffix.lower().lstrip("."),
                "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            })
        return result

    def get_shared_references_summary(self) -> str:
        """获取 shared_references 中材料的文本摘要，用于注入 Agent System Prompt。

        对每本书提取标题和目录/前几页内容，帮助 LLM 了解每本书的覆盖范围。
        """
        refs = self._get_retrievable_files("shared_references")
        if not refs:
            return ""

        parts = ["## 课程拓展阅读库\n\n以下为课程提供的课外阅读材料：\n"]
        for i, file_path in enumerate(refs):
            name = file_path.stem
            file_type = file_path.suffix.lower().lstrip(".")
            # 提取前 1500 字符作为内容摘要
            text = self.extract_text(file_path, max_chars=1500)
            summary = text[:300].replace("\n", " ") if text else "（无法提取摘要）"
            parts.append(
                f"### {i+1}. {name}\n"
                f"- 格式: {file_type}\n"
                f"- 内容摘要: {summary}...\n"
            )

        return "\n".join(parts)
