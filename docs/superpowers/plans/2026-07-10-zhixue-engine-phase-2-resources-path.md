# Zhixue Engine Phase 2 Resources and Learning Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver persistent multi-resource generation with resumable SSE progress, complete resource renderers, online quiz submission, learning event collection, and a resource-linked learning path.

**Architecture:** Resource submission creates a persisted task and starts one in-process async runner. The SSE endpoint replays ordered events from SQLite and sends heartbeats, so browser refreshes can resume from `Last-Event-ID`. Resources use a fixed discriminated payload schema; React Flow powers both mind maps and learning paths.

**Tech Stack:** FastAPI, SQLAlchemy 2, SQLite, asyncio, Pillow/imageio mock media, Next.js 15, TanStack Query, React Markdown, React Flow, Recharts, Vitest, pytest, Playwright.

---

## File Map

### Backend

- Modify: `backend/pyproject.toml` - add demo media dependencies.
- Modify: `backend/app/core/config.py` - configured media root.
- Modify: `backend/app/db/models.py` - resources, paths, quiz attempts, learning events.
- Modify: `backend/app/schemas/task.py` - resource types and completed task payloads.
- Create: `backend/app/schemas/resource.py`.
- Create: `backend/app/schemas/learning.py`.
- Create: `backend/app/schemas/course.py` - phase 2 course summaries.
- Modify: `backend/app/agents/base.py` - resource stream protocol.
- Modify: `backend/app/agents/mock.py` - deterministic five-resource stream.
- Create: `backend/app/repositories/resources.py`.
- Create: `backend/app/repositories/learning.py`.
- Modify: `backend/app/repositories/tasks.py` - event replay, idempotency, retry source.
- Create: `backend/app/tasks/manager.py` - tracked in-process runners.
- Create: `backend/app/services/resource_service.py`.
- Create: `backend/app/services/quiz_service.py`.
- Create: `backend/app/services/learning_path_service.py`.
- Create: `backend/app/services/learning_event_service.py`.
- Create: `backend/app/services/course_catalog.py` - mock-mode course metadata.
- Create: `backend/app/api/routes/resources.py`.
- Create: `backend/app/api/routes/learning.py`.
- Create: `backend/app/api/routes/courses.py` - course list endpoint.
- Create: `backend/app/media/seed.py` - local mock image/video generation.
- Modify: `backend/app/main.py` - media mounting and task manager lifecycle.
- Create: `backend/tests/test_resource_repository.py`.
- Create: `backend/tests/test_resource_generation.py`.
- Create: `backend/tests/test_resource_sse.py`.
- Create: `backend/tests/test_quiz_submit.py`.
- Create: `backend/tests/test_learning_events.py`.
- Create: `backend/tests/test_learning_path.py`.
- Create: `backend/tests/test_course_list.py`.
- Modify: `backend/tests/conftest.py` - isolated media directory and mock provider fixture.

### Frontend

- Create: `Course-Agent/creative/lib/api/resource-types.ts`.
- Create: `Course-Agent/creative/lib/query/resource-cache.ts`.
- Create: `Course-Agent/creative/lib/sse/resource-event-source.ts`.
- Create: `Course-Agent/creative/components/resources/generation-form.tsx`.
- Create: `Course-Agent/creative/components/resources/task-rail.tsx`.
- Create: `Course-Agent/creative/components/resources/resource-grid.tsx`.
- Create: `Course-Agent/creative/components/resources/resource-card.tsx`.
- Create: `Course-Agent/creative/components/resources/markdown-renderer.tsx`.
- Create: `Course-Agent/creative/components/resources/code-block.tsx`.
- Create: `Course-Agent/creative/components/resources/mind-map-viewer.tsx`.
- Create: `Course-Agent/creative/components/resources/media-card.tsx`.
- Create: `Course-Agent/creative/components/resources/video-player.tsx`.
- Create: `Course-Agent/creative/components/resources/quiz-player.tsx`.
- Replace: `Course-Agent/creative/app/(platform)/workspace/page.tsx`.
- Create: `Course-Agent/creative/app/(platform)/resources/[resourceId]/page.tsx`.
- Create: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`.
- Create: `Course-Agent/creative/components/learning-path/profile-summary.tsx`.
- Create: `Course-Agent/creative/app/(platform)/learning-path/page.tsx`.
- Create: frontend unit tests under `Course-Agent/creative/tests/resources/` and `tests/learning-path/`.
- Create: `Course-Agent/creative/e2e/resource-path-flow.spec.ts`.
- Create: `Course-Agent/creative/e2e/helpers.ts`.

## Task 1: Add Resource, Quiz, Event, and Path Persistence

**Files:**
- Modify: `backend/app/db/models.py`
- Create: `backend/app/repositories/resources.py`
- Create: `backend/app/repositories/learning.py`
- Create: `backend/tests/test_resource_repository.py`

- [ ] **Step 1: Write failing persistence tests**

```py
from app.repositories.resources import ResourceRepository


