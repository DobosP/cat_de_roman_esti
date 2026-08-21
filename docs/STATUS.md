# Status — cat_de_roman_esti

_As of 2026-08-21. This file is the repository's current source of truth._

_Last verified: 2026-08-21 (exact V63 feature commit
`8d5f061084bec94dc836c1266aad9e912e13106b`; GitHub Actions run `32511269364` passed
frontend and backend gates on Python 3.12 and 3.14)._

## Current work — V63 film-and-television case morphology

- The frozen funnel covers two case forms for each of 25 existing film/TV concepts. It
  admits exactly 48 qualified aliases across 24 owners and rejects _rolului_ and
  _rolurilor_ because the bare forms span incompatible ordinary senses.
- Candidate-funnel digest:
  `73f31447e8fff86bb918d3830ebf886ba6fc1d2f14a1a88793fa396c03b5acef`.
- Build `fixture-v63-film-and-television-morphology` contains exactly 2,364 nodes / 9,217
  edges / 8,066 aliases / 180 puzzles: +48 aliases only.
- Accepted forms resolve to their reviewed owners in Contexto and on otherwise-legal Lanț
  hops. Both rejected forms remain absent through exact, projection, and fuzzy resolution.
- V63 adds no projection, node, edge, puzzle, game record, hold disposition, ranking row,
  derived board, account/session behavior, frontend, or deployment change.
- Focused V63 passed 6/6; affected V31–V33/V44/V47–V63 passed 161/161; complete backend
  collected and passed 841/841; post-bind accounts-on passed 53/53; sessions passed 16/16.
- Fixture and games-pack validators are green. Ranking is 618 total / 449 eligible; derived
  remains 336 boards. Strict pending Lanț checked 3 with 0 flagged and 0 FAIL.
- Package/test mirrors, Ruff with `--no-cache`, global `git diff --check`, the exact
  +48-only audit, resolver checks, and immutable-payload invariants are green.
- Exact feature CI run `32511269364` is green; V63 remains unlanded and undeployed.

## Landed baseline and preserved inventory

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

## V63 artifact pins

Bundled KG: `a27d86ee3b820edcb9d7cad2485362f2fde5c23adc25c6999e997c6b0aa9ac51`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `c6cf62066f8c68c199d3830e59c72a1625f3a58acdce37471a8c7a985af65442`;
derived: `b22b7dfab519c84a8fbae31b88a4aaf06bec178622d03877b6089aa62030079f`;
mobile: `9bdfdef1d79eff03baae360df18fb01ef4a0484e42c667653bb300a429d78780`;
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
  in scope. Neither V62 nor V63 is deployed.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v63_film_and_television_morphology.py -q
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

- Require exact-head CI on the release-evidence commit before any fast-forward to `main`.
- Keep _rolului_, _rolurilor_, all earlier rejected/held forms, projections, topology,
  games, sessions, accounts, frontend, and deployment unchanged.
- Keep production on V61; deploying V62 or V63 requires a separate explicit request.
