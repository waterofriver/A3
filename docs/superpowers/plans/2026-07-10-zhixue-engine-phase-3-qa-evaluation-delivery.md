# Zhixue Engine Phase 3 QA Evaluation and Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete global multimodal QA, learning evaluation and plan application, real course-file indexing, remote Agent integration, production-style error states, Docker deployment, documentation, screenshots, and demonstration artifacts.

**Architecture:** Reuse the Phase 1/2 gateway event contract for QA and remote providers. Derive mock evaluation from persisted quiz attempts and learning events. Scan real course directories into SQLite without fabricating content. Package Next.js, FastAPI, Nginx, SQLite, media, and course volumes in Docker Compose.

**Tech Stack:** FastAPI, SQLAlchemy, HTTPX/httpx-sse, pypdf, python-docx, python-pptx, Next.js, TanStack Query, Recharts, Playwright, axe, Docker Compose, Nginx.

---

## File Map

### Backend

- Modify: `backend/pyproject.toml` - remote SSE and document parsers.
- Modify: `backend/app/db/models.py` - evaluations, courses, documents.
- Modify: `backend/app/agents/base.py` - QA/path/evaluation methods.
- Modify: `backend/app/agents/mock.py` - QA/media and evaluation behavior.
- Create: `backend/app/agents/remote.py` - teammate service adapter.
- Create: `backend/app/services/qa_service.py`.
- Create: `backend/app/services/evaluation_service.py`.
- Create: `backend/app/services/course_indexer.py`.
- Create: `backend/app/repositories/evaluations.py`.
- Create: `backend/app/repositories/courses.py`.
- Create: `backend/app/schemas/qa.py`.
- Create: `backend/app/schemas/evaluation.py`.
- Modify: `backend/app/schemas/course.py` - add chapter/document detail schemas.
- Create: `backend/app/api/routes/qa.py`.
- Create: `backend/app/api/routes/evaluation.py`.
- Modify: `backend/app/api/routes/courses.py` - add course base endpoint.
- Create: backend tests for QA, evaluation, course indexing, remote adapter, and fallback policy.

### Frontend

- Create: `Course-Agent/creative/components/qa/qa-drawer.tsx`.
- Create: `Course-Agent/creative/components/qa/answer-mode-control.tsx`.
- Modify: `Course-Agent/creative/components/app-shell/app-shell.tsx` - global QA trigger/drawer.
- Create: `Course-Agent/creative/components/evaluation/score-panel.tsx`.
- Create: `Course-Agent/creative/components/evaluation/weakness-chart.tsx`.
- Create: `Course-Agent/creative/components/evaluation/plan-changes.tsx`.
- Create: `Course-Agent/creative/app/(platform)/evaluation/page.tsx`.
- Create: `Course-Agent/creative/components/knowledge/knowledge-tree.tsx`.
- Create: `Course-Agent/creative/components/knowledge/document-preview.tsx`.
- Create: `Course-Agent/creative/app/(platform)/knowledge/page.tsx`.
- Create: `Course-Agent/creative/components/shared/empty-state.tsx`.
- Create: `Course-Agent/creative/components/shared/offline-banner.tsx`.
- Create: `Course-Agent/creative/components/shared/resource-error-boundary.tsx`.
- Create: frontend tests for QA, evaluation, knowledge, and error states.
- Create: `Course-Agent/creative/e2e/full-platform-flow.spec.ts`.
- Create: `Course-Agent/creative/e2e/visual-capture.spec.ts`.

### Delivery

- Create: `backend/Dockerfile`.
- Create: `Course-Agent/creative/Dockerfile`.
- Create: `infra/nginx/default.conf`.
- Create: `docker-compose.yml`.
- Create: `.env.example`.
- Create: `start.ps1`.
- Create: `start.sh`.
- Rewrite: `README.md` as valid UTF-8 project documentation.
- Create: `docs/components.md`.
- Create: `docs/api-integration.md`.
- Create: `docs/deployment.md`.
- Create: `docs/demo-script.md`.
- Create: `artifacts/screenshots/` through Playwright capture.
- Create: `artifacts/demo/` through Playwright video/trace capture.

## Task 1: Stream Profile-Aware Multimodal QA

**Files:**
- Create: `backend/app/schemas/qa.py`
- Modify: `backend/app/agents/base.py`
- Modify: `backend/app/agents/mock.py`
- Create: `backend/app/services/qa_service.py`
- Create: `backend/app/api/routes/qa.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_qa_stream.py`

- [ ] **Step 1: Write the failing QA stream test**

