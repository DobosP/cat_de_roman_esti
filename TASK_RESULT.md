# Task Result — V62 transport-and-mobility morphology

## Summary

- V61 is already landed, pushed, and deployed at
  `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`; exact CI run `31811714317` and anonymous
  production remain green.
- V62 freezes 50 normalized-unique transport-and-mobility case surfaces for 25 existing
  concepts. It adds 48 exact aliases across 24 owners, with _portului_ and
  _porturilor_ rejected because neither bare form has one safe transport owner.
- The revised inventory assigns _pașaportului de călătorie_ and
  _pașapoartelor de călătorie_ to `n_v20soc_pasaport`.
- V62 is reviewable but intentionally uncommitted and unlanded. All local gates are green;
  exact remote CI has not run.

## Frozen review contract

- Candidate-funnel digest:
  `f85e8955697e44bd53b802fcc71f8a0bb6ebe9d4b099292b4d44dbd2c7b4b79b`.
- Build: `fixture-v62-transport-and-mobility-morphology`.
- Fixture counts: 2,364 nodes / 9,217 edges / 8,018 aliases / 180 puzzles.
- Exact delta: +48 aliases; no projection, node, edge, puzzle, game record, hold
  disposition, ranking row, or derived board.
- Earlier accepted inventories remain in force and all earlier rejected, deferred, held, and
  unauthored surfaces remain absent.

## Implementation scope

- Added the reviewed V62 data module, rollback-safe apply wrapper, complete review archive,
  ADR-0086, and focused six-test regression contract.
- Regenerated only the alias-bearing KG/mobile/ranking/derived wrappers and updated their
  current build, alias-count, and digest pins.
- Preserved both fixture mirrors, games-pack mirrors, ranking rows, derived boards, Contexto
  projection inventory, V49 rejection ledger, sessions, accounts, frontend, and deployment.
- Updated the V33 compatibility assertion for the V62-owned transport inventory.

## Artifact evidence

- KG: `ecd3fffa195497678bcc442ea1ae789f41358cb50be588df56731b3542b66dca`.
- Games pack:
  `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`.
- Ranking wrapper:
  `05343dc62cd1c262253fa1e74b8eac12bf69dd94238e429ff62fd2ec693d7025`;
  derived wrapper: `af9fe04e9c7840cb789d2573c5be047499c03b831fe17d9bfd916e4725b5cafb`.
- Mobile snapshot:
  `153af3ac3bcb3db872e95a31678c6d1356382a55fbaca4cb1ee765a83a4bc316`;
  Lanț ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
- Immutable ranking rows remain
  `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`.
- Immutable derived boards remain
  `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
- Nodes excluding aliases, edges, puzzles, games-pack payloads, ranking rows, and derived
  boards are unchanged; package/test mirrors are byte-identical.

## Verification state

- Focused V62 passed 6/6; affected V31–V33/V44/V47–V62 passed 155/155; complete backend
  passed 829/829; the post-bind accounts-on rerun passed 53/53; sessions passed 16/16.
- Fixture and games-pack validators are green. Ranking is 618 total / 449 eligible; the
  derived catalog is 336 boards.
- Strict pending Lanț checked 3 items with 0 flagged and 0 FAIL. Fixture/ranking/derived
  mirrors, Ruff with `--no-cache`, and global `git diff --check` are green.
- Exact-head remote CI has not run because V62 is uncommitted.

## Production state

- Production remains on V61; V62 has not been deployed.
- Accounts and debug remain off, submissions remain disabled, and no database, OAuth, extra
  worker, frontend, DNS, TLS, or infrastructure change is authorized by this wave.

## Risks and manual review

- Both rejected port forms must remain absent from exact, projection, and fuzzy resolution.
- Every accepted qualifier needs one normalized owner and an already-legal Lanț predecessor;
  aliases must not create graph edges or broaden projection resolution.
- The alias-only artifact audit confirms exactly +48 aliases and preserves all immutable
  payloads; final review must still confirm no unrelated file entered the change.

## Release result

V62 is intentionally uncommitted, unlanded, and undeployed for review. Do not merge until
exact-head remote CI is green.
