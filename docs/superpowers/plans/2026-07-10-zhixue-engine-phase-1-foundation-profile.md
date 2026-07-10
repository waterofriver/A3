# Zhixue Engine Phase 1 Foundation and Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the active legacy shell with a tested Zhixue Engine application shell and deliver a working user initialization plus six-dimension profile collection flow backed by FastAPI, SQLite, and a deterministic mock agent.

**Architecture:** Keep the existing Next.js project and shadcn/ui components, but remove the active monolithic creative/Coze/forum experience. Add a new FastAPI application with a SQLite repository layer, a stable gateway event schema, and a mock `AgentProvider` that streams profile events. Generate frontend API types from FastAPI OpenAPI.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, TanStack Query, Vitest, Testing Library, Playwright, FastAPI, SQLAlchemy 2, Pydantic 2, pytest, HTTPX.

---

## File Map

### Repository

- Modify: `.gitignore` - ignore brainstorm, generated databases, media, coverage, and test artifacts.
- Track: existing `Course-Agent/`, `mywebsite/`, root manifests, and documentation as the source baseline.

### Frontend

- Modify: `Course-Agent/creative/package.json` - strict scripts and runtime/test dependencies.
- Modify: `Course-Agent/creative/next.config.mjs` - remove ignored TypeScript failures.
- Create: `Course-Agent/creative/vitest.config.ts` - component test configuration.
- Create: `Course-Agent/creative/tests/setup.ts` - jest-dom setup.
- Create: `Course-Agent/creative/app/providers.tsx` - TanStack Query provider.
- Modify: `Course-Agent/creative/app/layout.tsx` - Zhixue metadata and providers; no Coze.
- Modify: `Course-Agent/creative/app/globals.css` - A3 visual tokens and stable desktop shell styles.
- Replace: `Course-Agent/creative/app/page.tsx` - client bootstrap redirect.
- Create: `Course-Agent/creative/app/(auth)/login/page.tsx` - simple user ID login.
- Create: `Course-Agent/creative/app/(platform)/layout.tsx` - guarded platform shell.
- Create: `Course-Agent/creative/app/(platform)/profile/page.tsx` - profile collection page.
- Create: `Course-Agent/creative/app/(platform)/workspace/page.tsx` - phase 1 gated workspace empty state.
- Create: `Course-Agent/creative/components/app-shell/app-shell.tsx` - fixed desktop navigation shell.
- Create: `Course-Agent/creative/components/app-shell/session-guard.tsx` - local user guard.
- Create: `Course-Agent/creative/components/profile/profile-chat.tsx` - streaming conversation.
- Create: `Course-Agent/creative/components/profile/profile-panel.tsx` - fixed six-dimension display.
- Create: `Course-Agent/creative/components/profile/profile-page.tsx` - profile flow coordinator.
- Create: `Course-Agent/creative/components/shared/agent-progress.tsx` - shared current-agent progress.
- Create: `Course-Agent/creative/components/shared/error-notice.tsx` - normalized error presentation.
- Create: `Course-Agent/creative/lib/api/client.ts` - JSON API client and error mapping.
- Create: `Course-Agent/creative/lib/api/generated.ts` - generated OpenAPI types.
- Create: `Course-Agent/creative/lib/session/user-session.ts` - local user ID accessors.
- Create: `Course-Agent/creative/lib/sse/post-event-stream.ts` - POST stream reader.
- Create: `Course-Agent/creative/lib/sse/task-reducer.ts` - ordered event reducer.
- Create: `Course-Agent/creative/lib/query/keys.ts` - stable query keys.
- Create: `Course-Agent/creative/tests/session/user-session.test.ts`.
- Create: `Course-Agent/creative/tests/sse/task-reducer.test.ts`.
- Create: `Course-Agent/creative/tests/profile/profile-panel.test.tsx`.
- Create: `Course-Agent/creative/playwright.config.ts`.
- Create: `Course-Agent/creative/e2e/profile-flow.spec.ts`.

### Backend

- Create: `backend/pyproject.toml` - dependencies and pytest configuration.
- Create: `backend/app/__init__.py`.
- Create: `backend/app/main.py` - application factory and lifespan.
- Create: `backend/app/core/config.py` - environment settings.
- Create: `backend/app/core/errors.py` - error codes and handlers.
- Create: `backend/app/core/logging.py` - trace ID middleware and structured logs.
- Create: `backend/app/db/base.py` - SQLAlchemy declarative base.
- Create: `backend/app/db/database.py` - engine/session wrapper.
- Create: `backend/app/db/models.py` - users, profiles, messages, tasks, events.
- Create: `backend/app/repositories/users.py`.
- Create: `backend/app/repositories/profiles.py`.
- Create: `backend/app/repositories/tasks.py`.
- Create: `backend/app/schemas/common.py` - response/error envelopes.
- Create: `backend/app/schemas/profile.py` - six-dimension profile schemas.
- Create: `backend/app/schemas/task.py` - event and task schemas.
- Create: `backend/app/agents/base.py` - provider protocol.
- Create: `backend/app/agents/mock.py` - deterministic profile stream.
- Create: `backend/app/services/profile_service.py` - persistence and event orchestration.
- Create: `backend/app/api/dependencies.py` - database/provider dependencies.
- Create: `backend/app/api/routes/health.py`.
- Create: `backend/app/api/routes/users.py`.
- Create: `backend/app/api/routes/profile.py`.
- Create: `backend/scripts/export_openapi.py`.
- Create: `backend/tests/conftest.py`.
- Create: `backend/tests/test_health.py`.
- Create: `backend/tests/test_users.py`.
- Create: `backend/tests/test_profile_stream.py`.
- Create: `backend/tests/test_task_repository.py`.

### Legacy Removal

