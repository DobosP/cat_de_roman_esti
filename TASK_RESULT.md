# Task Result — V61 refined home-care-and-maintenance morphology

## Summary

- V60 landed and was pushed at `2a4d683`; its exact GitHub Actions run `31773557256`
  passed frontend and backend gates on Python 3.12 and 3.14.
- V61 landed and was pushed at `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`;
  exact GitHub Actions run `31811714317` passed frontend and backend gates on Python 3.12
  and 3.14.
- The fixed refined funnel contains 50 normalized-unique case surfaces for 25 existing
  home-care-and-maintenance concepts. It calls for 48 qualified exact aliases across 24
  owners; `cheii` and `cheilor` remain rejected because the bare forms do not have one safe
  home-care owner.
- The fixture is `fixture-v61-home-care-and-maintenance-morphology`: 2,364 nodes,
  9,217 edges, 7,970 aliases, and 180 puzzles.
- V61 changes no projection, node, edge, puzzle, game record, hold disposition, or derived
  board. The artifact audit confirms topology, pack bytes, ranking rows, and derived boards
  remain unchanged while exactly 48 aliases were added.

## Implementation scope

- Added the bounded V61 data module and transactional apply wrapper.
- Archived both complete reviews of the fixed funnel and recorded the V61 decision.
- Added a focused V61 regression contract covering accepted aliases, both new rejections,
  and every inherited rejected surface.
- Regenerated only alias-bearing KG/mobile/ranking/derived wrappers and updated current
  build, alias-count, and digest pins while preserving invariant payloads.
- Updated current README, mobile-contract, status, and task-result documentation.

## Review and artifact evidence

- Candidate-funnel digest:
  `218fef7d717e5c373c0390586e9dacee207b405f773e6795c4e4a6c42bec4de6`.
- KG: `544fe547c875acb913c3d188917304b246a84997ba3cfccb586da119ac89913c`;
  games pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper: `ce03c2a69a98a6905dc14e4f66a143c89dafee9b689532e6d2e4266632f2b5ee`;
  derived wrapper: `2a3ad0e2f9345396780481f72ab0a2cc144eef3b96d0ab11dc0b814182c9138a`.
- Mobile snapshot: `387bb3bcdcccebfca9d1f5615604bc28279a087463a7162653f97972245e1665`;
  Lanț ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- Immutable ranking rows remain `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`;
  derived boards remain `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Verification

- Source assertions, both reviewer partitions, transaction dry-run and apply, exact
  resolution, inherited rejection checks, and the exact +48-alias-only artifact audit passed.
- Focused V61: 6 passed. Affected V31–V33/V44/V47–V61: 149 passed. Accounts-on:
  53 passed. Session store: 16 passed.
- Ranking and derived checks, pack and fixture validators, strict Lanț sweep (3 checked,
  0 flagged, 0 FAIL), fixture mirrors, Ruff, and whitespace checks passed.
- Exact landed commit `1c42de0d52cf56fd0d49f930aaccaafbc96906f9` passed complete backend
  and accounts-on gates on Python 3.12 and 3.14 plus frontend contracts, lint, and build in
  GitHub Actions run `31811714317`.

## Production deployment evidence

- The anonymous production stack was upgraded from V48 `d59caed` to exact V61 on
  2026-08-14. The host checkout is clean at `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`;
  the app is healthy with zero restarts.
- `rollback-d59caed` points to the previous image ID prefix `sha256:d18295ae`; the deployed
  image ID begins `sha256:efa179af`.
- Accounts and debug are off, `CAT_SUBMISSIONS_DIR` is absent, and submissions return HTTP
  503. No accounts stack, database, OAuth, extra workers, or infrastructure were enabled.
- `/api/manifest` reports `fixture-v61-home-care-and-maintenance-morphology`, public content
  hash `sha256:bfc3e868f49d8e07f23e2895c3010ecb9bd966dbfef6e5b543157937e49a1699`, and counts
  2,364 nodes / 9,217 edges / 180 puzzles.
- `/api/health`, `/healthz`, `/api/me`, all 14 `/api/categories` rows, and seeded Intrusul
  and Perechi creation passed. Preserve the rollback tag; never use `down -v` or Docker prune.

## Risks and manual review

- Both rejected `cheie` forms remain absent from exact, projection, and fuzzy paths.
- The 48 accepted aliases have their intended unique owners and open no route for inherited
  rejected surfaces; package/test mirrors and invariant payloads match.

## Release result

V61 is landed, pushed, exact-CI-green, and deployed to anonymous production. Accounts and
submissions remain off.
