# Zhixue Engine Execution Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the complete Zhixue Engine teaching platform in three independently testable phases.

**Architecture:** Rebuild the active product inside the existing Next.js application and add a FastAPI/SQLite gateway. The frontend consumes one stable OpenAPI/SSE contract while the backend switches between deterministic mock agents and teammate-provided remote agents.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Flow, FastAPI, SQLAlchemy 2, SQLite, pytest, Vitest, Playwright, Docker Compose.

---

## Execution Order

1. [Phase 1: Foundation and Profile](./2026-07-10-zhixue-engine-phase-1-foundation-profile.md)
2. [Phase 2: Resources and Learning Path](./2026-07-10-zhixue-engine-phase-2-resources-path.md)
3. [Phase 3: QA, Evaluation, Knowledge Base, and Delivery](./2026-07-10-zhixue-engine-phase-3-qa-evaluation-delivery.md)

Each phase must finish with a green test suite and a working browser flow before the next phase starts. Do not combine phase commits or defer broken tests to a later phase.

## Specification Coverage

| Approved requirement | Owning tasks |
|---|---|
| Repository baseline, strict frontend checks, FastAPI, SQLite, errors | Phase 1 Tasks 1-5 |
| Six-dimension profile Agent, APIs, login, app shell, streaming UI | Phase 1 Tasks 6-12 |
| Remove active forum, Coze, and legacy landing behavior | Phase 1 Task 13 |
| Profile onboarding browser proof | Phase 1 Task 14 |
| Five resource types, persistent tasks, SSE replay, task retry | Phase 2 Tasks 1-8 |
| Markdown, code, media, mind map, and resource history | Phase 2 Tasks 9-10 and 14 |
| Quiz submission and learning event persistence | Phase 2 Tasks 11-12 |
| Five-stage personalized learning path | Phase 2 Tasks 13-14 |
| Global text/image/video QA | Phase 3 Tasks 1-2 |
| Evaluation report and one-click path update | Phase 3 Tasks 3-4 |
| Real course indexing and read-only knowledge browser | Phase 3 Tasks 5-6 |
| Remote Agent adapter and explicit mock fallback | Phase 3 Task 7 |
| Unified errors, empty states, and partial success | Phase 3 Task 8 |
| Windows/Linux startup and Docker Compose deployment | Phase 3 Task 9 |
| Component/API/deployment documentation | Phase 3 Task 10 |
| PC screenshots, video, traces, accessibility, and final verification | Phase 3 Tasks 11-12 |

## Repository Precondition

The source tree is currently mostly untracked. Phase 1 begins by adding repository hygiene, scanning for secrets, and committing the existing source baseline without `.superpowers/` or generated artifacts. Only then should feature work proceed.

## Shared Completion Commands

Run from `C:\Users\PEIWENHAO2\Desktop\A3` unless a task specifies another directory:

```powershell
git status --short
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative test:e2e
python -m pytest backend/tests -q
docker compose config
```

Expected final result: every command exits with code `0`, and `git status --short` contains no generated files or unintended edits.
