# Task Result — basic words v28

## Summary

- Added 15 first-class easy concepts, 44 collision-safe inflections, and 53 explicit
  non-distractor semantic edges through the rollback-safe content applier.
- Completed eligible beginner resolution at 234/234 while retaining all 11 deferred
  ambiguous terms and the `lună`/Moon and `vapor`/ship sense boundaries.
- Balanced every new node to at least two forward choices, four incident links, and two
  same-category links; no generic `related_to` edge was added.
- Updated the fixture to 2,199 nodes, 8,845 edges, 7,077 aliases, and 180 puzzles. The
  deterministic rebuild changed 23 legacy puzzle records; the curated pack remained
  byte-identical at SHA-256 `2c7d2eb298781a12250b087e6f4bd92c204928180fadd743b35883b61444a023`.
- Restored the v25 source pin to that actual pack SHA and made its regression tests
  additive without weakening the exact 168-alias, 25-edge, and 33-item guarantees.
- Added ADR-0036, refreshed durable status, and generated the public mobile contract.

## Files changed

- Source: `scripts/basic_words_v28_data.py`, `scripts/apply_basic_words_v28.py`, and the
  corrected v25 pack pin.
- Generated: both KG mirrors and `tests/fixtures/cat_mobile_app_pack_contract.json`.
- Tests: additive v25 guards plus `tests/test_v28_basic_words.py`.
- Docs: `docs/STATUS.md` and ADR-0036.

## Verification

- Full backend: `355 passed in 85.38s`.
- Focused v25/v28: 16 passed; v24: 12 passed; app-pack/data: 23 passed; sessions: 11 passed.
- Fixture validator: GREEN, 0 errors. Games-pack validator: GREEN.
- Exact critique gate: 33 checked, 0 flagged, 0 FAIL.
- Whole pending critique: 222 checked; before/after JSON byte-identical at SHA-256
  `122e35c819f6bdacbbcf95b7dcbac09bf5b2a3de56314487df187493ac86919a`.
- Ruff: all checks passed. Workflow JavaScript syntax and `git diff --check`: clean.
- Graph mirrors and pack mirrors are byte-identical; no curated record was added,
  promoted, demoted, or edited.

## Risks / manual review

- The 23 regenerated legacy puzzles are validator-green but remain appropriate for a
  quick human playtest with the new beginner words.
- The exact 33 pending curated boards still require the planned subjective review before
  promotion. This branch is not deployed.

## Merge recommendation

Green for review and coordinated landing with the matching roedu-mobile v28 contract
branch. No commit, push, merge, deployment, or worktree deletion was performed.
