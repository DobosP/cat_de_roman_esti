# Task result

## Summary

- Added ADR-0061 and superseded ADR-0053 without editing its landed body.
- Corrected product, compliance, served legal, account-gate, deletion, and code-comment copy:
  browser progress is device-local; the account receives an upload-only private copy of
  completed-score rows; no automatic download, restore, or merge exists.
- Kept `PlayedPuzzle` repeat avoidance and `VerifiedBest` public ranking separate.
- No data, authentication, ranking, session, or generated-static behavior changed.

## Files changed

- ADR/release/deploy: `docs/adr/0053-*`, `docs/adr/0060-*`,
  `docs/V39_REFINEMENT.md`, `docs/DEPLOY.md`.
- Compliance drafts: README, privacy RO/EN, terms RO/EN, DPIA, ROPA, consent spec,
  retention/DSAR.
- Served/player copy: `cat_de_roman_esti/web/legal.py`,
  `frontend/src/components/AccountBar.tsx`.
- Terminology comments and focused legal/frontend tests.

## Verification

- `pytest tests/test_legal.py -q`: 8 passed.
- Accounts-on `pytest tests/accounts -q`: 53 passed.
- Required session-store target: 16 passed.
- `npm test`: 21 test files passed.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- Ruff: passed.
- Vite production build to `/tmp`: passed; initial JS/CSS 119.17/120 KiB gzip,
  four Romanian font subsets.
- `git diff --check`: passed.

## Risks / manual review

- Compliance documents remain drafts requiring the existing legal-review and go-live gates.
- ADR-0061 intentionally documents the current one-way behavior; future automatic restore
  requires account namespacing and a new decision.
- Root integration must add the V41 STATUS/release references in its assembled commit.

## Merge recommendation

Cherry-pick green commit `4df0dd7`; do not push this worker branch.
