# Status — cat_de_roman_esti

_As of 2026-08-26. This file is the repository's current source of truth._

_Last verified: 2026-08-26 (V68+V69 preservation 11/11, selector contracts 99/99,
ranking 9/9, derived 33/33, generators, validators, Ruff, and mirrors are green)._

## Current work — V69 impactful Cald sau Rece targets

- `ct_muzica_163` remains approved for provenance but is the sole member of the mirrored
  V69 impact reserve. Its secret, _Refren viral_, gives the distinct ordinary concept
  _Refren_ rank 2; neither resolver owner nor shared vocabulary changes.
- Digest-ranked Contexto seeded and daily picks derive positive 1–5 tickets inside the
  exact eligible category+difficulty shelf by `pilot_score` descending and stable ID.
  Player-history exclusions apply only after those weights are fixed.
- All 201 eligible, unique Contexto targets remain distributed across all 14 categories.
  The music/easy shelf retains six targets, above the four-board category-daily floor.
- Neutral/custom packs and every other game keep their prior selector. The pack, KG,
  topology, projections, frontend, accounts, session shape, TTL, and capacity are unchanged.
- The frozen 336-board derived payload remains byte-identical; only its ranking-bound
  metadata and reviewed digest pin change.
- Ranking generation reports 618 total / 448 eligible, and derived generation reports
  336 boards; package/test ranking and derived mirrors are byte-identical.
- V69 is unlanded, undeployed, and has no integrated-head CI run.

## Integrated baseline and preserved inventory

- Exact V68 `5e9fadf450a70e6e1b24d9a16cc7859fec6c8e99` is the integration base and is
  landed and pushed on `main`. It retains 2,364 nodes / 9,217 edges / 8,306 aliases /
  180 puzzles and ADR-0092's bounded Romanian-language morphology contracts.
- V68 exact feature CI run `32907211185` is green. Exact landed-main run `32907879041`
  is in progress; no green conclusion is recorded here yet.
- V51–V68 accepted inventories retain their owners; every prior rejected, deferred, held,
  or unauthored surface retains its disposition. V49 keeps 104 durable Lanț rejections.

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 201 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories. Ranked
original-game inventory is 618 total / 448 eligible; derived inventory remains 336.

## V69 artifact pins

Bundled KG: `ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128`;
pack: `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`;
ranking: `c32b648885cf9d0aad718bda9c1dcbd86f49ddda6819ceb14a7c372e32ddb424`;
derived: `9199f60c41d334f620403ca68926790b57292d71761175a470ba7385af52da91`;
mobile: `1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae`;
ledger: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`.
Protected payload pins: nodes without aliases `c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0`;
edges `f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0`;
puzzles `3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc`;
ranking rows `faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031`;
derived boards `71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.

## Runtime, accounts, and deployment

- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.
- Anonymous production remains on exact V65 `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`;
  accounts and debug remain off. No deployment or infrastructure changes belong to V69.

## Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v68_romanian_language_and_grammar_morphology.py tests/test_v69_contexto_impactful_targets.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_contexto.py tests/test_v37_board_rankings.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_board_rankings_v37.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/validate_fixture.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/validate_games_pack.py
/home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Require exact-head CI before any landing decision.
- Keep `ct_muzica_163` approved but unselectable and keep V44's three-record reserve unchanged.
- Preserve V68's _punctului_/_punctelor_ rejections, prior ownership, topology, and payloads.
- Keep production on exact V65 `aefcc2c64feda`.
