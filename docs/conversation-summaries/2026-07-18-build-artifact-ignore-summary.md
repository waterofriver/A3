# Build Artifact Ignore Conversation Summary

## Request

Ignore non-functional build artifacts that caused GitHub's 100 MB file-limit rejection.

## Change

Added these project-local ignore rules to `.gitignore`:

- `Course-Agent/creative/.next-*/` for named Next.js build and verification caches, including `.next-immersive-verify`.
- `Course-Agent/creative/output/` for local screenshots and generated verification output.

## Verification and Limitation

- Verified both rules with `git check-ignore --no-index`.
- The oversized `.next-immersive-verify` packs are already tracked in commit `dae3a48`. Ignoring prevents future additions but cannot remove those blobs from existing Git history.
- A separate authorized history rewrite is required before GitHub will accept a push containing that commit.
