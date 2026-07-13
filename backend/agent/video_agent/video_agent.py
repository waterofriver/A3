# -*- coding: utf-8 -*-
"""
视频推送 Agent (Video Agent)
============================
根据学生画像、学习进度和课件材料，判断当前应该推送哪个知识点的演示视频，
并生成个性化视频导览脚本（分镜描述 + 学习要点）。

设计原则：
- 素材驱动：从 A3 知识库中读取已有的 MP4 演示视频，不生成新视频
- 智能推送：根据学生薄弱环节、学习路径和画像判断推送时机和内容
- 脚本增强：基于课件材料生成视频导览脚本，告诉学生每个阶段在看什么
- 同步和异步两套 API

用法示例::

    from video_agent import VideoAgent
    from utils.material_loader import MaterialLoader

    loader = MaterialLoader("A3/knowledge_base")
    agent = VideoAgent()

    # 为指定知识点生成视频推送
    result = agent.generate(knowledge_point, student_profile, loader)
    if result.success:
        print(result.push_reason)          # 推送理由
        print(result.resource.content.scenes)  # 视频导览脚本
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Config
from ..utils import LLMClient, LLMResponse, get_client
from ..utils.json_parser import extract_json
from ..models import (
    StudentProfile,
    KnowledgePoint,
    VideoScene,
    VideoScriptContent,
    ResourceMetadata,
    ResourceOutput,
    ResourceType,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class VideoResult:
    """视频推送的返回结果。"""

    resource: Optional[ResourceOutput] = None
    """生成的资源（含 metadata 和 VideoScriptContent）；失败或无视频时为 None"""

    success: bool = True
    """处理是否成功"""

    error: Optional[str] = None
    """失败时的错误信息"""

    has_video: bool = False
    """该知识点是否有 MP4 视频文件"""

    video_path: Optional[str] = None
    """MP4 文件的绝对路径（供前端播放）"""

    video_duration_seconds: int = 0
    """视频时长（秒），通过 ffprobe 获取"""

    push_reason: str = ""
    """推送理由：为什么此时推荐这个视频"""

    reasoning_content: Optional[str] = None
    """deepseek-reasoner 思维链"""

    warnings: list[str] = field(default_factory=list)
    """非致命警告"""


# ═══════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """
你是一位课程视频导览员，负责为学生生成实验演示视频的导览脚本。你的任务是根据知识点信息、学生画像和课件材料，输出一份结构化的视频分镜导览。

## 你的职责

1. **概述视频内容**：根据课件材料描述这个视频主要演示了什么实验
2. **分阶段导览**：将视频内容拆分为 3-6 个关键阶段/分镜，每个分镜说明：
   - 这个阶段演示了什么（画面描述）
   - 学生应该关注什么（旁白/解说要点）
3. **个性化提示**：根据学生画像给出针对性的观看建议

## 分镜设计原则

- 第 1 个分镜：实验准备/环境搭建阶段
- 中间分镜：核心操作/关键步骤演示
- 最后 1 个分镜：实验结果/总结回顾
- 每个分镜的 narration 是给学生看的"导览提示"，20-80 字
- 每个分镜的 visual_description 描述视频画面内容
- 每个分镜估算 duration_seconds（15-90 秒）

## 输出格式

