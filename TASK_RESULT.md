# Task result — V38 derived catalog

## Summary

- Added an offline deterministic generator for strict Intrusul and Perechi derivations
  from the 123 V37-eligible Conexiuni sources.
- Committed byte-identical private catalog copies containing 183 Intrusul and 153
  Perechi boards, capped at three diversity-first variants per source.
- Added a digest-pinned runtime loader and source-first seeded/daily selectors with
  standard and starter profiles. Empty filtered shelves never widen.
- Kept V37 pack loading and daily selection code unchanged.

## Files changed

- `scripts/build_derived_catalog_v38.py`
- `cat_de_roman_esti/wordgames/derived_catalog.py`
- `cat_de_roman_esti/fixtures/derived_catalog_v38.json`
- `tests/fixtures/derived_catalog_v38.json`
- `tests/test_v38_derived_rankings.py`
- `tests/test_v38_ranked_catalog.py`

## Verification

- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py -q`
  — 18 passed; only the expected missing pytest-django config warning in this pure-Python venv.
- `PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q`
  — 16 passed; same harmless config warning.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache scripts/build_derived_catalog_v38.py cat_de_roman_esti/wordgames/derived_catalog.py tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py`
  — all checks passed.
- `PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py`
  — 336 boards; committed artifacts current; green.
- `git diff --check` — clean.

## Risks / integration notes

- No endpoints or session behavior are included. Later game modules must construct public
  responses manually and never serialize catalog/source IDs or ranking fields.
- Any `CAT_GAMES_PACK` or `CAT_KG_FIXTURE` override disables the bundled derived catalog
  by failing closed; explicit matching override support is intentionally deferred.
- The two JSON copies are about 249 KiB each and are server package data, not frontend assets.
- STATUS/ADR updates were explicitly deferred to the V38 integration branch.

## Merge recommendation

Green and suitable to cherry-pick into the V38 integration branch.
