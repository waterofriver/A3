# Learning Path Node Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Present readable, staggered learning-path nodes with a detail popover and a single reversible completion-state control.

**Architecture:** Keep the React Flow graph responsible for presentation and selection. The path page translates a requested target state into the existing learning-event endpoint. Extend that endpoint and repository only with a reset event that clears `completed_at`, then invalidate the existing query to render server truth.

**Tech Stack:** Next.js 15, React 19, React Flow, Radix UI Dialog, Lucide, Vitest, Testing Library, FastAPI, SQLAlchemy, Pytest.

---

### Task 1: Support resetting a path node on the server

**Files:**
- Modify: `backend/app/schemas/learning.py`
- Modify: `backend/app/repositories/learning.py`
- Modify: `backend/app/services/learning_event_service.py`
- Modify: `backend/tests/test_learning_events.py`

- [ ] **Step 1: Write failing test** for a completed node receiving `path_node_reset`; assert its returned `completed_at` is `None`.
- [ ] **Step 2: Run** `pytest backend/tests/test_learning_events.py -q` and verify the reset case fails because the event is not accepted.
- [ ] **Step 3: Add `path_node_reset`** to the event type literal, add `reset_path_node(node_id)` that assigns `None` to `completed_at`, and dispatch it beside `complete_path_node`.
- [ ] **Step 4: Run** `pytest backend/tests/test_learning_events.py -q` and verify it passes.

### Task 2: Define graph detail behavior through component tests

**Files:**
- Modify: `Course-Agent/creative/tests/learning-path/learning-path-graph.test.tsx`
- Modify: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`

- [ ] **Step 1: Write failing tests** that click a node, expect the complete stage title and suggestion in a dialog, expect the single “未完成” state button, click it, and assert `onToggleNode(nodeId, stageName, true)`; repeat with a completed node and expect “已完成” plus `false`.
- [ ] **Step 2: Run** `pnpm test tests/learning-path/learning-path-graph.test.tsx` and verify the tests fail because node clicks do not open a dialog.
- [ ] **Step 3: Implement** selected-node state, a Radix dialog detail surface, status-color card styles, a two-line card title, and `onToggleNode`. Generate node positions from a repeatable staggered offset sequence while retaining edges in the sorted node order.
- [ ] **Step 4: Run** `pnpm test tests/learning-path/learning-path-graph.test.tsx` and verify it passes.

### Task 3: Connect the path page to reversible events

**Files:**
- Modify: `Course-Agent/creative/app/(platform)/path/page.tsx`
- Modify: `Course-Agent/creative/lib/api/learning-events.ts`
- Test: `Course-Agent/creative/tests/learning-path/learning-path-graph.test.tsx`

- [ ] **Step 1: Add a failing page-level or extracted-handler test** expecting a `path_node_reset` event when the graph requests a false target state.
- [ ] **Step 2: Run** the selected test with `pnpm test` and verify it fails because only completion events are emitted.
- [ ] **Step 3: Make the page handler accept `(nodeId, stageName, completed)` and send `path_node_completed` for `true` and `path_node_reset` for `false`; add the reset event to `LearningEventType`; preserve query invalidation after a successful request.
- [ ] **Step 4: Run** the frontend learning-path tests and verify they pass.

### Task 4: Verify the integrated behavior

**Files:**
- Verify: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`
- Verify: `Course-Agent/creative/app/(platform)/path/page.tsx`
- Verify: `backend/app/services/learning_event_service.py`

- [ ] **Step 1: Run** `pnpm typecheck`, `pnpm lint`, `pnpm test tests/learning-path/learning-path-graph.test.tsx`, and `pytest backend/tests/test_learning_events.py -q`.
- [ ] **Step 2: Start the application and capture `/path` at desktop and mobile viewport widths with Playwright. Verify title visibility, no text overlap, dialog content, state-button labels, and staggered route layout.
- [ ] **Step 3: Update** `docs/conversation-summaries/2026-07-19-learning-path-node-detail-summary.md` with final changed files and verification results.