严格按照以下 JSON 格式输出，放在 ```json 代码块中。

```json
{
    "push_reason": "推荐理由：为什么建议学生此时观看这个视频（结合画像说明，50-120字）",
    "target_audience": "目标受众描述（结合学生画像，如：机器人工程大三学生，已掌握ROS基础）",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "导览旁白：这个阶段你应该注意...",
            "visual_description": "画面描述：视频此时正在演示...",
            "duration_seconds": 30
        },
        {
            "scene_number": 2,
            "narration": "...",
            "visual_description": "...",
            "duration_seconds": 45
        }
    ],
    "watch_focus": ["观看重点1：关注xxx操作", "观看重点2：注意xxx配置", "观看重点3：理解xxx原理"],
    "after_watching": "看完后建议做什么（如：动手复现实验、做配套练习题）"
}
```

## 课件依据

如果提供了课件参考材料，你的 scene 描述必须：
- 与课件中的实验步骤对应
- 使用课件中的术语和命令
- 分镜顺序与课件中的操作顺序一致
""".strip()


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _get_video_duration(file_path: str | Path) -> int:
    """用 ffprobe 获取 MP4 视频时长（秒）。

    失败时返回 0（前端将不显示时长）。
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(file_path),
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(float(result.stdout.strip()))
    except Exception as e:
        logger.warning(f"获取视频时长失败: {e}")
    return 0


def _find_mp4(materials_dir: Path, kp_id: str) -> Optional[Path]:
    """在知识点素材目录中查找 MP4 文件。

    优先选择不带"新_"前缀的版本（更稳定），
    如果只有一个文件则直接返回。
    """
    kp_dir = materials_dir / kp_id
    if not kp_dir.exists():
        return None

    mp4_files = list(kp_dir.glob("*.mp4"))
    if not mp4_files:
        return None

    # 优先选非"新_"版本
    stable = [f for f in mp4_files if not f.name.startswith("新_")]
    if stable:
        return stable[0]
    return mp4_files[0]


# ═══════════════════════════════════════════════════════════════
# VideoAgent
# ═══════════════════════════════════════════════════════════════

class VideoAgent:
    """视频推送 Agent。

    根据学生画像和学习进度，判断是否推送知识点演示视频，
    并生成个性化视频导览脚本。

    用法::

        from video_agent import VideoAgent
        from utils.material_loader import MaterialLoader

        loader = MaterialLoader("A3/knowledge_base")
        agent = VideoAgent()
        result = agent.generate(knowledge_point, student_profile, loader)

    参数:
        client: LLM 客户端（注入 Mock 用于测试）
        model: 覆盖默认模型
        temperature: LLM 温度，默认 0.3
        max_tokens: 最大输出 token 数，默认 4096
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self._client = client or get_client()
        self._model = model or Config.DEEPSEEK_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens

    # ── 公开 API ──────────────────────────────────────────

    def generate(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
        materials_dir: Optional[str | Path] = None,
    ) -> VideoResult:
        """同步生成视频推送。

        参数:
            knowledge_point: 目标知识点
            student_profile: 学生画像
            material_context: 从课件材料中提取的参考文本（由 MaterialLoader 提供）
            materials_dir: A3/knowledge_base/materials 目录路径，用于查找 MP4

        返回:
            VideoResult: 包含推送理由、视频路径和导览脚本
        """
        return self._generate_impl(
            knowledge_point, student_profile, material_context, materials_dir
        )

    async def generate_async(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile] = None,
        material_context: str = "",
        materials_dir: Optional[str | Path] = None,
    ) -> VideoResult:
        """异步生成视频推送。签名与 generate 一致。"""
        from ..utils import AsyncLLMClient, get_async_client

        client = get_async_client()
        return await self._generate_impl_async(
            client, knowledge_point, student_profile, material_context, materials_dir
        )

    # ── 视频发现 ──────────────────────────────────────────

    def has_video(self, knowledge_point: KnowledgePoint, materials_dir: str | Path) -> bool:
        """检查知识点是否有对应的 MP4 视频。"""
        mp4 = _find_mp4(Path(materials_dir), knowledge_point.id)
        return mp4 is not None

    # ── 内部实现 ──────────────────────────────────────────

    def _generate_impl(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str,
        materials_dir: Optional[str | Path],
    ) -> VideoResult:
        """同步生成的核心实现。"""

        if not knowledge_point.name:
            return VideoResult(success=False, error="知识点名称为空")

        # ── 1. 查找 MP4 ──
        mp4_path: Optional[Path] = None
        duration = 0

        if materials_dir:
            mp4_path = _find_mp4(Path(materials_dir), knowledge_point.id)
            if mp4_path:
                duration = _get_video_duration(mp4_path)

        if mp4_path is None:
            logger.info(f"知识点 {knowledge_point.id} 无 MP4 视频")
            return VideoResult(
                success=True,
                has_video=False,
                error=None,
            )

        # ── 2. 调用 LLM 生成导览脚本 ──
        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, material_context, duration
        )
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"VideoAgent.generate | model={self._model} | "
            f"kp={knowledge_point.id} | video={mp4_path.name} | "
            f"duration={duration}s"
        )

        response = self._client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(
            response, knowledge_point, student_profile,
            mp4_path, duration,
        )

    async def _generate_impl_async(
        self,
        client,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str,
        materials_dir: Optional[str | Path],
    ) -> VideoResult:
        """异步生成的核心实现。"""

        if not knowledge_point.name:
            return VideoResult(success=False, error="知识点名称为空")

        mp4_path: Optional[Path] = None
        duration = 0
        if materials_dir:
            mp4_path = _find_mp4(Path(materials_dir), knowledge_point.id)
            if mp4_path:
                duration = _get_video_duration(mp4_path)

        if mp4_path is None:
            return VideoResult(success=True, has_video=False)

        system_prompt = self._build_system_prompt(
            knowledge_point, student_profile, material_context, duration
        )
        user_message = self._build_user_message(knowledge_point, student_profile)

        logger.info(
            f"VideoAgent.generate_async | kp={knowledge_point.id} | "
            f"video={mp4_path.name}"
        )

        response = await client.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            model=self._model,
        )

        return self._handle_response(
            response, knowledge_point, student_profile,
            mp4_path, duration,
        )

    def _handle_response(
        self,
        response: LLMResponse,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        mp4_path: Path,
        duration: int,
    ) -> VideoResult:
        """统一处理 LLM 响应：解析 JSON → 构建 VideoScriptContent → 包装 ResourceOutput。"""

        if not response.success:
            logger.error(f"LLM 调用失败: {response.error}")
            return VideoResult(
                success=False,
                has_video=True,
                video_path=str(mp4_path),
                video_duration_seconds=duration,
                error=response.error or "LLM 调用失败",
            )

        parsed, json_error = extract_json(response.content)
        warnings: list[str] = []

        if parsed is None:
            logger.warning(f"JSON 解析失败: {json_error}")
            # 降级：没有脚本也能推送视频
            warnings.append(f"视频脚本生成失败（{json_error}），视频本身仍可推送")
            parsed = {}

        # ── 提取字段 ──
        push_reason = parsed.get("push_reason", f"推荐观看「{knowledge_point.name}」的演示视频")
        target_audience = parsed.get("target_audience", "")
        raw_scenes = parsed.get("scenes") or []
        watch_focus = parsed.get("watch_focus") or []
        after_watching = parsed.get("after_watching") or ""

        # ── 构建分镜 ──
        scenes: list[VideoScene] = []
        for scene_data in raw_scenes:
            try:
                scene = VideoScene(
                    scene_number=int(scene_data.get("scene_number", len(scenes) + 1)),
                    narration=str(scene_data.get("narration", "")).strip(),
                    visual_description=str(scene_data.get("visual_description", "")).strip(),
                    duration_seconds=int(scene_data.get("duration_seconds", 30)),
                )
                if scene.narration or scene.visual_description:
                    scenes.append(scene)
            except Exception as e:
                warnings.append(f"分镜 {scene_data.get('scene_number', '?')} 无效: {e}")

        # ── 无分镜时生成兜底 ──
        if not scenes:
            scenes = [
                VideoScene(
                    scene_number=1,
                    narration=f"请观看「{knowledge_point.name}」的演示视频",
                    visual_description=f"视频演示了{knowledge_point.name}的实验全流程",
                    duration_seconds=max(30, duration // 2),
                ),
                VideoScene(
                    scene_number=2,
                    narration="请注意实验中的关键步骤和操作细节",
                    visual_description="视频中的关键操作特写和注意事项",
                    duration_seconds=max(30, duration // 2),
                ),
            ]
            warnings.append("LLM 未返回有效分镜，已使用默认导览脚本")

        # ── 视频标题 ──
        video_title = f"{knowledge_point.name} — 演示视频"

        # ── 构建 VideoScriptContent ──
        video_content = VideoScriptContent(
            title=video_title,
            total_duration_seconds=duration,
            target_audience=target_audience,
            scenes=scenes,
        )

        # ── 注入观看重点到 target_audience 的补充字段 ──
        if watch_focus:
            focus_text = " | 观看重点: " + "; ".join(watch_focus)
            video_content.target_audience = (target_audience or "") + focus_text

        # ── 构建 ResourceMetadata ──
        profile_snapshot = ""
        if student_profile is not None:
            profile_snapshot = student_profile.snapshot()

        metadata = ResourceMetadata(
            resource_type=ResourceType.VIDEO_SCRIPT,
            knowledge_point_id=knowledge_point.id,
            knowledge_point_name=knowledge_point.name,
            title=video_title,
            difficulty=knowledge_point.difficulty,
            estimated_read_time_minutes=max(1, duration // 60),
            tags=knowledge_point.tags + (watch_focus[:2] if watch_focus else []),
            student_profile_snapshot=profile_snapshot,
        )

        # ── 组装 ResourceOutput ──
        resource = ResourceOutput(
            metadata=metadata,
            content=video_content,
            status="generated",
            generated_by="VideoAgent",
        )

        logger.info(
            f"VideoAgent 结果 | kp={knowledge_point.id} | "
            f"scenes={len(scenes)} | duration={duration}s | "
            f"warnings={len(warnings)}"
        )

        return VideoResult(
            resource=resource,
            success=True,
            has_video=True,
            video_path=str(mp4_path.resolve()),
            video_duration_seconds=duration,
            push_reason=push_reason,
            reasoning_content=response.reasoning_content,
            warnings=warnings,
        )

    # ── System Prompt 构建 ────────────────────────────────

    def _build_system_prompt(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
        material_context: str,
        duration: int,
    ) -> str:
        """构建 System Prompt。"""
        prompt = _SYSTEM_PROMPT

        prompt += f"""

## 当前知识点

- 名称: {knowledge_point.name}
- 描述: {knowledge_point.description or '暂无描述'}
- 分类: {knowledge_point.category or '未分类'}
- 难度: {knowledge_point.difficulty}/5
- 视频时长: {duration} 秒（约 {duration // 60} 分 {duration % 60} 秒）

请根据以上视频时长合理分配各分镜的 duration_seconds，所有分镜时长之和应接近 {duration} 秒。
"""

        if student_profile is not None:
            snapshot = student_profile.snapshot()
            if snapshot.strip():
                prompt += f"""
## 学生画像

{snapshot}

请根据画像生成个性化推送理由和观看建议。
"""
        else:
            prompt += "\n## 学生画像\n\n未提供，请使用通用风格。\n"

        if material_context and material_context.strip():
            ctx = material_context.strip()
            if len(ctx) > 10000:
                ctx = ctx[:10000] + "\n\n...(截断)"
            prompt += f"\n{ctx}\n"

        return prompt

    def _build_user_message(
        self,
        knowledge_point: KnowledgePoint,
        student_profile: Optional[StudentProfile],
    ) -> str:
        """构建 user message。"""
        parts = [f"请为「{knowledge_point.name}」的演示视频生成导览脚本。"]

        if student_profile is not None:
            if student_profile.weak_points:
                wp_names = [w.knowledge_point_name for w in student_profile.weak_points]
                if knowledge_point.name in wp_names or any(
                    w.knowledge_point_id == knowledge_point.id
                    for w in student_profile.weak_points
                ):
                    parts.append("这是学生的薄弱环节，请在推送理由中说明视频如何帮助克服这个薄弱点。")
            if student_profile.learning_goal_short:
                parts.append(f"学生短期目标: {student_profile.learning_goal_short}。")

        parts.append("请确保分镜的 duration_seconds 之和接近视频总时长。")
        return " ".join(parts)
