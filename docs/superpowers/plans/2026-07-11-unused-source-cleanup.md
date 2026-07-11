# Unused Source Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the inactive Django project and local design leftovers without deleting active dependencies, build caches, runtime data, or delivery artifacts.

**Architecture:** Treat the repository boundary as the behavior under test: the active platform must contain only the Next.js frontend and FastAPI gateway, while a regression test proves the Django tree cannot return unnoticed. Documentation and ignore rules will describe only the active architecture; historical plans remain unchanged as decision records.

**Tech Stack:** Git, PowerShell, Vitest, Next.js 15, FastAPI/Pytest, Markdown

---

### Task 1: Make legacy removal explicit

**Files:**
- Modify: `Course-Agent/creative/tests/legacy-removal.test.ts`

- [ ] **Step 1: Replace the Django route-content assertion with a repository-absence assertion**

Replace:

```typescript
  it("disables the Django forum root route", () => {
    const urls = fs.readFileSync(
      path.join(repositoryRoot, "mywebsite/mywebsite/urls.py"),
      "utf8",
    )

    expect(urls).not.toContain("include('core.urls')")
  })
```

with:

```typescript
  it("removes the legacy Django project", () => {
    expect(fs.existsSync(path.join(repositoryRoot, "mywebsite"))).toBe(false)
  })
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
```

Expected: FAIL because `mywebsite/` still exists.

### Task 2: Remove inactive source and synchronize active documentation

**Files:**
- Delete: `mywebsite/`
- Modify: `README.md`
- Modify: `.gitignore`
- Delete locally: `data/`
- Delete locally: `.worktrees/`
- Delete locally: `.superpowers/`

- [ ] **Step 1: Delete the tracked Django tree through Git**

Run:

```powershell
git rm -r -- mywebsite
```

Expected: all 50 tracked Django files are staged for deletion.

- [ ] **Step 2: Update the active architecture description**

In `README.md`, replace the opening sentence that says `mywebsite` is retained with:

```markdown
智学引擎是一个面向 PC 演示和后续云部署的教学平台框架。活动前端位于 `Course-Agent/creative`，活动后端是 `backend` 中的 FastAPI + SQLite 网关。原论坛、旧 Django 项目和 Coze 智能体接入已从仓库移除。
```

Remove this directory line from the README tree:

```text
mywebsite/              非活动的历史 Django 参考代码
```

- [ ] **Step 3: Remove Django-project-only ignore rules**

Delete these exact lines from `.gitignore`:

```gitignore
mywebsite/venv/
mywebsite/.venv/
mywebsite/upload/materials/
mywebsite/upload/
mywebsite/**/*.db
```

Keep the general Python, SQLite, Node.js, Next.js, artifact, course-data, and environment rules unchanged.

- [ ] **Step 4: Delete only the approved local temporary directories**

Resolve each target, confirm it is directly under the repository root, then remove `data/`, `.worktrees/`, and `.superpowers/` with native PowerShell. Do not remove `artifacts/`, `backend/.venv/`, `backend/data/`, `Course-Agent/creative/node_modules/`, or `Course-Agent/creative/.next/`.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run:

```powershell
pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
```

Expected: 3 tests pass.

- [ ] **Step 6: Commit the source cleanup**

Run:

```powershell
git add -- .gitignore README.md Course-Agent/creative/tests/legacy-removal.test.ts mywebsite
git commit -m "chore: remove inactive Django project"
```

Expected: one commit containing the agreed tracked deletions and reference updates.

### Task 3: Verify the active platform after cleanup

**Files:**
- No source changes expected

- [ ] **Step 1: Verify repository boundaries**

Run:

```powershell
Test-Path mywebsite
Test-Path data
Test-Path .worktrees
Test-Path .superpowers
git grep -n -I mywebsite -- README.md .gitignore start.ps1 start.sh docker-compose.yml backend Course-Agent/creative
```

Expected: all `Test-Path` calls return `False`; grep finds only the regression test that asserts removal.

- [ ] **Step 2: Run backend and frontend verification**

Run:

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative build
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
docker compose config --quiet
```

Expected: 52 backend tests pass, 55 frontend tests pass, and all checks exit 0.

- [ ] **Step 3: Verify running services**

Run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
(Invoke-WebRequest http://127.0.0.1:3000/login -UseBasicParsing).StatusCode
```

Expected: health reports `status=ok`; login returns HTTP 200.

### Task 4: Record this conversation and final evidence

**Files:**
- Create: `docs/conversation-summaries/2026-07-11-unused-source-cleanup-summary.md`

- [ ] **Step 1: Write the window summary**

Record the user-approved scope, deleted paths, retained paths, TDD red/green evidence, full verification results, service URLs, Git status, and any external limitations.

- [ ] **Step 2: Validate and commit the summary**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
git diff --check
git add -- docs/conversation-summaries/2026-07-11-unused-source-cleanup-summary.md
git commit -m "docs: record unused source cleanup"
```

Expected: documentation validation passes and the summary is committed.

- [ ] **Step 3: Final audit**

Run:

```powershell
git status --short
git log -5 --oneline
git ls-files mywebsite
```

Expected: clean worktree, cleanup commits at HEAD, and no tracked `mywebsite` files.

