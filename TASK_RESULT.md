# Task Result — V64 history-and-heritage morphology

## Summary

- V63 is landed and pushed on final `main` head
  `08038ee28c95a33c8295268de91c015697249f15`; exact final GitHub Actions run `32512940422`
  is green.
- Anonymous production remains on V61. V62 and V63 are landed but undeployed.
- Refined V64 freezes 50 normalized-unique history-and-heritage case surfaces for 25
  existing concepts. It adds exactly 48 aliases across 24 owners while rejecting
  _frontului_ and _fronturilor_ because neither bare form has one safe bounded sense.
- V64 is locally implemented with all reported gates green, but remains unlanded and
  undeployed. Exact feature commit `7a2d441ded82c1b276e6f18428a5556e1e0c9dbc` passed
  GitHub Actions run `32528498910`.

## Frozen review contract

- Candidate-funnel digest:
  `42137b42712597779ce402ce4a9f9065060701c5a19b444235b4abed69ecef40`.
- Build: `fixture-v64-history-and-heritage-morphology`.
- Fixture counts: 2,364 nodes / 9,217 edges / 8,114 aliases / 180 puzzles.
- Exact delta: +48 aliases; no projection, node, edge, puzzle, game record, hold
  disposition, ranking row, or derived board.
- Earlier accepted inventories retain their owners; earlier rejected, deferred, held, and
  unauthored surfaces retain their prior absence or disposition.

## Implementation scope

- Added the reviewed V64 data module, rollback-safe apply wrapper, complete two-reviewer
  archive, ADR-0088, and focused six-test regression contract.
- Regenerated the alias-bearing KG/mobile/ranking/derived wrappers and migrated current
  build/count/hash pins.
- Games-pack bytes, ranking rows, derived boards, projection inventory, V49 ledger,
  sessions, accounts, frontend, and deployment remain preserved by scope.
- Migrated current cumulative compatibility pins while keeping historical wave constants
  historical.

## Artifact evidence

- KG: `d8db3ca58272e26192c9e0a3b556fc796c15dc4cec9d828f67a1245cf75d90b3`.
- Games pack:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper:
  `e9a5acd3fc62753912728dc6ca5f8a9e2ead00edfba14ef7f44a3e752fb6e13e`.
- Derived wrapper:
  `39a77d724ad4436d0529ceeaf87e46e9cbf3a85661a60b3ca09f141211652089`.
- Mobile wrapper:
  `92cc85b8658acae05b343ea55cc773d51f2642ce84725f06ff0c34577bd0302c`.
- V49 ledger:
  `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- The exact +48-only audit, exact/projection/fuzzy resolver audit, immutable topology,
  puzzle, pack, ranking-row, derived-board, ledger, and package/test mirror checks are green.

## Verification state

- Focused V64 passed 6/6; affected V31–V33/V44/V47–V64 passed 167/167; exact full backend
  collection and execution passed 847/847 with process exit 0.
- Accounts-on passed 53/53; sessions passed 16/16.
- Fixture and games-pack validators are green. Ranking is 618 total / 449 eligible; derived
  remains 336 boards. Strict pending Lanț checked 3 with 0 flagged and 0 FAIL.
- Fixture/ranking/derived mirrors, exact +48 audit, resolver and protected-surface checks,
  immutable-payload invariants, Ruff with `--no-cache`, and global `git diff --check` are green.
- Exact feature CI run `32528498910` passed frontend and backend gates on Python 3.12 and
  3.14 for `7a2d441ded82c1b276e6f18428a5556e1e0c9dbc`.

## Production state

- Production remains on exact V61 `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`.
- Accounts and debug remain off, submissions remain disabled, and no database, OAuth,
  worker, frontend, DNS, TLS, or infrastructure change is authorized by V64.
- V62–V64 are not deployed.

## Risks and manual review

- _Frontului_ and _fronturilor_ must remain absent from exact, projection, and fuzzy
  resolution.
- Every accepted qualifier has one reviewed owner and an existing legal Lanț predecessor;
  aliases must not create graph edges or broaden projection resolution.
- Final independent review confirmed no unrelated file entered the bounded V64 change.
- Historical data-module build constants must remain historical.

## Release state

V64's exact feature commit is green. It remains unlanded and undeployed; require exact-head
CI on this release-evidence update before any fast-forward to `main`.
