# Task Result — V37 fun-first selection runtime

## Summary

- Added a strict loader for the digest-bound `board_rankings_v37.json` sidecar.
- Attached private familiarity/quality/pilot fields to curated items with neutral defaults.
- Added pilot-eligible preference, integer weighted seeded selection, and weighted daily
  rendezvous tickets while preserving filters, exclusions, daily floors, and fallbacks.
- Neutralized bundled rankings for custom packs/graph overrides unless an explicit
  digest-matching `rankings_path` or `CAT_BOARD_RANKINGS` is supplied.
- Added 21 focused tests, including all four create-response secrecy boundaries.

## Files changed

- `cat_de_roman_esti/wordgames/packs.py`
- `tests/test_v37_board_rankings.py`

## Commands run and exact results

- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v37_board_rankings.py -q`
  - **21 passed**
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v37_board_rankings.py tests/test_games_pack_invariants.py tests/test_wordgames_curated.py -q`
  - **56 passed**
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
  - **16 passed** (one expected pytest config warning because this venv lacks pytest-django)
- `CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/accounts/test_avoid_repeats.py -q`
  - **4 passed**
- `CAT_BOARD_RANKINGS=/home/dobo/work/_worktrees/cat_de_roman_esti/feat__board-ranking-model-v37/cat_de_roman_esti/fixtures/board_rankings_v37.json PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_curated.py tests/test_mobile_contract.py -q`
  - **30 passed** with the real scoring sidecar active
- Same real-sidecar environment with `python -m pytest -o addopts='' -q`
  - **green; 459 tests collected**
- Cross-worktree real-sidecar load:
  - approved/pilot eligible counts: Conexiuni `209/123`, Contexto `192/192`,
    Lanț `94/94`, Alchimie `77/77`
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python scripts/validate_games_pack.py`
  - **games pack GREEN**
- `/home/dobo/work/romania_scraper/.venv/bin/ruff check .`
  - **All checks passed**
- `git diff --check`
  - **clean**

## Risks / manual review

- The bundled sidecar remains optional in this branch because the artifact is produced
  by sibling commit `b3bcb11b54f1506005a17ed4d5de22c21f915bda`; integration should make it
  mandatory after cherry-picking that commit.
- Pack and KG digests are always verified. Rubric digest is recomputed when the source
  `docs/CRITIQUE_RUBRIC.md` exists; an installed wheel does not package that document,
  so runtime there validates its SHA-256 shape while the source/build gate provides the
  independent rubric binding.
- No frontend, session model, TTL/cap, score, or public API field changed.

## Merge recommendation

Cherry-pick this runtime commit after the scoring artifact, switch the bundled-sidecar
absence branch to fail closed, then run the combined backend gate.
