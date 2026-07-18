# 学习记忆助手 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为学生提供基于学习证据的知识记忆保持度、遗忘预警、前置知识阻塞定位和可执行微复习建议。

**Architecture:** FastAPI 从已持久化的测验、学习事件、学习路径和课程知识 DAG 计算只读的记忆快照。每个知识点的保持度由最近作答、完成事件和距离上次学习的时间组成；前置知识在错题证据存在时被标记为阻塞点。Next.js 在“我的记忆地图”页面展示总体状态、曲线、阻塞路径和今日微任务。

**Tech Stack:** FastAPI、Pydantic、SQLAlchemy、Next.js 15、React 19、Recharts、Vitest、pytest。

---

### Task 1: 记忆快照 API 与算法

**Files:**
- Create: `backend/app/schemas/memory.py`
- Create: `backend/app/services/memory_service.py`
- Create: `backend/app/api/routes/memory.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_memory_report.py`

- [ ] **Step 1: Write the failing test**

```python
def test_memory_report_returns_retention_curve_and_review_advice(client, evaluation_records):
    response = client.get("/api/memory/report", params={
        "user_id": evaluation_records["user_id"],
        "course_name": evaluation_records["course_name"],
    })
    assert response.status_code == 200
    report = response.json()["data"]
    assert 0 <= report["memory_health"] <= 100
    assert report["knowledge_points"]
    assert report["knowledge_points"][0]["curve"]
    assert report["today_actions"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `backend\\.venv\\Scripts\\python -m pytest backend/tests/test_memory_report.py -q`
Expected: FAIL because `/api/memory/report` is not registered.

- [ ] **Step 3: Write minimal implementation**

```python
def retention_percent(days_since_review: float, base_mastery: int, decay_rate: float) -> int:
    return round(max(0, min(100, base_mastery * math.exp(-decay_rate * days_since_review))))
```

Return one `MemoryPoint` per DAG knowledge point, derive an action for the lowest retention points, and label all algorithmic deductions as estimates.

- [ ] **Step 4: Run test to verify it passes**

Run: `backend\\.venv\\Scripts\\python -m pytest backend/tests/test_memory_report.py -q`
Expected: PASS.

### Task 2: 我的记忆地图页面

**Files:**
- Create: `Course-Agent/creative/app/(platform)/memory/page.tsx`
- Create: `Course-Agent/creative/components/memory/memory-dashboard.tsx`
- Modify: `Course-Agent/creative/lib/api/generated.ts`
- Modify: `Course-Agent/creative/components/app-shell/app-shell.tsx`
- Test: `Course-Agent/creative/tests/memory/memory-dashboard.test.tsx`

- [ ] **Step 1: Write the failing component test**

```tsx
it("shows the next review action and a retention chart", () => {
  render(<MemoryDashboard report={report} />)
  expect(screen.getByText("今日复习建议")).toBeInTheDocument()
  expect(screen.getByText(/建议复习/)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --dir Course-Agent/creative test tests/memory/memory-dashboard.test.tsx`
Expected: FAIL because `MemoryDashboard` does not exist.

- [ ] **Step 3: Write minimal implementation**

Render memory health, an accessible Recharts retention curve, a blocked-prerequisite list, and no more than three concise actions. Fetch the report through the existing `apiFetch` client and use the selected course/user session state.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --dir Course-Agent/creative test tests/memory/memory-dashboard.test.tsx`
Expected: PASS.

### Task 3: API types, regression tests, and demo evidence

**Files:**
- Modify: `backend/openapi.json`
- Modify: `Course-Agent/creative/lib/api/generated.ts`
- Modify: `docs/demo-script.md`
- Modify: `docs/conversation-summaries/2026-07-18-innovation-feature-analysis-summary.md`
- Test: `backend/tests/test_openapi_contract.py`

- [ ] **Step 1: Write the failing route contract assertion**

```python
def test_openapi_includes_memory_report(client):
    schema = client.get("/openapi.json").json()
    assert "/api/memory/report" in schema["paths"]
```

- [ ] **Step 2: Run it to verify the missing route fails**

Run: `backend\\.venv\\Scripts\\python -m pytest backend/tests/test_openapi_contract.py -q`
Expected: FAIL before the route is registered.

- [ ] **Step 3: Regenerate API types and document the 60-second demo**

```powershell
backend\\.venv\\Scripts\\python backend/scripts/export_openapi.py
pnpm --dir Course-Agent/creative api:types
```

Add a concise demo segment: produce a wrong QoS answer, open “我的记忆地图”, inspect the retention estimate and prerequisite blockage, then complete the micro-review action.

- [ ] **Step 4: Run focused and full verification**

Run: `backend\\.venv\\Scripts\\python -m pytest backend/tests -q`
Run: `pnpm --dir Course-Agent/creative typecheck`
Run: `pnpm --dir Course-Agent/creative test`
Expected: all commands exit 0.

## Self-review

- Scope is limited to deterministic, explainable estimates from existing local evidence; it does not claim a clinical or psychometrically validated memory measurement.
- The API is read-only and does not require a scheduler, notification provider, or external model service.
- The UI avoids new resource generation contracts and uses existing route/session patterns.
