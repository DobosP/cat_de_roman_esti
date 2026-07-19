# Task Result — Alchimie V35

## Summary

- Added server-authoritative unordered experiment memory, bounded at `C(32,2) = 496`.
- First distinct owned pairs behave as before; barren and formerly productive repeats return
  `already_tried=true` with authoritative state and mutate no move, score, dry spell, hint,
  or inventory state. Reset clears memory; public state exposes only `attempted_count`.
- Added a compact accent-insensitive inventory search that opens the complete discovered
  inventory while active, plus a visible ready-pair legend and terse no-cost retry copy.
- Superseded ADR-0035 with ADR-0047 and updated durable/mobile contract documentation.

## Files changed

- `cat_de_roman_esti/wordgames/alchimie.py`
- `frontend/src/api/alchimie.ts`
- `frontend/src/screens/Alchimie.tsx`
- `frontend/src/styles/arcade.css`
- `tests/test_wordgames_alchimie.py`
- `tests/test_alchimie_sparse_recipes.py`
- `tests/test_mobile_contract.py`
- `frontend/tests/alchimie-empty-recovery.test.mjs`
- `frontend/tests/alchimie-lineage.test.mjs`
- `frontend/tests/alchimie-projection.test.mjs`
- `docs/adr/0035-bounded-alchimie-empty-reaction-recovery.md`
- `docs/adr/0047-bounded-alchimie-experiment-memory.md`
- `docs/MOBILE_CONTRACT.md`
- `docs/STATUS.md`

## Commands run and exact results

- `PYTHONPATH=. .venv/bin/python -m pytest -q -p no:cacheprovider` — 422/422 passed.
- Focused Alchimie/scoping/mobile pytest gate — 52/52 passed.
- Exhaustive 496-request memory test alone — 1/1 passed; 0.97 seconds.
- Required `romania_scraper` session-store command — 11/11 passed; one harmless external-venv
  warning for its missing pytest-django `DJANGO_SETTINGS_MODULE` option.
- `.venv/bin/ruff check --no-cache .` — all checks passed.
- `npm test` — 11/11 frontend source-test suites passed.
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `git diff --check` — passed.

## Risks / manual review

- No production/static build was run or changed, per dispatcher scope.
- A real-device/browser Romanian pass at 320–390 px remains useful for visual polish; automated
  source tests pin full-inventory search, accent folding, 44 px sizing, and the ready legend.
- Session TTL remains 7,200 seconds and the store cap remains 1,000; the existing 11-test store
  contract is green.

## Merge recommendation

Green and recommended for merge. Do not include this task-result artifact in the commit.
