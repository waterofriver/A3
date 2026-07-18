# Zhixue Immersive Landing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static login page with an accessible, dark immersive landing experience that preserves the existing user-ID login flow.

**Architecture:** Keep semantic landing content in normal document flow and render a fixed Three.js learning-core canvas behind it. Extract the existing login API/session behavior into a reusable form, place it in a modal overlay, and let the landing page own scroll chapter state plus the overlay state. A CSS fallback provides the same readable page when WebGL or motion is unavailable.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, Three.js, Vitest, Testing Library.

---

## File Structure

- Modify: `Course-Agent/creative/package.json` and `Course-Agent/creative/pnpm-lock.yaml` to install `three` and its TypeScript declarations.
- Create: `Course-Agent/creative/components/auth/user-id-login-form.tsx` for the reusable existing user-ID submit behavior.
- Create: `Course-Agent/creative/components/landing/landing-content.ts` for the five sections and scene target data.
- Create: `Course-Agent/creative/components/landing/learning-core-scene.tsx` for the isolated WebGL canvas, pointer effect, reduced-motion mode, and cleanup.
- Create: `Course-Agent/creative/components/landing/scene-fallback.tsx` for non-WebGL/reduced-motion presentation.
- Create: `Course-Agent/creative/components/landing/immersive-login-page.tsx` for the navigation, semantic chapters, scroll tracking, and modal state.
- Modify: `Course-Agent/creative/components/auth/login-panel.tsx` to compose the new page.
- Create: `Course-Agent/creative/tests/auth/user-id-login-form.test.tsx` for preserved login routing behavior.
- Create: `Course-Agent/creative/tests/landing/immersive-login-page.test.tsx` for semantic chapters and modal interaction.

### Task 1: Preserve Login Behavior Behind a Reusable Form

**Files:**
- Create: `Course-Agent/creative/tests/auth/user-id-login-form.test.tsx`
- Create: `Course-Agent/creative/components/auth/user-id-login-form.tsx`
- Modify: `Course-Agent/creative/components/auth/login-panel.tsx`

- [ ] **Step 1: Write a failing form test for new-user routing**

Render `UserIdLoginForm`, mock `apiFetch` with `profile_confirmed: false`, submit `student-001`, and assert that `setUserId` storage and `/profile` routing occur.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `pnpm --dir Course-Agent/creative test tests/auth/user-id-login-form.test.tsx`
Expected: FAIL because `UserIdLoginForm` does not exist.

- [ ] **Step 3: Implement `UserIdLoginForm`**

Move the existing trimmed-ID validation, `/api/user/info` call, error rendering, disabled submit state, storage update, and `/profile`/`/workspace` routing into `UserIdLoginForm`. Accept an optional `onSuccess` callback and neutral visual class names.

- [ ] **Step 4: Recompose the old `LoginPanel` around the extracted form and run tests**

Run: `pnpm --dir Course-Agent/creative test tests/auth/user-id-login-form.test.tsx tests/auth/login-panel.test.tsx`
Expected: PASS.

### Task 2: Add Three.js and Prove the Landing Contract

**Files:**
- Modify: `Course-Agent/creative/package.json`
- Modify: `Course-Agent/creative/pnpm-lock.yaml`
- Create: `Course-Agent/creative/tests/landing/immersive-login-page.test.tsx`

- [ ] **Step 1: Install rendering dependencies**

Run: `pnpm --dir Course-Agent/creative add three @types/three`

- [ ] **Step 2: Write failing landing-page tests**

Assert the rendered page exposes title `智学引擎`, headings `学习画像`, `智能资源`, `成长路径`, `评估与记忆`, a button named `进入学习空间`, and no forbidden course-specific terms. Add a test that opening the button exposes the user-ID field and closing the dialog removes it.

