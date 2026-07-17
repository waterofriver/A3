# Local Update Review Summary

- Date: 2026-07-17
- Workspace: `C:\Users\PEIWENHAO2\Desktop\A3`
- Scope: review local frontend updates and document the local startup path. No application code was changed.

## Findings

1. `npm run typecheck` passed.
2. `npm run lint` completed with two existing warnings: an unused `stageName` variable and an unused ESLint disable directive.
3. `npm test` failed because `tests/resources/mermaid-diagram.test.tsx` waits up to eight seconds, while Vitest's default per-test timeout is five seconds. The focused test passes with a 20-second timeout and completes in about 5.5 seconds.
4. `npm run build` did not complete within 120 seconds during the webpack production-bundle phase. The installed Node.js is v24.12.0 while the repository documentation specifies Node.js 22; this compatibility difference needs confirmation before release builds are relied on.
5. `components/auth/login-panel.tsx` uses `to-slate-850` and `components/app-shell/app-shell.tsx` uses `bg-emerald-550`. Neither color exists in the configured Tailwind palette, so those declarations are ignored by the browser.
6. `git diff --check` found five trailing-whitespace locations in two updated frontend files.

## Startup State And Command

- A Next.js development process is currently listening on port 3000, but `GET /login` timed out after ten seconds, so it is not a usable website instance.
- The FastAPI service is not currently listening on port 8000.
- The login-page network error is expected in this state: the frontend API client falls back to `http://localhost:8000`, and its health endpoint could not be reached.
- From the repository root, create `.env` from `.env.example` if needed, then run `powershell -ExecutionPolicy Bypass -File .\start.ps1`.
- The script provisions dependencies, migrates the SQLite database, starts the API and frontend, and prints the actual URLs. It automatically selects a free port if 3000 or 8000 is occupied.

## Follow-Up Fixes

1. The API process crashed in mock mode because importing the optional local Agent provider imported an unavailable `openai` package. The local provider is now imported only when `AGENT_MODE=local`; a regression test verifies that mock startup does not need local Agent dependencies.
2. The startup scripts now set `WEB_ORIGINS` to the dynamically selected web port, so a frontend moved from port 3000 to 3001 is permitted by CORS.
3. The root layout now suppresses hydration warnings caused by the browser's `ai-translate` extension injecting attributes into the body element before React hydrates.
4. After restarting the updated script, API health returned `status=ok`, the login endpoint returned HTTP 200 with `Access-Control-Allow-Origin: http://127.0.0.1:3001`, and `/login` returned HTTP 200.

## Knowledge Base Fix

1. The root `.env` configured `KNOWLEDGE_BASE_ROOT=knowledge_base`, but the backend starts with `backend/` as its working directory. It therefore looked for `backend/knowledge_base` instead of the real repository-root knowledge base and marked only the empty demo course as available.
2. `Settings` now resolves relative knowledge-base paths from the repository root. On restart, the real `robot-safety` course was indexed with 73 documents and the course API reported `content_ready=true`.
3. The knowledge page now ignores a remembered empty demo course when an indexed course is available, selecting a ready course instead.
4. Verification: 9 backend startup/course tests passed; 2 frontend knowledge-page tests passed; frontend typecheck passed; the live course list returned the real ready course.

## Course Presentation Refinements

1. Course indexing now uses each knowledge point's `metadata.json.name` as its chapter title. For example, `exp02_robot_remote_control` is presented as `实验二：机器人连接与远程控制`.
2. `metadata.json` remains available to the indexing pipeline but is excluded from the frontend document list. The live course now exposes 58 learner-facing files after hiding 15 metadata files.
3. The selected course is persisted and announced within the app. The application header shows the selected course name and hides generic course/demo status badges while a course is selected.
4. Verification: 7 backend course-index/API tests passed, 8 frontend application-shell/course-selection tests passed, frontend typecheck passed, and the live API confirmed the Chinese chapter title with no visible metadata document.

## Knowledge Tree Interaction

1. The course knowledge tree now uses a controlled single-item accordion. Opening a chapter closes the previously open chapter; clicking the open chapter closes it.
2. The component resets its active chapter safely when the selected course changes.
3. Verification: the knowledge-tree interaction test and knowledge-page test passed, and frontend typecheck passed.

## Navigation Performance Diagnosis

1. The observed navigation lag is in the Next.js development server, not the FastAPI API or course-data requests. API health, course list, and user-info requests each completed in about 4ms.
2. The running command is `next dev` on Node.js v24.12.0, while the repository specifies Node.js 22. The development server occupied about 1.96GB of memory and webpack logs showed route compilation and route responses taking 3 to 23 seconds during cold starts or hot reloads.
3. After route compilation stabilized, direct responses for profile, workspace, path, evaluation, and knowledge pages measured about 80 to 150ms.
4. The local startup script is designed for development and always invokes `pnpm dev`; this is why the transient compilation delay is visible during page switching.
