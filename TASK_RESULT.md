# Task Result — V37 board ranking model

## Summary

- Added a deterministic, read-only-by-default ranking generator with explicit `--write`.
- Ranked all 794 curated records using a 60% Romanian KG-salience familiarity proxy and
  40% bounded game-specific critique/dossier evidence.
- Kept score, review status, and pilot eligibility separate. The pilot cohort contains
  486 payload-valid approved boards with no deterministic critique FAIL.
- Added byte-identical package/test sidecars bound to normalized pack, KG, and rubric
  SHA-256 digests, plus contiguous per-game ranks and eligible-stock weights 1..5.
- Session TTL (7,200 seconds), 1,000-entry cap, hidden answers, and gameplay payloads are
  unchanged.

## Files changed

- `scripts/rank_games_pack.py`
- `cat_de_roman_esti/fixtures/board_rankings_v37.json`
- `tests/fixtures/board_rankings_v37.json`
- `tests/test_board_rankings_v37.py`
- `TASK_RESULT.md`

## Commands run and exact results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/rank_games_pack.py`
  - exit 0; `794 total / 486 pilot-eligible`; `board rankings GREEN`
  - eligible by game: Conexiuni 123, Contexto 192, Lanț 94, Alchimie 77
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -o addopts='' -p no:cacheprovider tests/test_board_rankings_v37.py tests/test_critique_pack.py tests/test_games_pack_invariants.py -q`
  - `59 passed in 30.51s`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest -o addopts='' -p no:cacheprovider tests/test_wordgames_session_store.py -q`
  - `16 passed, 1 warning in 0.24s`
  - warning: the intentionally minimal `romania_scraper` venv does not know the existing
    repository `DJANGO_SETTINGS_MODULE` pytest option; the session tests still passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_games_pack.py`
  - all seven classes `ok`; `games pack GREEN`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/critique_pack.py`
  - exit 0; `794 item(s) checked, 483 flagged, 236 FAIL finding(s)`
  - these are the known historical stock findings; records carrying a FAIL cannot be
    `pilot_eligible` in the new sidecar.
- `PYTHONDONTWRITEBYTECODE=1 /home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache .`
  - `All checks passed!`
- `git diff --check`
  - exit 0, no output
- `cmp -s cat_de_roman_esti/fixtures/board_rankings_v37.json tests/fixtures/board_rankings_v37.json`
  - exit 0; mirrors are byte-identical

## Risks / manual review

- `romanian_familiarity` and `play_quality` are editorial proxies, not player-measured
  knowledge or enjoyment. Larger-pilot completion, quit, hint, and mistake evidence should
  recalibrate a later schema/version.
- Rank intentionally covers pending and ineligible inventory too; consumers must filter on
  `pilot_eligible`. Every ineligible row has `selection_weight: 1`.
- No pack, KG, critique rubric, ADR, STATUS, API, frontend, or runtime selection code changed.

## Merge recommendation

Merge after the V37 runtime loader/selection integration validates this exact schema and
the orchestrator adds the required ADR/STATUS update in its integration branch.
