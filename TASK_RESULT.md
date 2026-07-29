# Task Result — V43 import verification contract

## Summary

- Added a pure, whole-batch preflight before `densify_content.run()` or pack access.
- Bound factual verification to every raw node ID, canonical
  `edge:<src>-><dst>` ref, and game-instance ref exactly once.
- Required category-bound, nonblank factual and quality coverage plus exactly one
  resolved quality row per game instance.
- Made missing, extra, duplicate, unknown, and unresolved `fix` states fail closed.
  Explicit factual `block` and quality `drop` remain valid exclusions.
- Corrected factual edge-block parsing so `edge:` is not retained in the source ID.
- Updated the Fable verification workflow schema/prompt to emit the enforced contract.

## Files changed

- `.claude/workflows/verify-authored-content.js`
- `scripts/import_candidates.py`
- `tests/test_import_candidates.py`
- `tests/test_critique_pack.py`

No fixture, ranking, derived-catalog, runtime, session, status, or ADR file changed.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest -p no:cacheprovider tests/test_import_candidates.py tests/test_critique_pack.py -q`
  - **68 passed**.
  - One existing environment warning: pytest does not recognize
    `DJANGO_SETTINGS_MODULE` without the optional pytest-django plugin in this venv.
- `/home/dobo/work/romania_scraper/.venv/bin/ruff check --no-cache scripts/import_candidates.py tests/test_import_candidates.py tests/test_critique_pack.py`
  - **All checks passed**.
- `git diff --check`
  - **Passed** with no output.
- Read-only fixture census:
  - pack **825**, Conexiuni **308**, KG **2,364 / 9,219**, derived **336**.
  - Session TTL **7,200s** and cap **1,000** were not touched.

## Risks / compatibility

- Verification artifacts created under the old schema are intentionally incompatible:
  they lack `reviewed_refs` and must be regenerated.
- A `fix` no longer means “import pending.” Authors must apply the correction and rerun
  verification; only factual `block`, quality `drop`, and quality `keep` are resolved.
- The importer still delegates game payload/graph semantics to its existing re-derivation
  and pack validators; this change only hardens verification completeness and ordering.

## Merge recommendation

Merge into the V43 integration branch. The focused contract suite, lint, whitespace, and
fixture census are green, and invalid verification is regression-tested to abort before
graph or pack mutation.
