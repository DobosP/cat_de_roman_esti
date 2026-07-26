# Task result

## Summary

- Added a separate, versioned replay-memory document capped at one opaque completed
  non-daily session ID for each of `intrusul` and `perechi`.
- Every free start falls back to that ID, while daily starts neither read nor write it.
- Direct replay still prefers the just-completed session, and expired predecessor IDs
  remain harmless through the existing server fallback.
- Corrected the active-session TTL comment from six hours to 7,200 seconds (two hours).
- Regenerated the tracked frontend release bundle.

## Files changed

- `frontend/src/derivedReplay.ts`
- `frontend/src/screens/Intrusul.tsx`
- `frontend/src/screens/Perechi.tsx`
- `frontend/src/hooks/useActiveGame.ts`
- `frontend/tests/derived-replay-memory.test.mjs`
- `frontend/tests/v38-six-game-ui.test.mjs`
- `tests/test_wordgames_intrusul.py`
- `tests/test_wordgames_perechi.py`
- `cat_de_roman_esti/web/static/` generated release assets

## Verification

- `npm test` — 18/18 frontend test files passed.
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npm run build` — passed; 470 modules, initial JS/CSS 117.69/120 KiB gzip,
  four Romanian font subsets.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest
  tests/test_wordgames_intrusul.py tests/test_wordgames_perechi.py -q
  -p no:cacheprovider` — 36/36 passed.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest
  tests/test_wordgames_session_store.py -q` — 16/16 passed; only the known shared-venv
  config/cache warnings.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest
  tests/test_static_asset_cache.py tests/test_web.py -q -p no:cacheprovider` —
  16/16 passed.
- `git diff --check` — passed.

## Risk / manual review

- Replay memory is best-effort when local storage is unavailable.
- An expired stored ID may be sent again until the next non-daily completion, but the
  server resolves it to an empty predecessor ring without error.
- TTL remains 7,200 seconds; each game store remains capped at 1,000 sessions; no source,
  catalog, answer, or rank fields enter browser storage.

## Commit

- `744ffdb` (`fix(web): preserve derived replay continuity`)

## Merge recommendation

Cherry-pick `744ffdb` onto the V39 integration branch. Do not include `TASK_BRIEF.md` or
`TASK_RESULT.md`.
