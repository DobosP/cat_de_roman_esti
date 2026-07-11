# Status — cat_de_roman_esti

_As of 2026-07-11. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-11 (v15 backend 255 + accounts 28, Ruff, both validators, clean frontend install, lint/typecheck/test/build, bundle gate, and complete npm plus constrained-Python audits with zero known vulnerabilities green.)_

## Latest — v15 low-resource launch baseline

The deploy now targets Python 3.12 and Node 24 LTS; the SPA is on React 19.2 and Vite 8.1.
Each game/ranking route is a dynamic chunk and Motion loads only its DOM feature pack.
The Vite-manifest gate recursively caps initial JS/CSS at 120 KiB gzip (115.34 KiB now),
and explicit Latin + Latin Extended imports emit four fonts instead of ten (ADR-0020).
Development checks use ESLint 10.7 flat config, typescript-eslint 8.63, and TypeScript
5.9.3; TypeScript 7 remains outside typescript-eslint's supported peer range.
The final production image is 241,861,503 bytes at
`sha256:03b8288a928a2166e9a2c4d2586eedeb72f0e8c95cdfa882bcea53a15f7845ff` and runs as
the fixed `appuser` account.

Vite-hashed JS, CSS, and fonts receive immutable WhiteNoise caching. Game sessions now
default to a two-hour sliding TTL and 1,000-entry LRU per game; both are environment
configurable and validated. Request bodies default to a 64 KiB ceiling at Caddy and the ASGI
receive boundary, so declared or chunked oversize requests stop before Django buffers the complete
body; the origin returns a bounded JSON 413. The one-process session constraint remains (ADR-0020).

The v14 game/content baseline remains: exact-action Alchimie par, branch-quality Lanț,
Romanian-first replay UX, directed guess-to-target Contexto rank, and the broad-audience
reviewed pack (ADR-0015 through ADR-0019). Curated-first seeded selection, daily rendezvous
hashing, signed-in avoid-repeats, and bounded-miner fallbacks are unchanged (ADR-0011).

## Product phase

**v1.3 — Romanian text word-game arcade over an offline knowledge graph.** The web
product has four server-authoritative games: Alchimie (category-scoped Infinite Craft),
Cald sau Rece (Contexto-style ranked proximity), Lanțul Cuvintelor (semantic word
ladder), and Conexiuni (four authored groups). Each supports difficulty, seeded daily
play, score/share output, categories, and bounded local history. The old graph SPA was
removed; no graph UI unless the owner reopens ADR-0001.

Backend: Django 5.2 + DRF, stateless by default, WhiteNoise SPA serving, uvicorn ASGI.
Frontend: React 19.2 + Vite 8.1 + TypeScript, lazy game routes, shared shell/HUD/results,
Motion, and Web-Audio. Optional accounts add Google sign-in, saved puzzle ids, ranking
handles, scores, and donations.

Accounts/ranking remain **staging-only**: rankings currently accept client-authored scores
and timestamps, and profile visibility defaults on. Public launch requires scores written
from server-authoritative game completion and explicit opt-in ranking visibility, in
addition to the compliance checklist in `docs/DEPLOY.md`.

## Shipped content

| Game | Approved | Pending | Runtime source |
|---|---:|---:|---|
| Conexiuni | 181 | 105 | curated first; mixed-board miner fallback only |
| Cald sau Rece | 192 | 5 | curated first; category-scoped miner fallback |
| Lanțul Cuvintelor | 89 | 106 | curated first; branch-aware miner fallback |
| Alchimie | 75 | 16 | curated first; category-scoped closure fallback |

Pack total: **769 instances = 537 approved + 232 pending**, across 14 categories.
Bundled KG: **1,459 nodes / 5,656 edges / 4,688 aliases / 180 legacy puzzles**;
both fixture copies and both pack copies are byte-identical.

The curated fixture path is the delivered content source. The `romania_scraper →
ro_data_server` corpus path remains blocked by restricted processed-data access; live
pull stays optional and fail-soft. `kg_puzzles` powers only the legacy terminal HopGame.

## Runtime contracts and safety

- Sessions use a 2-hour sliding TTL and a 1,000-entry LRU cap **per game**, configurable
  through validated env. Cleanup is lazy, lock-protected, monotonic, and deterministic.
- Request bodies default to a 64 KiB edge + ASGI receive ceiling; Vite-hashed assets cache
  immutably.
- Contexto withholds target id/label/description until win or give-up. Alchimie withholds
  target id until crafted. Lanț reveals only played/hinted hops. Conexiuni reveals solved
  groups as earned but withholds all unsolved membership and full solution until terminal.
- Conexiuni clues remain one redacted label pattern after two distinct mistakes. Contexto
  exposes one broad category clue after three counted guesses. Both retain score penalties.
- `GET /api/manifest`, stable OpenAPI operationIds, the public mobile app-pack fixture,
  and hidden-answer boundaries are pinned by `docs/MOBILE_CONTRACT.md` and tests.
- Curated submissions remain opt-in through `CAT_SUBMISSIONS_DIR`; only approved records
  are served. Validators reuse the same runtime playability functions as the server.

## Quality gate

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
cd frontend && npm test && npm run lint && npm run typecheck && npm run build
git diff --check
```

The shared session-only command remains:
`PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest
tests/test_wordgames_session_store.py -q` (11 passed). Frontend changes include the matching
tracked `web/static` release bundle + manifest; backend-only work does not regenerate it.

## Verified follow-up candidates

- Repair the v11 enrichment tail: 183 nodes currently have non-distractor degree ≤2
  (157 are `n_v11*`), below the play-density direction in ADR-0012.
- Make ranking scores server-authored, bound retained score history, and default ranking
  visibility off before enabling accounts for public users.
