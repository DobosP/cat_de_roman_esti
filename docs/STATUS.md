# Status — cat_de_roman_esti

_As of 2026-07-18. This file is the repository's current source of truth._
_Last verified: 2026-07-18 (local v33 data gate remains green: backend 391, focused content 52, session 11, exact critique 33/33, mobile 227/26. Local ADR-0043 gate: Lanț 46, mobile contract 6, curated/pack invariants 35, session 11; full Ruff, both validators, workflow syntax, whitespace; frontend lint/typecheck and 9/9 source suites, with the generated bundle intentionally unchanged for combined integration. Live release remains `f40fa8bc1b8880637aeeb01816c612ea850f73c0`: healthy image `sha256:3ed5fc61a95ec08417f1ebb68f329bf85779ab0988dffdcc7537c5d769dc6e9a`; manifest `sha256:670cc16bcbf8f5d1ba4184c0867ea3e68f6331533afe7cc259be060eb655a8ee`, 2,269 nodes / 9,068 edges / 180 puzzles; all 14 categories positive, available, and curated; anonymous mode and production smoke remain healthy.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

The critique layer now fails closed from generation through promotion:

- `critique_pack.py` validates explicit IDs, cross-board reuse, projected member overuse, and directed Contexto dossiers with live degree.
- Gate mode verifies every item adversarially; only clean approved-stock sweeps may sample 1-in-4, and returned IDs must match requested IDs.
- Lanț and Alchimie have explicit branch/craft judge criteria; all four games have game-specific review.
- Version-2 artifacts bind the exact batch, dossiers, and rubric; apply rebuilds and reruns them before writing.
- Re-review/demotion validates identity and verdict, restoring both pack copies on any red or exception.
- Imports enter `pending`; persistent per-game high-water marks prevent retired ID reuse.

## Current outcome — browser recovery and Lanț navigation (ADR-0027–ADR-0029, ADR-0034, ADR-0035, ADR-0043)

Lanț exposes up to three private-corridor choices plus safe detours as ID-free label/relation
chips; visible homonyms bind exactly and every other direct hop stays legal. Hints prefer a
safe forward route before free undo. Conexiuni retains one-away swaps; Cald sau Rece keeps
target-filtered typo recovery. Alchimie keeps a 12-reaction journal and authoritative empty
pair for one visible swap. All remain server-authoritative; score, undo, secrecy, TTL, and
caps are unchanged.

## Current outcome — beginner mobile interface (ADR-0031)

All four games now default to `Ușor`, teach their loop with three terse actions, and show
one live `ACUM` cue instead of repeating rules. Mobile gets 44 px targets, scrollable
status/theme rails, readable long labels, reachable primary actions, visible rank meaning,
and safe keyboard shortcuts; desktop retains the same focused play column.

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

Anonymous v1 at <https://cat-de-roman-esti.dobolabs.ro> runs release `f40fa8b`, deployed
and smoke-verified on 2026-07-18. Accounts/rankings remain staging-only: scores are
client-authored and visibility needs opt-in by default.

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
  Alchimie hides target ID; Lanț local choices have no IDs/on-track flag and reveals one
  hop ID only on the third requested hint; Conexiuni withholds unsolved membership/solution.
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

- Playtest the beginner UI and recovery flows at 320–390 px; measure friction and abandonment.
- Complete adversarial review over the exact 33 v23/v24 pending IDs; inspect Contexto
  ordering after v33, route meaning, Conexiuni predicates, and Alchimie recipe intuition.
- Work the approved-stock critique/A7 queues; generic regional KG edges remain cleanup inventory, while owner demotions stay explicit proposals.
- Make ranking scores server-authored, bound retained score history, and default ranking visibility off before enabling public accounts.
