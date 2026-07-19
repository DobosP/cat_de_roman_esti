# Task result — Lanț visible route corridors

## Summary

Implemented the ADR-0043 Lanț beginner-navigation slice across the server, API types,
mobile-first browser UI, tests, and durable documentation.

- A private directed corridor accepts routes up to `par + 2`, while ADR-0016's strict
  two-branch curated gate remains unchanged. Easy selection prefers width three when
  available and falls back safely for thin categories.
- Every state exposes up to six ID-free `{label, relation}` choices. The menu mixes up
  to three useful corridor hops with target-reachable detours, never backfills a fourth
  corridor hop, removes visited/dead-end options, and softly penalizes generic hubs. A
  submitted visible homonym is rebound to its exact authored node without exposing IDs.
  Any omitted real direct graph hop remains legal through free typing.
- Hints now escalate at the unchanged state from direction, to at most two ID-free
  alternatives, to one shortest-hop reveal. No complete path or corridor marker is
  serialized. If the shortest continuation was visited, hints prefer another safe forward
  route; only true recovery traps return the explicit free-undo stage. The capped three-step
  counter resets on every move or undo instead of retaining historical chains.
- The browser presents large two-column phone / three-column wide choice controls,
  spans an odd final phone choice for a balanced grid, keeps free typing available, and
  avoids automatically opening the phone keyboard.
- Free undo, scoring, seeded/daily determinism, operation IDs, two-hour TTL, and the
  1,000-session cap remain unchanged.

## Files changed

- `cat_de_roman_esti/wordgames/lant.py`
- `frontend/src/api/lant.ts`
- `frontend/src/screens/Lant.tsx`
- `frontend/src/styles/arcade.css`
- `frontend/tests/lant-recovery-feedback.test.mjs`
- `frontend/tests/mobile-beginner-ui.test.mjs`
- `tests/test_wordgames_lant.py`
- `tests/test_mobile_contract.py`
- `docs/MOBILE_CONTRACT.md`
- `docs/STATUS.md`
- `docs/adr/0022-confident-auto-accept-and-lant-guidance.md`
- `docs/adr/0043-lant-visible-route-corridors.md`

## Commands and exact results

- Focused final forward/backtrack/homonym/quota/counter selection: **6 passed**.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_lant.py -q`: **46 passed**.
- Lanț plus mobile-contract exact integration run: **52 passed**.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_mobile_contract.py -q`: **6 passed**.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_curated.py tests/test_games_pack_invariants.py -q`: **35 passed**.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`: **11 passed**.
- `/home/dobo/work/romania_scraper/.venv/bin/ruff check --no-cache .`: **all checks passed**.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python scripts/validate_games_pack.py`: **green**.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python scripts/validate_fixture.py`: **green**.
- `node --check .claude/workflows/critique-games.js`: **passed**.
- `git diff --check`: **passed**.
- `npm run lint`: **passed**.
- `npm run typecheck`: **passed**.
- `npm test`: **9/9 source suites passed**.
- An earlier `npm run build` TypeScript/Vite emission succeeded, but its post-build
  manifest comparison rejected paths introduced by the temporary worktree dependency
  symlink. Final source lint/typecheck/tests are green; generated static was restored and
  excluded. Run the normal combined build after integration.

## Audit and performance

- Fifty representative easy curated creates showed 3–4 choices (mean 3.02): the strict
  quota supplied 150 corridor slots and the graph exposed one safe detour slot.
- Capped hub pressure changed 12/50 representative menus and reduced hub slots from 31
  to 19 without suppressing a genuinely stronger authored hub edge.
- Across 12 representative mined easy seeds, hub endpoints fell from 7 to 5 and mean
  endpoint degree from 14.62 to 13.12 (maximum 38 to 30).
- Ten representative easy board creates measured 7.42 ms cold mean / 24.10 ms cold max
  and 2.43 ms warm mean / 3.12 ms warm max.

## Risks / manual review

- The source gates are green, but the final combined static bundle should be built and
  checked from the integration worktree where dependencies have their normal path.
- Safe detours are rare in the current easy openings, so the strict no-fourth-corridor
  rule usually presents three choices; confirm that density in beginner playtesting.
- A 320–390 px manual playtest remains useful for visual polish and to measure whether
  relation wording is terse enough across real boards.

## Merge recommendation

Ready to integrate. Re-run the combined frontend build plus the root aggregate gates,
then land with ADR-0043 and the STATUS update in the same commit.
