# Task Result — V65 music-and-performance morphology

## Summary

- V64 is landed and pushed on final `main` head
  `156736a04c705406625ca4ef35752cd41a558187`; exact final GitHub Actions run `32530075329`
  is green.
- Anonymous production remains on exact V61. V62 through V65 are undeployed.
- The fixed V65 funnel contains 50 normalized-unique music-and-performance case surfaces.
  It adds exactly 48 aliases across 24 existing owners while rejecting _notei_ and
  _notelor_ because neither ordinary form has one safely bounded musical sense.
- V65 landed and was pushed at `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; exact
  GitHub Actions run `32557471621` and feature run `32557087552` are green.
- Anonymous production was upgraded from V61 to exact V65 on 2026-08-22.

## Frozen review contract

- Candidate-funnel digest:
  `abfaaf5cf29a3e3624cc401cc36b767f90e5e0ff102634c32d17111c6b2321f6`.
- Build: `fixture-v65-music-and-performance-morphology`.
- Fixture counts: 2,364 nodes / 9,217 edges / 8,162 aliases / 180 puzzles.
- Exact delta: +48 aliases; no projection, node, edge, puzzle, game record, hold
  disposition, ranking row, or derived board.
- Earlier accepted inventories retain their owners; earlier rejected, deferred, held, and
  unauthored surfaces retain their prior absence or disposition.

## Implementation scope

- The worktree contains the reviewed V65 data module, rollback-safe apply wrapper,
  two-reviewer archive, ADR-0089, and focused regression contract.
- Regenerated the alias-bearing KG/mobile/ranking/derived wrappers and migrated current
  build/count/hash pins.
- Games-pack bytes, ranking rows, derived boards, projection inventory, V49 ledger,
  sessions, accounts, frontend, and deployment remain preserved by scope.
- Migrated current cumulative compatibility pins while keeping historical wave constants
  historical.

## Artifact evidence

- KG: `412dce67a5c49803e0a31d4e5453b32187449e15da2ebe0b0e430457668c2bf7`.
- Games pack:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper:
  `c9a3c678240631f9622a508126d6ad39158624052019d8478bbdbc14f9850849`.
- Derived wrapper:
  `a28539995c1ac5e95ee6c87ba1302edab4067e4dc614678a7cd2680d8b73ae4b`.
- Mobile wrapper:
  `d5acd5d62336090b5093182bb6897443794f1c0ae858edc63d0bdf2453895430`.
- V49 ledger:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- The exact +48-only delta audit and package/test mirror comparisons are green. Topology,
  puzzle, pack, ranking-row, derived-board, and ledger payloads remain invariant.

## Verification state

- Fixture and games-pack validators are green. Ranking is 618 total / 449 eligible; derived
  remains 336 boards. Strict pending Lanț is green at 3 checked / 0 flagged / 0 FAIL, with
  16 pack-level WARN only.
- Focused V65 passed 6/6; affected V31–V33/V44/V47–V65 passed 173/173; exact full
  backend collection and execution passed 853/853.
- Accounts-on passed 53/53; word-game sessions passed 16/16; Ruff with `--no-cache` and
  global whitespace checks are green.
- Package/test mirrors, exact +48 delta, resolver/protected-surface, inherited-binding,
  immutable-payload, and source-coupling audits are green.
- Exact feature CI run `32557087552` passed frontend and backend gates on Python 3.12 and
  3.14 for `502ea4004fc0fac391a6a74d8a8c619334eb057c`.

## Production deployment evidence

- The production host checkout is clean at exact V65
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; the healthy app image begins
  `sha256:71f3e2cc`, has zero restarts, and is tagged `release-aefcc2c64fed`.
- `rollback-1c42de0` preserves the previous V61 image `sha256:efa179af`. Caddy was not
  recreated; no env, DNS, TLS, database, OAuth, extra worker, or infrastructure changed.
- Accounts and debug are off, `CAT_SUBMISSIONS_DIR` is absent, and submissions return HTTP 503.
- The public manifest reports `fixture-v65-music-and-performance-morphology`, content hash
  `sha256:6670819a1eefe0b15b7d410371c713515f54196f8d340ed7da959ec69057ba15`,
  and 2,364 nodes / 9,217 edges / 180 puzzles.
- Runtime KG/pack/ranking/derived hashes match the V65 pins. Health, healthz, all 14 populated
  categories, seeded Intrusul/Perechi, and the V65 resolver/rejection probes pass.

## Risks and manual review

- _Notei_ and _notelor_ must remain absent from exact, projection, and fuzzy
  resolution.
- Every accepted qualifier has one reviewed owner and an existing legal Lanț predecessor;
  aliases must not create graph edges or broaden projection resolution.
- Historical data-module build constants must remain historical.

## Release result

V65 is landed, pushed, exact-CI-green, and deployed to anonymous production. Require exact
CI on this rollout record before V66 starts from the final V65 `main` head.