def test_resource_repository_lists_course_history(client):
    db = client.app.state.db
    with db.session() as session:
        repository = ResourceRepository(session)
        repository.create(
            resource_id="res-1",
            task_id="task-1",
            user_id="student-001",
            course_name="机器人操作系统",
            resource_type="handout",
            title="ROS2 节点通信讲义",
            payload={"markdown": "# ROS2"},
            media_url=None,
        )

        resources = repository.list_for_course("student-001", "机器人操作系统")

    assert [resource.id for resource in resources] == ["res-1"]
    assert resources[0].payload == {"markdown": "# ROS2"}
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_repository.py -q
```

Expected: FAIL because the resource model/repository is absent.

- [ ] **Step 3: Add persistence models**

Add these SQLAlchemy models with UUID string primary keys and timestamps:

```py
class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    resource_type: Mapped[str] = mapped_column(String(24), index=True)
    title: Mapped[str] = mapped_column(String(240))
    payload: Mapped[dict] = mapped_column(JSON)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="active")


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    stage_name: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(24))
    resource_id: Mapped[str | None] = mapped_column(ForeignKey("resources.id"), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

Also add `QuizAttempt` and `LearningEvent`. `LearningEvent` stores `event_type`, `resource_id`, `path_node_id`, `client_started_at`, `client_ended_at`, and JSON metadata.

- [ ] **Step 4: Implement repositories and rerun tests**

`ResourceRepository` must implement `create`, `get`, `list_for_course`, and `list_by_task`. `LearningRepository` must create/version paths, replace ordered nodes, record quiz attempts, record learning events, and complete path nodes idempotently.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_repository.py backend/tests/test_task_repository.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate the resources/learning migration and commit**

Run from `backend`:

```powershell
.\.venv\Scripts\python -m alembic revision --autogenerate -m "resources and learning"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m alembic current
```

Expected: the new revision is at head and creates resources, learning paths, path nodes, quiz attempts, and learning events.

```powershell
git add backend/app/db/models.py backend/app/repositories backend/migrations backend/tests/test_resource_repository.py
git commit -m "feat(api): persist resources and learning records"
```

## Task 2: Define Fixed Resource and Learning Schemas

**Files:**
- Create: `backend/app/schemas/resource.py`
- Create: `backend/app/schemas/learning.py`
- Modify: `backend/app/schemas/task.py`
- Create: `backend/tests/test_resource_schemas.py`

- [ ] **Step 1: Write failing discriminated-union tests**

```py
from pydantic import TypeAdapter, ValidationError
import pytest

from app.schemas.resource import ResourceDetail


def test_resource_detail_requires_payload_for_its_type():
    adapter = TypeAdapter(ResourceDetail)
    resource = adapter.validate_python({
        "id": "res-1",
        "resource_type": "code",
        "title": "ROS2 publisher",
        "payload": {"language": "python", "code": "print('ok')"},
        "media_url": None,
    })
    assert resource.payload.language == "python"

    with pytest.raises(ValidationError):
        adapter.validate_python({
            "id": "res-2",
            "resource_type": "code",
            "title": "broken",
            "payload": {"markdown": "wrong payload"},
            "media_url": None,
        })
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_schemas.py -q
```

Expected: FAIL because the schemas are absent.

- [ ] **Step 3: Implement fixed resource schemas**

Define:

```py
ResourceType = Literal["handout", "mindmap", "quiz", "code", "video"]

class HandoutPayload(BaseModel):
    markdown: str

class MindMapNode(BaseModel):
    id: str
    label: str
    parent_id: str | None = None

class MindMapPayload(BaseModel):
    nodes: list[MindMapNode]

class QuizQuestion(BaseModel):
    id: str
    question_type: Literal["choice", "blank", "programming"]
    prompt: str
    options: list[str] = Field(default_factory=list)
    answer: str
    explanation: str

class QuizPayload(BaseModel):
    questions: list[QuizQuestion]

class CodePayload(BaseModel):
    language: str
    code: str
    description: str

class VideoPayload(BaseModel):
    summary: str
    poster_url: str
    duration_seconds: int
```

Create a Pydantic discriminated union on `resource_type`. Define request/response schemas for generation, list, detail, quiz submit, learning event batch, and path nodes.

- [ ] **Step 4: Run schema tests**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_schemas.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit resource contracts**

```powershell
git add backend/app/schemas backend/tests/test_resource_schemas.py
git commit -m "feat(api): define fixed resource contracts"
```

## Task 3: Generate Offline Mock Media

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/media/seed.py`
- Create: `backend/tests/test_demo_media.py`

- [ ] **Step 1: Write the failing media seed test**

```py
def test_demo_media_seed_creates_image_and_video(client, tmp_path):
    media = client.app.state.demo_media
    assert media.poster_path.exists()
    assert media.video_path.exists()
    assert media.poster_path.stat().st_size > 1000
    assert media.video_path.stat().st_size > 1000
```

- [ ] **Step 2: Add dependencies and verify the test fails**

Add to `backend/pyproject.toml` dependencies:

```toml
"pillow>=11,<13",
"numpy>=2,<3",
"imageio>=2.37,<3",
"imageio-ffmpeg>=0.6,<1",
```

Install and run:

```powershell
backend\.venv\Scripts\python -m pip install -e "backend[test]"
backend\.venv\Scripts\python -m pytest backend/tests/test_demo_media.py -q
```

Expected: FAIL because the media seed is absent.

- [ ] **Step 3: Implement deterministic PNG and MP4 generation**

Add `media_root: Path = Path("./media")` to `Settings` and override it with `tmp_path / "media"` in the pytest settings fixture. `ensure_demo_media(root: Path)` must create a 1280x720 poster with the title “智学引擎 · 演示课程” and a 3-second, 12-fps MP4 whose frames animate the approved blue/green/coral progress bars. Use Pillow for frames and `imageio.v2.mimwrite(video_path, np.stack(frames), fps=12, codec="libx264", quality=8)` for video.

Return:

```py
@dataclass(frozen=True)
class DemoMedia:
    poster_path: Path
    video_path: Path
```

- [ ] **Step 4: Seed and mount generated media**

In the FastAPI lifespan, call `ensure_demo_media(settings.media_root / "generated")`, store it on `app.state.demo_media`, and mount:

```py
app.mount("/media", StaticFiles(directory=settings.media_root), name="media")
```

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_demo_media.py -q
```

Expected: PASS and generated files remain ignored by Git.

- [ ] **Step 5: Commit media seeding code**

```powershell
git add backend/pyproject.toml backend/app/core/config.py backend/app/media backend/app/main.py backend/tests/conftest.py backend/tests/test_demo_media.py
git commit -m "feat(api): generate offline demo media"
```

## Task 4: Stream Deterministic Five-Resource Mock Events

**Files:**
- Modify: `backend/app/agents/base.py`
- Modify: `backend/app/agents/mock.py`
- Create: `backend/tests/test_mock_resource_agent.py`

- [ ] **Step 1: Write the failing mock resource test**

```py
import pytest


@pytest.mark.asyncio
async def test_mock_resource_stream_completes_selected_types(mock_provider):
    events = [event async for event in mock_provider.stream_resources(
        task_id="task-1",
        trace_id="trace-1",
        user_id="student-001",
        course_name="机器人操作系统",
        weak_point="ROS2 节点通信",
        resource_types=["handout", "mindmap", "quiz", "code", "video"],
    )]

    ready_types = [event.resource_type for event in events if event.event == "resource.ready"]
    assert ready_types == ["handout", "mindmap", "quiz", "code", "video"]
    assert events[-1].event == "task.completed"
    assert events[-1].progress == 100
```

- [ ] **Step 2: Run and verify failure**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_mock_resource_agent.py -q
```

Expected: FAIL because `stream_resources` is absent.

Add this shared fixture to `backend/tests/conftest.py` before rerunning the test:

```py
from app.agents.mock import MockAgentProvider


@pytest.fixture
def mock_provider(settings):
    return MockAgentProvider(settings)
```

- [ ] **Step 3: Extend the provider contract with internal resource events**

The internal event carries a resource draft; the public `GatewayEvent` continues to expose stable progress fields and persisted resource IDs.

```py
class ResourceDraft(BaseModel):
    resource_type: ResourceType
    title: str
    payload: dict
    media_url: str | None = None


class ResourceAgentEvent(BaseModel):
    event: Literal["agent.started", "task.progress", "content.delta", "resource.ready"]
    current_agent: str
    progress: int = Field(ge=0, le=99)
    resource_type: ResourceType
    content: str = ""
    resource: ResourceDraft | None = None


@abstractmethod
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
    raise NotImplementedError
```

- [ ] **Step 4: Implement deterministic resource payloads and events**

For each selected type, emit `agent.started`, one or more `content.delta`/`task.progress` internal events, then `resource.ready` with a populated `ResourceDraft.resource`. `ResourceService` assigns the final resource ID, persists the draft, and maps the internal event to a public `GatewayEvent` whose `resource_ids` contains that ID. Finish the public stream with `task.completed` and all generated resource IDs. The mock content must display an “演示资源” badge in its title or metadata.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_mock_resource_agent.py -q
```

Expected: PASS with the exact selected order.

- [ ] **Step 5: Commit resource provider changes**

```powershell
git add backend/app/agents backend/app/schemas/task.py backend/tests/test_mock_resource_agent.py
git commit -m "feat(api): stream mock learning resources"
```

## Task 5: Add the Persistent Task Manager and SSE Replay

**Files:**
- Create: `backend/app/tasks/manager.py`
- Modify: `backend/app/repositories/tasks.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_resource_sse.py`

- [ ] **Step 1: Write failing replay and heartbeat tests**

```py
def test_resource_sse_replays_events_after_last_event_id(client, seeded_resource_task):
    response = client.get(
        f"/api/resource/progress/{seeded_resource_task.id}",
        headers={"Last-Event-ID": "2"},
    )
    assert response.status_code == 200
    assert "id: 1\n" not in response.text
    assert "id: 2\n" not in response.text
    assert "id: 3\n" in response.text
    assert "event: task.completed" in response.text
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_sse.py -q
```

Expected: FAIL because the SSE route and replay query are absent.

- [ ] **Step 3: Implement event replay repository methods**

Add:

```py
def list_events(self, task_id: str, after_seq: int = 0) -> list[TaskEvent]:
    statement = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id, TaskEvent.seq > after_seq)
        .order_by(TaskEvent.seq)
    )
    return list(self.session.scalars(statement))
```

Also add `find_idempotent`, `get_request_snapshot`, and `mark_interrupted_running_tasks`.

- [ ] **Step 4: Implement `TaskManager` and database-polling SSE**

`TaskManager.start(task_id, coroutine)` stores the created asyncio task, removes it when done, and cancels outstanding runners during shutdown. The SSE generator polls events every 250 ms, sends a heartbeat after 15 seconds without data, and exits after a terminal task event. It begins after `Last-Event-ID` or query `after_seq`.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_sse.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit task management**

```powershell
git add backend/app/tasks backend/app/repositories/tasks.py backend/app/main.py backend/tests/test_resource_sse.py
git commit -m "feat(api): replay persistent task events over SSE"
```

## Task 6: Implement Resource Generate, List, Detail, Snapshot, and Retry APIs

**Files:**
- Create: `backend/app/services/resource_service.py`
- Create: `backend/app/services/course_catalog.py`
- Create: `backend/app/api/routes/resources.py`
- Create: `backend/app/api/routes/courses.py`
- Modify: `backend/app/api/routes/tasks.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_resource_generation.py`
- Create: `backend/tests/test_course_list.py`

- [ ] **Step 1: Write failing API tests**

```py
def test_resource_generation_is_idempotent(client):
    payload = {
        "user_id": "student-001",
        "course_name": "机器人操作系统",
        "weak_point": "ROS2 通信",
        "resource_type_list": ["handout", "quiz"],
    }
    first = client.post("/api/resource/generate", json=payload, headers={"Idempotency-Key": "same-request"})
    second = client.post("/api/resource/generate", json=payload, headers={"Idempotency-Key": "same-request"})

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["data"]["task_id"] == second.json()["data"]["task_id"]
```

Add tests asserting list/detail and retry returns a new task ID with `retry_of_task_id`.

`backend/tests/test_course_list.py`:

```py
def test_mock_mode_lists_an_explicit_demo_course(client):
    response = client.get("/api/course/list")
    assert response.status_code == 200
    assert response.json()["data"] == [{
        "name": "机器人操作系统（演示）",
        "slug": "robotics-demo",
        "content_ready": False,
        "is_demo": True,
    }]
```

- [ ] **Step 2: Run and verify failures**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_generation.py -q
```

Expected: FAIL because resource and course-list APIs are absent.

- [ ] **Step 3: Implement `ResourceService`**

`submit` validates the user and selected types, returns an existing idempotent task when present, otherwise creates the task and starts `run`. `run` persists each gateway event, creates a `Resource` on every `resource.ready`, and commits the terminal task snapshot atomically.

`retry` requires a failed task with `error.retryable=true`, creates a new task whose request snapshot includes `retry_of_task_id`, and starts it.

`CourseCatalogService` returns the explicit course below only when `agent_mode="mock"`; during Phase 2, remote mode returns an empty list until the real-file repository is added in Phase 3:

```py
CourseSummary(
    name="机器人操作系统（演示）",
    slug="robotics-demo",
    content_ready=False,
    is_demo=True,
)
```

- [ ] **Step 4: Add routes and run tests**

Routes:

```text
POST /api/resource/generate
GET  /api/resource/progress/{task_id}
GET  /api/resource/list
GET  /api/resource/detail/{resource_id}
GET  /api/task/{task_id}
POST /api/task/{task_id}/retry
GET  /api/course/list
```

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_resource_generation.py backend/tests/test_resource_sse.py backend/tests/test_course_list.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit resource APIs**

```powershell
git add backend/app/services/resource_service.py backend/app/services/course_catalog.py backend/app/api/routes backend/app/schemas/course.py backend/app/main.py backend/tests/test_resource_generation.py backend/tests/test_course_list.py
git commit -m "feat(api): add persistent resource generation APIs"
```

## Task 7: Add Frontend Resource Types, Cache, and SSE Client

**Files:**
- Create: `Course-Agent/creative/lib/api/resource-types.ts`
- Create: `Course-Agent/creative/lib/query/resource-cache.ts`
- Create: `Course-Agent/creative/lib/sse/resource-event-source.ts`
- Create: `Course-Agent/creative/tests/resources/resource-cache.test.ts`

- [ ] **Step 1: Write the failing cache reducer test**

```ts
import { describe, expect, it } from "vitest"

import { applyResourceEvent, emptyResourceTask } from "@/lib/query/resource-cache"

describe("applyResourceEvent", () => {
  it("buffers content independently by resource type", () => {
    const handout = applyResourceEvent(emptyResourceTask, event({ seq: 1, resource_type: "handout", content: "A" }))
    const quiz = applyResourceEvent(handout, event({ seq: 2, resource_type: "quiz", content: "B" }))

    expect(quiz.byType.handout.content).toBe("A")
    expect(quiz.byType.quiz.content).toBe("B")
  })
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/resource-cache.test.ts
```

Expected: FAIL because resource cache code is absent.

- [ ] **Step 3: Implement discriminated frontend types and cache reducer**

Mirror the OpenAPI union and expose:

```ts
export type ResourceType = "handout" | "mindmap" | "quiz" | "code" | "video"

export type ResourceTaskState = {
  taskId?: string
  lastSeq: number
  globalProgress: number
  currentAgent?: string
  status: "idle" | "running" | "partial_success" | "succeeded" | "failed"
  byType: Record<ResourceType, ResourceProgressState>
  resourceIds: string[]
}
```

- [ ] **Step 4: Implement EventSource lifecycle and rerun tests**

`subscribeToResourceTask(taskId, onEvent, onConnectionState)` opens `${API_BASE_URL}/api/resource/progress/${taskId}`, parses named events, closes on terminal events, and reports browser connection errors without clearing cache. Native EventSource handles `Last-Event-ID` reconnects.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/resource-cache.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit resource state utilities**

```powershell
git add Course-Agent/creative/lib/api/resource-types.ts Course-Agent/creative/lib/query/resource-cache.ts Course-Agent/creative/lib/sse/resource-event-source.ts Course-Agent/creative/tests/resources/resource-cache.test.ts
git commit -m "feat(web): manage persistent resource task streams"
```

## Task 8: Build the Resource Workbench and Task Rail

**Files:**
- Create: `Course-Agent/creative/components/resources/generation-form.tsx`
- Create: `Course-Agent/creative/components/resources/task-rail.tsx`
- Create: `Course-Agent/creative/components/resources/resource-grid.tsx`
- Replace: `Course-Agent/creative/app/(platform)/workspace/page.tsx`
- Create: `Course-Agent/creative/tests/resources/generation-form.test.tsx`
- Create: `Course-Agent/creative/tests/resources/task-rail.test.tsx`

- [ ] **Step 1: Write failing form and progress tests**

```tsx
it("submits stable resource enum values", async () => {
  const onGenerate = vi.fn()
  render(<GenerationForm courses={[demoCourse]} onGenerate={onGenerate} />)
  await user.selectOptions(screen.getByLabelText("课程"), "robotics")
  await user.type(screen.getByLabelText("薄弱知识点"), "ROS2 通信")
  await user.click(screen.getByLabelText("讲义文档"))
  await user.click(screen.getByLabelText("习题题库"))
  await user.click(screen.getByRole("button", { name: "生成学习资源" }))

  expect(onGenerate).toHaveBeenCalledWith(expect.objectContaining({
    resource_type_list: ["handout", "quiz"],
  }))
})
```

Task rail test asserts all selected types keep fixed rows and one failed type does not remove completed types.

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/generation-form.test.tsx tests/resources/task-rail.test.tsx
```

Expected: FAIL because components are absent.

- [ ] **Step 3: Implement form and task rail**

Use `Select`, `Input`, `Checkbox`, `Progress`, and Lucide icons. Course options display an “演示” badge when `is_demo=true`. The right rail appears only while a task exists and collapses after completion unless the user pins it.

- [ ] **Step 4: Implement workspace orchestration**

The workspace loads `/api/course/list` and `/api/resource/list`, submits generation with a UUID idempotency key, subscribes to SSE, writes progress to Query cache, and fetches final resource details after `task.completed`. A failed stream calls `/api/task/{id}` before offering retry.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/generation-form.test.tsx tests/resources/task-rail.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit the workbench**

```powershell
git add 'Course-Agent/creative/app/(platform)/workspace' Course-Agent/creative/components/resources Course-Agent/creative/tests/resources
git commit -m "feat(web): add multi-agent resource workbench"
```

## Task 9: Add Markdown, Code, Media, and Resource Cards

**Files:**
- Create: renderer files listed in the file map.
- Create: `Course-Agent/creative/tests/resources/resource-card.test.tsx`

- [ ] **Step 1: Write the failing renderer test**

```tsx
it("renders handout, code, and video payloads with actions", () => {
  const { rerender } = render(<ResourceCard resource={handoutResource} />)
  expect(screen.getByRole("heading", { name: "ROS2 讲义" })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "复制内容" })).toBeInTheDocument()

  rerender(<ResourceCard resource={codeResource} />)
  expect(screen.getByText("python")).toBeInTheDocument()

  rerender(<ResourceCard resource={videoResource} />)
  expect(screen.getByTestId("video-player")).toHaveAttribute("src", videoResource.media_url)
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/resource-card.test.tsx
```

Expected: FAIL because renderers are absent.

- [ ] **Step 3: Implement renderers**

- `MarkdownRenderer`: `react-markdown`, `remark-gfm`, `rehype-highlight`.
- `CodeBlock`: fixed header, language label, copy icon, scrollable `<pre>`.
- `MediaCard`: preview/download icon buttons and local URL handling.
- `VideoPlayer`: native `<video controls preload="metadata">` with stable 16:9 dimensions.
- `ResourceCard`: one outer card only; select renderer by `resource_type`.

- [ ] **Step 4: Run tests and visual component checks**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/resource-card.test.tsx
pnpm --dir Course-Agent/creative typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit content renderers**

```powershell
git add Course-Agent/creative/components/resources Course-Agent/creative/tests/resources/resource-card.test.tsx
git commit -m "feat(web): render generated learning resources"
```

## Task 10: Render Mind Maps with React Flow

**Files:**
- Create: `Course-Agent/creative/components/resources/mind-map-viewer.tsx`
- Create: `Course-Agent/creative/tests/resources/mind-map-viewer.test.tsx`

- [ ] **Step 1: Write the failing mind map test**

```tsx
it("renders every mind map node", () => {
  render(<MindMapViewer nodes={[
    { id: "root", label: "ROS2", parent_id: null },
    { id: "topic", label: "节点通信", parent_id: "root" },
  ]} />)
  expect(screen.getByText("ROS2")).toBeInTheDocument()
  expect(screen.getByText("节点通信")).toBeInTheDocument()
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/mind-map-viewer.test.tsx
```

Expected: FAIL because the viewer is absent.

- [ ] **Step 3: Implement deterministic tree layout**

Convert `parent_id` relationships to React Flow nodes/edges. Root depth is 0; each depth uses a fixed x increment and siblings use a fixed y increment. Disable node dragging and editing, enable fit view, zoom controls, and a minimum height of 420px.

- [ ] **Step 4: Run test and typecheck**

```powershell
pnpm --dir Course-Agent/creative test -- tests/resources/mind-map-viewer.test.tsx
pnpm --dir Course-Agent/creative typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit mind map rendering**

```powershell
git add Course-Agent/creative/components/resources/mind-map-viewer.tsx Course-Agent/creative/tests/resources/mind-map-viewer.test.tsx
git commit -m "feat(web): visualize generated mind maps"
```

## Task 11: Add Quiz Submission and Interactive Quiz UI

**Files:**
- Create: `backend/app/services/quiz_service.py`
- Create: `backend/app/api/routes/learning.py`
- Create: `backend/tests/test_quiz_submit.py`
- Create: `Course-Agent/creative/components/resources/quiz-player.tsx`
- Create: `Course-Agent/creative/tests/resources/quiz-player.test.tsx`

- [ ] **Step 1: Write failing backend scoring test**

```py
def test_quiz_submit_returns_per_question_results(client, seeded_quiz_resource):
    response = client.post("/api/quiz/submit", json={
        "user_id": "student-001",
        "resource_id": seeded_quiz_resource.id,
        "answers": {"q1": "B", "q2": "节点"},
    })
    assert response.status_code == 200
    assert response.json()["data"]["score"] == 100
    assert all(item["correct"] for item in response.json()["data"]["results"])
```

- [ ] **Step 2: Run backend and frontend tests to verify failure**

Create a frontend test that fills answers, clicks “提交答案”, and expects the API response score and explanations. Then run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_quiz_submit.py -q
pnpm --dir Course-Agent/creative test -- tests/resources/quiz-player.test.tsx
```

Expected: both FAIL.

- [ ] **Step 3: Implement scoring and persistence**

Choice answers compare exact option values, blank answers compare normalized trimmed strings, and programming answers compare normalized expected output. Persist `QuizAttempt` with submitted answers, per-question results, and score. Do not execute arbitrary submitted code.

- [ ] **Step 4: Implement `QuizPlayer` and run tests**

Use radio groups for choice, inputs for blank, and a textarea for programming output. Disable resubmission while pending. Show per-question correctness and explanation after response.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_quiz_submit.py -q
pnpm --dir Course-Agent/creative test -- tests/resources/quiz-player.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit quiz flow**

```powershell
git add backend/app/services/quiz_service.py backend/app/api/routes/learning.py backend/tests/test_quiz_submit.py Course-Agent/creative/components/resources/quiz-player.tsx Course-Agent/creative/tests/resources/quiz-player.test.tsx
git commit -m "feat: add interactive quiz submission"
```

## Task 12: Record Learning Events

**Files:**
- Create: `backend/app/services/learning_event_service.py`
- Modify: `backend/app/api/routes/learning.py`
- Create: `backend/tests/test_learning_events.py`
- Create: `Course-Agent/creative/lib/api/learning-events.ts`

- [ ] **Step 1: Write the failing event validation test**

```py
def test_learning_events_complete_path_nodes_idempotently(client, seeded_path_node):
    payload = {
        "user_id": "student-001",
        "course_name": "机器人操作系统",
        "events": [{
            "event_type": "path_node_completed",
            "path_node_id": seeded_path_node.id,
            "client_started_at": "2026-07-10T08:00:00Z",
            "client_ended_at": "2026-07-10T08:10:00Z",
            "metadata": {},
        }],
    }
    first = client.post("/api/learning/events", json=payload)
    second = client.post("/api/learning/events", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["accepted"] == 1
```

- [ ] **Step 2: Run and verify failure**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_learning_events.py -q
```

Expected: FAIL because the service is absent.

- [ ] **Step 3: Implement event validation and persistence**

Accept only `resource_opened`, `resource_closed`, `path_node_completed`, `question_asked`, and `video_progress`. Reject end times before start times. Compute duration from timestamps server-side and cap one event at four hours. Complete referenced path nodes idempotently.

- [ ] **Step 4: Add a frontend batching helper and run tests**

`queueLearningEvent` buffers events in memory and flushes at 10 events, page visibility change, or 10 seconds. Use `navigator.sendBeacon` only for unload; normal flushes use `apiFetch`.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_learning_events.py -q
pnpm --dir Course-Agent/creative typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit learning event collection**

```powershell
git add backend/app/services/learning_event_service.py backend/app/api/routes/learning.py backend/tests/test_learning_events.py Course-Agent/creative/lib/api/learning-events.ts
git commit -m "feat: record learning behavior events"
```

## Task 13: Generate and Render the Learning Path

**Files:**
- Create: `backend/app/services/learning_path_service.py`
- Modify: `backend/app/agents/base.py`
- Modify: `backend/app/agents/mock.py`
- Modify: `backend/app/api/routes/learning.py`
- Create: `backend/tests/test_learning_path.py`
- Create: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`
- Create: `Course-Agent/creative/components/learning-path/profile-summary.tsx`
- Create: `Course-Agent/creative/app/(platform)/learning-path/page.tsx`
- Create: `Course-Agent/creative/tests/learning-path/learning-path-graph.test.tsx`

- [ ] **Step 1: Write failing path API test**

```py
def test_path_orders_five_stages_and_binds_resources(client, seeded_resource_set):
    response = client.get("/api/path/get", params={
        "user_id": "student-001",
        "course_name": "机器人操作系统",
    })
    assert response.status_code == 200
    nodes = response.json()["data"]["nodes"]
    assert [node["stage_name"] for node in nodes] == [
        "基础补全", "知识点学习", "习题训练", "代码实操", "拓展视频",
    ]
    assert all("difficulty" in node for node in nodes)
```

- [ ] **Step 2: Run backend and frontend tests to verify failure**

The frontend test renders five nodes and asserts clicking a resource-bound node calls the resource navigation callback.

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_learning_path.py -q
pnpm --dir Course-Agent/creative test -- tests/learning-path
```

Expected: both FAIL.

- [ ] **Step 3: Implement deterministic path creation/versioning**

Add this provider contract:

```py
@abstractmethod
async def build_learning_path(
    self,
    *,
    user_id: str,
    course_name: str,
    profile: StudentProfileData,
    resources: list[ResourceSummary],
) -> LearningPathDraft:
    raise NotImplementedError
```

`MockAgentProvider.build_learning_path` returns the five fixed stages. Bind the best matching resource type in this order: handout, handout/mindmap, quiz, code, video. Missing resource types produce disabled nodes with `resource_id=null`, not fake resources. `LearningPathService` persists the provider draft as version 1 when no active path exists.

- [ ] **Step 4: Implement React Flow path UI and run tests**

Use a horizontal fixed layout with status colors, difficulty badges, and resource links. The top area renders the six-dimension profile summary from `/api/user/info`. Clicking a bound node routes to `/resources/[resourceId]`.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_learning_path.py -q
pnpm --dir Course-Agent/creative test -- tests/learning-path
```

Expected: PASS.

- [ ] **Step 5: Commit learning path flow**

```powershell
git add backend/app/services/learning_path_service.py backend/app/agents backend/app/api/routes/learning.py backend/tests/test_learning_path.py 'Course-Agent/creative/app/(platform)/learning-path' Course-Agent/creative/components/learning-path Course-Agent/creative/tests/learning-path
git commit -m "feat: add personalized learning path"
```

## Task 14: Add Resource Detail Routing, History Cache, and Phase 2 E2E

**Files:**
- Create: `Course-Agent/creative/app/(platform)/resources/[resourceId]/page.tsx`
- Create: `Course-Agent/creative/e2e/helpers.ts`
- Create: `Course-Agent/creative/e2e/resource-path-flow.spec.ts`
- Modify: `Course-Agent/creative/components/resources/resource-grid.tsx`
- Modify: `Course-Agent/creative/app/(platform)/workspace/page.tsx`

- [ ] **Step 1: Write the failing browser flow**

`Course-Agent/creative/e2e/helpers.ts`:

```ts
import type { Page } from "@playwright/test"

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000"

export async function seedConfirmedUser(page: Page, userId: string) {
  await page.request.post(`${API_BASE}/api/chat/profile`, {
    data: { user_id: userId, chat_text: "具备基础，希望通过代码案例强化学习。" },
  })
  await page.request.post(`${API_BASE}/api/profile/confirm`, {
    data: { user_id: userId },
  })
  await page.addInitScript((id) => {
    window.localStorage.setItem("zhixue_user_id", id)
  }, userId)
}
```

```ts
import { seedConfirmedUser } from "./helpers"

test("generates resources, submits a quiz, and opens the learning path", async ({ page }) => {
  await seedConfirmedUser(page, "resource-student")
  await page.goto("/workspace")
  await page.getByLabel("课程").selectOption({ label: /演示/ })
  await page.getByLabel("薄弱知识点").fill("ROS2 节点通信")
  await page.getByRole("button", { name: "全选资源" }).click()
  await page.getByRole("button", { name: "生成学习资源" }).click()

  await expect(page.getByText("题库Agent")).toBeVisible()
  await expect(page.getByText("全部资源已生成")).toBeVisible({ timeout: 30_000 })
  await page.getByRole("link", { name: /习题题库/ }).click()
  await page.getByLabel("B").check()
  await page.getByRole("button", { name: "提交答案" }).click()
  await expect(page.getByText(/得分/)).toBeVisible()

  await page.getByRole("link", { name: "学习路径" }).click()
  await expect(page.getByText("基础补全")).toBeVisible()
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test:e2e -- e2e/resource-path-flow.spec.ts
```

Expected: FAIL until resource detail and history routing are complete.

- [ ] **Step 3: Implement detail route and history restoration**

The detail route loads `/api/resource/detail/{id}`, renders the fixed union, and sends `resource_opened`/`resource_closed` events. The workspace always requests `/api/resource/list` on entry, seeds Query cache, and does not regenerate existing resources automatically.

- [ ] **Step 4: Run all Phase 2 checks**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e -- e2e/profile-flow.spec.ts e2e/resource-path-flow.spec.ts
```

Expected: all commands pass.

- [ ] **Step 5: Commit Phase 2 browser flow**

```powershell
git add 'Course-Agent/creative/app/(platform)/resources' Course-Agent/creative/components/resources Course-Agent/creative/e2e/helpers.ts Course-Agent/creative/e2e/resource-path-flow.spec.ts
git commit -m "test: cover resource and path workflow"
```

## Phase 2 Completion Check

Expected behavior:

- One resource task can generate any selected subset of five resource types.
- Global and per-resource progress survive page refresh through task snapshots/event replay.
- History loads without regeneration.
- Markdown, code, mind map, quiz, image/video media, and deep links render correctly.
- Quiz results and learning events persist.
- The five-stage learning path binds existing resources and updates completion state.
- Backend, frontend, build, and both Playwright flows are green.
