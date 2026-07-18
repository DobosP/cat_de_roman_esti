# Status — cat_de_roman_esti

_As of 2026-07-18. This file is the repository's current source of truth._
_Last verified: 2026-07-18 (V34 combined verification pending. Contexto source gate: backend 403, focused 53, mobile/session aggregate 70. Lanț source gate: focused 46, mobile aggregate 52, curated/pack/session 46. Both passed Ruff, validators, workflow syntax, whitespace, and frontend source gates. Live release remains V32 `f40fa8bc1b8880637aeeb01816c612ea850f73c0`; manifest `sha256:670cc16bcbf8f5d1ba4184c0867ea3e68f6331533afe7cc259be060eb655a8ee`, 2,269 nodes / 9,068 edges / 180 puzzles.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

The critique layer now fails closed from generation through promotion:

- `critique_pack.py` validates IDs, reuse, overuse, live degree, and game-specific judge criteria.
- Version-2 artifacts bind the exact batch, dossiers, and rubric; apply rebuilds and reruns
  them before writing, while re-review restores both copies on any red or exception.
- Imports enter `pending`; persistent per-game high-water marks prevent retired ID reuse.

## Current outcome — browser recovery (ADR-0027 through ADR-0029, ADR-0034, ADR-0035)

Lanț exposes up to three private-corridor choices plus safe detours as ID-free label/relation
chips; visible homonyms bind exactly and every other direct hop stays legal. Hints prefer a
safe forward route before free undo. Conexiuni retains one-away swaps; Cald sau Rece keeps
target-filtered typo recovery. Alchimie keeps a 12-reaction journal and authoritative empty
pair. All remain server-authoritative; score, undo, secrecy, TTL, and caps are unchanged.

## Current outcome — beginner mobile interface (ADR-0031)

All four games now default to `Ușor`, teach their loop with three terse actions, and show
one live `ACUM` cue instead of repeating rules. Mobile gets 44 px targets, scrollable
status/theme rails, readable long labels, reachable primary actions, visible rank meaning,
and safe keyboard shortcuts; desktop retains the same focused play column.

## Current outcome — broad Contexto guidance (ADR-0042)

Cald sau Rece accepts **444 collision-screened everyday guesses across 26 domains** through
89 reviewed KG anchors without changing graph/pack bytes or creating projection wins.
Clues progress from category to one strictly warmer familiar word; themed boards skip category.

## Current outcome — beginner vocabulary waves (ADR-0030, ADR-0032, ADR-0033, ADR-0036 through ADR-0041)

V23 retains 22 childhood/story nodes and 78 edges. V24 adds **150 everyday nodes, 511
edges, 276 aliases, and 26 pending items**; V25 adds **168 safe aliases and 25 links**.
V28 completes the eligible beginner benchmark with **15 concepts, 44 inflections, and 53
links**, reaching **234/234**. V29 adds **17 concepts, 66 inflections, and 64 links**.
V30 adds **18 farm, clothing, and kitchen concepts, 60 inflections, and 54 links** in
three inbound-reachable meshes. V31 adds **17 hygiene, lower-limb, and cleaning concepts,
61 inflections, and 51 links**. V32 adds **18 face, workshop, and garden concepts, 69
inflections, and 54 links**. V33 adds **18 bathroom, household-electrical, and forest
concepts, 67 inflections, and 54 links**; combined eligible probes resolve **322/322**.
All 33 affected pending dossiers and the full report stay unchanged and clean; all 794
curated records remain unchanged.

## Product and deployment

The Romanian arcade has four server-authoritative games: Alchimie, Cald sau Rece, Lanțul
Cuvintelor, and Conexiuni, using Django 5.2/DRF and React 19/Vite 8 over the offline KG.

Anonymous v1 at <https://cat-de-roman-esti.dobolabs.ro> runs release `f40fa8b`, verified
2026-07-18. Accounts/rankings remain staging-only and client-authored.

## Shipped content

| Game | Total | Approved | Pending | Runtime source |
|---|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | curated first; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | curated first; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | curated first; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | curated first; category closure fallback |

Pack: **794 items = 572 approved + 222 pending**, across 14 categories.
Bundled KG: **2,287 nodes / 9,122 edges / 7,400 aliases / 180 legacy puzzles**.
Both fixture copies and both pack copies are byte-identical and validator-green.

## Runtime contracts and safety

- Sessions use a validated two-hour sliding TTL and 1,000-entry LRU cap per game; cleanup
  is lazy, lock-protected, monotonic, and deterministic.
- Request bodies default to a 64 KiB Caddy plus ASGI receive ceiling.
- Hidden-answer boundaries remain pinned: Contexto hides its target until terminal;
  Alchimie hides target ID; Lanț reveals played/hinted hops; Conexiuni withholds unsolved
  membership and the full solution until terminal.
- Curated submissions are opt-in through `CAT_SUBMISSIONS_DIR`; only approved records
  are served. Import candidates remain pending until the critique gate promotes them.
- Mobile fixture/OpenAPI contracts and curated-first seeded selection remain test-pinned.

## Quality gate

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
node --check .claude/workflows/critique-games.js
git diff --check
```
Run frontend lint/typecheck/test/build only when frontend files change. The shared
session-store target remains `tests/test_wordgames_session_store.py` (11 tests).

## Next verified work

- Playtest beginner guidance at 320–390 px, including projected Contexto terms and clues.
- Continue exact pending/approved-stock adversarial review and generic-edge cleanup.
- Make rankings server-authored, bounded, and private-by-default before public accounts.
