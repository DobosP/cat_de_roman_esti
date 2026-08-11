# Status — cat_de_roman_esti

_As of 2026-08-12. This file is the repository's current source of truth._

_Last verified: 2026-08-12 (V49+V50 backend 759/759, accounts 53/53, sessions
16/16, V49 22/22, V50 11/11, affected historical gates, all artifact validators,
Ruff, workflow syntax, and whitespace green; frontend untouched)._

## Current outcome — V50 bounded typed vocabulary (ADR-0074)

- Two independent lexical passes reviewed one finite 50-surface funnel: eight exact shared
  aliases and twelve Contexto-only non-winning projections passed unanimously; eight
  surfaces remain deferred and twenty-two are rejected. No quota overrode disagreement.
- Exact aliases serve typed Contexto input and legal Lanț hops. Related/basic words remain
  Contexto projections with penalty one; tap-only games receive no lexical substitution.
- V50 adds no nodes, edges, puzzles, game records, hold dispositions, or derived boards.
  KG topology and pack bytes stay fixed; only aliases and bound wrapper metadata change.
- Archived V48 Alchimie evidence replays its embedded historical provenance, while a new
  live gate fails closed unless KG, rubric, runtime sources, generator, and pack match
  current bytes. Tampering at every boundary is regression-tested.
- V49 remains in force: the non-runtime Lanț ledger retains all 104 V45 rejections as
  digest-bound directed pairs. Import, pending critique, and review apply reject exact
  reuse; future rejects append transactionally. The three repair holds remain excluded.
- V48 remains: Alchimie has 79 approved/selectable + 3 pending alcohol A5 owner holds.
  V47 leaves Cald sau Rece at 205 approved / 2 pending / 202 unique selectable targets.
- V46 leaves Conexiuni at 232 approved / 74 selectable / 0 pending with 122 rejected-board
  tombstones. V45 leaves Lanț at 94 selectable boards and three pending repair holds.
- V44's 71-node Cald sau Rece repair remains. The projection now has 465 terms across the
  same 26 domains, and the frozen 336-board Intrusul/Perechi payload is unchanged.

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
Bundled KG: **2,364 nodes / 9,217 edges / 7,460 aliases / 180 puzzles**
(`fixture-v50-typed-vocabulary`).

V49 evidence is under `docs/reviews/v49-lant-rejection-ledger/`; V50's 50-row lexical
funnel is under `docs/reviews/v50-synonym-basic-word-funnel/`. Rankings remain estimates.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode only uploads validated completed-score rows; public records remain
  server-authored and consent-gated.
- Anonymous production still runs V48 at `d59caed` since 2026-08-01. Accounts and
  submissions remain off; its exact public/runtime probes remain the deployment evidence.

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

- Start V51 only from landed V50 in a separate worktree. Use another finite two-reviewer
  lexical funnel; no V50 defer/reject becomes accepted without fresh exact evidence.
- Resolve the three Alchimie alcohol holds and two Cald sau Rece A5 holds only through
  explicit owner disposition and fresh game-specific gates.
- Census the full Lanț pack and durable ledger before authoring/import. Repair its three
  holds only after their named blockers change, then generate fresh exact dossiers.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion. Keep accounts off until the compliance checklist is complete.
