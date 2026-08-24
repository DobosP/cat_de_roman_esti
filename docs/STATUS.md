# Status — cat_de_roman_esti

_As of 2026-08-24. This file is the repository's current source of truth._

_Last verified: 2026-08-24 (exact V67 full backend 865/865 in 590.85 seconds on stable
CPU14 scheduler placement; the unchanged Alchimie timing gate passed inside the full run)._

## Current work — V67 online-content and social-media case morphology

- The fixed 50-surface funnel admits exactly 48 normalized-unique, sense-qualified aliases
  across 24 existing owners. It rejects _fluxului_ and _fluxurilor_ because the ordinary
  forms span tide/surge, physical or information flow, and social-feed senses.
- Candidate digest:
  `d694a4baca37eb864e0acf9fdd9608f01b4f24346cea9589bde2931b551663e3`.
- Build `fixture-v67-online-content-and-social-media-morphology` contains 2,364 nodes /
  9,217 edges / 8,258 aliases / 180 puzzles: +48 aliases only. Contexto remains at 473
  projection terms across 26 domains.
- V67 adds no projection, node, edge, puzzle, game payload, ranking row, derived board,
  account/session behavior, frontend, or deployment change.
- Focused V67 passed 6/6; affected V31–V33/V44/V47–V67 passed 185/185; accounts-on
  passed 53/53; sessions passed 16/16.
- Fixture/pack/ranking/derived validators, ranking inventory 618/449, 336 derived boards,
  strict Lanț 3 checked / 0 flagged / 0 FAIL with 16 WARN, mirrors, exact-delta, inherited
  bindings, protected surfaces, immutable payloads, and source coupling are green.
- The exact full backend passed 865/865 in 590.85 seconds on stable CPU14 scheduler
  placement; the unchanged Alchimie timing gate passed inside the full run. An earlier
  loaded-host 864/865 run was contention-only and is superseded by this terminal result.
- V67 is intentionally uncommitted, unlanded, undeployed, and has no CI run.

## Landed baseline and preserved inventory

- V66 is landed and pushed on final `main` head
  `631d9b2bba6eae42903713d70aa5b051b7a78f34`. Exact feature run `32763537804`, evidence
  run `32764788526`, and landed-main run `32765738442` are green.
- V51–V66 accepted inventories retain their owners; every prior rejected, deferred, held,
  or unauthored surface retains its disposition. V49 keeps 104 durable Lanț rejections.

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

## V67 artifact pins

Bundled KG: `89437c8aaeb84818c9e9acbc879985f146d5dadaab04777c8820fb5d42b87f84`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `dbc9410d5040215c4301096fbc195e3630a6a6d8896492414301f73a8067dd95`;
derived: `82a2b1c5e5c7744bf79961351b451ecc12c2522c71e354606e168c7c0218481c`;
mobile: `0b67f50f3d255e523bb72c3bf997e9439cae2a08f08c837b64016e84f29ce9c7`;
ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Frozen V66 invariants remain: nodes without aliases `c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0`;
edges `f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0`;
puzzles `3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc`;
ranking rows `46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0`;
derived boards `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Runtime, accounts, and deployment

- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.
- Anonymous production remains healthy on exact V65
  `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`; image `sha256:71f3e2cc` has zero restarts,
  and `rollback-1c42de0` preserves the V61 image `sha256:efa179af`.
- Accounts and debug are off, submissions return HTTP 503, and no database, OAuth, extra
  worker, frontend, DNS, TLS, or infrastructure changed. The public manifest remains V65.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v67_online_content_and_social_media_morphology.py -q
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Commit the V67 feature, then require exact feature CI before any landing decision.
- Keep _fluxului_, _fluxurilor_, prior rejected/held forms, projections, topology, payloads,
  sessions, accounts, frontend, and deployment unchanged.
- Keep production on exact V65 `aefcc2c64feda` and preserve `rollback-1c42de0`.
