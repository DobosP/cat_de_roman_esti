# Status — cat_de_roman_esti

_As of 2026-07-19. This file is the repository's current source of truth._
_Last verified: 2026-07-19 (V35 integrated backend suite and frontend 67/67, lint,
typecheck, and production build green at 117.03/120 KiB with four font subsets; final
session-hardening gate pending. Live remains V32 `f40fa8b`; V33–V35 are not deployed.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

The critique layer now fails closed from generation through promotion:

- `critique_pack.py` validates IDs, reuse, overuse, live degree, and game-specific judge criteria.
- Version-2 artifacts bind the exact batch, dossiers, and rubric; apply rebuilds and reruns
  them before writing, while re-review restores both copies on any red or exception.
- Imports enter `pending`; persistent per-game high-water marks prevent retired ID reuse.

## Current outcome — browser recovery (ADR-0027 through ADR-0029, ADR-0034, ADR-0047)

Lanț exposes private-corridor choices plus safe detours as ID-free label/relation chips;
visible homonyms bind exactly and every direct hop stays legal. Easy hops add only a coarse
direction; after two non-improving moves, one boolean emphasizes free undo. Hints remain
staged and route-private; score, undo, secrecy, TTL, and caps are unchanged (ADR-0043/0046).
Alchimie remembers at most 496 unordered experiments; retries are free and inert, reset clears
them, and only their count is public. Score, secrecy, TTL, and session cap remain unchanged.

## Current outcome — beginner mobile interface (ADR-0031, ADR-0048)

All games default to `Ușor`, teach three terse actions, and show one live `ACUM` cue.
Mobile gets 44 px actions and compact rails. Conexiuni keeps recovery, accessible mistake
dots, and authoritative conflict refresh in one sticky channel with one live owner.

## Current outcome — V35 guided word space and comparison (ADR-0042 through ADR-0045)

Cald sau Rece accepts **444 everyday guesses across 26 domains** through 89 reviewed anchors
without changing graph/pack bytes or creating projection wins.
Clues progress from category to one strictly warmer familiar word; themed boards skip category.
Distinct guesses keep stable numbers and one comparison from public ranks; repeats stay free.
`Bune`/`Recente`, 44 px actions, clue countdown, guarded reveal, and terminal cleanup stay local.
Alchimie projects 1–4 target-useful routes into at most 24 private pairs / 32 concepts.
Runtime normally returns one result; exact par remains unchanged. Mined boards prefer two live
openings; useful/recent/all views retire depleted items and hints progress from output to pair.

## Current outcome — beginner vocabulary waves (ADR-0030, ADR-0032, ADR-0033, ADR-0036 through ADR-0041)

V23 retains 22 childhood/story nodes and 78 edges. V24 adds **150 nodes, 511 edges, 276
aliases, and 26 pending items**; V25 adds **168 safe aliases and 25 links**. V28 reaches
**234/234** eligible probes; V29 adds **17 concepts, 66 inflections, and 64 links**.
V30–V33 add 71 farm, clothing, kitchen, hygiene, cleaning, face, workshop, garden,
bathroom, household-electrical, and forest concepts; eligible probes reach **322/322**.
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
Run frontend gates when frontend changes; session-store target: `tests/test_wordgames_session_store.py` (11).

## Next verified work

- Continue exact pending/approved-stock adversarial review and generic-edge cleanup.
- Make rankings server-authored, bounded, and private-by-default before public accounts.
