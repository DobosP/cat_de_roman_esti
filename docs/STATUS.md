# Status — cat_de_roman_esti

_As of 2026-07-23. This file is the repository's current source of truth._
_Last verified: 2026-07-23 (V39: backend 548, accounts 52, frontend 21, session store 16;
lint/build/artifacts green, bundle 119.01/120 KiB; live V32, V38–V39 not on main/deployed.)_

## Current outcome — local V39 release candidate (ADR-0053, ADR-0054)

- The six-game, tap-first lobby is complete in fun-first order: Alchimie → Intrusul →
  Perechi → Conexiuni → Cald sau Rece → Lanț. A seventh mode waits for pilot evidence.
- Intrusul and Perechi remain strict catalog-only games over **336 boards**: 183 from 66
  sources and 153 from 51. Runtime prefers standard-score ≥55 boards (144/113), but falls
  back only inside the already filtered strict shelf; explicit category filters never widen.
- Unscoped starter selection balances category, then source, then variant. A derived game
  stays on its beginner shelf until a non-daily win or three non-daily completions; daily
  play does not graduate it. Free replay remembers one opaque completed session per game,
  never content or answers, and daily play is isolated from that memory.
- Home shows a local-only six-game daily circuit: completion includes zero-score runs and
  each game's best contribution is clamped to 0–1,000 (total 6,000). No aggregate, action
  trail, board identity, or telemetry is uploaded.
- Accounts-on staging has per-game server-verified records only. Public rows require current
  consent, an explicit nickname, and opt-in; ties use competition ranks and the player's
  bounded row can sit below the top 50. Imported/browser score history remains private.
- Intrusul drops its unrelated source-level badge. Perechi removes solved tiles from the
  active grid while retaining the solved stack and keyboard focus. Daily results name the
  transition to free play directly.

## Retained V37 baseline (ADR-0051)

- The private V37 sidecar ranks all **794** curated boards at 60% Romanian-concept
  familiarity and 40% game-specific structural quality, bound to pack, KG, and rubric.
  Its **486** eligible boards are Conexiuni 123, Cald sau Rece 192, Lanț 94, Alchimie 77; focused critique has zero strict FAILs.
- Existing game/category/difficulty/repeat filters run first. Eligible shelves use
  deterministic 1–5-ticket rotation; daily shelves retain their minimum of eight and their
  approved/mined fallback. Custom packs stay neutral without a digest-matching sidecar.
- Board rankings are editorial pre-playtest estimates, not measured fun or
  player-knowledge ratings. Accounts remain off by default; no telemetry was added.

## Retained beginner play and vocabulary

- Every original game defaults to `Ușor`, teaches three terse actions, shows one live `ACUM`
  cue, and keeps mobile actions at least 44 px. Conexiuni centralizes recovery feedback;
  Lanț has direction, free undo, and a 64-hop cap; Alchimie caps remembered experiments at
  496 and projects at most 24 useful pairs.
- Cald sau Rece accepts **444 screened guesses across 26 domains** through 89 KG anchors,
  keeps repeats free, and progresses to a warmer familiar clue. Targets and hidden routes
  or recipes remain private in every game.
- V23–V33 added childhood, farm, clothing, kitchen, hygiene, cleaning, face, workshop,
  garden, bathroom, household-electrical, and forest concepts. Vocabulary probes are
  **322/322**; all 794 curated records pass schema and playability validation.

## Product and deployment

The Romanian arcade uses Django 5.2/DRF and React 19/Vite 8 over the offline KG. On
2026-07-23, <https://cat-de-roman-esti.dobolabs.ro/api/manifest> still reported
`fixture-v32-face-workshop-garden` and the health API exposed four games. Shared `main`
remains V37 `18400f9`; V38/V39 and accounts/player rankings remain local only.

## Shipped content baseline

| Game | Total | Approved | Pending | V37 eligible | Runtime source |
|---|---:|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | 123 | ranked curated; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | 192 | ranked curated; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 | ranked curated; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | 77 | ranked curated; sparse projection miner fallback |
| Intrusul | 183 | 183 | 0 | 144 preferred | strict derived catalog only |
| Perechi | 153 | 153 | 0 | 113 preferred | strict derived catalog only |

Pack: **794 = 572 approved + 222 pending**, across 14 categories. Bundled KG:
**2,287 nodes / 9,122 edges / 7,400 aliases / 180 puzzles**; mirrors remain byte-identical.

## Runtime contracts and quality gate

- Sessions use a validated 7,200-second sliding TTL and 1,000-entry LRU cap. Per-entry locks
  serialize one session while allowing concurrent sessions; all-borrowed capacity returns
  503. Request bodies have a 64 KiB Caddy and ASGI receive ceiling.
- Account history is capped at 500 rows per user; public verified records are capped at one
  row for each of the exact six game keys. Current consent is rechecked under a profile lock.
- Curated submissions require `CAT_SUBMISSIONS_DIR`; only approved records are served.
  Mobile fixture/OpenAPI contracts and deterministic seeded/daily selection remain pinned.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
node --check .claude/workflows/critique-games.js
git diff --check
```

Frontend: 21/21, lint/build green, 119.01 KiB. Required session-store target: **16**.

## Next verified work

- Run a larger anonymous six-game pilot before adding a seventh game or changing scores.
- Merge/deploy V38/V39 only on explicit instruction; keep accounts off until the compliance
  checklist is complete. Any analytics still requires a separate privacy/retention decision.
