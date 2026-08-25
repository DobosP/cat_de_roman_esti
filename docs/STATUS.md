# Status — cat_de_roman_esti

_As of 2026-08-25. This file is the repository's current source of truth._

_Last verified: 2026-08-25 (V68 focused 6/6, affected 191/191, exact full backend
871/871 in 569.61 seconds on stable CPU14 scheduler placement, accounts 53/53, sessions
16/16, validators, strict Lanț, invariant audits, Ruff, and whitespace are green)._

## Current work — V68 Romanian-language and grammar case morphology

- The fixed 50-surface funnel admits exactly 48 normalized-unique, sense-qualified aliases
  across 24 existing owners. It rejects _punctului_ and _punctelor_ because the ordinary
  forms span punctuation, geometric/location, measurement, score, and viewpoint senses.
- Candidate digest:
  `ff4cee7a4ac2f39601a19efd3aad2a305e85303e282451ba606fe1c8b68b3377`.
- Build `fixture-v68-romanian-language-and-grammar-morphology` contains 2,364 nodes /
  9,217 edges / 8,306 aliases / 180 puzzles: +48 aliases only. Contexto remains at 473
  projection terms across 26 domains.
- V68 adds no projection, node, edge, puzzle, game payload, ranking row, derived board,
  account/session behavior, frontend, or deployment change.
- Focused V68 passed 6/6; affected V31–V33/V44/V47–V68 passed 191/191; accounts-on
  passed 53/53; sessions passed 16/16; exact full backend passed 871/871 in 569.61 seconds
  on stable CPU14 scheduler placement.
- Fixture/pack/ranking/derived validators, ranking inventory 618/449, 336 derived boards,
  strict Lanț 3 checked / 0 flagged / 0 FAIL with 16 WARN, mirrors, exact-delta, inherited
  bindings, protected surfaces, immutable payloads, and source coupling are green.
- The original six-word part-of-speech pair failed the hard alias-style validator; the
  transaction rolled back fully. The corrected five-word pair is triple-absent and green.
- V68 is intentionally uncommitted, unlanded, undeployed, and has no CI run.

## Landed baseline and preserved inventory

- V67 is landed and pushed on final `main` head
  `46cf65f05a39b001e429c9f0a14fe0bfb611cb38`. Exact feature run `32772547384`, evidence
  run `32773388527`, and landed-main run `32774376592` are green.
- V51–V67 accepted inventories retain their owners; every prior rejected, deferred, held,
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

## V68 artifact pins

Bundled KG: `ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `b521d5d698a036aa81589ba059d7c04d731dbd69a2bf1a2f6b627e881a19bfe6`;
derived: `e7acd141a357409559a93f68514b977dbd697e19a97939afa9bb200d9d70dc97`;
mobile: `1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae`;
ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Frozen V67 invariants remain: nodes without aliases `c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0`;
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
PYTHONPATH=. .venv/bin/python -m pytest tests/test_v68_romanian_language_and_grammar_morphology.py -q
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Commit V68, then require exact feature CI before any landing decision.
- Keep _punctului_, _punctelor_, prior rejected/held forms, projections, topology, payloads,
  sessions, accounts, frontend, and deployment unchanged.
- Keep production on exact V65 `aefcc2c64feda` and preserve `rollback-1c42de0`.
