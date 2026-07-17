# Task Result

## Summary

Implemented frontend-only Conexiuni one-away recovery. A nonterminal authoritative
`one_away` response keeps the submitted four tiles selected, blocks the same unordered
set from being submitted again, and gives persistent one-tile swap guidance. Correct,
ordinary-wrong, terminal, new, and restored states clear recovery. Backend mistake,
duplicate, secrecy, TTL, and capacity behavior is unchanged.

## Files changed

- `frontend/src/screens/Conexiuni.tsx`
- `frontend/tests/conexiuni-one-away.test.mjs`
- `docs/adr/0028-conexiuni-one-away-recovery.md`
- `docs/STATUS.md`
- Tracked production files under `cat_de_roman_esti/web/static/`

## Verification

- `npm ci`: 164 packages installed; 0 vulnerabilities.
- `npm test`: 21 passed.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- `npm run build`: passed; 461 modules; initial gzip 115.38 KiB / 120 KiB.
- `pytest tests/test_wordgames_conexiuni.py tests/test_wordgames_session_store.py -q`:
  35 passed.
- `pytest -q`: 321 passed.
- `ruff check .`: passed.
- `scripts/validate_games_pack.py`: GREEN.
- `scripts/validate_fixture.py`: GREEN.
- `node --check .claude/workflows/critique-games.js`: passed.
- `git diff --check` and staged diff check: passed.
- Final manifest points to `Conexiuni-DizqQaSB.js` and `index-aA-tQDY5.js`; the emitted
  Conexiuni chunk contains the new recovery guidance.

## Risks / manual review

The in-app browser was unavailable, so no visual click-through is claimed. Romanian
playtesting should confirm the retained selection and disabled unchanged retry are clear
on desktop and mobile. The pre-existing shake animation may remount the tile grid and
move keyboard focus after a wrong guess; this slice does not broaden into that behavior.

## Merge recommendation

Recommend landing after the independent final read-only audit reports no material issue.
Keep this file and `TASK_BRIEF.md` untracked per dispatcher policy.
