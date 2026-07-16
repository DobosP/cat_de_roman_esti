# Status — cat_de_roman_esti

_As of 2026-07-16. This file is the repository's current source of truth._
_Last verified: 2026-07-16 (backend 321; focused critique 41; Ruff; both validators;
workflow syntax; binding smoke; candidate structure; `git diff --check`. Frontend
unchanged; last gate 2026-07-14: lint, typecheck, 12 tests, build, bundle 115.38 KiB.)_

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

This is enforcement of ADR-0023's existing two-layer gate, not a new editorial policy.
No game/session behavior and no served content changed in this pass.

## Current outcome — v22 web-grounded authoring session started

A managed-handoff session, outside shipped fixtures, holds **12 candidate nodes, 53
candidate edges, and one normal Conexiuni board**: Dacia models, tourist salt mines,
banknote figures, and traditional instruments, sourced primarily to Dacia/SALROM,
county authorities, BNR, UNESCO, and Romanian heritage registers.

All references resolve; every new node has at least three candidate connections; the 16
tiles are unique with no existing three-member overlap. The batch remains unimported and
unapproved pending factual review, disposable import, exact-ID lint/dossiers, and both
judges. An earlier group was rejected as a near-duplicate of `cx_arta_cultura_242`.

## Product and deployment

The Romanian arcade has four server-authoritative games: Alchimie, Cald sau Rece, Lanțul
Cuvintelor, and Conexiuni, using Django 5.2/DRF and React 19/Vite 8 over the offline KG.

Anonymous v1 is live at <https://cat-de-roman-esti.dobolabs.ro>. The last recorded live
deploy is `0b68f4e` from 2026-07-13; later content and critique work is landed-only until
the next owner deploy. Accounts/rankings remain staging-only because ranking scores are
still client-authored and profile visibility needs an explicit opt-in default.

## Shipped content

| Game | Total | Approved | Pending | Runtime source |
|---|---:|---:|---:|---|
| Conexiuni | 283 | 209 | 74 | curated first; mixed-board miner fallback |
| Cald sau Rece | 197 | 192 | 5 | curated first; category miner fallback |
| Lanțul Cuvintelor | 191 | 94 | 97 | curated first; branch-aware miner fallback |
| Alchimie | 90 | 77 | 13 | curated first; category closure fallback |

Pack: **761 items = 572 approved + 189 pending**, across 14 categories.
Bundled KG: **2,012 nodes / 8,178 edges / 6,564 aliases / 180 legacy puzzles**.
Both fixture copies and both pack copies are byte-identical and validator-green.

## Runtime contracts and safety

- Sessions use a validated two-hour sliding TTL and 1,000-entry LRU cap per game;
  cleanup is lazy, lock-protected, monotonic, and deterministic.
- Request bodies default to a 64 KiB Caddy plus ASGI receive ceiling.
- Hidden-answer boundaries remain pinned: Contexto hides its target until terminal;
  Alchimie hides target ID; Lanț reveals only played/hinted hops; Conexiuni withholds
  unsolved membership and the full solution until terminal.
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

- Adversarially review v22 facts/edges, import into a disposable copy, then run exact-ID
  strict critique and version-2 gate artifacts before any promotion.
- Work the approved-stock critique/A7 queues; generic regional KG edges remain a cleanup
  inventory, while owner demotions stay explicit proposals.
- Deploy the landed v17+ content and critique improvements when the owner opens a deploy.
- Make ranking scores server-authored, bound retained score history, and default ranking
  visibility off before enabling public accounts.
