# Zhixue Engine README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore and update all five README files so they accurately present the competition project, preserve technical depth, and remain usable for setup, judging, and later documentation work.

**Architecture:** The root README is the authoritative project overview and links to specialized README files. Agent, knowledge-base, and artifact details remain in their owning directories; each file distinguishes implemented behavior, demo behavior, external dependencies, and future extension points.

**Tech Stack:** Markdown, Next.js 15, React 19, FastAPI, SQLite, SSE, Three.js, Docker Compose, Nginx, local/remote multi-agent adapters.

---

## File Structure

- Modify: `README.md` for project value, competition alignment, features, architecture, technology, structure, operation, deployment, verification, limitations, and document links.
- Modify: `backend/agent/README.md` for the eight local Agent modules, their contracts, configuration, testing, and active gateway relationship.
- Modify: `knowledge_base/README.md` for the full DAG and course-material construction guide.
- Modify: `artifacts/README.md` for committed screenshots/video and ignored local verification outputs.
- Modify: `backend/agent/knowledge_base/README.md` for the legacy template's scope and minimum schema.
- Modify: `docs/conversation-summaries/2026-07-18-readme-refresh-summary.md` for the final conversation record.

### Task 1: Root Project README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Restore the original project-level information**

Preserve the original sections for implemented scope, architecture, directory tree, environment requirements, local startup, Docker Compose, Agent modes, knowledge base, verification commands, and delivery documentation.

- [ ] **Step 2: Add judge-facing context without turning the README into a report**

Add concise sections in this order:

```text
Project positioning and educational pain points
Competition requirements mapped to implemented features and evidence
Innovation and practical value
Architecture and core learning loop
Technology stack and open-source usage
```

State external boundaries explicitly: Mock output is demonstrative, remote Agent/media services require configuration, and simple `user_id` login is not production authentication.

- [ ] **Step 3: Add complete operational and repository information**

Document the current routes, project tree, `.env` modes, local commands, Docker/HTTPS path, test commands, artifacts, known limitations, and AI Coding disclosure.

- [ ] **Step 4: Validate root README references**

Run:

```powershell
git diff --check -- README.md
rg -n "Course-Agent/creative|backend/|knowledge_base/|docker compose|AGENT_MODE|AI Coding" README.md
```

Expected: no whitespace errors and all key project areas are present.

### Task 2: Agent README

**Files:**
- Modify: `backend/agent/README.md`

- [ ] **Step 1: Restore the local Agent directory and role table**

Document ProfileAgent, PlannerAgent, Supervisor, DocAgent, MindMapAgent, QuizAgent, VideoAgent, and ReferenceAgent with inputs, outputs, and their relationship to resource types.

- [ ] **Step 2: Correct integration boundaries**

Explain that `backend/app/agents/` owns the active gateway adapters, `mock` and `remote` are stable deployment modes, and `local` depends on the local Agent stack and DeepSeek configuration. Remove references to nonexistent files or endpoints.

- [ ] **Step 3: Preserve configuration and test instructions**

Include the root `.env` variables, dependency installation, per-Agent tests, gateway tests, and safe media-path conversion requirements.

### Task 3: Knowledge Base READMEs

**Files:**
- Modify: `knowledge_base/README.md`
- Modify: `backend/agent/knowledge_base/README.md`

- [ ] **Step 1: Restore the complete top-level knowledge-base guide**

Include DAG concepts, current `robot-safety` source layout, schema fields, dependency rules, supported formats, validation, metadata generation, runtime synchronization, Git size constraints, delivery checklist, and FAQs.

- [ ] **Step 2: Keep the nested template useful but non-authoritative**

Document its template-only role, minimum JSON schema, and migration path to the top-level knowledge base without duplicating the full guide.

### Task 4: Artifact README

**Files:**
- Modify: `artifacts/README.md`

- [ ] **Step 1: Restore the complete artifact inventory**

List all eleven committed screenshots, the main-flow WebM, viewport assumptions, and regeneration commands.

- [ ] **Step 2: Explain current landing evidence and ignored outputs**

Note that the current immersive landing page supersedes the older login screenshot when fresh evidence is captured. Distinguish committed review evidence from ignored logs, raw traces, `.next-*`, `output/`, and `.playwright-cli/` data.

### Task 5: Cross-README Verification and Conversation Record

**Files:**
- Modify: all five README files
- Modify: `docs/conversation-summaries/2026-07-18-readme-refresh-summary.md`

- [ ] **Step 1: Run structural checks**

```powershell
rg --files -g "README.md" -g "README.*"
git diff --check
```

Expected: exactly five README files and no whitespace errors.

- [ ] **Step 2: Validate local Markdown links and referenced paths**

Check each relative Markdown link and every command path referenced by the README files against the working tree.

- [ ] **Step 3: Check truthfulness and competition coverage**

Compare the root README against current routes, API route files, Agent modules, the four core competition functions, both optional functions, non-functional requirements, and actual deployment/test documentation. Remove unsupported claims.

- [ ] **Step 4: Update the conversation summary**

Record the five updated files, restored information, competition-facing additions, boundaries, and verification evidence.

## Plan Review

- Spec coverage: all five README responsibilities and all truthfulness rules are represented.
- Scope: documentation only; no application behavior or configuration changes.
- Placeholder scan: no TBD/TODO steps or undefined follow-up work.
- Verification: structure, links, paths, Markdown formatting, project reality, and competition coverage are all checked.
