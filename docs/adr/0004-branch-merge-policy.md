# ADR-0004: Branch/merge policy — direct local merges to main; push is opt-in

Date: 2026-06-22
Status: accepted
Supersedes: the PR-only policy of 2026-06-21 (`351b657`, pre-ADR — recorded only in
CONTRIBUTING.md history)

## Decision
Allow **direct local merges to `main`**: substantial work happens on a feature branch
(`feat/…`, `fix/…`) and is merged/fast-forwarded into `main` locally once the CI gate
is green (fixture validation + ruff + pytest on py3.11/3.12 + frontend eslint/build);
trivial changes may land on `main` directly. **Pushing to `origin` remains opt-in:**
assistants must NOT `git push` or open a remote PR without Paul's explicit request —
local merges are fine, publishing is not. [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
stays the living how-to for the quality gate.

## Context / why
Relaxed 2026-06-22 by owner request (`db99f57`) from the 2026-06-21 PR-only rule
("no direct commits, merges, or pushes to `main`"). The repo is developed by a local
agent fleet where PR round-trips added friction without adding review value, while
the actual risk boundary is **publication**, not local integration. Why not keep
PR-only: no second reviewer exists locally; CI green is the effective gate either
way. Why not allow pushing too: fleet-wide policy keeps publishing to remotes an
explicit owner decision.

## Consequences
- Local `main` may be ahead of `origin/main` for extended periods; that is expected.
- The push/no-push line matters more than the branch line: any automation must treat
  `git push` as owner-gated.
- README/CONTRIBUTING must describe this policy by linking here, not by restating
  older rules (the stale PR-only wording in README was fixed 2026-07-02).
