# Evaluation and Learning Path Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore inset spacing in evaluation score cards and keep learning-path nodes readable without overlap.

**Architecture:** Keep the existing React and React Flow component boundaries. Fix the invalid Tailwind spacing token in the score card, and make each graph node own a stable content layout with bounded title lines and a fixed height that is preserved by React Flow.

**Tech Stack:** Next.js, React 19, Tailwind CSS, React Flow, Vitest, Testing Library, Playwright.

---

### Task 1: Lock in score-card padding

**Files:**
- Create: `Course-Agent/creative/tests/evaluation/score-panel.test.tsx`
- Modify: `Course-Agent/creative/components/evaluation/score-panel.tsx`

- [ ] **Step 1: Write a failing test** asserting each score card has Tailwind's valid `p-6` spacing class.
- [ ] **Step 2: Run** `pnpm test tests/evaluation/score-panel.test.tsx` and confirm it fails because the card uses `p-5.5`.
- [ ] **Step 3: Replace** the invalid padding class with `p-6`.
- [ ] **Step 4: Run** `pnpm test tests/evaluation/score-panel.test.tsx` and confirm it passes.

### Task 2: Preserve readable node content

**Files:**
- Modify: `Course-Agent/creative/tests/learning-path/learning-path-graph.test.tsx`
- Modify: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`

- [ ] **Step 1: Write a failing test** asserting a long node title is clamped to two lines and that the graph has a fixed readable node height.
- [ ] **Step 2: Run** `pnpm test tests/learning-path/learning-path-graph.test.tsx` and confirm it fails before the classes exist.
- [ ] **Step 3: Implement** a vertical node layout, two-line title clamp, and fixed node height; increase the graph viewport height and tighten `fitView` padding.
- [ ] **Step 4: Run** `pnpm test tests/learning-path/learning-path-graph.test.tsx` and confirm it passes.

### Task 3: Verify production rendering

**Files:**
- Verify: `Course-Agent/creative/components/evaluation/score-panel.tsx`
- Verify: `Course-Agent/creative/components/learning-path/learning-path-graph.tsx`

- [ ] **Step 1: Run** `pnpm typecheck` and `pnpm lint`.
- [ ] **Step 2: Start the local app**, capture the `/path` and `/evaluation` desktop views with Playwright, and inspect the screenshots for card insets, readable titles, and no node-content overlap.
