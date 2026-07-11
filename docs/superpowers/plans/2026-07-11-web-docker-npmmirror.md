# Web Docker npmmirror Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Dockerized frontend dependency installation use npmmirror before running the frozen pnpm install.

**Architecture:** Keep the change inside the Web image dependencies stage so it affects only container builds. Preserve the lockfile and frozen-install behavior; do not modify host-level package-manager configuration.

**Tech Stack:** Dockerfile, pnpm, PowerShell static checks, Docker Compose

---

### Task 1: Add the Docker build registry configuration

**Files:**
- Modify: `Course-Agent/creative/Dockerfile`

- [ ] **Step 1: Run the registry contract check and verify RED**

Run:

```powershell
$content = Get-Content -Raw Course-Agent/creative/Dockerfile
$registry = $content.IndexOf('RUN pnpm config set registry https://registry.npmmirror.com')
$install = $content.IndexOf('RUN pnpm install --frozen-lockfile')
if ($registry -lt 0 -or $registry -gt $install) { throw 'npmmirror registry must be configured before pnpm install' }
```

Expected: FAIL because the registry command is absent.

- [ ] **Step 2: Insert the minimal Dockerfile change**

Change the dependencies stage to:

```dockerfile
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm config set registry https://registry.npmmirror.com
RUN pnpm install --frozen-lockfile
```

- [ ] **Step 3: Re-run the registry contract check and verify GREEN**

Run the Step 1 command again.

Expected: exit 0; the registry command exists before the install command.

- [ ] **Step 4: Run repository verification**

Run:

```powershell
docker compose config --quiet
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative build
git diff --check
```

Expected: all commands exit 0; frontend reports 55 tests passed.

- [ ] **Step 5: Commit the Dockerfile change**

Run:

```powershell
git add -- Course-Agent/creative/Dockerfile
git commit -m "build(web): use npmmirror for Docker installs"
```

### Task 2: Record the conversation

**Files:**
- Create: `docs/conversation-summaries/2026-07-11-web-docker-npmmirror-summary.md`

- [ ] **Step 1: Record scope and verification evidence**

Document the cloud failure, exact Dockerfile change, red/green check, repository verification, commit, push requirement, and cloud rebuild commands.

- [ ] **Step 2: Validate and commit the summary**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
git diff --check
git add -- docs/conversation-summaries/2026-07-11-web-docker-npmmirror-summary.md
git commit -m "docs: record Web Docker registry fix"
```

