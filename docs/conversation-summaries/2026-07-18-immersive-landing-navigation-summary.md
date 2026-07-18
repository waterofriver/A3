# Immersive Landing Navigation Conversation Summary

## Request

Continue the unfinished landing-page frontend work with these interaction requirements:

- Particle effects must not react to wheel, touch, keyboard, or page-scroll state.
- Particles rotate slowly by themselves and rotate from primary-button mouse dragging only.
- Wheel, touch, ArrowUp/ArrowDown, and PageUp/PageDown should move one complete chapter at a time, without leaving the page between chapters.

## Implemented

- Added guarded 700 ms chapter navigation in `ImmersiveLoginPage`.
- Routed wheel, vertical touch swipes, ArrowUp/ArrowDown, PageUp/PageDown, and chapter links through one navigation callback.
- Prevented native free-form smooth scrolling by removing document-level `scroll-behavior: smooth`.
- Removed the chapter-state input from `LearningCoreScene`; its particles now remain independent of page navigation.
- Kept slow automatic rotation and added fine-pointer primary-button drag handling. Plain pointer movement, right-clicks, and scroll do not alter the particle orientation.
- Added tests for keyboard chapter movement and the absence of chapter state on the scene boundary.

## Verification

- `pnpm --dir Course-Agent/creative test tests/landing/immersive-login-page.test.tsx`: 4 tests passed.
- `pnpm --dir Course-Agent/creative typecheck`: passed.
- Browser verification at `http://localhost:3010/login` with Microsoft Edge confirmed desktop first and second chapters, mobile layout, and primary-button drag rendering.
- `pnpm --dir Course-Agent/creative lint` exceeded two 120-second execution windows without output, so it has no passing result in this session.
- The full `pnpm --dir Course-Agent/creative test` run has three unrelated existing failures: two resource tests expect the old `习题题库` text, and the invalid Mermaid test times out. The landing regression test passes independently.