- [ ] **Step 3: Run the focused test and verify RED**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx`
Expected: FAIL because `ImmersiveLoginPage` does not exist.

### Task 3: Build Semantic Landing Content and the Login Overlay

**Files:**
- Create: `Course-Agent/creative/components/landing/landing-content.ts`
- Create: `Course-Agent/creative/components/landing/immersive-login-page.tsx`
- Create: `Course-Agent/creative/components/landing/scene-fallback.tsx`

- [ ] **Step 1: Define the five-section content model**

Create an exported `landingChapters` array with `intro`, `profile`, `resources`, `path`, and `memory` IDs; only the four approved feature names appear after the intro. Keep all text course-neutral.

- [ ] **Step 2: Implement the HTML structure and modal behavior**

Use fixed transparent navigation, five `section` elements with heading IDs, anchors for the four capability chapters, an accessible `role=dialog` overlay, `Escape` close support, and `UserIdLoginForm` inside the overlay. Implement `SceneFallback` as dark grid and line decoration.

- [ ] **Step 3: Run the focused landing test and verify GREEN**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx`
Expected: PASS.

### Task 4: Implement the Isolated Three.js Learning Core

**Files:**
- Create: `Course-Agent/creative/components/landing/learning-core-scene.tsx`
- Modify: `Course-Agent/creative/components/landing/immersive-login-page.tsx`

- [ ] **Step 1: Add a canvas lifecycle implementation**

Create a client component that initializes a transparent renderer, perspective camera, points cloud, line segments, central wireframe core, and faint grid. Use `requestAnimationFrame`, `ResizeObserver`, `visibilitychange`, and cleanup that disposes renderer/materials/geometries and listeners.

- [ ] **Step 2: Map scroll and pointer input to scene state**

Accept normalized `scrollProgress` and `activeChapter`; interpolate scale, camera target, line opacity, particle drift, and point colors across the five scene targets. For fine pointers, map pointer position to a small camera offset; for coarse pointers or reduced motion, disable pointer drift.

- [ ] **Step 3: Add defensive fallback behavior**

If `WebGLRenderer` initialization throws or context is lost, report unavailable through a callback and allow `SceneFallback` to remain visible; reduce particle count and pixel ratio on narrow screens.

- [ ] **Step 4: Run unit, type, and lint verification**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx tests/auth/user-id-login-form.test.tsx && pnpm --dir Course-Agent/creative typecheck && pnpm --dir Course-Agent/creative lint`
Expected: all commands pass; pre-existing unrelated warnings may remain but no errors are introduced.

### Task 5: Integrate, Visually Verify, and Document

**Files:**
- Modify: `Course-Agent/creative/components/auth/login-panel.tsx`
- Modify: `docs/conversation-summaries/2026-07-18-login-visual-prompt-summary.md`

- [ ] **Step 1: Replace the old page composition**

Make `LoginPanel` return `ImmersiveLoginPage`; preserve the `LoginPanel` public export so the route and current test imports continue working.

- [ ] **Step 2: Run the full frontend verification suite**

Run: `pnpm --dir Course-Agent/creative test && pnpm --dir Course-Agent/creative typecheck && pnpm --dir Course-Agent/creative lint && pnpm --dir Course-Agent/creative build`
Expected: tests, type checking, linting, and production build pass.

- [ ] **Step 3: Capture visual evidence**

Start a local frontend server, capture `/login` screenshots at 1366x768 and 440x900, open and close the login overlay, and inspect that the canvas is nonblank, headings are readable, controls do not overlap, and mobile layout remains usable.

- [ ] **Step 4: Update the conversation summary and commit scoped files**

Add the final changed files and verification results to the summary, then create a focused commit with a message such as `feat(web): add immersive Zhixue landing page`.

## Plan Review

- Spec coverage: Tasks 1 and 3 preserve login behavior and implement the overlay; Task 2 fixes the content contract; Task 4 covers Three.js, scrolling, pointer interaction, reduced motion, cleanup, and fallback; Task 5 covers responsive visual verification.
- No placeholders: each task names exact files, verification commands, and expected behavior.
- Consistency: `ImmersiveLoginPage`, `LearningCoreScene`, `SceneFallback`, and `UserIdLoginForm` are defined before integration tasks use them.