```py
def test_video_qa_stream_uses_profile_and_returns_local_media(client, confirmed_user):
    with client.stream("POST", "/api/chat/qa", json={
        "user_id": confirmed_user.id,
        "question": "请解释 ROS2 发布订阅模型",
        "answer_mode": "video",
    }) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: content.delta" in body
    assert "event: media.ready" in body
    assert "/media/generated/demo-lesson.mp4" in body
    assert "event: task.completed" in body
```

- [ ] **Step 2: Run and verify failure**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_qa_stream.py -q
```

Expected: FAIL because the QA route/provider method is absent.

- [ ] **Step 3: Define QA schemas and provider protocol**

```py
class QaRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=4000)
    answer_mode: Literal["text", "image", "video"] = "text"
```

Add `stream_qa` to `AgentProvider`, receiving the confirmed profile and returning gateway events.

- [ ] **Step 4: Implement mock QA and persistence**

The mock response must mention one profile adaptation, stream at least three text chunks, emit the local poster for image mode or local MP4 for video mode, record a `question_asked` learning event, and persist the task/event sequence through `QaService`.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_qa_stream.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit QA API**

```powershell
git add backend/app/schemas/qa.py backend/app/agents backend/app/services/qa_service.py backend/app/api/routes/qa.py backend/app/main.py backend/tests/test_qa_stream.py
git commit -m "feat(api): stream profile-aware multimodal QA"
```

## Task 2: Add the Global QA Drawer

**Files:**
- Create: `Course-Agent/creative/components/qa/answer-mode-control.tsx`
- Create: `Course-Agent/creative/components/qa/qa-drawer.tsx`
- Modify: `Course-Agent/creative/components/app-shell/app-shell.tsx`
- Create: `Course-Agent/creative/tests/qa/qa-drawer.test.tsx`

- [ ] **Step 1: Write the failing drawer test**

```tsx
it("streams an answer and renders returned media", async () => {
  render(<QaDrawer open onOpenChange={() => undefined} userId="student-001" />)
  await user.type(screen.getByLabelText("课程问题"), "什么是发布订阅？")
  await user.click(screen.getByRole("radio", { name: "短视频讲解" }))
  await user.click(screen.getByRole("button", { name: "发送问题" }))

  await waitFor(() => expect(screen.getByText(/发布者/)).toBeInTheDocument())
  expect(screen.getByTestId("video-player")).toBeInTheDocument()
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/qa/qa-drawer.test.tsx
```

Expected: FAIL because the drawer is absent.

- [ ] **Step 3: Implement segmented answer mode and stream handling**

Use a Radix radio group styled as a three-option segmented control. The drawer uses `postEventStream`, renders streamed Markdown, and appends media cards on `media.ready`. It retains the question and partial answer on failure.

- [ ] **Step 4: Add one global shell trigger and run tests**

Add a “智能答疑” navigation action with a message icon. It opens the drawer without route changes and is present on every platform page.

```powershell
pnpm --dir Course-Agent/creative test -- tests/qa/qa-drawer.test.tsx tests/app-shell/app-shell.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit global QA UI**

```powershell
git add Course-Agent/creative/components/qa Course-Agent/creative/components/app-shell/app-shell.tsx Course-Agent/creative/tests/qa
git commit -m "feat(web): add global multimodal QA drawer"
```

## Task 3: Compute and Persist Evaluation Reports

**Files:**
- Modify: `backend/app/db/models.py`
- Create: `backend/app/repositories/evaluations.py`
- Create: `backend/app/schemas/evaluation.py`
- Create: `backend/app/services/evaluation_service.py`
- Modify: `backend/app/agents/base.py`
- Modify: `backend/app/agents/mock.py`
- Create: `backend/app/api/routes/evaluation.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_evaluation_report.py`
- Create: `backend/tests/test_evaluation_apply.py`

- [ ] **Step 1: Write failing report test**

```py
def test_evaluation_uses_quiz_and_learning_records(client, evaluation_records):
    response = client.get("/api/eval/report", params={
        "user_id": "student-001",
        "course_name": "机器人操作系统",
    })
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["theory_score"] == 80
    assert 0 <= report["practice_score"] <= 100
    assert report["weak_points"]
    assert report["recommended_changes"]
```

- [ ] **Step 2: Run report/apply tests and verify failure**

The apply test calls `/api/eval/apply` twice with the same report ID and expects one new active path version.

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_evaluation_report.py backend/tests/test_evaluation_apply.py -q
```

Expected: FAIL because evaluation storage/services are absent.

- [ ] **Step 3: Add evaluation model and calculation**

Store `theory_score`, `practice_score`, `weak_points`, `recommended_changes`, `source_path_id`, and `applied_path_id`. Mock calculation rules:

```py
theory_score = round(mean(attempt.score for attempt in attempts)) if attempts else 0
practice_score = round(100 * completed_practice_nodes / max(total_practice_nodes, 1))
```

Weak points come from incorrect quiz result metadata and `question_asked` event metadata, sorted by frequency. If no evidence exists, return `EVALUATION_NOT_READY` rather than invented scores.

Add this provider method so remote mode can replace the deterministic calculation without changing the route:

```py
@abstractmethod
async def build_evaluation(
    self,
    *,
    user_id: str,
    course_name: str,
    evidence: EvaluationEvidence,
) -> EvaluationDraft:
    raise NotImplementedError
```

`MockAgentProvider.build_evaluation` applies the formulas above. `EvaluationService` gathers and validates evidence, calls the provider, then persists the returned draft.

- [ ] **Step 4: Implement idempotent plan application**

`POST /api/eval/apply` clones the active path to version `n+1`, inserts/reorders recommended practice nodes, marks the old path superseded, and records `applied_path_id`. A second call returns the existing applied path.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_evaluation_report.py backend/tests/test_evaluation_apply.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate the evaluation migration and commit APIs**

```powershell
Push-Location backend
.\.venv\Scripts\python -m alembic revision --autogenerate -m "evaluation reports"
.\.venv\Scripts\python -m alembic upgrade head
Pop-Location
```

```powershell
git add backend/app/db/models.py backend/app/repositories/evaluations.py backend/app/schemas/evaluation.py backend/app/services/evaluation_service.py backend/app/api/routes/evaluation.py backend/app/main.py backend/app/agents backend/migrations backend/tests/test_evaluation_report.py backend/tests/test_evaluation_apply.py
git commit -m "feat(api): add learning evaluation and plan updates"
```

## Task 4: Build the Evaluation Dashboard

**Files:**
- Create: `Course-Agent/creative/components/evaluation/score-panel.tsx`
- Create: `Course-Agent/creative/components/evaluation/weakness-chart.tsx`
- Create: `Course-Agent/creative/components/evaluation/plan-changes.tsx`
- Create: `Course-Agent/creative/app/(platform)/evaluation/page.tsx`
- Create: `Course-Agent/creative/tests/evaluation/evaluation-page.test.tsx`

- [ ] **Step 1: Write the failing evaluation page test**

```tsx
it("shows scores, weak points, and applies the recommended plan", async () => {
  render(<EvaluationPageContent report={report} onApply={onApply} />)
  expect(screen.getByText("理论掌握度")).toBeInTheDocument()
  expect(screen.getByText("80")).toBeInTheDocument()
  expect(screen.getByText("ROS2 服务通信")).toBeInTheDocument()
  await user.click(screen.getByRole("button", { name: "一键更新学习计划" }))
  expect(onApply).toHaveBeenCalledWith(report.id)
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/evaluation/evaluation-page.test.tsx
```

Expected: FAIL because the page/components are absent.

- [ ] **Step 3: Implement score and weakness visualizations**

Use compact metric panels for theory/practice, Recharts horizontal bars for weak point frequency, and an unframed recommendation section. Stable chart height is 280px. Do not nest cards.

- [ ] **Step 4: Implement report loading, empty state, and apply mutation**

The page loads the current course report. `EVALUATION_NOT_READY` renders “评估数据不足”; apply invalidates evaluation and learning-path Query keys and displays the new path version.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/evaluation/evaluation-page.test.tsx
pnpm --dir Course-Agent/creative typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit evaluation UI**

```powershell
git add 'Course-Agent/creative/app/(platform)/evaluation' Course-Agent/creative/components/evaluation Course-Agent/creative/tests/evaluation
git commit -m "feat(web): add learning evaluation dashboard"
```

## Task 5: Index Real Course Files Without Fabricating Content

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/db/models.py`
- Create: `backend/app/repositories/courses.py`
- Modify: `backend/app/schemas/course.py`
- Create: `backend/app/services/course_indexer.py`
- Modify: `backend/app/api/routes/courses.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_course_indexer.py`
- Create: `backend/tests/test_course_api.py`

- [ ] **Step 1: Write failing indexer tests**

```py
def test_course_indexer_builds_chapter_tree_from_real_files(tmp_path, course_indexer):
    course = tmp_path / "ros2"
    chapter = course / "01-basics"
    chapter.mkdir(parents=True)
    (course / "course.json").write_text('{"name":"机器人操作系统","slug":"ros2"}', encoding="utf-8")
    (chapter / "intro.md").write_text("# ROS2 基础", encoding="utf-8")

    result = course_indexer.index_root(tmp_path)

    assert result[0].name == "机器人操作系统"
    assert result[0].content_ready is True
    assert result[0].chapters[0].documents[0].filename == "intro.md"
```

Add a path traversal test proving preview/download never escapes the configured course root.

- [ ] **Step 2: Add parser dependencies and verify failure**

Add:

```toml
"pypdf>=5,<7",
"python-docx>=1.1,<2",
"python-pptx>=1,<2",
```

Run:

```powershell
backend\.venv\Scripts\python -m pip install -e "backend[test]"
backend\.venv\Scripts\python -m pytest backend/tests/test_course_indexer.py backend/tests/test_course_api.py -q
```

Expected: FAIL because indexing is absent.

- [ ] **Step 3: Implement course and document persistence**

Add `Course` and `CourseDocument` with `slug`, `name`, `root_path`, `content_ready`, `is_demo`, chapter path, filename, file type, SHA-256, size, preview text, and media URL. Index only files whose resolved paths remain under the course root.

Extraction rules:

- Markdown/TXT/code: UTF-8 text with replacement for invalid bytes.
- PDF: first 30 pages of extracted text.
- DOCX: paragraphs and table cell text.
- PPTX: slide titles and text frames.
- Image/video: metadata plus `/media/courses/{course_slug}/{relative_path}` URL; no fake transcript.

- [ ] **Step 4: Implement list/base APIs and empty behavior**

`GET /api/course/list` returns configured courses with `content_ready` and `is_demo`. `GET /api/course/base` returns the chapter tree. Missing real documents return `COURSE_NOT_READY`, while the course selector can still list an explicitly configured demo course in mock mode.

Update `CourseCatalogService` to merge indexed `CourseRepository` rows with the mock-only demo summary, de-duplicate by slug, and exclude demo summaries in remote mode.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_course_indexer.py backend/tests/test_course_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate the course migration and commit indexing**

```powershell
Push-Location backend
.\.venv\Scripts\python -m alembic revision --autogenerate -m "course index"
.\.venv\Scripts\python -m alembic upgrade head
Pop-Location
```

```powershell
git add backend/pyproject.toml backend/app/db/models.py backend/app/repositories/courses.py backend/app/schemas/course.py backend/app/services/course_indexer.py backend/app/api/routes/courses.py backend/app/main.py backend/migrations backend/tests/test_course_indexer.py backend/tests/test_course_api.py
git commit -m "feat(api): index real course knowledge files"
```

## Task 6: Build the Read-Only Knowledge Browser

**Files:**
- Create: `Course-Agent/creative/components/knowledge/knowledge-tree.tsx`
- Create: `Course-Agent/creative/components/knowledge/document-preview.tsx`
- Create: `Course-Agent/creative/app/(platform)/knowledge/page.tsx`
- Create: `Course-Agent/creative/tests/knowledge/knowledge-page.test.tsx`

- [ ] **Step 1: Write failing knowledge page tests**

```tsx
it("renders real chapters and an explicit not-ready state", () => {
  const { rerender } = render(<KnowledgePageContent course={readyCourse} />)
  expect(screen.getByText("01 基础知识")).toBeInTheDocument()
  expect(screen.getByText("intro.md")).toBeInTheDocument()

  rerender(<KnowledgePageContent course={notReadyCourse} />)
  expect(screen.getByText("课程资料未同步")).toBeInTheDocument()
  expect(screen.queryByText("示例正文")).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/knowledge/knowledge-page.test.tsx
```

Expected: FAIL because knowledge components are absent.

- [ ] **Step 3: Implement chapter tree and preview selection**

Use an accordion/tree on the left and one unframed preview area on the right. Text/code previews use existing renderers; PDF/image/video use backend URLs. DOCX/PPTX show extracted text and a download button.

- [ ] **Step 4: Implement course selection and not-ready state**

Load `/api/course/list`, choose the current course, then load `/api/course/base`. Do not create placeholder chapters. Keep selection and scroll stable when revisiting the page.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/knowledge/knowledge-page.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit knowledge browser**

```powershell
git add 'Course-Agent/creative/app/(platform)/knowledge' Course-Agent/creative/components/knowledge Course-Agent/creative/tests/knowledge
git commit -m "feat(web): add read-only course knowledge browser"
```

## Task 7: Implement the Remote Agent Adapter and Explicit Fallback Policy

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/agents/remote.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/api/dependencies.py`
- Create: `backend/tests/test_remote_agent.py`
- Create: `backend/tests/test_agent_fallback.py`

- [ ] **Step 1: Write failing remote mapping test**

```py
@pytest.mark.asyncio
async def test_remote_profile_events_map_to_gateway_contract(remote_provider, mock_transport):
    mock_transport.queue_sse([
        {"type": "agent", "name": "画像抽取Agent", "progress": 10},
        {"type": "delta", "text": "正在提取画像"},
        {"type": "profile", "profile": valid_profile},
        {"type": "done"},
    ])
    events = [event async for event in remote_provider.stream_profile(
        task_id="task-1",
        trace_id="trace-1",
        user_id="student-001",
        chat_text="我想加强 ROS2 通信",
        current_profile=None,
    )]
    assert [event.event for event in events] == [
        "agent.started", "content.delta", "profile.patch", "task.completed",
    ]
```

Fallback test configures remote mode with a failing transport and asserts `UPSTREAM_TIMEOUT`, then enables `allow_mock_fallback` and asserts events are marked `demo_mode=true`.

Add companion mapping tests for:

- `stream_resources` returning ordered `ResourceAgentEvent` values with validated `ResourceDraft` payloads;
- `stream_qa` returning gateway text/media events;
- `build_learning_path` returning the fixed five-stage draft schema;
- `build_evaluation` returning validated score and recommendation fields.

- [ ] **Step 2: Add `httpx-sse` and verify tests fail**

Add `"httpx-sse>=0.4,<1"` and run:

```powershell
backend\.venv\Scripts\python -m pip install -e "backend[test]"
backend\.venv\Scripts\python -m pytest backend/tests/test_remote_agent.py backend/tests/test_agent_fallback.py -q
```

Expected: FAIL because the adapter is absent.

- [ ] **Step 3: Implement remote client and event mapping**

Add exact endpoint settings with these defaults:

```py
remote_profile_path: str = "/profile/stream"
remote_resources_path: str = "/resources/stream"
remote_qa_path: str = "/qa/stream"
remote_path_path: str = "/path"
remote_evaluation_path: str = "/evaluation"
```

Use one `httpx.AsyncClient` with configured base URL, bearer API key, and timeout. Parse upstream SSE with `aconnect_sse`. `RemoteAgentProvider` must implement `stream_profile`, `stream_resources`, `stream_qa`, `build_learning_path`, and `build_evaluation`. Map every upstream event through explicit functions; reject unknown required fields with `UPSTREAM_REJECTED`. Resource SSE maps to internal `ResourceAgentEvent`; profile and QA SSE map to public `GatewayEvent`; path and evaluation endpoints map JSON responses to their fixed draft schemas.

- [ ] **Step 4: Enforce fallback policy and run tests**

`get_agent_provider` returns `MockAgentProvider` only in mock mode. Remote errors propagate unless `allow_mock_fallback=true`; fallback events include `demo_mode=true`, and the frontend displays an “演示模式” banner.

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_remote_agent.py backend/tests/test_agent_fallback.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the remote adapter**

```powershell
git add backend/pyproject.toml backend/app/agents/remote.py backend/app/api/dependencies.py backend/tests/test_remote_agent.py backend/tests/test_agent_fallback.py
git commit -m "feat(api): add remote Agent service adapter"
```

## Task 8: Complete Error, Empty, Offline, and Partial-Success UI

**Files:**
- Create: shared state components listed in the file map.
- Modify: workspace, profile, QA, evaluation, knowledge, and resource cards.
- Create: `Course-Agent/creative/tests/shared/error-states.test.tsx`

- [ ] **Step 1: Write failing state mapping tests**

```tsx
it.each([
  ["VALIDATION_ERROR", "检查输入内容", false],
  ["CONTENT_BLOCKED", "调整问题后重试", false],
  ["UPSTREAM_TIMEOUT", "重试此任务", true],
  ["COURSE_NOT_READY", "课程资料未同步", false],
])("maps %s to the expected action", (code, label, retryable) => {
  render(<ErrorNotice error={{ code, message: "message", retryable, traceId: "trace-1" }} />)
  expect(screen.getByText(label)).toBeInTheDocument()
  expect(screen.queryByRole("button", { name: /重试/ }) !== null).toBe(retryable)
})
```

- [ ] **Step 2: Run and verify failure**

```powershell
pnpm --dir Course-Agent/creative test -- tests/shared/error-states.test.tsx
```

Expected: FAIL until state components are complete.

- [ ] **Step 3: Implement shared state components**

`EmptyState` accepts one icon, title, description, and optional single action. `OfflineBanner` is non-modal and does not hide cached data. `ResourceErrorBoundary` isolates a broken resource renderer and reports `trace_id` when present.

- [ ] **Step 4: Integrate partial-success and demo-mode indicators**

Completed resource cards stay visible when another type fails. Task rail shows individual retry eligibility. Remote fallback shows a persistent “演示模式” indicator; it must never look identical to real Agent output.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/shared tests/resources tests/profile tests/qa tests/evaluation tests/knowledge
```

Expected: PASS.

- [ ] **Step 5: Commit state handling**

```powershell
git add Course-Agent/creative/components/shared Course-Agent/creative/components/resources Course-Agent/creative/components/profile Course-Agent/creative/components/qa Course-Agent/creative/components/evaluation Course-Agent/creative/components/knowledge Course-Agent/creative/tests/shared
git commit -m "feat(web): unify errors and empty states"
```

## Task 9: Package Web, API, and Nginx with Docker Compose

**Files:**
- Modify: `Course-Agent/creative/next.config.mjs`
- Create: `Course-Agent/creative/Dockerfile`
- Create: `backend/Dockerfile`
- Create: `infra/nginx/default.conf`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `start.ps1`
- Create: `start.sh`

- [ ] **Step 1: Write failing deployment configuration checks**

Run before files exist:

```powershell
docker compose config
```

Expected: FAIL because `docker-compose.yml` is absent.

- [ ] **Step 2: Add production build configuration and Dockerfiles**

Set `output: "standalone"` in Next config. The web Dockerfile must use a Node 22 multi-stage pnpm build, set build argument `NEXT_PUBLIC_API_BASE_URL` to an empty string for same-origin Nginx access, and run `.next/standalone/server.js`. The API Dockerfile uses Python 3.12 slim, runs `pip install .` without test extras, creates a non-root user, and starts one Uvicorn worker.

`Course-Agent/creative/Dockerfile`:

```dockerfile
FROM node:22-alpine AS dependencies
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
RUN corepack enable
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL=""
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

`backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir . \
    && addgroup --system zhixue \
    && adduser --system --ingroup zhixue zhixue \
    && mkdir -p /app/data /app/media \
    && chown -R zhixue:zhixue /app
USER zhixue
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

- [ ] **Step 3: Add Nginx SSE-safe proxy configuration**

`infra/nginx/default.conf` must include:

```nginx
server {
listen 80;
server_name _;

location = /health {
    proxy_pass http://api:8000/health;
    proxy_set_header X-Trace-ID $request_id;
    proxy_set_header Host $host;
}

location /api/ {
    proxy_pass http://api:8000;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_set_header X-Trace-ID $request_id;
    proxy_set_header Host $host;
}

location /media/ {
    proxy_pass http://api:8000;
}

location / {
    proxy_pass http://web:3000;
}
}
```

- [ ] **Step 4: Add Compose volumes, health checks, and local scripts**

Compose services: `web`, `api`, `nginx`. Use this file:

```yaml
services:
  api:
    build:
      context: ./backend
    env_file: .env
    environment:
      DATABASE_URL: sqlite:////app/data/zhixue.db
      MEDIA_ROOT: /app/media
      COURSE_ROOT: /app/data/courses
    volumes:
      - zhixue-data:/app/data
      - zhixue-media:/app/media
      - ./backend/data/courses:/app/data/courses:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 10

  web:
    build:
      context: ./Course-Agent/creative
      args:
        NEXT_PUBLIC_API_BASE_URL: ""
    depends_on:
      api:
        condition: service_healthy

  nginx:
    image: nginx:1.27-alpine
    depends_on:
      - web
      - api
    ports:
      - "8080:80"
    volumes:
      - ./infra/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  zhixue-data:
  zhixue-media:
```

Add `course_root: Path = Path("./data/courses")` to backend settings.

`start.ps1` creates missing virtualenv/dependencies, starts API and web as hidden child processes writing to `artifacts/logs/`, prints URLs/PIDs, and stops both on Ctrl+C. `start.sh` performs equivalent startup with `trap` cleanup.

`start.ps1` core process management:

```powershell
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'Course-Agent\creative'
$Logs = Join-Path $Root 'artifacts\logs'
$Python = Join-Path $Backend '.venv\Scripts\python.exe'

New-Item -ItemType Directory -Force -Path $Logs | Out-Null
if (-not (Test-Path -LiteralPath $Python)) {
  python -m venv (Join-Path $Backend '.venv')
}
& $Python -m pip install -e "$Backend[test]"
corepack pnpm --dir $Frontend install --frozen-lockfile

$Api = Start-Process -FilePath $Python -ArgumentList @(
  '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1'
) -WorkingDirectory $Backend -RedirectStandardOutput (Join-Path $Logs 'api.log') -RedirectStandardError (Join-Path $Logs 'api-error.log') -WindowStyle Hidden -PassThru
$Web = Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('dev', '--hostname', '127.0.0.1') -WorkingDirectory $Frontend -RedirectStandardOutput (Join-Path $Logs 'web.log') -RedirectStandardError (Join-Path $Logs 'web-error.log') -WindowStyle Hidden -PassThru

Write-Host "Web: http://127.0.0.1:3000"
Write-Host "API: http://127.0.0.1:8000/docs"
Write-Host "PIDs: api=$($Api.Id), web=$($Web.Id)"
try {
  Wait-Process -Id $Api.Id, $Web.Id
} finally {
  Stop-Process -Id $Api.Id, $Web.Id -Force -ErrorAction SilentlyContinue
}
```

`start.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/artifacts/logs"
python3 -m venv "$ROOT/backend/.venv"
"$ROOT/backend/.venv/bin/python" -m pip install -e "$ROOT/backend[test]"
corepack pnpm --dir "$ROOT/Course-Agent/creative" install --frozen-lockfile
"$ROOT/backend/.venv/bin/python" -m uvicorn app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000 --workers 1 >"$ROOT/artifacts/logs/api.log" 2>&1 &
API_PID=$!
corepack pnpm --dir "$ROOT/Course-Agent/creative" dev --hostname 127.0.0.1 >"$ROOT/artifacts/logs/web.log" 2>&1 &
WEB_PID=$!
trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM
echo "Web: http://127.0.0.1:3000"
echo "API: http://127.0.0.1:8000/docs"
wait "$API_PID" "$WEB_PID"
```

Root `.env.example`:

```dotenv
AGENT_MODE=mock
REMOTE_AGENT_BASE_URL=
REMOTE_AGENT_API_KEY=
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
WEB_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080
```

Run:

```powershell
docker compose config
docker compose build
docker compose up -d
Invoke-RestMethod http://localhost:8080/health
docker compose down
```

Expected: config/build succeed and health returns `status=ok`.

- [ ] **Step 5: Commit deployment assets**

```powershell
git add Course-Agent/creative/next.config.mjs Course-Agent/creative/Dockerfile backend/Dockerfile infra/nginx/default.conf docker-compose.yml .env.example start.ps1 start.sh
git commit -m "build: add local and Docker deployment"
```

## Task 10: Write Component, API, Deployment, and Demo Documentation

**Files:**
- Rewrite: `README.md`
- Create: `docs/components.md`
- Create: `docs/api-integration.md`
- Create: `docs/deployment.md`
- Create: `docs/demo-script.md`
- Update: `docs/conversation-summaries/2026-07-10-zhixue-engine-brainstorm-summary.md`

- [ ] **Step 1: Write a documentation acceptance checklist**

Create `docs/test-documentation.ps1`:

```powershell
$required = @(
  'README.md',
  'docs/components.md',
  'docs/api-integration.md',
  'docs/deployment.md',
  'docs/demo-script.md',
  'backend/.env.example',
  'Course-Agent/creative/.env.example'
)
$missing = $required | Where-Object { -not (Test-Path -LiteralPath $_) }
if ($missing) { throw "Missing documentation: $($missing -join ', ')" }

$apiDoc = Get-Content -Raw -Encoding UTF8 'docs/api-integration.md'
foreach ($needle in @('/api/chat/profile', '/api/resource/generate', '/api/chat/qa', 'Last-Event-ID', 'AGENT_MODE')) {
  if (-not $apiDoc.Contains($needle)) { throw "API documentation missing $needle" }
}
```

- [ ] **Step 2: Run and verify failure**

```powershell
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
```

Expected: FAIL until all required documents exist.

- [ ] **Step 3: Write the documentation**

- `README.md`: product purpose, architecture, prerequisites, one-command startup, URLs, tests, project tree.
- `docs/components.md`: responsibilities, props/data ownership, renderer contracts, no nested-card rule.
- `docs/api-integration.md`: every endpoint, request/response examples, SSE event examples, error codes, remote provider mapping checklist.
- `docs/deployment.md`: Windows, Linux, Docker Compose, volumes, backups, Nginx/HTTPS, remote API environment variables.
- `docs/demo-script.md`: ordered 6-10 minute demonstration and fallback steps.
- Conversation summary: add implementation status and artifact links without deleting brainstorming decisions.

- [ ] **Step 4: Run documentation checks and link validation**

```powershell
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
$placeholderPattern = @('T' + 'BD', 'T' + 'ODO', 'FIX' + 'ME') -join '|'
Get-ChildItem README.md,docs -Recurse -File -Include *.md | Select-String -Pattern $placeholderPattern
```

Expected: checklist passes and placeholder scan returns no matches.

- [ ] **Step 5: Commit documentation**

```powershell
git add README.md docs backend/.env.example Course-Agent/creative/.env.example
git commit -m "docs: add platform integration and deployment guides"
```

## Task 11: Capture Full-Page Screenshots, Video, and Accessibility Evidence

**Files:**
- Modify: `Course-Agent/creative/playwright.config.ts`
- Create: `Course-Agent/creative/e2e/full-platform-flow.spec.ts`
- Create: `Course-Agent/creative/e2e/visual-capture.spec.ts`
- Create: `Course-Agent/creative/e2e/layout-audit.ts`
- Create: `artifacts/screenshots/*.png` through the test.
- Create: `artifacts/demo/*` through the test.

- [ ] **Step 1: Add failing visual and accessibility assertions**

Install:

```powershell
pnpm --dir Course-Agent/creative add -D @axe-core/playwright
```

`layout-audit.ts`:

```ts
import { expect, type Page } from "@playwright/test"

export async function expectNoHorizontalOverflow(page: Page) {
  const metrics = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }))
  expect(metrics.document).toBeLessThanOrEqual(metrics.viewport)
}
```

The visual test must run Axe and fail on any `critical` impact violation.

- [ ] **Step 2: Configure screenshot/video outputs and verify initial failures**

Enable Playwright video `on`, trace `on-first-retry`, and projects for 1366x768, 1440x900, and 1920x1080. Run:

```powershell
pnpm --dir Course-Agent/creative test:e2e -- e2e/visual-capture.spec.ts
```

Expected: FAIL until every page/state has deterministic setup and capture code.

- [ ] **Step 3: Implement deterministic capture scenarios**

Capture these named files under `artifacts/screenshots/`:

```text
01-login.png
02-profile-stream.png
03-workspace-generating.png
04-workspace-results.png
05-resource-quiz.png
06-learning-path.png
07-qa-drawer.png
08-evaluation.png
09-knowledge.png
10-network-error.png
11-agent-failure.png
```

Use API seed helpers and mock delay controls so streaming/progress screenshots are stable. When real course files are absent, `09-knowledge.png` must show the truthful not-ready state.

- [ ] **Step 4: Run full browser QA and inspect artifacts**

```powershell
pnpm --dir Course-Agent/creative test:e2e
Get-ChildItem artifacts/screenshots/*.png | Select-Object Name,Length
Get-ChildItem artifacts/demo -Recurse -File | Select-Object Name,Length
```

Expected: all browser tests pass; every screenshot is non-empty; one main-flow video and trace exist. Visually inspect all screenshots for overlap, clipped text, blank media, and missing Agent progress.

- [ ] **Step 5: Commit deterministic screenshots and scripts**

Commit screenshots and the selected final demo video if repository size is acceptable; otherwise commit scripts plus `artifacts/README.md` and keep large raw traces ignored.

```powershell
git add Course-Agent/creative/playwright.config.ts Course-Agent/creative/e2e Course-Agent/creative/package.json Course-Agent/creative/pnpm-lock.yaml artifacts/screenshots artifacts/README.md
git commit -m "test: capture full platform demonstration"
```

## Task 12: Run Final Verification and Release Audit

**Files:**
- Modify only files required by failing checks.
- Update: `docs/conversation-summaries/2026-07-10-zhixue-engine-brainstorm-summary.md` with final verification results.

- [ ] **Step 1: Run backend verification**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
```

Expected: all tests pass with no warnings that indicate unclosed clients, leaked tasks, or database locks.

- [ ] **Step 2: Run frontend verification**

```powershell
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e
```

Expected: every command exits `0`.

- [ ] **Step 3: Run legacy, contract, and deployment audits**

```powershell
pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
backend\.venv\Scripts\python backend\scripts\export_openapi.py
pnpm --dir Course-Agent/creative api:types
git diff --exit-code -- Course-Agent/creative/lib/api/generated.ts
docker compose config
docker compose up -d --build
Invoke-RestMethod http://localhost:8080/health
docker compose down
```

Expected: all pass; generated API types are current; containers become healthy.

- [ ] **Step 4: Audit Git and document final evidence**

```powershell
git status --short
git log --oneline --decorate -20
```

Update the conversation summary with exact passing command results, startup URLs, screenshot paths, remaining external prerequisites, and the final commit ID. Do not claim real Agent or formal course-content integration when those inputs are still absent.

- [ ] **Step 5: Commit final audit corrections**

```powershell
git add docs/conversation-summaries/2026-07-10-zhixue-engine-brainstorm-summary.md
git commit -m "chore: finalize Zhixue Engine delivery"
```

Expected: commit contains the final verification evidence only. Commit any code correction immediately with its owning task before this step; do not sweep unrelated files into the final commit. If the summary did not change, do not create an empty commit.

## Phase 3 Completion Check

The project is complete when:

- Mock mode runs all seven business scenarios end to end.
- Remote mode has a tested adapter and never silently fabricates results.
- QA supports text/image/video response modes with local mock media.
- Evaluation reads persisted behavior and applies one new path version idempotently.
- Knowledge pages index only real files and show a truthful empty state otherwise.
- Windows scripts and Docker Compose start the product.
- Full tests, typecheck, build, OpenAPI drift check, accessibility audit, screenshots, and demo recording pass.
- Documentation names the external Agent endpoints and course files as the only remaining teammate inputs.
