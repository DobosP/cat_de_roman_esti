# Status — cat_de_roman_esti

_As of 2026-08-21. This file is the repository's current source of truth._

_Last verified: 2026-08-21 (V63 is landed and pushed on final `main` head
`08038ee28c95a33c8295268de91c015697249f15`; exact GitHub Actions run `32512940422`
passed frontend and backend gates on Python 3.12 and 3.14)._

## Current work — V64 history-and-heritage case morphology

- The refined frozen funnel covers two case forms for each of 25 existing history/heritage
  concepts. It admits exactly 48 qualified aliases across 24 owners and rejects _frontului_
  and _fronturilor_ because the bare forms span incompatible ordinary senses.
- Candidate-funnel digest:
  `42137b42712597779ce402ce4a9f9065060701c5a19b444235b4abed69ecef40`.
- Build `fixture-v64-history-and-heritage-morphology` contains 2,364 nodes / 9,217 edges /
  8,114 aliases / 180 puzzles: +48 aliases only.
- Accepted forms resolve to their reviewed owners in Contexto and on otherwise-legal Lanț
  hops. Both rejected forms remain absent through exact, projection, and fuzzy
  resolution.
- V64 adds no projection, node, edge, puzzle, game record, hold disposition, ranking
  row, derived board, account/session behavior, frontend, or deployment change.
- Focused V64 passed 6/6; affected V31–V33/V44/V47–V64 passed 167/167; exact full backend
  collection and execution passed 847/847; accounts-on passed 53/53; sessions passed 16/16.
- Validators, ranking 618/449, derived 336, strict Lanț 3/0/0, mirrors, exact +48 audit,
  resolver/protected-surface checks, immutable-payload invariants, Ruff with `--no-cache`,
  and `git diff --check` are green. Exact feature CI has not run.
- V64 remains unlanded and undeployed; exact feature-head CI has not run.

## Landed baseline and preserved inventory

- V63 is landed and pushed at final `main` head
  `08038ee28c95a33c8295268de91c015697249f15`; exact final CI run `32512940422` is green.
  Its 48 film/TV aliases remain in force, while _rolului_ and _rolurilor_ remain rejected.
- V62 is landed and pushed at `6e9f1dba75fc4a1b6fccdb3a91a5bd77a5f14734`; exact
  final CI run `32456325843` is green. Its 48 transport aliases remain in force, while
  _portului_ and _porturilor_ remain rejected. V62 is not deployed.
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

## V64 artifact pins

Bundled KG: `d8db3ca58272e26192c9e0a3b556fc796c15dc4cec9d828f67a1245cf75d90b3`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `e9a5acd3fc62753912728dc6ca5f8a9e2ead00edfba14ef7f44a3e752fb6e13e`;
derived: `39a77d724ad4436d0529ceeaf87e46e9cbf3a85661a60b3ca09f141211652089`;
mobile: `92cc85b8658acae05b343ea55cc773d51f2642ce84725f06ff0c34577bd0302c`;
ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Games-pack bytes, topology, puzzles, ranking rows, derived boards, and the ledger payload
remain invariant.

## Runtime, accounts, and deployment

- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.
- Anonymous production remains on exact landed V61
  `1c42de0d52cf56fd0d49f930aaccaafbc96906f9`; accounts and debug are off, submissions are
  disabled, and the prior V48 rollback image remains retained.
- No account, submission, database, worker, frontend, DNS, TLS, or infrastructure change is
  in scope. V62–V64 are not deployed.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v64_history_and_heritage_morphology.py -q
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

- V64 is locally green and independently reviewable; exact feature CI has not run.
- Keep _frontului_, _fronturilor_, all earlier rejected/held forms, projections, topology,
  games, sessions, accounts, frontend, and deployment unchanged.
- Keep V64 unlanded until exact feature-head CI is green. Production stays on V61;
  deployment requires a separate explicit request.
