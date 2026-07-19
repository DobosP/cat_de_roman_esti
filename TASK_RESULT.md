# Task result — V38 frontend recovery

## Summary

- Reconciled Intrusul and Perechi after failed mutations by reloading authoritative session state.
- Preserved resumable sessions across transient resume failures and adopted terminal resume state.
- Added synchronous single-flight guards shared by actions and hints, plus separate create/replay guards.
- Disabled result actions during create/replay and exposed an accessible visible Intrusul hint requirement.
- Added executable async-control tests and source regressions for recovery, locking, and accessibility.
- Regenerated the checked-in frontend static bundle.

## Files

- `frontend/src/asyncControl.mjs`
- `frontend/src/asyncControl.d.mts`
- `frontend/src/components/ResultCard.tsx`
- `frontend/src/screens/IntrusGame.tsx`
- `frontend/src/screens/PerechiGame.tsx`
- `frontend/tests/async-control.test.mjs`
- `frontend/tests/v38-recovery.test.mjs`
- Generated files under `static/frontend/`

## Verification

- `npm test`: 86/86 passed.
- `npm run lint`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed; 469 modules, 117.60/120 KiB gzip, four fonts.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -p no:cacheprovider tests/test_static_asset_cache.py tests/test_web.py tests/test_mobile_contract.py tests/test_wordgames_intrusul.py tests/test_wordgames_perechi.py -q`: passed (60 tests).
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m ruff check .`: passed.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest -p no:cacheprovider tests/test_wordgames_session_store.py -q`: 16/16 passed; lightweight environment emitted the known pytest-django option warning.
- `git diff --check`: passed.

## Commit

- `82775d51854ba53ee380ed7bebcb58372fde0f8b` (`fix(web): reconcile V38 game actions`)

## Risks and integration notes

- Browser E2E and physical-phone testing were not run.
- Starter behavior is intentionally excluded because it is owned by the separate starter-fix branch.
- The recovery and starter branches both touch game screens and generated static assets. Apply the source commits in integration order, resolve screen overlap if needed, then rebuild static assets once on the integrated tree.

## Merge recommendation

Cherry-pick `82775d51854ba53ee380ed7bebcb58372fde0f8b` after the V38 frontend commit/current integration base. Integrate the starter fix afterward and run the combined frontend plus targeted backend gates before landing.
