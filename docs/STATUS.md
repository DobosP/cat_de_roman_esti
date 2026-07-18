# Status — cat_de_roman_esti

_As of 2026-07-19. This file is the repository's current source of truth._
_Last verified: 2026-07-19 (V35 focused gates: Alchimie 422/422, Contexto/mobile 61/61,
Lanț bounded-path 51/51, session store 11/11, frontend 12/12, lint, typecheck, Ruff, and
whitespace. Static rebuild is pending. Live is V32 `f40fa8b`; V33–V35 are not deployed.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

- `critique_pack.py` validates IDs, reuse, overuse, live degree, and game-specific judge criteria.
- Version-2 artifacts bind the batch, dossiers, and rubric; apply rebuilds and reruns them
  before writing, while re-review restores both copies on any red or exception.
- Imports enter `pending`; persistent per-game high-water marks prevent retired ID reuse.

## Current outcome — browser recovery (ADR-0027 through ADR-0029, ADR-0034, ADR-0047)

Lanț exposes ID-free corridor/detour choices; homonyms bind exactly and direct hops stay legal.
Easy hops add coarse direction and recommend free undo after two non-improving moves. A chain
retains at most 64 moves / 65 earned nodes; the cap offers undo, and a 64th-hop win scores
normally. Hints and routes stay private; TTL/store caps are unchanged (ADR-0043/0046/0050).
Alchimie remembers at most 496 unordered experiments; retries are free and inert, reset clears
them, and only their count is public. Score, secrecy, TTL, and session cap remain unchanged.

## Current outcome — beginner mobile interface (ADR-0031, ADR-0048)

All games default to `Ușor`, teach three terse actions, and show one live `ACUM` cue.
Mobile gets 44 px actions, compact rails, and one near-board Conexiuni recovery channel
with mistake dots; desktop keeps the same loop in a focused play column.

## Current outcome — V35 guided word space and comparison (ADR-0042 through ADR-0045)

Cald sau Rece accepts **444 screened everyday guesses across 26 domains** through 89 KG
anchors without projection wins. Clues progress to one warmer familiar word. Distinct guesses
keep stable numbers and one public-rank comparison; repeats stay free. Browser `Bune`/`Recente`
views and sticky 44 px clue/reveal/options actions do not change targets or scoring.
Alchimie projects 1–4 target-useful routes into at most 24 private recipe pairs / 32 concepts.
Runtime normally returns one result and exact par holds; views retire depleted items and hints progress to a pair.

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

The Romanian arcade has four server-authoritative games: Alchimie, Cald sau Rece, Lanțul Cuvintelor, and Conexiuni, using Django 5.2/DRF and React 19/Vite 8 over the offline KG.

Anonymous v1 at <https://cat-de-roman-esti.dobolabs.ro> runs release `f40fa8b`, verified 2026-07-18. Accounts/rankings remain staging-only and client-authored.

## Shipped content

| Game | Total | Approved | Pending | Runtime source |
|---|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | curated first; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | curated first; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | curated first; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | curated first; sparse projection miner fallback |

Pack: **794 items = 572 approved + 222 pending**, across 14 categories.
Bundled KG: **2,287 nodes / 9,122 edges / 7,400 aliases / 180 legacy puzzles**.
Both fixture copies and both pack copies are byte-identical and validator-green.

## Runtime contracts and safety

- Sessions keep a validated 7,200-second sliding TTL and 1,000-entry LRU cap; cleanup stays
  lazy, lock-protected, monotonic, and deterministic. Lanț caps paths at 64 moves / 65 nodes.
- Request bodies default to a 64 KiB Caddy plus ASGI receive ceiling.
- Hidden answers stay pinned: Contexto hides its target; Alchimie hides target ID; Lanț
  reveals earned/hinted hops; Conexiuni hides unsolved membership/full solution until terminal.
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
Run frontend gates when frontend changes; session-store target: `tests/test_wordgames_session_store.py` (11).

## Next verified work

- Playtest V35 comparison/actions at 320–390 px, including projected terms and both clues.
- Continue exact pending/approved-stock adversarial review and generic-edge cleanup.
- Make rankings server-authored, bounded, and private-by-default before public accounts.
