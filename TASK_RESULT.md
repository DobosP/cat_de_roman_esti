# Task result — V38 first non-daily starter eligibility

## Summary

- Added a monotonic, bounded `completedNonDaily` marker to normalized local score records.
- Daily completions leave that marker false; Intrusul and Perechi request `starter=1`
  until the first completed non-daily run.
- Older history without the marker is inferred from retained best/recent/puzzle entries.
  Malformed storage still normalizes to an empty, beginner-safe board.
- Rebasing onto recovery commit `82775d5` retained its shared mutation/start locks and
  authoritative recovery behavior. The tracked Vite bundle was regenerated once from
  the combined source.

## Files changed

- `frontend/src/scores.ts`
- `frontend/src/screens/Intrusul.tsx`
- `frontend/src/screens/Perechi.tsx`
- `frontend/tests/scores-nondaily-history.test.mjs`
- `frontend/tests/v38-six-game-ui.test.mjs`
- Generated `cat_de_roman_esti/web/static/` release bundle and manifest

## Commands and exact results

- `npm test`: **17/17 test-file processes passed**, including executable empty,
  daily-only, non-daily, 50-entry-cap, legacy, and malformed-history cases.
- `npm run lint`: green.
- `npm run typecheck`: green.
- `npm run build`: green; **469 modules**, combined initial bundle
  **117.69/120.00 KiB gzip**, four Romanian font subsets.
- `git diff --check`: green.
- Final production rebuild was deterministic: the worktree had no tracked diff afterward.

## Risks / manual review

- Eligibility intentionally changes only after a completed non-daily result. An abandoned
  or expired first board remains beginner-eligible.
- The marker is one boolean per bounded game record and remains monotonic through imports;
  it adds no backend state and changes no session contract.

## Merge recommendation

Recovery commit `82775d51854ba53ee380ed7bebcb58372fde0f8b` is the direct parent.
Land starter commit `e9df66e652730fe0fdbb9bc217dd3818d4d474cb` after it. Do not use the
pre-rebase SHA `b361345`.