- Delete: `Course-Agent/creative/components/coze-chat.tsx`.
- Delete: `Course-Agent/creative/app/api/coze/token/route.ts`.
- Delete: `Course-Agent/creative/app/api/auth/login/route.ts`.
- Delete: `Course-Agent/creative/app/api/auth/register/route.ts`.
- Delete: `Course-Agent/creative/components/creative.tsx` after its active replacement is verified.
- Delete: `Course-Agent/creative/app/main/page.tsx`.
- Delete: root `package.json` and root `pnpm-lock.yaml` after confirming they only exist for `@coze/api`.
- Modify: `mywebsite/mywebsite/urls.py` - remove the active `core.urls` include while keeping legacy resource/admin references.

## Task 1: Establish Repository Hygiene and a Source Baseline

**Files:**
- Modify: `.gitignore`
- Inspect: all currently untracked source files

- [ ] **Step 1: Verify brainstorm files are currently visible to Git**

Run:

```powershell
git check-ignore .superpowers/brainstorm/probe.txt
```

Expected: exit code `1`, proving `.superpowers/` is not yet ignored.

- [ ] **Step 2: Add project-specific generated paths to `.gitignore`**

Append exactly:

```gitignore

# Codex design companion and generated delivery artifacts
.superpowers/
backend/.venv/
backend/data/*.db
backend/data/*.db-*
backend/media/generated/
backend/openapi.json
backend/data/courses/
artifacts/playwright/
artifacts/test-results/
artifacts/logs/
Course-Agent/creative/playwright-report/
Course-Agent/creative/test-results/
mywebsite/upload/
!.env.example
!**/.env.example
```

- [ ] **Step 3: Verify ignore rules and scan tracked candidates for obvious secrets**

Run:

```powershell
git check-ignore .superpowers/brainstorm/probe.txt
Get-ChildItem Course-Agent,mywebsite -Recurse -File |
  Where-Object { $_.FullName -notmatch '\\(node_modules|\.next|upload)\\' } |
  Select-String -Pattern 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|sk-[A-Za-z0-9]{20,}|COZE_PRIVATE_KEY\s*=' -List
```

Expected: `git check-ignore` prints the probe path; the secret scan prints no real credential values. If a real secret is found, stop and remove it from the baseline before staging.

- [ ] **Step 4: Commit the existing source baseline without generated folders**

Run:

```powershell
git add .gitignore Course-Agent mywebsite package.json pnpm-lock.yaml README.md LICENSE
git status --short
git commit -m "chore: track existing application baseline"
```

Expected: `.superpowers/` remains untracked/ignored; the commit contains the existing application source. If root `package.json` or `pnpm-lock.yaml` has already been deleted, omit those two paths.

- [ ] **Step 5: Verify the baseline commit**

Run:

```powershell
git show --stat --oneline HEAD
git status --short
```

Expected: source baseline is committed; only intentionally untracked files remain.

## Task 2: Add Strict Frontend Tooling

**Files:**
- Modify: `Course-Agent/creative/package.json`
- Modify: `Course-Agent/creative/next.config.mjs`
- Create: `Course-Agent/creative/vitest.config.ts`
- Create: `Course-Agent/creative/tests/setup.ts`

- [ ] **Step 1: Add the frontend runtime and test dependencies**

Run from `Course-Agent/creative`:

```powershell
pnpm add @tanstack/react-query eventsource-parser react-markdown remark-gfm rehype-highlight @xyflow/react
pnpm add -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitejs/plugin-react vite-tsconfig-paths @playwright/test openapi-typescript eslint eslint-config-next
```

Expected: `package.json` and `pnpm-lock.yaml` update successfully.

- [ ] **Step 2: Replace the scripts block with strict commands**

Use:

```json
"scripts": {
  "build": "next build",
  "dev": "next dev",
  "lint": "eslint .",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test",
  "api:types": "openapi-typescript ../../backend/openapi.json -o lib/api/generated.ts",
  "start": "next start"
}
```

Remove the `typescript.ignoreBuildErrors` block from `next.config.mjs`; keep `images.unoptimized` for local media compatibility.

- [ ] **Step 3: Create Vitest configuration and setup**

`Course-Agent/creative/vitest.config.ts`:

```ts
import react from "@vitejs/plugin-react"
import tsconfigPaths from "vite-tsconfig-paths"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
})
```

`Course-Agent/creative/tests/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest"
```

- [ ] **Step 4: Run the strict commands to record the legacy failures**

Run:

```powershell
pnpm typecheck
pnpm test
```

Expected: typecheck may fail in legacy files and tests may report no test files. Record the exact failures; do not restore `ignoreBuildErrors`.

- [ ] **Step 5: Commit tooling changes**

```powershell
git add Course-Agent/creative/package.json Course-Agent/creative/pnpm-lock.yaml Course-Agent/creative/next.config.mjs Course-Agent/creative/vitest.config.ts Course-Agent/creative/tests/setup.ts
git commit -m "build: enforce frontend type and test checks"
```

## Task 3: Scaffold FastAPI and the Health Contract

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/database.py`
- Create: `backend/app/api/routes/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing health test**

`backend/tests/test_health.py`:

```py
def test_health_reports_database_and_agent_mode(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "agent_mode": "mock",
    }
```

`backend/tests/conftest.py`:

```py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        agent_mode="mock",
        mock_event_delay_ms=0,
    )


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client
```

- [ ] **Step 2: Add Python dependencies and verify the test fails**

`backend/pyproject.toml`:

