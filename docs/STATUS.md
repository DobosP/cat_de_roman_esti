# Status — cat_de_roman_esti

_As of 2026-08-22. This file is the repository's current source of truth._

_Last verified: 2026-08-22 (V65 landed and was pushed at
`aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; exact GitHub Actions run `32557471621`
and anonymous production smokes are green)._

## Current work — V65 music-and-performance case morphology

- The fixed 50-surface funnel admits exactly 48 normalized-unique, sense-qualified aliases
  across 24 existing owners. It rejects _notei_ and _notelor_ because the ordinary forms span
  musical, educational, written, accounting, diplomatic, and descriptive senses.
- Candidate-funnel digest:
  `abfaaf5cf29a3e3624cc401cc36b767f90e5e0ff102634c32d17111c6b2321f6`.
- Build `fixture-v65-music-and-performance-morphology` contains 2,364 nodes / 9,217 edges /
  8,162 aliases / 180 puzzles: +48 aliases only.
- V65 adds no projection, node, edge, puzzle, game payload, ranking row, derived board,
  account/session behavior, frontend, or deployment change.
- Fixture and games-pack validators, package/test mirror comparisons, the exact +48 delta
  audit, ranking 618/449, derived 336, and strict Lanț 3 checked / 0 flagged / 0 FAIL are
  green. Strict Lanț also reports 16 pack-level WARN only.
- Focused V65 passed 6/6; affected V31–V33/V44/V47–V65 passed 173/173; exact full
  backend collection and execution passed 853/853; accounts-on passed 53/53; sessions
  passed 16/16; Ruff with `--no-cache` and whitespace checks are green.
- V65 landed and was pushed at `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; exact
  landed-head CI run `32557471621` and feature run `32557087552` are green.

## Landed baseline and preserved inventory

- V64 is landed and pushed on final `main` head
  `156736a04c705406625ca4ef35752cd41a558187`; exact final CI run `32530075329` is green.
  Its history/heritage aliases remain in force; _frontului_ and _fronturilor_ stay rejected.
- V63 (`08038ee28c95a33c8295268de91c015697249f15`) and V62
  (`6e9f1dba75fc4a1b6fccdb3a91a5bd77a5f14734`) remain landed, green, and undeployed.
- V61 remains deployed in anonymous production: its 48 home-care aliases remain accepted,
  while _cheii_ and _cheilor_ remain rejected. V51–V60 inventories remain in force.
- The V44 projection remains 473 terms across 26 domains; V49 retains all 104 durable Lanț
  rejections; the frozen V38 derived payload remains 336 boards.

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 202 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories. Ranked
original-game inventory remains 618 total / 449 eligible; derived inventory remains 336.

## V65 artifact pins

Bundled KG: `412dce67a5c49803e0a31d4e5453b32187449e15da2ebe0b0e430457668c2bf7`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `c9a3c678240631f9622a508126d6ad39158624052019d8478bbdbc14f9850849`;
derived: `a28539995c1ac5e95ee6c87ba1302edab4067e4dc614678a7cd2680d8b73ae4b`;
mobile: `d5acd5d62336090b5093182bb6897443794f1c0ae858edc63d0bdf2453895430`;
ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Games-pack bytes, topology, puzzles, ranking rows, derived boards, and the ledger payload
remain invariant.

## Runtime, accounts, and deployment

- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.
- Anonymous production was upgraded from V61 to exact landed V65
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de` on 2026-08-22. The app image begins
  `sha256:71f3e2cc`; `rollback-1c42de0` preserves prior image `sha256:efa179af`.
- Accounts and debug are off, submissions return HTTP 503, and the app is healthy with zero
  restarts. No database, OAuth, extra worker, frontend, DNS, TLS, or infrastructure changed.
- The public manifest reports the V65 build, content hash
  `sha256:6670819a1eefe0b15b7d410371c713515f54196f8d340ed7da959ec69057ba15`,
  and counts 2,364/9,217/180. Health, healthz, all 14 categories, Intrusul, and Perechi pass.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v65_music_and_performance_morphology.py -q
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Require exact-head CI on this rollout record, then start V66 from that final landed head.
- Keep _notei_, _notelor_, every earlier rejected/held form, projections, topology, payloads,
  sessions, accounts, frontend, and deployment unchanged.
- Keep production on exact V65 and preserve `rollback-1c42de0` through the next rollout.
