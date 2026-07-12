# Status — cat_de_roman_esti

_As of 2026-07-12. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-12 (backend 271 + accounts 28, Ruff, both validators, anon+prod compose config render; frontend lint/typecheck/test/build + bundle gate last ran green at b245886 — untouched since.)_

## Latest — v17 Fable-authored concept expansion (2026-07-12)

131 NEW concepts + 638 edges + 438 aliases across all 14 categories, authored by Fable 5
agents (owner-requested model) and adversarially verified by Opus reviewers (1 node,
4 edges, 13 aliases blocked pre-import; the importer's duplicate-folding remapped 8 more
nodes onto existing concepts and dropped 20 colliding aliases). ADR-0019's editorial
boundary was part of the authoring brief. Graph: **1,459 → 1,590 nodes, 6,099 → 6,730
edges, ZERO nodes under non-distractor degree 3** (weak tail fully eliminated);
`related_to` share 59.3% → 56.5%; categories balanced at 93–128 nodes. Pack counts
unchanged (765 = 592 approved + 173 pending), all items re-derived green on the larger
graph; `kg_puzzles` regenerated; mobile app-pack snapshot regenerated. NOT yet deployed —
owner asked to land only; the server stays at the v16 build (`473ee63`).

## Latest — v16 KG enrichment + content promotion (2026-07-12)

443 adversarially-verified high-quality edges + 57 aliases imported across all 14
categories via `scripts/import_enrichment.py` (14 author agents, 14 reviewer agents;
13 factually-weak edges and 78 collision-prone aliases blocked pre-import). Weak tail
(non-distractor degree ≤2) drops **180 → 4 nodes, zero isolated**; generic `related_to`
share 64.6% → 59.3%; mean non-distractor degree 6.9 → 7.97; edges 5,656 → 6,099.
`kg_puzzles` regenerated; all pack items re-derived (one approved greu Lanț board retired —
new shortcuts pulled its optimal below its band). Then an Opus judge fleet reviewed the
135 pending pack items that validate on the denser graph (9 Lanț boards newly clear the
ADR-0016 branch floor): 70 promoted, 62 kept pending, 3 rejected — then the ADR-0019
editorial quarantine was REASSERTED over the judges' factual verdicts (13 conexiuni + 1
contexto returned to pending; that boundary is the owner's, not a quality call). Net
**approved served content 537 → 592** (conexiuni 227, contexto 194, lant 93, alchimie 78;
pack total 765). Lanț `usor` now hard-filters endpoint candidates to salience ≥ 0.6
(mirroring Contexto's pool — the enrichment made low-fame nodes branchy enough to win on
structure alone). Mobile app-pack contract snapshot regenerated. Judge/author verdict
archives live in the deploy-session scratchpad, applied via `scripts/apply_rereview.py`.

## Latest — graded similarity feel + fuzzy input (2026-07-12, ADR-0021)

Cald sau Rece and Lanțul Cuvintelor now feel smarter without any frontend or API-shape
change. New service primitives: `WordGameService.suggest(text, limit=3)` (difflib fuzzy
"did you mean" over the resolution index; `resolve()` stays exact-match) and
`weighted_distances_to(target)` (Dijkstra over the same reversed non-distractor adjacency as
ADR-0018, edge cost `2.0 − clamp(strength,0,1)`, missing/invalid strength → 1.5). Contexto
guesses now rank *within* a hop bucket by path tightness (refined rank =
`closer_than[d] + bisect_left(sorted_weighted[d], w) + 1`, precomputed once per session in
O(N log N)); closeness derives from that rank and temperature is a per-target rank
percentile, so tiers spread across all six labels instead of piling into "Rece". Hop
ordering across buckets, the win-100/Găsit invariants, `reachable_count`, ADR-0009 hidden
answer, ADR-0005 clue penalties, `score_for` (2 attempts → 940), MIN_REACHABLE/MIN_RESPONSIVE
floors, the packs validator (still unweighted `distances_to`), operationIds and session
bounds are all unchanged. Unknown guesses/moves now carry an additive `suggestions: [labels]`
array and embed the top hint in the existing Romanian message — Contexto strips any
suggestion that resolves to the secret (ADR-0009); unresolved guesses still never count.
Lanț's hint dead-end now names the nearest reachable node on the player's own chain
("Fundătură — întoarce-te la <label>") instead of a bare "step back". Adds 10 tests
(backend 261 → 271). See ADR-0021.

## Latest — anonymous v1 production deploy path (2026-07-12)

**LIVE 2026-07-12: <https://cat-de-roman-esti.dobolabs.ro>** — anonymous v1 deployed from
`934765e` via `docker-compose.anon.yml` on a Netcup VPS (Debian 13, 2 vCPU / 3.8 GiB,
Docker 29.6.1; ufw 22/80/443 + fail2ban + key-only SSH; Docker json-file logs capped
10 MiB×3 as the access-log/IP retention bound). Cloudflare DNS-only (grey cloud), Caddy
Let's Encrypt. Public smoke green: `/api/health` (1,459 concepts), `/healthz`, `/api/me`
`accounts_enabled:false`, HTTP→308→HTTPS, homepage, `/legal/privacy` with real operator +
`contact@dobolabs.ro` (no placeholders), and a gameplay round created through the public
URL. Owner-side: Cloudflare Email Routing rule for `contact@` (pending confirmation);
donations unset (button hidden). Post-launch follow-ups: raise `CAT_HSTS_SECONDS` once
stable, consider Cloudflare proxy flip per DEPLOY.md production path, uptime monitoring.

**Launch-day content incident (fixed same day):** the prod compose/env defaults pointed
`CAT_KG_FIXTURE` at `kg_real.json` — a stale thin corpus export (932 nodes / 135 edges)
whose node ids the curated games pack does not reference — so the live site served zero
curated games and every category showed `available: false` while the daily/miner fallback
still played. The canonical shipped KG is the curated `kg_sample.json` (1,459 nodes /
5,656 edges; the pack's node ids). Fixed live via `.env.anon` override, and the defaults
in all three compose files + `.env.prod.example` now point at `kg_sample.json`; the
DEPLOY.md smoke tests now include the `/api/categories` non-empty check that would have
caught this.

The v1 public launch ships the anonymous arcade (accounts OFF), per the go-live gate below
and in docs/DEPLOY.md. New `docker-compose.anon.yml` (app + Caddy only: no Postgres, no
OAuth, no submissions volume — zero persisted user data) with `.env.anon.example` and an
"Anonymous arcade (v1) launch" section in docs/DEPLOY.md. The served legal pages'
operator identity and privacy contact are now deploy-time configurable via
`CAT_LEGAL_OPERATOR` + `CAT_LEGAL_CONTACT_EMAIL` (web/legal.py; HTML-escaped; DRAFT
banner keeps the lawyer-review wording always, drops the "not finalized" sentence only
when both are set; `tests/test_legal.py`). Accounts/ranking remain staging-only (see
Product phase below).

## v15 low-resource launch baseline

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