```toml
[project]
name = "zhixue-engine-gateway"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115,<1",
  "uvicorn[standard]>=0.34,<1",
  "sqlalchemy>=2.0,<3",
  "alembic>=1.14,<2",
  "pydantic-settings>=2.7,<3",
  "httpx>=0.28,<1",
]

[project.optional-dependencies]
test = [
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.25,<1",
]

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["app*"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Run from `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[test]"
.\.venv\Scripts\python -m pytest tests/test_health.py -q
```

Expected: FAIL because `app.main` and settings do not exist.

- [ ] **Step 3: Implement settings, application factory, and health route**

`backend/app/core/config.py`:

```py
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/zhixue.db"
    agent_mode: Literal["mock", "remote"] = "mock"
    mock_event_delay_ms: int = 40
    remote_agent_base_url: str = ""
    remote_agent_api_key: str = ""
    remote_agent_timeout_seconds: int = 120
    allow_mock_fallback: bool = False
```

`backend/app/api/routes/health.py`:

```py
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    request.app.state.db.ping()
    return {
        "status": "ok",
        "database": "ok",
        "agent_mode": request.app.state.settings.agent_mode,
    }
```

`backend/app/db/base.py`:

```py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/db/database.py`:

```py
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


class Database:
    def __init__(self, url: str):
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def dispose(self) -> None:
        self.engine.dispose()
