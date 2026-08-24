# Status — cat_de_roman_esti

_As of 2026-08-24. This file is the repository's current source of truth._

_Last verified: 2026-08-24 (exact V66 feature commit
`c1da6c617767f5e49ca6302ded470160c3e7919a`; GitHub Actions run `32763537804` passed
frontend and backend gates on Python 3.12 and 3.14)._

## Current work — V66 science-and-discovery case morphology

- The fixed 50-surface funnel admits exactly 48 normalized-unique, sense-qualified aliases
  across 24 existing owners. It rejects _curentului_ and _curenților_ because the ordinary
  forms span moving air, flowing water, and electric-current senses.
- Candidate-funnel digest:
  `9604f43ea173fac3051b5114e464c91b0acde4a9b3fefddb760f6ca5430c4100`.
- Build `fixture-v66-science-and-discovery-morphology` contains 2,364 nodes / 9,217 edges /
  8,210 aliases / 180 puzzles: +48 aliases only.
- V66 adds no projection, node, edge, puzzle, game payload, ranking row, derived board,
  account/session behavior, frontend, or deployment change.
- Generated KG, ranking, derived, and mobile wrappers carry the V66 build and pins below;
  games-pack bytes, topology, ranking rows, and frozen derived boards remain unchanged.
- Focused V66 passed 6/6; affected V31–V33/V44/V47–V66 passed 179/179; accounts-on
  passed 53/53; sessions passed 16/16.
- Fixture/pack/ranking/derived validators, strict Lanț 3/0/0, mirrors, exact-delta,
  inherited-binding, protected-surface, immutable-payload, source-coupling, Ruff, and
  whitespace audits are green.
- Quiet-host verification on 2026-08-24 passed the isolated Alchimie timing gate in 16.29
  seconds and the exact full backend 859/859 in 230.96 seconds.
- Exact feature CI run `32763537804` is green; V66 remains unlanded pending exact CI on
  this release-evidence update.

## Landed baseline and preserved inventory

- V65 is landed and pushed on final `main` head
  `f8d9d435105c221457e4fe9e9bf3e81f04ed1e19`; exact final CI run `32558067986` is green.
  Its music aliases remain in force; _notei_ and _notelor_ stay rejected.
- V64 through V62 remain landed and green. V51–V64 accepted inventories and every prior
  rejected, deferred, held, or unauthored surface retain their dispositions.
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

## V66 artifact pins

Bundled KG: `a98bc426bf3091cebf00e069296fae07adc17febdeb9da875c4f9fef4f109e8f`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `b76308fb2cd88768609fff0a96f7459157ec7a5ce007fd97833742bc13c8f17f`;
derived: `1e2ddde7f3731b0f7e36e2477b1bb2c9848e8ba766ef789c0dfc5657d67c6477`;
mobile: `e243340676c435d0b5b8feace2f934b748bd3edbe75195370055315fbc0d3e68`;
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
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v66_science_and_discovery_morphology.py -q
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Require exact-head CI on this release-evidence commit before any landing decision.
- Keep _curentului_, _curenților_, every earlier rejected/held form, projections, topology,
  payloads, sessions, accounts, frontend, and deployment unchanged.
- Keep production on exact V65 app commit `aefcc2c64feda` and preserve `rollback-1c42de0`.
