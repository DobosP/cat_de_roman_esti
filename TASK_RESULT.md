# Task Result — V61 refined home-care-and-maintenance morphology

## Summary

- V60 landed and was pushed at `2a4d683`; its exact GitHub Actions run `31773557256`
  passed frontend and backend gates on Python 3.12 and 3.14.
- V61 starts from that landed baseline on `feat/v61-home-care-maintenance-morphology` and
  is intentionally uncommitted and unlanded until the complete backend and CI gates pass.
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
- The complete backend suite and exact-commit CI have not run for V61. Their absence keeps
  the landing gate incomplete despite every scoped gate above being green.

## Authorized post-landing deployment

- The owner authorizes only the anonymous V61 stack after the exact landed commit and CI
  are green. Accounts and submissions must remain off; this does not authorize the accounts
  stack, database, OAuth, extra workers, or infrastructure changes.
- Before rebuilding production, confirm the exact running revision, preserve its app image
  as the rollback target, verify the host checkout can fast-forward to exact V61 `main`, and
  retain the existing `.env.anon`, DNS, Caddy, and TLS configuration.
- Required public smokes cover `/api/health`, `/api/manifest`, `/healthz`, `/api/me`, all
  14 `/api/categories` rows, and seeded Intrusul/Perechi creation. Accounts must report off,
  submissions must remain unavailable, and the manifest must report the exact V61 build.
- On any mandatory smoke failure, restore the preserved image or previous-good commit;
  never use `down -v` or Docker prune. No V61 deployment has occurred yet.

## Risks and manual review

- Both rejected `cheie` forms remain absent from exact, projection, and fuzzy paths.
- The 48 accepted aliases have their intended unique owners and open no route for inherited
  rejected surfaces; package/test mirrors and invariant payloads match.

## Merge recommendation

Do not land V61 until the complete backend suite and exact-commit CI are green.
After landing, deploy only the exact green commit through the authorized anonymous procedure.