```

`backend/app/main.py`:

```py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import Settings
from app.db.database import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    db = Database(resolved.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.create_schema()
        yield
        db.dispose()

    app = FastAPI(title="Zhixue Engine Gateway", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved
    app.state.db = db
    app.include_router(health_router)
    return app


app = create_app()
```

Create empty `__init__.py` files for each Python package used above.

- [ ] **Step 4: Run the health test**

```powershell
.\.venv\Scripts\python -m pytest tests/test_health.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the FastAPI scaffold**

```powershell
git add backend
git commit -m "feat(api): scaffold FastAPI health service"
```

## Task 4: Add the SQLite Database and Core Models

**Files:**
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/db/database.py`
- Create: `backend/app/db/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/versions/*_initial_core.py`
- Create: `backend/app/repositories/users.py`
- Create: `backend/app/repositories/profiles.py`
- Create: `backend/app/repositories/tasks.py`
- Create: `backend/tests/test_task_repository.py`

- [ ] **Step 1: Write failing repository tests**

`backend/tests/test_task_repository.py`:

```py
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository


def test_user_creation_and_task_event_sequence(client):
    db = client.app.state.db
    with db.session() as session:
        user = UserRepository(session).get_or_create("student-001")
        task = TaskRepository(session).create(
            user_id=user.id,
            task_type="profile",
            request_snapshot={"chat_text": "我想学习 ROS2"},
        )
        first = TaskRepository(session).append_event(task.id, "task.started", {"progress": 0})
        second = TaskRepository(session).append_event(task.id, "content.delta", {"content": "你好"})

        assert first.seq == 1
        assert second.seq == 2
        assert TaskRepository(session).get(task.id).status == "queued"
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
.\.venv\Scripts\python -m pytest tests/test_task_repository.py -q
```

Expected: FAIL because the models and repositories are absent.

- [ ] **Step 3: Implement the database wrapper and models**

`backend/app/db/base.py`:

```py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/db/database.py`:

```py
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


class Database:
    def __init__(self, url: str):
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        from app.db import models  # noqa: F401
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def dispose(self) -> None:
        self.engine.dispose()
```

`backend/app/db/models.py` must define `User`, `StudentProfile`, `ProfileMessage`, `Task`, and `TaskEvent` with UUID string IDs, JSON payload columns, timestamps, a unique `(task_id, seq)` constraint, and a unique `(user_id, idempotency_key)` task constraint when the key is non-null. Use the following task fields exactly:

```py
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_agent: Mapped[str | None] = mapped_column(String(80), nullable=True)
    request_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    result_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
```

- [ ] **Step 4: Implement repository methods and rerun tests**

Implement the repositories with these concrete method bodies (add the shown SQLAlchemy imports):

```py
class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create(self, user_id: str) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            user = User(id=user_id)
            self.session.add(user)
            self.session.flush()
        return user

class ProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: str) -> StudentProfile | None:
        return self.session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )

    def upsert(self, user_id: str, profile: dict, revision: int) -> StudentProfile:
        current = self.get(user_id)
        if current is None:
            current = StudentProfile(
                id=str(uuid4()),
                user_id=user_id,
                profile_data=profile,
                revision=revision,
            )
            self.session.add(current)
        else:
            current.profile_data = profile
            current.revision = revision
        self.session.flush()
        return current

    def confirm(self, user_id: str) -> StudentProfile:
        profile = self.get(user_id)
        if profile is None:
            raise LookupError(user_id)
        profile.confirmed_at = utcnow()
        self.session.flush()
        return profile

class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: str, task_type: str, request_snapshot: dict, idempotency_key: str | None = None) -> Task:
        task = Task(
            id=str(uuid4()),
            user_id=user_id,
            task_type=task_type,
            request_snapshot=request_snapshot,
            idempotency_key=idempotency_key,
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, task_id: str) -> Task:
        task = self.session.get(Task, task_id)
        if task is None:
            raise LookupError(task_id)
        return task

    def append_event(self, task_id: str, event_type: str, payload: dict) -> TaskEvent:
        next_seq = self.session.scalar(
            select(func.coalesce(func.max(TaskEvent.seq), 0) + 1)
            .where(TaskEvent.task_id == task_id)
        )
        event = TaskEvent(
            id=str(uuid4()),
            task_id=task_id,
            seq=int(next_seq),
            event_type=event_type,
            payload=payload,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def update_state(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        current_agent: str | None = None,
        result_snapshot: dict | None = None,
        error: dict | None = None,
    ) -> Task:
        task = self.get(task_id)
        task.status = status
        task.progress = progress
        task.current_agent = current_agent
        if result_snapshot is not None:
            task.result_snapshot = result_snapshot
        task.error = error
        self.session.flush()
        return task
```

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_task_repository.py tests/test_health.py -q
```

Expected: PASS.

- [ ] **Step 5: Create and verify the initial Alembic migration, then commit**

Run from `backend`:

```powershell
.\.venv\Scripts\python -m alembic init migrations
```

In `migrations/env.py`, import `Base` and all models, set `target_metadata = Base.metadata`, and override the URL before `run_migrations_online()`:

```py
from app.core.config import Settings
from app.db.base import Base
from app.db import models  # noqa: F401

config.set_main_option("sqlalchemy.url", Settings().database_url)
target_metadata = Base.metadata
```

Generate and verify:

```powershell
.\.venv\Scripts\python -m alembic revision --autogenerate -m "initial core"
$env:DATABASE_URL="sqlite:///./data/migration-check.db"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m alembic current
Remove-Item Env:DATABASE_URL
```

Expected: `current` prints the generated revision with `(head)` and the database contains users, profiles, messages, tasks, and task events.

```powershell
git add backend/app/db backend/app/repositories backend/alembic.ini backend/migrations backend/tests/test_task_repository.py
git commit -m "feat(api): add SQLite task and profile storage"
```

## Task 5: Define Errors, Trace IDs, and Gateway Events

**Files:**
- Create: `backend/app/core/errors.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/app/schemas/task.py`
- Create: `backend/app/api/routes/tasks.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_error_contract.py`

- [ ] **Step 1: Write the failing error contract test**

```py
def test_unknown_task_returns_normalized_error(client):
    response = client.get("/api/task/missing")

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == {
        "code": "TASK_NOT_FOUND",
        "message": "任务不存在或已被清理。",
        "retryable": False,
        "details": None,
    }
    assert body["trace_id"]
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
.\.venv\Scripts\python -m pytest tests/test_error_contract.py -q
```

Expected: FAIL because the task route and normalized handler are absent.

- [ ] **Step 3: Implement the error and event schemas**

`backend/app/schemas/task.py`:

```py
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "task.started",
    "agent.started",
    "task.progress",
    "content.delta",
    "profile.patch",
    "media.ready",
    "resource.ready",
    "task.completed",
    "task.failed",
    "heartbeat",
]


class GatewayError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: Any | None = None


class GatewayEvent(BaseModel):
    event: EventType
    task_id: str
    seq: int = 0
    trace_id: str
    current_agent: str | None = None
    progress: int = Field(default=0, ge=0, le=100)
    resource_type: str | None = None
    content: str = ""
    media_url: str | None = None
    finish_flag: bool = False
    resource_ids: list[str] = Field(default_factory=list)
    profile_patch: dict[str, Any] | None = None
    error: GatewayError | None = None
    demo_mode: bool = False
```

`AppError` must carry `status_code`, `code`, `message`, `retryable`, and `details`. Add middleware that creates or forwards `X-Trace-ID`, places it on `request.state.trace_id`, and returns it in every response header.

- [ ] **Step 4: Add `GET /api/task/{task_id}` and rerun the contract test**

The route returns a task snapshot when found and raises:

```py
raise AppError(
    status_code=404,
    code="TASK_NOT_FOUND",
    message="任务不存在或已被清理。",
    retryable=False,
)
```

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_error_contract.py -q
```

Expected: PASS and response includes `X-Trace-ID`.

- [ ] **Step 5: Commit the contract layer**

```powershell
git add backend/app/core backend/app/schemas backend/app/api/routes backend/app/main.py backend/tests/test_error_contract.py
git commit -m "feat(api): normalize gateway events and errors"
```

## Task 6: Implement the Six-Dimension Profile Mock Provider

**Files:**
- Create: `backend/app/schemas/profile.py`
- Create: `backend/app/agents/base.py`
- Create: `backend/app/agents/mock.py`
- Create: `backend/tests/test_mock_profile_agent.py`

- [ ] **Step 1: Write the failing provider test**

```py
import pytest

from app.agents.mock import MockAgentProvider


@pytest.mark.asyncio
async def test_mock_profile_stream_emits_fixed_profile_schema(settings):
    provider = MockAgentProvider(settings)
    events = [event async for event in provider.stream_profile(
        task_id="task-1",
        trace_id="trace-1",
        user_id="student-001",
        chat_text="我在 ROS2 节点通信方面基础薄弱，喜欢代码案例。",
        current_profile=None,
    )]

    assert events[0].event == "task.started"
    patch = next(event.profile_patch for event in events if event.event == "profile.patch")
    assert set(patch) == {
        "knowledge_foundation",
        "cognitive_style",
        "weak_points",
        "learning_pace",
        "content_preferences",
        "short_term_goal",
    }
    assert events[-1].event == "task.completed"
    assert events[-1].finish_flag is True
```

- [ ] **Step 2: Run the provider test and verify it fails**

```powershell
.\.venv\Scripts\python -m pytest tests/test_mock_profile_agent.py -q
```

Expected: FAIL because the provider is absent.

- [ ] **Step 3: Implement profile schemas and provider protocol**

`backend/app/schemas/profile.py`:

```py
from pydantic import BaseModel, Field


class StudentProfileData(BaseModel):
    knowledge_foundation: str = "待采集"
    cognitive_style: str = "待采集"
    weak_points: list[str] = Field(default_factory=list)
    learning_pace: str = "待采集"
    content_preferences: list[str] = Field(default_factory=list)
    short_term_goal: str = "待采集"


class ProfileChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    chat_text: str = Field(min_length=1, max_length=4000)
```

Use an abstract base class so the method contract is explicit without a placeholder body:

```py
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas.profile import StudentProfileData
from app.schemas.task import GatewayEvent


class AgentProvider(ABC):
    @abstractmethod
    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
        current_profile: StudentProfileData | None,
    ) -> AsyncIterator[GatewayEvent]:
        raise NotImplementedError
```

Do not add resource or QA methods until their phases.

- [ ] **Step 4: Implement deterministic mock events and rerun the test**

Use this profile mapping in `MockAgentProvider`:

```py
profile = StudentProfileData(
    knowledge_foundation="具备入门基础，需要通过结构化练习巩固概念。",
    cognitive_style="偏好案例驱动与步骤化讲解。",
    weak_points=[chat_text.strip()[:80]],
    learning_pace="分阶段推进，每个阶段包含讲解与练习。",
    content_preferences=["图解", "代码案例"],
    short_term_goal="完成当前课程薄弱知识点的强化学习。",
)
```

Emit events in this order: `task.started`, `agent.started`, two `content.delta` events, `profile.patch`, `task.completed`. Sleep for `mock_event_delay_ms` between events.

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_mock_profile_agent.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the mock provider**

```powershell
git add backend/app/agents backend/app/schemas/profile.py backend/tests/test_mock_profile_agent.py
git commit -m "feat(api): stream deterministic profile agent events"
```

## Task 7: Deliver User Info, Profile Streaming, and Confirmation APIs

**Files:**
- Create: `backend/app/api/dependencies.py`
- Create: `backend/app/api/routes/users.py`
- Create: `backend/app/api/routes/profile.py`
- Create: `backend/app/services/profile_service.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_users.py`
- Create: `backend/tests/test_profile_stream.py`

- [ ] **Step 1: Write failing API tests**

`backend/tests/test_users.py`:

```py
def test_unknown_user_returns_exists_false(client):
    response = client.get("/api/user/info", params={"user_id": "new-student"})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "exists": False,
        "user_id": "new-student",
        "display_name": None,
        "profile": None,
        "profile_confirmed": False,
    }
```

`backend/tests/test_profile_stream.py`:

```py
def test_profile_stream_persists_profile_and_can_be_confirmed(client):
    with client.stream(
        "POST",
        "/api/chat/profile",
        json={"user_id": "student-001", "chat_text": "我想加强 ROS2 通信"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-task-id"]
    assert "event: profile.patch" in body
    assert "event: task.completed" in body

    confirm = client.post("/api/profile/confirm", json={"user_id": "student-001"})
    assert confirm.status_code == 200
    assert confirm.json()["data"]["profile_confirmed"] is True
```

- [ ] **Step 2: Run both tests and verify they fail**

```powershell
.\.venv\Scripts\python -m pytest tests/test_users.py tests/test_profile_stream.py -q
```

Expected: FAIL because the routes are absent.

- [ ] **Step 3: Implement SSE encoding and the profile service**

Use this encoder:

```py
def encode_sse(event: GatewayEvent) -> str:
    return (
        f"id: {event.seq}\n"
        f"event: {event.event}\n"
        f"data: {event.model_dump_json()}\n\n"
    )
```

`ProfileService.stream_profile` must:

1. create/get the user;
2. create a `profile` task;
3. iterate provider events;
4. assign persisted sequence numbers;
5. persist each event;
6. upsert `profile.patch` data;
7. update task status/progress;
8. yield encoded events.

- [ ] **Step 4: Implement routes and verify API behavior**

`POST /api/chat/profile` creates the task before constructing the response, then returns:

```py
stream = service.stream_profile(
    task_id=task.id,
    trace_id=request.state.trace_id,
    user_id=payload.user_id,
    chat_text=payload.chat_text,
)
return StreamingResponse(
    stream,
    media_type="text/event-stream",
    headers={"X-Task-ID": task.id, "Cache-Control": "no-cache"},
)
```

`POST /api/profile/confirm` rejects a missing profile with `VALIDATION_ERROR` and confirms an existing profile.

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_users.py tests/test_profile_stream.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit profile APIs**

```powershell
git add backend/app/api backend/app/services backend/app/main.py backend/tests/test_users.py backend/tests/test_profile_stream.py
git commit -m "feat(api): add profile collection endpoints"
```

## Task 8: Export OpenAPI and Generate Frontend Types

**Files:**
- Create: `backend/scripts/export_openapi.py`
- Create: `Course-Agent/creative/lib/api/generated.ts`
- Create: `Course-Agent/creative/lib/api/client.ts`
- Create: `Course-Agent/creative/tests/api/client.test.ts`

- [ ] **Step 1: Write the failing frontend API error test**

```ts
import { describe, expect, it, vi } from "vitest"

import { ApiError, apiFetch } from "@/lib/api/client"

describe("apiFetch", () => {
  it("maps the gateway error envelope", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: {
        code: "TASK_NOT_FOUND",
        message: "任务不存在或已被清理。",
        retryable: false,
        details: null,
      },
      trace_id: "trace-1",
    }), { status: 404, headers: { "content-type": "application/json" } })))

    await expect(apiFetch("/api/task/missing")).rejects.toEqual(
      new ApiError("TASK_NOT_FOUND", "任务不存在或已被清理。", false, "trace-1"),
    )
  })
})
```

- [ ] **Step 2: Export OpenAPI and verify the test fails**

`backend/scripts/export_openapi.py`:

```py
import json
from pathlib import Path

from app.main import create_app

target = Path(__file__).resolve().parents[1] / "openapi.json"
target.write_text(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
print(target)
```

Run:

```powershell
backend\.venv\Scripts\python backend\scripts\export_openapi.py
pnpm --dir Course-Agent/creative api:types
pnpm --dir Course-Agent/creative test -- tests/api/client.test.ts
```

Expected: generated types exist; the test FAILS because `apiFetch` is absent.

- [ ] **Step 3: Implement the typed client**

`Course-Agent/creative/lib/api/client.ts`:

```ts
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "")

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly retryable: boolean,
    readonly traceId?: string,
  ) {
    super(message)
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
  })
  const body = await response.json()
  if (!response.ok) {
    throw new ApiError(body.error.code, body.error.message, body.error.retryable, body.trace_id)
  }
  return body.data as T
}

export { API_BASE_URL }
```

- [ ] **Step 4: Run test, typecheck, and OpenAPI generation**

```powershell
pnpm --dir Course-Agent/creative test -- tests/api/client.test.ts
pnpm --dir Course-Agent/creative typecheck
```

Expected: API client test passes. Typecheck may still show legacy-only failures scheduled for Task 12.

- [ ] **Step 5: Commit generated contract tooling**

```powershell
git add backend/scripts/export_openapi.py Course-Agent/creative/lib/api Course-Agent/creative/tests/api/client.test.ts Course-Agent/creative/package.json Course-Agent/creative/pnpm-lock.yaml
git commit -m "feat(web): generate and consume gateway API types"
```

## Task 9: Add Session Storage, Root Redirect, and Login

**Files:**
- Create: `Course-Agent/creative/lib/session/user-session.ts`
- Create: `Course-Agent/creative/tests/session/user-session.test.ts`
- Replace: `Course-Agent/creative/app/page.tsx`
- Create: `Course-Agent/creative/app/(auth)/login/page.tsx`
- Create: `Course-Agent/creative/components/auth/login-panel.tsx`

- [ ] **Step 1: Write the failing session tests**

```ts
import { beforeEach, describe, expect, it } from "vitest"

import { clearUserId, getUserId, setUserId } from "@/lib/session/user-session"

describe("user session", () => {
  beforeEach(() => localStorage.clear())

  it("stores a trimmed user id", () => {
    setUserId("  student-001  ")
    expect(getUserId()).toBe("student-001")
  })

  it("clears the user id", () => {
    setUserId("student-001")
    clearUserId()
    expect(getUserId()).toBeNull()
  })
})
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
pnpm --dir Course-Agent/creative test -- tests/session/user-session.test.ts
```

Expected: FAIL because the session helpers do not exist.

- [ ] **Step 3: Implement session helpers**

```ts
const USER_ID_KEY = "zhixue_user_id"

export const getUserId = () => window.localStorage.getItem(USER_ID_KEY)

export const setUserId = (value: string) => {
  const userId = value.trim()
  if (!userId) throw new Error("user_id is required")
  window.localStorage.setItem(USER_ID_KEY, userId)
}

export const clearUserId = () => window.localStorage.removeItem(USER_ID_KEY)
```

- [ ] **Step 4: Implement root redirect and login behavior**

`LoginPanel` submits the trimmed ID, calls `/api/user/info`, stores the ID, and routes to `/profile` when `profile_confirmed=false` or `/workspace` when true. It displays `ApiError.message` inline.

`app/page.tsx` is a client component that routes to `/login` when no ID exists and `/workspace` otherwise. Show only a stable loading shell during the redirect.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/session/user-session.test.ts
pnpm --dir Course-Agent/creative typecheck
```

Expected: session tests pass; the new login files typecheck.

- [ ] **Step 5: Commit login bootstrap**

```powershell
git add Course-Agent/creative/lib/session Course-Agent/creative/tests/session Course-Agent/creative/app/page.tsx 'Course-Agent/creative/app/(auth)' Course-Agent/creative/components/auth
git commit -m "feat(web): add simple user initialization"
```

## Task 10: Build the A3 Platform Shell

**Files:**
- Create: `Course-Agent/creative/app/providers.tsx`
- Modify: `Course-Agent/creative/app/layout.tsx`
- Modify: `Course-Agent/creative/app/globals.css`
- Create: `Course-Agent/creative/app/(platform)/layout.tsx`
- Create: `Course-Agent/creative/components/app-shell/app-shell.tsx`
- Create: `Course-Agent/creative/components/app-shell/session-guard.tsx`
- Create: `Course-Agent/creative/app/(platform)/workspace/page.tsx`
- Create: `Course-Agent/creative/tests/app-shell/app-shell.test.tsx`

- [ ] **Step 1: Write the failing shell test**

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { AppShell } from "@/components/app-shell/app-shell"

describe("AppShell", () => {
  it("renders the five fixed navigation destinations", () => {
    render(<AppShell><div>content</div></AppShell>)

    for (const label of ["画像采集", "资源工作台", "学习路径", "学习评估", "课程知识库"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument()
    }
    expect(screen.queryByText("社区")).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test and verify it fails**

```powershell
pnpm --dir Course-Agent/creative test -- tests/app-shell/app-shell.test.tsx
```

Expected: FAIL because the shell is absent.

- [ ] **Step 3: Implement providers, metadata, and visual tokens**

`app/providers.tsx` creates one `QueryClient` with query retries limited to two. Update metadata to:

```ts
export const metadata: Metadata = {
  title: "智学引擎",
  description: "多智能体个性化学习系统",
}
```

Set light tokens in `globals.css` using the approved palette:

```css
:root {
  --background: 220 20% 98%;
  --foreground: 218 24% 18%;
  --card: 0 0% 100%;
  --primary: 222 70% 47%;
  --primary-foreground: 0 0% 100%;
  --secondary: 220 23% 95%;
  --muted: 216 20% 95%;
  --muted-foreground: 215 12% 45%;
  --accent: 79 47% 46%;
  --destructive: 8 65% 60%;
  --border: 216 20% 88%;
  --radius: 0.5rem;
}
```

- [ ] **Step 4: Implement the shell and guarded platform layout**

Use Lucide icons for the five navigation items. `SessionGuard` reads `getUserId()` after mount and routes missing users to `/login`. The shell width is fixed for desktop, uses an unframed main content area, and reserves no permanent right rail.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/app-shell/app-shell.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit the application shell**

```powershell
git add Course-Agent/creative/app Course-Agent/creative/components/app-shell Course-Agent/creative/tests/app-shell
git commit -m "feat(web): add Zhixue Engine platform shell"
```

## Task 11: Parse POST SSE Streams and Reduce Ordered Events

**Files:**
- Create: `Course-Agent/creative/lib/sse/post-event-stream.ts`
- Create: `Course-Agent/creative/lib/sse/task-reducer.ts`
- Create: `Course-Agent/creative/tests/sse/task-reducer.test.ts`
- Create: `Course-Agent/creative/tests/sse/post-event-stream.test.ts`

- [ ] **Step 1: Write failing reducer and parser tests**

```ts
import { describe, expect, it } from "vitest"

import { initialTaskState, reduceTaskEvent } from "@/lib/sse/task-reducer"

describe("reduceTaskEvent", () => {
  it("ignores duplicate or older events", () => {
    const first = reduceTaskEvent(initialTaskState, {
      event: "content.delta",
      task_id: "task-1",
      seq: 2,
      trace_id: "trace-1",
      progress: 20,
      content: "第一段",
      finish_flag: false,
      resource_ids: [],
    })
    const duplicate = reduceTaskEvent(first, { ...first.lastEvent!, content: "重复" })

    expect(duplicate.content).toBe("第一段")
    expect(duplicate.lastSeq).toBe(2)
  })
})
```

The parser test must feed two split byte chunks containing one SSE event and assert one parsed gateway event.

- [ ] **Step 2: Run tests and verify they fail**

```powershell
pnpm --dir Course-Agent/creative test -- tests/sse
```

Expected: FAIL because parser and reducer do not exist.

- [ ] **Step 3: Implement the event reducer**

Use:

```ts
export type TaskState = {
  taskId?: string
  lastSeq: number
  progress: number
  currentAgent?: string
  content: string
  profile: Record<string, unknown> | null
  status: "idle" | "running" | "succeeded" | "failed"
  error?: { code: string; message: string; retryable: boolean }
  lastEvent?: GatewayEvent
}

export function reduceTaskEvent(state: TaskState, event: GatewayEvent): TaskState {
  if (event.seq <= state.lastSeq) return state
  return {
    ...state,
    taskId: event.task_id,
    lastSeq: event.seq,
    progress: event.progress,
    currentAgent: event.current_agent ?? state.currentAgent,
    content: event.event === "content.delta" ? state.content + event.content : state.content,
    profile: event.profile_patch ? { ...(state.profile ?? {}), ...event.profile_patch } : state.profile,
    status: event.event === "task.completed" ? "succeeded" : event.event === "task.failed" ? "failed" : "running",
    error: event.error ?? state.error,
    lastEvent: event,
  }
}
```

- [ ] **Step 4: Implement `postEventStream` with `eventsource-parser` and rerun tests**

The function must POST JSON, throw `ApiError` for non-2xx responses, read `response.body`, decode chunks, and call `onEvent(JSON.parse(message.data))`. Return the `X-Task-ID` response header when the stream ends.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/sse
```

Expected: PASS.

- [ ] **Step 5: Commit streaming utilities**

```powershell
git add Course-Agent/creative/lib/sse Course-Agent/creative/tests/sse
git commit -m "feat(web): add ordered gateway event streaming"
```

## Task 12: Build the Profile Collection Page

**Files:**
- Create: `Course-Agent/creative/components/profile/profile-chat.tsx`
- Create: `Course-Agent/creative/components/profile/profile-panel.tsx`
- Create: `Course-Agent/creative/components/profile/profile-page.tsx`
- Create: `Course-Agent/creative/components/shared/agent-progress.tsx`
- Create: `Course-Agent/creative/components/shared/error-notice.tsx`
- Create: `Course-Agent/creative/app/(platform)/profile/page.tsx`
- Create: `Course-Agent/creative/tests/profile/profile-panel.test.tsx`
- Create: `Course-Agent/creative/tests/profile/profile-page.test.tsx`

- [ ] **Step 1: Write failing profile component tests**

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ProfilePanel } from "@/components/profile/profile-panel"

const profile = {
  knowledge_foundation: "入门基础",
  cognitive_style: "案例驱动",
  weak_points: ["ROS2 通信"],
  learning_pace: "分阶段",
  content_preferences: ["图解", "代码案例"],
  short_term_goal: "完成通信强化",
}

describe("ProfilePanel", () => {
  it("renders exactly the six fixed dimensions", () => {
    render(<ProfilePanel profile={profile} />)
    for (const label of ["知识基础", "认知风格", "薄弱知识点", "学习节奏", "内容偏好", "短期学习目标"]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })
})
```

The page test submits one message, feeds `content.delta` and `profile.patch`, then asserts streamed assistant text and the updated panel are both visible.

- [ ] **Step 2: Run profile tests and verify they fail**

```powershell
pnpm --dir Course-Agent/creative test -- tests/profile
```

Expected: FAIL because the components are absent.

- [ ] **Step 3: Implement the profile panel and chat**

`ProfilePanel` receives only the fixed six-dimension object. Array dimensions render compact value lists; string dimensions render text. `ProfileChat` owns message input and presentation but receives `onSend`, `isStreaming`, and messages from its parent.

`AgentProgress` must render a stable-height progress bar, current Agent label, and status text without resizing the layout.

- [ ] **Step 4: Implement page orchestration and confirmation**

`ProfilePage` must:

1. load `/api/user/info` for the stored ID;
2. initialize previous profile data;
3. stream `POST /api/chat/profile` events into the reducer;
4. append user and assistant messages;
5. enable “画像确认完成” only when all six fields contain collected values rather than the literal value `待采集`;
6. call `/api/profile/confirm` and route to `/workspace`.

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/profile
```

Expected: PASS.

- [ ] **Step 5: Commit profile UI**

```powershell
git add 'Course-Agent/creative/app/(platform)/profile' Course-Agent/creative/components/profile Course-Agent/creative/components/shared Course-Agent/creative/tests/profile
git commit -m "feat(web): add streaming profile collection"
```

## Task 13: Remove Active Coze, Forum, and Legacy Landing Code

**Files:**
- Delete: active Coze and monolith files listed in the file map.
- Modify: `Course-Agent/creative/app/layout.tsx`
- Modify: `mywebsite/mywebsite/urls.py`
- Delete: root Coze-only package manifests after verification.
- Create: `Course-Agent/creative/tests/legacy-removal.test.ts`

- [ ] **Step 1: Write the failing source scan test**

`Course-Agent/creative/tests/legacy-removal.test.ts`:

```ts
import fs from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

const projectRoot = path.resolve(__dirname, "..")

describe("legacy integrations", () => {
  it("contains no active Coze or forum implementation", () => {
    const activeFiles = [
      "app/layout.tsx",
      "app/page.tsx",
      "components",
    ]
    const source = activeFiles.map((entry) => {
      const target = path.join(projectRoot, entry)
      if (fs.statSync(target).isFile()) return fs.readFileSync(target, "utf8")
      return fs.readdirSync(target, { recursive: true })
        .filter((name) => /\.(ts|tsx)$/.test(String(name)))
        .map((name) => fs.readFileSync(path.join(target, String(name)), "utf8"))
        .join("\n")
    }).join("\n")

    expect(source).not.toMatch(/Coze|coze|论坛|\/api\/blogs/)
  })
})
```

- [ ] **Step 2: Run the scan and verify it fails**

```powershell
pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
```

Expected: FAIL with Coze/forum matches in legacy active files.

- [ ] **Step 3: Remove active legacy code**

Delete the Coze component and token route, old auth proxy routes, `creative.tsx`, the old `/main` page, and unused marketing landing imports. Replace the root layout with the Zhixue providers only. Confirm root `package.json` contains only `@coze/api`; if true, delete root `package.json` and root `pnpm-lock.yaml`.

In `mywebsite/mywebsite/urls.py`, remove:

```py
path('', include('core.urls')),
```

Keep Django admin and legacy resource URLs so the directory remains inspectable but forum routes are inactive.

- [ ] **Step 4: Run source scan, typecheck, and build**

```powershell
pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative build
```

Expected: all pass; no Coze SDK network code or forum UI remains in the active frontend.

- [ ] **Step 5: Commit legacy removal**

```powershell
git add -A Course-Agent/creative mywebsite/mywebsite/urls.py package.json pnpm-lock.yaml
git commit -m "refactor: remove active forum and Coze integrations"
```

Omit deleted root files from the command when Git no longer resolves them as paths; `git add -A` records their deletion.

## Task 14: Add Phase 1 Browser Coverage

**Files:**
- Create: `Course-Agent/creative/playwright.config.ts`
- Create: `Course-Agent/creative/e2e/profile-flow.spec.ts`
- Modify: `backend/app/main.py` - CORS for configured web origins.
- Create: `backend/.env.example`
- Create: `Course-Agent/creative/.env.example`

- [ ] **Step 1: Write the failing Playwright flow**

```ts
import { expect, test } from "@playwright/test"

test("new user completes profile collection", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel("用户 ID").fill("e2e-student")
  await page.getByRole("button", { name: "进入学习平台" }).click()

  await expect(page).toHaveURL(/\/profile$/)
  await page.getByPlaceholder("介绍你的专业、基础或学习目标").fill("我想加强 ROS2 节点通信，喜欢代码案例。")
  await page.getByRole("button", { name: "发送" }).click()

  await expect(page.getByText("题库Agent").or(page.getByText("画像抽取Agent"))).toBeVisible()
  await expect(page.getByText("ROS2 节点通信", { exact: false })).toBeVisible()
  await page.getByRole("button", { name: "画像确认完成" }).click()
  await expect(page).toHaveURL(/\/workspace$/)
})
```

- [ ] **Step 2: Configure Playwright and verify the test fails**

`playwright.config.ts` must use `http://127.0.0.1:3000`, a 1440x900 viewport, trace on first retry, and two `webServer` entries:

```ts
webServer: [
  { command: "pnpm dev", url: "http://127.0.0.1:3000", reuseExistingServer: true },
  { command: "..\\..\\backend\\.venv\\Scripts\\python -m uvicorn app.main:app --app-dir ..\\..\\backend --host 127.0.0.1 --port 8000", url: "http://127.0.0.1:8000/health", reuseExistingServer: true },
]
```

Run:

```powershell
pnpm --dir Course-Agent/creative exec playwright install chromium
pnpm --dir Course-Agent/creative test:e2e -- e2e/profile-flow.spec.ts
```

Expected: FAIL until CORS, labels, and exact page behavior are aligned.

- [ ] **Step 3: Add environment templates and CORS**

`backend/.env.example`:

```dotenv
DATABASE_URL=sqlite:///./data/zhixue.db
AGENT_MODE=mock
MOCK_EVENT_DELAY_MS=40
WEB_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
REMOTE_AGENT_BASE_URL=
REMOTE_AGENT_API_KEY=
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
```

`Course-Agent/creative/.env.example`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Add `web_origins` parsing to settings and `CORSMiddleware` to the FastAPI factory.

- [ ] **Step 4: Run all Phase 1 checks**

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e -- e2e/profile-flow.spec.ts
```

Expected: all commands pass.

- [ ] **Step 5: Commit Phase 1 browser coverage**

```powershell
git add backend Course-Agent/creative
git commit -m "test: cover profile onboarding flow"
```

## Phase 1 Completion Check

Run:

```powershell
git status --short
git log --oneline -10
```

Expected:

- Active frontend has no Coze or forum functionality.
- New users can stream and confirm a six-dimension profile.
- Old users can be routed based on persisted confirmation state.
- FastAPI health, profile, task snapshot, SQLite persistence, frontend tests, build, and Playwright flow are green.
- Worktree is clean except for intentionally uncommitted user files.
