# Status — cat_de_roman_esti

_As of 2026-08-26. This file is the repository's current source of truth._

_Last verified: 2026-08-26 (frontend 29/29, ESLint, typecheck/build, bundle/manifest/static
parity, backend preservation 11/11 + 99/99 + 42/42 + 6/6, generators, validators, Ruff,
mirrors, browser acceptance, and whitespace are green)._

## Current work — persistent game navigation and beginner entry

- Shared game navigation is sticky below the mobile safe area and labeled `Ieși`; returning
  to the lobby replaces history so browser Back cannot reopen an explicitly exited game.
- Conexiuni forgets only its own active-game pointer on explicit exit from intro, board, or
  result. Reload still resumes a live board, and Escape/Backspace still clears selection.
- Only the compact Conexiuni next-move coach stays sticky. Feedback and earned clues remain
  in normal flow immediately before the grid; Alchimie and other secondary sticky controls
  share the header-safe offset.
- Intrusul is the sole `Începe aici` recommendation. Conexiuni describes easy, normal, and
  hard as clear groups, a balanced mix, and subtle connections.
- Independent Chrome acceptance of the reviewed navigation snapshot kept the 44 px exit
  visible at maximum scroll on 390 × 620, 360 × 430, and 375 × 330 viewports with zero
  header/coach overlap. At 360 × 430 the measured gap was 7 px.
- That acceptance also preserved the identical Conexiuni token and 16 tiles on reload.
  Explicit exit cleared only that token, preserved unrelated/game sentinels, returned to
  `/`, and browser Back stayed home without a board or token.
- The integrated production build byte-matches the tracked static tree. Its manifest graph
  has 18 entries / 37 edges / 25 referenced files, and initial JS/CSS is 118.17 KiB gzip
  against the 120 KiB budget.
- The work is frontend-only. It changes no server session, TTL/cap, payload, catalog,
  scoring, content, account, infrastructure, or deployment behavior.
- The navigation change is unlanded, undeployed, and has no exact integrated-head CI run.

## Integrated baseline and preserved inventory

- Exact V69 `75255a46924bf1f4964cc3c9f24a1228b4c72d70` is the integration base. It
  retains ADR-0093's Contexto impact reserve and filtered-shelf weighting, 201 eligible
  Contexto targets, 618 total / 448 eligible original-game boards, and 336 derived boards.
  V69 is unlanded; branch CI `32908368059` is in progress and is not claimed green.
- Exact V68 `5e9fadf450a70e6e1b24d9a16cc7859fec6c8e99` is landed and pushed on
  `main`. Feature CI `32907211185` and landed-main CI `32907879041` are green.
- V68 retains 2,364 nodes / 9,217 edges / 8,306 aliases / 180 puzzles and ADR-0092's
  bounded Romanian-language morphology contracts. ADR-0091 remains superseded by ADR-0092.
- V51–V69 accepted inventories and owners remain intact; V49 keeps 104 Lanț rejections.

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 201 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories.

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

## Runtime and deployment

- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.
- Anonymous production remains on exact V65 `aefcc2c64feda8b18bd66d68f5330bfe75c1d9de`;
  accounts/debug remain off. No deployment or infrastructure changes belong to this work.

## Reproduction

```bash
(cd frontend && npm test && npm run lint && npm run build)
git diff --exit-code -- cat_de_roman_esti/web/static
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_v68_romanian_language_and_grammar_morphology.py tests/test_v69_contexto_impactful_targets.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_contexto.py tests/test_v37_board_rankings.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_board_rankings_v37.py tests/test_v38_derived_rankings.py tests/test_v38_ranked_catalog.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_static_asset_cache.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/rank_games_pack.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/validate_fixture.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/dobo/work/cat_de_roman_esti/.venv/bin/python scripts/validate_games_pack.py
/home/dobo/work/cat_de_roman_esti/.venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Require exact-head CI before landing V69 or this navigation change.
- Preserve V69's Contexto reserve/weights and V68's morphology, topology, and payloads.
- Keep production on exact V65 `aefcc2c64feda`.
