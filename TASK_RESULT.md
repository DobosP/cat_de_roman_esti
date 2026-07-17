# Task result

- Commit: `a125062` (`fix/content` task branch only; not pushed).
- Diagnosed the failure as a stale v25 expected pack SHA introduced by branch landing order.
- Verified both tracked `games_pack.json` copies are byte-identical: 497,281 bytes,
  SHA-256 `13dcf6e8bccf98ccf7a14c973f4dbf9a21002a109c5358d573cbcb40cd52cc45`.
- Verified the pack is the same Git blob (`84f8a5d02b97c68dd94a0ef9efd6816fab1bb7aa`)
  at `35b5883`, `bf43429`, and the task branch.
- Changed only `BASELINE_PACK_SHA256` in `scripts/semantic_edge_alias_v25_data.py`.

## Verification

- Focused v25 pack/playability regression: 1 passed.
- Full backend: 345 passed (105 seconds).
- Ruff: all checks passed.
- Games-pack validator: GREEN, including byte-identical copies.
- Fixture validator: GREEN (0 errors).
- Critique workflow JavaScript syntax: passed.
- `git diff --check`: passed.
- Frontend not touched; no frontend gate required.
