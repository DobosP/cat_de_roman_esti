# Status — cat_de_roman_esti

_As of 2026-07-19. This file is the repository's current source of truth._
_Last verified: 2026-07-19 (local V38 backend: targeted derived-catalog and game tests
59/59 plus required session-store tests 16/16 green; full backend, frontend, and release
gates pending. Live remains V32 `f40fa8b`; V33–V38 are not pushed or deployed.)_

## Current outcome — local V38 refinement (ADR-0052)

- Two strict catalog-only games are implemented locally: Intrusul (a 3+1 odd-one-out)
  and Perechi (four semantic pairs). Neither game mines or widens to unreviewed content.
- The reproducible private catalog contains **336 boards**: Intrusul **183** from 66
  Conexiuni sources and Perechi **153** from 51. Starter shelves contain 24 and 26.
- Standard score is 60% visible-word familiarity and 40% mechanic clarity; starter score is
  75% familiarity and 25% clarity with stricter gates. Selection chooses a source before a
  candidate, uses fixed 1–5 score bands, and gives tied scores competition ranks (`1, 1, 3`).
- Catalog IDs, source IDs, scores, ranks, gates, weights, and unearned answers remain
  server-private. The loader rejects pack/KG/V37-ranking overrides and any bound pack, KG,
  critique-rubric, V37-ranking, or catalog-digest drift.
- Intrusul allows three distinct mistakes and one hint after the first; Perechi allows six
  distinct unordered wrong pairs and one non-solving pair hint after two. Repeats are free,
  losses score zero, and win penalties are bounded to a 100-point floor.
- V37 selection, hash namespaces, and all four existing daily schedules are unchanged.
  Shared 7,200-second sliding TTL, 1,000-entry per-game cap, atomic mutation, and terminal
  answer gates remain in force; non-daily repeat memory holds at most four private sources.
- The accepted frontend contract is tap-first and mobile-first, with lobby order Alchimie →
  Intrusul → Perechi → Conexiuni → Cald sau Rece → Lanț and only Alchimie featured as
  `Începe aici`. Its separate integration and frontend gates are still pending.

## Retained V37 baseline (ADR-0051)

- The private V37 sidecar ranks all **794** curated boards at 60% Romanian-concept
  familiarity and 40% game-specific structural quality, bound to pack, KG, and rubric.
  Its **486** eligible boards are Conexiuni 123, Cald sau Rece 192, Lanț 94, Alchimie 77.
- Existing game/category/difficulty/repeat filters run first. Eligible shelves use
  deterministic 1–5-ticket rotation; daily shelves retain their minimum of eight and their
  approved/mined fallback. Custom packs stay neutral without a digest-matching sidecar.
- Rankings are editorial pre-playtest estimates, not measured fun or player-knowledge
  ratings. Accounts, public rankings, and telemetry remain off.

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
  **322/322**; 33 affected pending dossiers and all 794 curated records remain clean.

## Product and deployment

The Romanian arcade uses Django 5.2/DRF and React 19/Vite 8 over the offline KG. Anonymous
v1 at <https://cat-de-roman-esti.dobolabs.ro> runs V32 `f40fa8b`, verified 2026-07-18.
Production has neither V37 ranking rotation nor V38 games. Accounts and the player
leaderboard remain staging-only.

## Shipped content baseline

| Game | Total | Approved | Pending | V37 eligible | Runtime source |
|---|---:|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | 123 | ranked curated; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | 192 | ranked curated; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 | ranked curated; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | 77 | ranked curated; sparse projection miner fallback |

Pack: **794 = 572 approved + 222 pending**, across 14 categories. Bundled KG:
**2,287 nodes / 9,122 edges / 7,400 aliases / 180 legacy puzzles**. Fixture mirrors and
private ranking artifacts remain digest-bound and byte-identical where duplicated.

## Runtime contracts and quality gate

- Sessions use a validated 7,200-second sliding TTL and 1,000-entry LRU cap. Per-entry locks
  serialize one session while allowing concurrent sessions; all-borrowed capacity returns
  503. Request bodies have a 64 KiB Caddy and ASGI receive ceiling.
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

Run frontend gates when frontend files change. Required session-store target:
`tests/test_wordgames_session_store.py` (**16**).

## Next verified work

- Integrate and gate the six-game mobile frontend, then run the complete release suite.
- Recalibrate rankings only after a separate privacy/storage decision permits bounded,
  server-authored aggregate starts, outcomes, hints, and action counts.
