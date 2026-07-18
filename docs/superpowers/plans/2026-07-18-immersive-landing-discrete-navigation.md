# Immersive Landing Discrete Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the immersive login landing page navigate chapter-by-chapter and decouple particle rotation from page scroll.

**Architecture:** `ImmersiveLoginPage` owns a guarded active chapter index and converts navigation inputs into a single `goToChapter` callback. `LearningCoreScene` remains isolated from chapter navigation and accepts primary-button drag deltas only, while its render loop retains a low-speed automatic rotation.

**Tech Stack:** Next.js 15, React 19, TypeScript, Three.js, Vitest, Testing Library.

---

## File Structure

- Modify: `Course-Agent/creative/components/landing/immersive-login-page.tsx` for guarded chapter navigation, anchor interception, and keyboard/wheel/touch inputs.
- Modify: `Course-Agent/creative/components/landing/learning-core-scene.tsx` for active-chapter-only scene targets and primary-button drag rotation.
- Modify: `Course-Agent/creative/app/globals.css` to remove global smooth scrolling and establish section-aligned layout.
- Modify: `Course-Agent/creative/tests/landing/immersive-login-page.test.tsx` for keyboard and chapter-navigation regression coverage.

### Task 1: Establish Navigation Contract

**Files:**
- Modify: `Course-Agent/creative/tests/landing/immersive-login-page.test.tsx`
- Modify: `Course-Agent/creative/components/landing/immersive-login-page.tsx`

- [ ] **Step 1: Write failing tests**

Add a test that focuses a chapter navigation link, presses `ArrowDown`, and verifies the next chapter becomes active. Stub `window.scrollTo` and verify a navigation click targets its full section offset.

- [ ] **Step 2: Run the focused test to verify RED**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx`

Expected: the new test fails because the page still derives active state from unconstrained native scroll positions.

- [ ] **Step 3: Implement guarded chapter navigation**

Create `goToChapter(index)` that clamps the index, calls `window.scrollTo({ top: section.offsetTop, behavior: "smooth" })`, sets a 700 ms input lock, and updates the active index. Route wheel, vertical touch, ArrowUp/ArrowDown, and PageUp/PageDown through it; do not handle inputs originating in the login dialog, text fields, or editable content. Intercept chapter anchors to call the same function.

- [ ] **Step 4: Run the focused test to verify GREEN**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx`

Expected: PASS.

### Task 2: Decouple Scene Orientation From Scroll

**Files:**
- Modify: `Course-Agent/creative/components/landing/learning-core-scene.tsx`
- Modify: `Course-Agent/creative/components/landing/immersive-login-page.tsx`

- [ ] **Step 1: Remove navigation state from the scene interface**

Remove `activeChapter` and `scrollProgress` from `LearningCoreScene`. Use one stable particle target so no page-navigation event can affect its geometry, scale, or orientation.

- [ ] **Step 2: Add primary-button drag rotation**

Attach pointer handlers to the canvas. Begin drag only for `event.button === 0` and fine pointers, accumulate `clientX` and `clientY` deltas while pressed, and release capture on pointer-up or cancellation. Keep automatic time-based rotation in the render loop; plain pointer movement must not mutate the drag target.

- [ ] **Step 3: Check types**

Run: `pnpm --dir Course-Agent/creative typecheck`

Expected: PASS.

### Task 3: Apply CSS And Verify The User Flow

**Files:**
- Modify: `Course-Agent/creative/app/globals.css`

- [ ] **Step 1: Disable global free-form smooth scrolling**

Remove `scroll-behavior: smooth` from the document root. Keep each landing chapter at a viewport-stable minimum height so controlled jumps align to one chapter.

- [ ] **Step 2: Run quality checks**

Run: `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx && pnpm --dir Course-Agent/creative typecheck && pnpm --dir Course-Agent/creative lint`

Expected: all commands pass with no newly introduced errors.

- [ ] **Step 3: Perform browser verification**

At `/login`, verify desktop wheel/keyboard transitions change exactly one section; verify a primary-button drag rotates the particle scene, while normal pointer movement and wheel input do not. Verify at 440x900 that vertical touch-style navigation still lands on a complete chapter and that the login overlay remains usable.
