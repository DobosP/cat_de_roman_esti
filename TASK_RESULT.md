# Task result — V38 Perechi

## Summary

- Added a finite, server-authoritative Perechi API over the private V38 derived catalog.
- Added deterministic seed/daily/category/starter selection, signed-in plus private
  last-four source avoidance, and strict-catalog retry after exclusions are exhausted.
- Added bounded matching, free unordered wrong repeats, one earned hint, terminal scoring,
  answer-free sharing, private provenance, and atomic/capacity-safe sessions.
- Mounted only the Perechi routes; no frontend, lobby, miner, status, or ADR changes.

## Files changed

- `cat_de_roman_esti/wordgames/perechi.py`
- `cat_de_roman_esti/web/urls.py`
- `tests/test_wordgames_perechi.py`

## Verification

- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest -p no:cacheprovider tests/test_wordgames_perechi.py -q`
  — 22 passed.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
  — 16 passed; only the expected pytest-django config warning in this pure-Python venv.
- Combined project-venv Perechi + session run — 38 passed.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache cat_de_roman_esti/wordgames/perechi.py cat_de_roman_esti/web/urls.py tests/test_wordgames_perechi.py`
  — all checks passed.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py`
  — 336-board artifact current; green.
- `git diff --check` — clean.

## Risks / integration notes

- The existing global mobile-operation-ID snapshot predates both V38 games and will need
  its expected set updated once Intrusul and Perechi are integrated together.
- Later public serializers must continue using `_state`; catalog/source/ranking fields are
  intentionally private session fields and never appear in API state or share text.
- STATUS/ADR and frontend work are explicitly outside this focused branch.

## Merge recommendation

Green and suitable to cherry-pick into the V38 integration branch.
