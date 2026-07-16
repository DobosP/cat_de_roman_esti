# Status — cat_de_roman_esti

_As of 2026-07-16. This file is the repository's current source of truth._
_Last verified: 2026-07-16 (backend 324; session-store 11; exact v23 critique 7;
Ruff; both validators; workflow syntax; frontend lint/typecheck/26 tests/build;
bundle 115.38 KiB; `git diff --check`.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

The critique layer now fails closed from generation through promotion:

- `critique_pack.py` rejects bad explicit IDs, checks selected pending boards against one
  another, projects batch member overuse, and emits directed Contexto dossiers with live degree.
- Gate-mode `.claude/workflows/critique-games.js` verifies every item with the
  adversarial layer. Only clean approved-stock sweeps may use deterministic 1-in-4
  sampling. Returned IDs must match requested IDs.
- Lanț and Alchimie now have explicit judge criteria plus branch-choice and craft-choice
  dossier profiles; all four games have game-specific quality review.
- Version-2 artifacts bind the exact batch, canonical dossier content, and rubric digest.
  Apply rebuilds those dossiers, rejects stale/unverified/hand-combined artifacts, and
  reruns deterministic critique over the exact promotion set before writing.
- Re-review and demotion apply paths validate game, status, ID, and verdict before
  mutation and restore both pack copies on validator errors, red returns, or exceptions.
- `import_candidates.py` maps accepted generator output to `pending`; per-game ID
  high-water marks persist in pack metadata, so retired IDs are never reused later.

## Current outcome — browser recovery (ADR-0027 through ADR-0029)

Lanț renders server-authored recovery in a polite status; bounded spelling and path
choices fill but never submit. Conexiuni retains nonterminal one-away selections for
one-tile swaps and blocks the unchanged set without inferring hidden membership.
Cald sau Rece renders target-filtered typo suggestions as fill-only buttons and preserves
accepted correction messages, including wins. All three remain server-authoritative;
score, secrecy, TTL, and the 1,000-session caps are unchanged.

## Current outcome — v23 critique-informed childhood wave (ADR-0030)

A new batch adds **22 nodes, 78 edges, and seven pending game items**: one Conexiuni,
two Contexto, two Lanț, and two Alchimie. Familiar childhood games, school objects,
Creangă/Ispirescu stories, and fairy-tale archetypes avoid saturated celebrity/tourism
quads. Exact-ID deterministic critique is clean (zero WARN/FAIL); nothing is served
until the bound analyst plus adversarial-verifier gate reviews the final dossiers.

## Product and deployment

The Romanian arcade has four server-authoritative games: Alchimie, Cald sau Rece, Lanțul
Cuvintelor, and Conexiuni, using Django 5.2/DRF and React 19/Vite 8 over the offline KG.

Anonymous v1 is live at <https://cat-de-roman-esti.dobolabs.ro>. The last recorded live
deploy is `0b68f4e` from 2026-07-13; later work awaits an owner deploy. Accounts/rankings
remain staging-only: scores are client-authored and visibility needs opt-in by default.

## Shipped content

| Game | Total | Approved | Pending | Runtime source |
|---|---:|---:|---:|---|
| Conexiuni | 284 | 209 | 75 | curated first; mixed-board miner fallback |
| Cald sau Rece | 199 | 192 | 7 | curated first; category miner fallback |
| Lanțul Cuvintelor | 193 | 94 | 99 | curated first; branch-aware miner fallback |
| Alchimie | 92 | 77 | 15 | curated first; category closure fallback |

Pack: **768 items = 572 approved + 196 pending**, across 14 categories.
Bundled KG: **2,034 nodes / 8,256 edges / 6,589 aliases / 180 legacy puzzles**.
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

- Playtest Lanț recovery: measure invalid moves, hint reuse, undo, and abandonment.
- Review the external v22 batch, and run the bound judge gate over the seven exact v23
  pending IDs; keep both Alchimie closure-size profiles under adversarial review.
- Work the approved-stock critique/A7 queues; generic regional KG edges remain a cleanup
  inventory, while owner demotions stay explicit proposals.
- Deploy the landed v17+ content and critique improvements when the owner opens a deploy.
- Make ranking scores server-authored, bound retained score history, and default ranking
  visibility off before enabling public accounts.
