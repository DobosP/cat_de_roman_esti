# Status — cat_de_roman_esti

_As of 2026-07-19. This file is the repository's current source of truth._
_Last verified: 2026-07-19 (local V37: backend 477/477, required session store 16/16,
frontend 13/13, static/mobile 11/11, ranking/critique/pack/KG gates, packaged-runtime smoke,
Ruff, workflow syntax, lint, typecheck, and whitespace green; production bundle is
117.23/120 KiB with four font subsets. Live is V32 `f40fa8b`; V33–V37 are not pushed/deployed.)_

## Current outcome — V37 large-pilot consolidation (ADR-0051)

- A private, reproducible sidecar ranks all **794** curated boards with a pre-playtest
  estimate: 60% Romanian-concept familiarity and 40% game-specific structural quality.
  It is bound to the exact pack, KG, and critique rubric and fails closed on drift.
- Pilot preference is independent of score: only approved, payload-valid records without
  deterministic critique `FAIL` qualify. There are **486** eligible boards: Conexiuni 123,
  Cald sau Rece 192, Lanț 94, and Alchimie 77.
- Existing game/category/difficulty/repeat filters run first. Eligible shelves then use
  deterministic 1–5-ticket rotation; shared daily shelves retain their minimum of eight.
  Eligible-empty seeded shelves retain their approved pool; below-minimum daily shelves
  retain the existing approved/mined fallback. Custom packs stay neutral unless they
  provide a digest-matching ranking sidecar.
- The beginner lobby starts with Alchimie → Conexiuni → Cald sau Rece → Lanț. Only Alchimie
  says `Începe aici`; a first-time player does not see an empty history wall.
- Ranking scores, board ranks, selection weights, pack IDs, and pilot eligibility stay
  outside public responses. This is an editorial board-priority estimate, not measured fun
  or a rating of any player's knowledge. Accounts, public rankings, and telemetry remain off.

## Current outcome — bounded beginner play (ADR-0027 through ADR-0050)

- Every game defaults to `Ușor`, teaches three terse actions, shows one live `ACUM` cue,
  and keeps mobile actions at least 44 px. Conexiuni owns recovery/conflict feedback in one
  sticky channel; Lanț offers corridor/detour recovery, direction, free undo, and a 64-hop
  cap; Alchimie bounds remembered experiments at 496 and projects at most 24 useful pairs.
- Cald sau Rece accepts **444 screened everyday guesses across 26 domains** through 89 KG
  anchors, keeps repeated guesses free, and progresses to one warmer familiar clue. Public
  comparison remains one stable number; targets and hidden routes/recipes remain private.
- The critique gate validates IDs, reuse, live degree, and game-specific fairness. Version-2
  artifacts bind pack, dossiers, and rubric; imports remain pending until reviewed.

## Current outcome — vocabulary and graph

V23–V33 added childhood, farm, clothing, kitchen, hygiene, cleaning, face, workshop, garden,
bathroom, household-electrical, and forest concepts. Eligible vocabulary probes are
**322/322**; 33 affected pending dossiers stay clean and all 794 curated records are unchanged.

## Product and deployment

The Romanian arcade has four server-authoritative games over the offline KG, using Django
5.2/DRF and React 19/Vite 8. Anonymous v1 at
<https://cat-de-roman-esti.dobolabs.ro> runs `f40fa8b`, verified 2026-07-18. Accounts and
the player leaderboard remain staging-only; production has no V37 pilot behavior yet.

## Shipped content

| Game | Total | Approved | Pending | V37 eligible | Runtime source |
|---|---:|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | 123 | ranked curated; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | 192 | ranked curated; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 | ranked curated; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | 77 | ranked curated; sparse projection miner fallback |

Pack: **794 = 572 approved + 222 pending**, across 14 categories. Bundled KG:
**2,287 nodes / 9,122 edges / 7,400 aliases / 180 legacy puzzles**. Committed fixture
mirrors stay byte-identical; the V37 sidecar is digest-bound to pack, KG, and rubric.

## Runtime contracts and safety

- Sessions retain a validated 7,200-second sliding TTL and 1,000-entry LRU cap. Per-entry
  locks linearize a request; different sessions stay concurrent and all-borrowed capacity
  fails with 503. Lanț retains at most 64 moves / 65 nodes.
- Request bodies have a 64 KiB Caddy and ASGI receive ceiling. Hidden answers stay pinned;
  no private V37 ranking field is serialized by a game endpoint.
- Curated submissions require `CAT_SUBMISSIONS_DIR`; only approved records are served.
  Mobile fixture/OpenAPI contracts and deterministic seeded/daily selection remain pinned.

## Quality gate

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
node --check .claude/workflows/critique-games.js
git diff --check
```

Run frontend gates when frontend files change; session-store target:
`tests/test_wordgames_session_store.py` (**16**).

## Next verified work

- Recalibrate board priority only after a separate privacy/storage decision permits bounded,
  server-authored aggregate starts, outcomes, hints, and action counts.
- Continue exact pending-stock adversarial review and generic-edge cleanup.
