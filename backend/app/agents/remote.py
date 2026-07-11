import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from httpx_sse import SSEError, aconnect_sse
from pydantic import TypeAdapter, ValidationError

from app.agents.base import AgentProvider, ResourceAgentEvent, ResourceDraft
from app.agents.mock import MockAgentProvider
from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.evaluation import EvaluationDraft, EvaluationEvidence
from app.schemas.learning import LearningPathDraft
from app.schemas.profile import StudentProfileData
from app.schemas.qa import AnswerMode
from app.schemas.resource import ResourceDetail, ResourceSummary, ResourceType
from app.schemas.task import GatewayError, GatewayEvent

resource_type_adapter = TypeAdapter(ResourceType)
resource_detail_adapter = TypeAdapter(ResourceDetail)


def upstream_rejected(message: str, *, details: Any | None = None) -> AppError:
    return AppError(
        status_code=503,
        code="UPSTREAM_REJECTED",
        message=message,
        retryable=False,
        details=details,
    )


def require_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise upstream_rejected(f"上游事件缺少有效字段：{key}。")
    return value


def optional_string(payload: dict, key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise upstream_rejected(f"上游事件字段类型无效：{key}。")
    return value


def event_progress(payload: dict, default: int, *, maximum: int = 100) -> int:
    value = payload.get("progress", default)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise upstream_rejected("上游事件 progress 必须是有效百分比。")
    return value


def event_resource_type(payload: dict, fallback: ResourceType | None = None) -> ResourceType:
    value = payload.get("resource_type", fallback)
    try:
        return resource_type_adapter.validate_python(value)
    except ValidationError as error:
        raise upstream_rejected("上游事件 resource_type 无效。", details=str(error)) from error


def declared_upstream_error(payload: dict) -> AppError:
    error = payload.get("error")
    if not isinstance(error, dict):
        error = payload
    code = error.get("code") if isinstance(error.get("code"), str) else "UPSTREAM_REJECTED"
    message = (
        error.get("message")
        if isinstance(error.get("message"), str)
        else "上游 Agent 返回失败事件。"
    )
    return AppError(
        status_code=503,
        code=code,
        message=message,
        retryable=bool(error.get("retryable", True)),
        details=error.get("details"),
    )


class RemoteAgentProvider(AgentProvider):
    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ):
        self.settings = settings
        self._headers = (
            {"Authorization": f"Bearer {settings.remote_agent_api_key}"}
            if settings.remote_agent_api_key
            else {}
        )
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=settings.remote_agent_base_url.rstrip("/"),
            timeout=settings.remote_agent_timeout_seconds,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def _iter_sse(self, path: str, payload: dict) -> AsyncIterator[dict]:
        try:
            async with aconnect_sse(
                self.client,
                "POST",
                path,
                headers=self._headers,
                json=payload,
            ) as source:
                source.response.raise_for_status()
                async for event in source.aiter_sse():
                    if not event.data:
                        continue
                    try:
                        data = json.loads(event.data)
                    except json.JSONDecodeError as error:
                        raise upstream_rejected(
                            "上游 Agent 返回了无效 SSE JSON。"
                        ) from error
                    if not isinstance(data, dict):
                        raise upstream_rejected("上游 SSE 数据必须是 JSON 对象。")
                    if "type" not in data and event.event:
                        data["type"] = event.event
                    yield data
        except AppError:
            raise
        except httpx.TimeoutException as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_TIMEOUT",
                message="远程 Agent 服务响应超时。",
                retryable=True,
            ) from error
        except httpx.HTTPStatusError as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_REJECTED",
                message=f"远程 Agent 服务返回 HTTP {error.response.status_code}。",
                retryable=error.response.status_code >= 500,
            ) from error
        except (httpx.HTTPError, SSEError) as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_UNAVAILABLE",
                message="无法连接远程 Agent 服务。",
                retryable=True,
            ) from error

    async def _post_json(self, path: str, payload: dict) -> Any:
        try:
            response = await self.client.post(path, headers=self._headers, json=payload)
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_TIMEOUT",
                message="远程 Agent 服务响应超时。",
                retryable=True,
            ) from error
        except httpx.HTTPStatusError as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_REJECTED",
                message=f"远程 Agent 服务返回 HTTP {error.response.status_code}。",
                retryable=error.response.status_code >= 500,
            ) from error
        except httpx.HTTPError as error:
            raise AppError(
                status_code=503,
                code="UPSTREAM_UNAVAILABLE",
                message="无法连接远程 Agent 服务。",
                retryable=True,
            ) from error
        except (json.JSONDecodeError, ValueError) as error:
            raise upstream_rejected("远程 Agent 返回了无效 JSON。") from error
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body

    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        current_agent = "画像抽取Agent"
        progress = 0
        async for payload in self._iter_sse(
            self.settings.remote_profile_path,
            {
                "user_id": user_id,
                "chat_text": chat_text,
                "current_profile": current_profile.model_dump(mode="json")
                if current_profile
                else None,
            },
        ):
            event_type = payload.get("type")
            if event_type == "agent":
                current_agent = require_string(payload, "name")
                progress = event_progress(payload, 10)
                yield GatewayEvent(
                    event="agent.started",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            elif event_type == "delta":
                progress = event_progress(payload, progress)
                yield GatewayEvent(
                    event="content.delta",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                    content=require_string(payload, "text"),
                )
            elif event_type == "profile":
                try:
                    profile = StudentProfileData.model_validate(payload.get("profile"))
                except ValidationError as error:
                    raise upstream_rejected(
                        "上游返回的学生画像不符合六维契约。",
                        details=str(error),
                    ) from error
                progress = event_progress(payload, 85)
                yield GatewayEvent(
                    event="profile.patch",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                    profile_patch=profile.model_dump(mode="json"),
                )
            elif event_type == "progress":
                progress = event_progress(payload, progress)
                yield GatewayEvent(
                    event="task.progress",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            elif event_type == "done":
                yield GatewayEvent(
                    event="task.completed",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=100,
                    finish_flag=True,
                )
            elif event_type == "error":
                raise declared_upstream_error(payload)
            elif event_type == "heartbeat":
                yield GatewayEvent(
                    event="heartbeat",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            else:
                raise upstream_rejected(f"未知画像事件类型：{event_type!r}。")

    async def stream_resources(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        course_name: str,
        weak_point: str,
        resource_types: list[ResourceType],
    ) -> AsyncIterator[ResourceAgentEvent]:
        current_agent = "主管Agent"
        current_type = resource_types[0]
        progress = 0
        async for payload in self._iter_sse(
            self.settings.remote_resources_path,
            {
                "user_id": user_id,
                "course_name": course_name,
                "weak_point": weak_point,
                "resource_type_list": resource_types,
            },
        ):
            event_type = payload.get("type")
            if event_type == "done":
                continue
            if event_type == "error":
                raise declared_upstream_error(payload)
            current_type = event_resource_type(payload, current_type)
            if event_type == "agent":
                current_agent = require_string(payload, "name")
                progress = event_progress(payload, 10, maximum=99)
                yield ResourceAgentEvent(
                    event="agent.started",
                    current_agent=current_agent,
                    progress=progress,
                    resource_type=current_type,
                )
            elif event_type == "delta":
                current_agent = optional_string(payload, "name") or current_agent
                progress = event_progress(payload, progress, maximum=99)
                yield ResourceAgentEvent(
                    event="content.delta",
                    current_agent=current_agent,
                    progress=progress,
                    resource_type=current_type,
                    content=require_string(payload, "text"),
                )
            elif event_type == "progress":
                progress = event_progress(payload, progress, maximum=99)
                yield ResourceAgentEvent(
                    event="task.progress",
                    current_agent=current_agent,
                    progress=progress,
                    resource_type=current_type,
                )
            elif event_type == "resource":
                raw_resource = payload.get("resource")
                try:
                    draft = ResourceDraft.model_validate(raw_resource)
                    resource_detail_adapter.validate_python(
                        {
                            "id": "remote-contract-validation",
                            "resource_type": draft.resource_type,
                            "title": draft.title,
                            "payload": draft.payload,
                            "media_url": draft.media_url,
                        }
                    )
                except ValidationError as error:
                    raise upstream_rejected(
                        "上游资源不符合固定资源契约。", details=str(error)
                    ) from error
                if draft.resource_type != current_type:
                    raise upstream_rejected("资源事件与资源正文类型不一致。")
                current_agent = optional_string(payload, "name") or current_agent
                progress = event_progress(payload, 95, maximum=99)
                yield ResourceAgentEvent(
                    event="resource.ready",
                    current_agent=current_agent,
                    progress=progress,
                    resource_type=current_type,
                    resource=draft,
                )
            else:
                raise upstream_rejected(f"未知资源事件类型：{event_type!r}。")

    async def stream_qa(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        question: str,
        answer_mode: AnswerMode,
        profile: StudentProfileData,
    ) -> AsyncIterator[GatewayEvent]:
        current_agent = "智能答疑Agent"
        progress = 0
        async for payload in self._iter_sse(
            self.settings.remote_qa_path,
            {
                "user_id": user_id,
                "question": question,
                "answer_mode": answer_mode,
                "profile": profile.model_dump(mode="json"),
            },
        ):
            event_type = payload.get("type")
            if event_type == "agent":
                current_agent = require_string(payload, "name")
                progress = event_progress(payload, 10)
                yield GatewayEvent(
                    event="agent.started",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            elif event_type == "delta":
                progress = event_progress(payload, progress)
                yield GatewayEvent(
                    event="content.delta",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                    content=require_string(payload, "text"),
                )
            elif event_type == "media":
                kind = payload.get("kind")
                if kind not in {"image", "video"}:
                    raise upstream_rejected("上游媒体 kind 必须是 image 或 video。")
                progress = event_progress(payload, 88)
                yield GatewayEvent(
                    event="media.ready",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                    resource_type="video" if kind == "video" else None,
                    media_url=optional_string(payload, "url"),
                    content=optional_string(payload, "text") or "",
                )
            elif event_type == "progress":
                progress = event_progress(payload, progress)
                yield GatewayEvent(
                    event="task.progress",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            elif event_type == "done":
                yield GatewayEvent(
                    event="task.completed",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=100,
                    finish_flag=True,
                )
            elif event_type == "error":
                raise declared_upstream_error(payload)
            elif event_type == "heartbeat":
                yield GatewayEvent(
                    event="heartbeat",
                    task_id=task_id,
                    trace_id=trace_id,
                    current_agent=current_agent,
                    progress=progress,
                )
            else:
                raise upstream_rejected(f"未知答疑事件类型：{event_type!r}。")

    async def build_learning_path(
        self,
        *,
        user_id: str,
        course_name: str,
        profile: StudentProfileData,
        resources: list[ResourceSummary],
    ) -> LearningPathDraft:
        body = await self._post_json(
            self.settings.remote_path_path,
            {
                "user_id": user_id,
                "course_name": course_name,
                "profile": profile.model_dump(mode="json"),
                "resources": [resource.model_dump(mode="json") for resource in resources],
            },
        )
        try:
            return LearningPathDraft.model_validate(body)
        except ValidationError as error:
            raise upstream_rejected(
                "上游学习路径不符合固定节点契约。", details=str(error)
            ) from error

    async def build_evaluation(
        self,
        *,
        user_id: str,
        course_name: str,
        evidence: EvaluationEvidence,
    ) -> EvaluationDraft:
        body = await self._post_json(
            self.settings.remote_evaluation_path,
            {
                "user_id": user_id,
                "course_name": course_name,
                "evidence": evidence.model_dump(mode="json"),
            },
        )
        try:
            return EvaluationDraft.model_validate(body)
        except ValidationError as error:
            raise upstream_rejected(
                "上游评估结果不符合固定评分契约。", details=str(error)
            ) from error


class FallbackAgentProvider(AgentProvider):
    def __init__(
        self,
        primary: RemoteAgentProvider,
        fallback: MockAgentProvider,
    ):
        self.primary = primary
        self.fallback = fallback

    async def aclose(self) -> None:
        await self.primary.aclose()

    async def stream_profile(self, **kwargs) -> AsyncIterator[GatewayEvent]:
        try:
            async for event in self.primary.stream_profile(**kwargs):
                yield event
        except AppError:
            async for event in self.fallback.stream_profile(**kwargs):
                yield event.model_copy(update={"demo_mode": True})

    async def stream_resources(self, **kwargs) -> AsyncIterator[ResourceAgentEvent]:
        try:
            async for event in self.primary.stream_resources(**kwargs):
                yield event
        except AppError:
            async for event in self.fallback.stream_resources(**kwargs):
                yield event.model_copy(update={"demo_mode": True})

    async def stream_qa(self, **kwargs) -> AsyncIterator[GatewayEvent]:
        try:
            async for event in self.primary.stream_qa(**kwargs):
                yield event
        except AppError:
            async for event in self.fallback.stream_qa(**kwargs):
                yield event.model_copy(update={"demo_mode": True})

    async def build_learning_path(self, **kwargs) -> LearningPathDraft:
        try:
            return await self.primary.build_learning_path(**kwargs)
        except AppError:
            return await self.fallback.build_learning_path(**kwargs)

    async def build_evaluation(self, **kwargs) -> EvaluationDraft:
        try:
            return await self.primary.build_evaluation(**kwargs)
        except AppError:
            return await self.fallback.build_evaluation(**kwargs)
