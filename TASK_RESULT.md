# Task Result — Contexto broad guesses and progressive clues

## Summary

- Added a pure-stdlib, Contexto-only projection with 444 collision-screened everyday
  Romanian canonical terms across 26 domains and 89 existing KG scoring anchors.
- Replaced positional fallback behavior with 252 explicit mappings and 192 mappings to
  named, justified broad-domain fallbacks; domains without an honest fallback fail closed.
- Kept projected terms guess-only: deterministic opaque ids, normalized-surface dedupe,
  anchor rank/temperature feedback with a 0/1 penalty, and no win even at the target anchor.
- Added bounded progressive clues after three attempts: category first, then one familiar
  non-target word strictly warmer than the player's best. Explicitly themed games skip the
  redundant category stage; rank 2/no-safe-improvement states expose no warmer clue.
- Added short mobile-first category/warmer clue cards and typed additive API fields.
- Fixed stale warmer availability when a projected rank-3 guess has already played the
  only rank-2 anchor; rejected stale clue requests now refresh authoritative browser state.
- Superseded ADR-0005 with ADR-0042 and updated STATUS plus MOBILE_CONTRACT.
- Shared KG fixtures, curated pack copies, selection/scoring boundaries, TTL 7200 seconds,
  and the 1,000-session LRU cap remain unchanged. No tracked static bundle was generated.

## Files changed

- `cat_de_roman_esti/wordgames/contexto_projection.py` (new)
- `cat_de_roman_esti/wordgames/contexto.py`
- `tests/test_wordgames_contexto.py`
- `frontend/src/api/contexto.ts`
- `frontend/src/screens/CaldRece.tsx`
- `frontend/tests/contexto-api.test.mjs`
- `frontend/tests/contexto-progressive-clue.test.mjs` (new)
- `docs/adr/0005-contexto-category-clue.md`
- `docs/adr/0042-contexto-broad-projection-progressive-clues.md` (new)
- `docs/MOBILE_CONTRACT.md`
- `docs/STATUS.md`

## Verification and exact results

- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_contexto.py -q`
  - 53/53 passed.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_contexto.py tests/test_mobile_contract.py tests/test_wordgames_session_store.py -q`
  - 70/70 passed; only the sandbox `.pytest_cache` write warning.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -q`
  - 403/403 passed.
- `/home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache .`
  - all checks passed.
- `npm run lint`, `npm run typecheck`, `npm test` in `frontend/`
  - lint and typecheck passed; 10/10 frontend source-test files passed.
- Production build to `/tmp/cat-contexto-v34-build`
  - Vite transformed 462 modules; build passed.
  - initial JS/CSS gzip budget: 116.12 KiB / 120 KiB; four Romanian font subsets.
- `scripts/validate_games_pack.py` and `scripts/validate_fixture.py`
  - both GREEN, zero errors.
- Workflow syntax, `git diff --check`, fixture mirror `cmp`, and pack mirror `cmp`
  - all passed; tracked `cat_de_roman_esti/web/static` diff is empty.

## Projection audit metrics

- 444 unique live terms; 26 domains; minimum 14 terms/domain.
- 89 existing anchors; zero normalized KG label/id/alias collisions; zero missing anchors.
- 80 explicit semantic override clusters and all 26 named fallback policies are
  exhaustively test-pinned, plus one human-legible representative pairing per domain.
- Across 12 approved `usor` targets: at least 40 distinct ranks and three temperature
  buckets per target; largest single-rank tie share <= 15%; at least 24/26 domains span
  multiple ranks.
- Familiar warmer clues are pinned at salience >= 0.55 on the sampled approved easy boards.

## Risks / manual review

- This is a bounded authored approximation, not a Romanian embedding model. Broad default
  anchors intentionally trade fine-grained nuance for deterministic, reviewable behavior.
- The source UI is responsive and build/type/lint green, but a human 320–390 px device
  playtest should still check keyboard overlap and the visual prominence of both clue cards.
- The warmer-candidate reverse traversal runs only for post-threshold availability checks
  and clue issuance; it adds no per-session graph-sized cache.

## Merge recommendation

Recommended for orchestrator review and integration. Do not stage this result file. No
commit, merge, push, deployment, worktree deletion, or generated-static update was made.
