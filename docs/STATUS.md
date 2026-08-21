# Status — cat_de_roman_esti

_As of 2026-08-21. This file is the repository's current source of truth._

_Last verified: 2026-08-21 (V62 landed and was pushed at
`d7fd85543b27be14d8c3d79153b1f2371fe4ba99`; exact GitHub Actions run `32455606677`
passed frontend and backend gates on Python 3.12 and 3.14)._

## Current work — V62 transport-and-mobility case morphology

- The frozen funnel contains two case forms for each of 25 existing transport-and-mobility
  concepts. It admits 48 qualified exact aliases across 24 owners and rejects _portului_ and
  _porturilor_ because the bare forms do not have one safe transport owner. Its digest is
  `f85e8955697e44bd53b802fcc71f8a0bb6ebe9d4b099292b4d44dbd2c7b4b79b`.
- The revised accepted inventory binds _pașaportului de călătorie_ and
  _pașapoartelor de călătorie_ to `n_v20soc_pasaport`.
- Accepted forms are limited to typed Contexto input and otherwise-legal Lanț hops. V62 adds
  no projection, node, edge, puzzle, game record, hold disposition, or derived board.
- The alias-only apply raised aliases from 7,970 to exactly 8,018 while preserving 2,364
  nodes, 9,217 edges, 180 puzzles, pack bytes, ranking rows, and derived boards.
- Focused V62 passed 6/6; affected V31–V33/V44/V47–V62 passed 155/155; complete backend
  passed 835/835; post-bind accounts-on passed 53/53; sessions passed 16/16.
- Fixture and games-pack validators, ranking 618/449, derived 336, strict pending Lanț
  (3 checked / 0 flagged / 0 FAIL), mirrors, Ruff, global whitespace, and exact feature CI
  run `32455008129` are green.
- V62 is landed and pushed at `d7fd85543b27be14d8c3d79153b1f2371fe4ba99`;
  exact-head CI run `32455606677` is green. V62 remains undeployed.
- V61 remains in force and deployed: 48 home-care aliases across 24 owners were accepted;
  _cheii_ and _cheilor_ remain rejected. V51–V60 accepted and rejected inventories also
  remain in force.
- The V44 projection remains 473 terms across 26 domains; V49 retains all 104 durable Lanț
  rejections; the frozen V38 derived payload remains 336 boards.

## V62 content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 202 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **618 = 610 approved + 8 pending**, across 14 categories. The ranked original-game
runtime remains **449 zero-FAIL boards**. The derived catalog remains **336** boards; its
frozen `boards` payload hash is
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

Bundled KG: **2,364 nodes / 9,217 edges / 8,018 aliases / 180 puzzles**
(`fixture-v62-transport-and-mobility-morphology`), SHA-256
`ecd3fffa195497678bcc442ea1ae789f41358cb50be588df56731b3542b66dca`.
Pack `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking `05343dc62cd1c262253fa1e74b8eac12bf69dd94238e429ff62fd2ec693d7025`;
derived `af9fe04e9c7840cb789d2573c5be047499c03b831fe17d9bfd916e4725b5cafb`;
mobile `153af3ac3bcb3db872e95a31678c6d1356382a55fbaca4cb1ee765a83a4bc316`;
ledger `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Immutable topology, puzzle, ranking-row, derived-board, and games-pack payloads are preserved.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode only uploads validated completed-score rows; public records remain
  server-authored and consent-gated.
- Anonymous production remains on exact landed V61 `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`.
  It is healthy; accounts and debug are off, submissions are disabled, and the prior V48
  rollback image remains retained.
- Its manifest reports `fixture-v61-home-care-and-maintenance-morphology`, content hash
  `sha256:bfc3e868f49d8e07f23e2895c3010ecb9bd966dbfef6e5b543157937e49a1699`, and counts
  2,364/9,217/180; health, identity, category, Intrusul, and Perechi smokes remain green.
- V62 has not been landed or deployed. No account, submission, database, worker, frontend,
  DNS, TLS, or infrastructure change is in scope.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v62_transport_and_mobility_morphology.py -q
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Start V63 from exact landed V62 main using a new dedicated branch and worktree.
- Keep _portului_, _porturilor_, all earlier rejected/held forms, projections, topology,
  game records, sessions, accounts, frontend, and deployment unchanged.
- Keep V62 undeployed; production remains on V61 unless deployment is separately requested.
