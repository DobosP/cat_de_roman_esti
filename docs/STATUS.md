# Status — cat_de_roman_esti

_As of 2026-08-14. This file is the repository's current source of truth._

_Last verified: 2026-08-14 (V60 landed and was pushed at `2a4d683`; exact CI run
`31773557256` is green. V61 is intentionally uncommitted and unlanded: scoped gates are
green, but its complete backend suite and CI have not run)._

## Current work — V61 refined home-care-and-maintenance case morphology

- Two independent passes reviewed a fixed set of two case forms for each of 25 existing
  home-care-and-maintenance concepts. Forty-eight qualified exact aliases across 24 owners
  passed; _cheii_ and _cheilor_ remain rejected because the bare forms do not have one safe
  home-care owner. The fixed 50-surface funnel digest is
  `218fef7d717e5c373c0390586e9dacee207b405f773e6795c4e4a6c42bec4de6`.
- Accepted forms serve typed Contexto input and otherwise-legal Lanț hops. V61 adds no
  Contexto projection, node, edge, puzzle, game record, hold disposition, or derived board;
  KG topology and pack bytes stay fixed while only aliases and bound wrappers change.
- Source/review assertions, dry-run/apply, exact resolution, inherited rejections, and the
  exact +48-alias-only artifact audit passed. Focused V61 passed 6; affected
  V31–V33/V44/V47–V61 passed 149; accounts passed 53; sessions passed 16.
- Ranking/derived checks, pack and fixture validators, strict Lanț sweep (3/0/0), mirrors,
  Ruff, and whitespace checks passed. Complete backend and CI remain unrun; do not land V61.
- V52–V60 remain in force with their recorded accepted totals and rejected polysemes. V60
  landed/pushed at `2a4d683`; exact CI run `31773557256` is green.
- V51 remains in force: its 32 alias forms and eight penalty-one Contexto projections stay
  accepted; its seven deferrals, three rejections, and unauthored spellings stay absent.
- Archived V48 evidence retains provenance; its live gate fails closed on stale KG, rubric,
  runtime sources, generator, or pack. V49's ledger retains all 104 V45 rejections.
- V45–V48 runtime counts remain: Lanț 94 selectable, Conexiuni 74, Cald sau Rece 202, and
  Alchimie 79; their eight recorded holds stay excluded.
- V44's 71-node repair and 473-term/26-domain projection remain; the frozen 336-board
  Intrusul/Perechi payload is unchanged.

## Content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 202 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **618 = 610 approved + 8 pending**, across 14 categories. The ranked original-game
runtime serves **449 zero-FAIL boards**. The strict derived catalog remains **336** boards
from the frozen V38 source snapshot; its `boards` payload hash is
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
Bundled KG: **2,364 nodes / 9,217 edges / 7,970 aliases / 180 puzzles**
(`fixture-v61-home-care-and-maintenance-morphology`), SHA-256 `544fe547c875acb913c3d188917304b246a84997ba3cfccb586da119ac89913c`.
Pack `05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed`; ranking `ce03c2a69a98a6905dc14e4f66a143c89dafee9b689532e6d2e4266632f2b5ee`;
derived `2a3ad0e2f9345396780481f72ab0a2cc144eef3b96d0ab11dc0b814182c9138a`; mobile `387bb3bcdcccebfca9d1f5615604bc28279a087463a7162653f97972245e1665`;
ledger `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`. Immutable payload pins remain baseline.

V49 evidence is under `docs/reviews/v49-lant-rejection-ledger/`; V61's review archive is
the fixed 50-row home-care-and-maintenance funnel. Rankings remain estimates.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode only uploads validated completed-score rows; public records remain
  server-authored and consent-gated.
- Anonymous production still runs V48 at `d59caed` since 2026-08-01. Accounts and
  submissions remain off; its exact public/runtime probes remain the deployment evidence.
- The owner authorizes an anonymous V61 deployment only after V61 lands exact-green.
  Preserve rollback, keep accounts/submissions off, and pass all required public smokes;
  no V61 deployment has occurred.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
PYTHONPATH=. .venv/bin/ruff check --no-cache .
git diff --check
```

## Next verified work

- Run the complete backend suite and exact-commit CI before landing V61; deploy only after
  the exact landed commit is green and the rollback/smoke preflight passes.
- Any later lexical wave needs a new finite two-reviewer funnel. V50–V61 deferrals,
  rejections, folded collisions, and unauthored spellings stay absent without fresh evidence.
- Resolve the three Alchimie alcohol holds and two Cald sau Rece A5 holds only through
  explicit owner disposition and fresh game-specific gates.
- Census the full Lanț pack and durable ledger before authoring/import. Repair its three
  holds only after their named blockers change, then generate fresh exact dossiers.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion. Keep accounts off until the compliance checklist is complete.
