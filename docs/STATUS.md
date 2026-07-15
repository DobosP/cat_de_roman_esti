# Status — cat_de_roman_esti

_As of 2026-07-15. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-15 (backend 296 after the critique-gate tests below, Ruff, both
validators, `git diff --check`; frontend untouched — last frontend gate 2026-07-14:
lint/typecheck/test 12/12/build + bundle 115.38 KiB.)_

## Latest — content critique gate (2026-07-15, ADR-0023)

Player-reported quality drops (an approved "festival" group holding Untold/Neversea/
Electric Castle + the *village* Bonțida — cx_meme_net_136/203; festivals mirrored 1:1
against their host cities plus a generic-abstraction group — cx_muzica_271/206; Contexto
targets nobody free-associates to — Sonicitate 0.15, Meglenoromână, Pagaia din Deltă)
exposed that the pack validator checks solvability only, and that the mined-board
fairness rule (`conexiuni._board_quality`) never applied to curated boards. New
two-layer gate, backend-only: **`scripts/critique_pack.py`** (deterministic lints —
type-compatible tile fairness with raw engine parity in dossiers, red-herring budget <4,
mirrored groups ≥3, 3+1/2+2 node_type mixes, duplicate quads, salience floors
0.60/0.35/0.20 per difficulty, member overuse >8; `--strict` FAILs block promotion,
`--dossier` emits per-item judge dossiers) and **`.claude/workflows/critique-games.js`**
(fleet-routed judges: Sonnet critics → Opus adversarial verifiers with live
Romanian-relevance web checks) per **`docs/CRITIQUE_RUBRIC.md`**. Durable verdict
contract in ADR-0023 (apply_rereview vocabulary; sweeps over approved stock emit
owner proposals only; ADR-0019 stays above the gate). First full lint run over the
existing stock: **127 tile-fairness FAILs, 689 duplicate/near-duplicate WARNs,
254 salience WARNs, 83 mirrored-group WARNs** — the sweep queue. Backend suite
280 → 296 (`tests/test_critique_pack.py`). Promotion-time command:
`PYTHONPATH=. .venv/bin/python scripts/critique_pack.py --ids <batch> --strict`.
Pilot judge sweep ran same day (34 approved items incl. the player-reported boards,
65 agents, all verified or 1-in-4 sampled): quality proposals **18/20 conexiuni
demote + 2 revise; contexto 4 demote, 5 revise, 5 keep** — famous-but-low-salience
controls (Cuza, Sarmale, Transilvania) correctly kept. Verdict archive in the
session scratchpad (v16 convention); demotions are owner decisions, pack unchanged.

## Latest — Cald sau Rece playability: scroll + score + leave (2026-07-14)

Three player-reported mobile bugs on the Contexto game (`frontend/src/screens/CaldRece.tsx`
+ `frontend/src/styles/arcade.css`):
1. **Guesses unreachable / "buggy scroll".** The playing view pinned a tall header
   (Meniu + badge/button rows + title + description + input + best-line) and let only
   the guess list scroll in the leftover space; on a phone that space collapsed to
   ~0–130px (measured 0px with the keyboard up), stranding the guesses with no outer
   scroll. Fix: the whole screen scrolls (via the ADR-less `.screen-pad{overflow-y:auto}`
   default) and the input is a `position:sticky` `.contexto-input-bar` pinned to the top,
   so every guess is reachable at any height while typing stays available. Verified by
   headless-Chrome CDP at 375×330/360×430/390×620 with a 40-guess game: outer scrolls,
   input stays pinned, last guess reachable in all.
2. **Confusing score.** Each guess showed BOTH `#rank` and `closeness/100` — the two are
   derived from each other and point opposite ways. Per owner choice (2026-07-14) the row
   now shows temperature + `#rank` only (`#1` = the secret; tooltip "al câtelea cel mai
   apropiat"); the `/100` number is dropped everywhere (row, latest-verdict, best-so-far).
   The colored proximity bar (still driven by closeness) stays as the visual cue.
3. **Leaving not permanent.** "← Meniu" navigated home without dropping the resume token,
   so returning silently re-resumed the game ("Joc reluat." + intro flash). New
   `handleExit` calls `active.forget()` before exiting (menu button on intro + playing,
   and the result card); a genuine page refresh still resumes via `useActiveGame`.
   Verified: exit clears localStorage and the return shows a fresh intro.

Frontend gate green (lint/typecheck/12 tests/build, bundle 115.38 KiB). SPA rebuilt into
`web/static`.

## Latest — mobile intro scroll fix (2026-07-13)

Phone bug: on the difficulty-select intro screens the card could exceed the
viewport, and with nothing owning the vertical scroll the **Joacă/Începe** button
was clipped and unreachable. Root cause: every `.screen` is `position:absolute;
inset:0` inside an `overflow:hidden` `.app-shell`, but `.screen-pad` was not a
scroll container — playing screens masked it with inline `overflowY:auto` while the
Alchimie/Lanț/CaldRece intros did not. Fix: `.screen-pad` now defaults to
`overflow-y:auto` + `overscroll-behavior:contain` + touch scrolling
(`frontend/src/styles/arcade.css`), and CaldRece's intro drops the `fill center`
flex-centering trap for `minHeight:100%`+`justify-content:center` so it still
centers when short but scrolls when tall (`frontend/src/screens/CaldRece.tsx`).
Verified via headless-Chrome CDP at 360×460: all three intros overflow, scroll, and
the start button is reachable (autofocus even auto-scrolls it into view). SPA rebuilt
into `web/static`. Frontend gate green (lint/typecheck/12 tests/build, bundle 115.35
KiB). **DEPLOYED LIVE 2026-07-13** from `0b68f4e`: VPS `git pull` + `docker compose
-f docker-compose.anon.yml --env-file .env.anon up -d --build`; app healthy, public
smoke green (`/api/health` 2012 concepts, `/api/categories` all 14 available with
non-zero curated per game, live CSS bundle carries the `.screen-pad{overflow-y:auto}`
rule).

## Latest — v21 precision batch + promotions + dedup audit (2026-07-13)

Precision content pass: 113 new concepts + 412 edges + 360 aliases across all 14
categories (Fable authors, quality-only brief incl. "do not pad"; Opus web-verifiers
blocked 2 nodes / 11 edges / 22 aliases; 2 folded). Gaps filled include the missing
Babasha artist node, Nicole Cherry, Vlăduța Lupău, Direcția 5, SAGA Festival. Dedup
audit of the 12 v20-involving similarity pairs: ZERO true duplicates (all distinct —
Peleș/Pelișor, dish-vs-ingredient etc.). Four pending Lanț boards newly clearing the
ADR-0016 floor were judge-promoted (1 kept): lant approved 90 → 94. Graph: **1,899 →
2,012 nodes, 7,770 → 8,178 edges**, 2 weak nodes. No re-derivation retirements.
Pack 761 = 592 approved + 169 pending; snapshot + pins refreshed. This lands the
publish train: v17-v21 deploy together (owner call).

## Latest — engine feel v2: auto-accept + Lanț guidance (2026-07-13, ADR-0022)

Playability round on top of ADR-0021, backend-only and API-additive. New
`WordGameService.resolve_fuzzy()` confidently auto-corrects a typo (difflib ratio ≥ 0.90
on normalized keys, no second distinct node within 0.06, deterministic): Contexto guesses
and Lanț moves play the corrected node as if typed (attempts/moves count normally;
additive message "Am înțeles: <label>."), and a corrected typo OF THE ANSWER is a
legitimate win in both games; weaker/ambiguous input keeps ADR-0021's advisory
suggestions (target still stripped, ADR-0009). Lanț hints now pick the strongest-edged
on-path hop (salience only breaks ties), a SECOND hint request from the same chain state
adds `alternatives_labels` (≤3) + "Alte variante: …", and a legal move onto a node that
can no longer reach the target returns additive `dead_end: true` plus a warning.
Hidden-answer, clue, score_for and operationIds pinned unchanged; backend suite 271 → 280.

## Latest — v20 all-category content batch (2026-07-13)

157 new concepts + 549 edges + 509 aliases across ALL 14 categories (Fable 5 authors:
web-grounded trends for the pop six, canonical-gap depth for the classic eight; Opus
web-verifiers blocked 2 nodes / 8 edges / 10 aliases; 3 duplicate nodes folded by the
importer incl. a cross-batch Babasha re-add). Assembly now NORMALIZES freeform relation
names to the house vocabulary (109 edges mapped, incl. direction flips for created→
created_by) and remaps edges referencing merged-away duplicate ids. Graph: **1,746+ →
1,899 nodes, 7,237+ → 7,770 edges** (post-dedup baseline), 2 weak nodes (follow-up).
Re-derivation retired lt_istorie_115 + lt_stiinta_162 (approved Lanț; optimal below
band): pack 761 = 588 approved + 173 pending. Mobile snapshot + pins refreshed.

## Latest — v20 duplicate cleanup (2026-07-13)

New committed tool `scripts/merge_duplicates.py` (parameterized generalization of
refine_dataset.py's v11 merge machinery: survivor absorbs the duplicate's label+aliases,
edges redirected+deduped, pack payloads rewritten and re-derived, atomic validate+rollback;
salience untouched). A 144-pair similarity scan was judged by five Fable 5 agents
("when in doubt, keep"; the Moldova homonym stays split): **4 true duplicates merged**
(Filosofie→Filozofie, viral-phenomenon twins, sports-final twins, and v19's
specialty-coffee entering under two categories), 140 pairs confirmed distinct. One
approved usor Alchimie board retired (target became one-action craftable post-merge):
pack 763 = 590 approved + 173 pending. Mobile snapshot + pins refreshed.

## Latest — v19 meme/trend expansion (2026-07-13)

84 new pop concepts + 273 edges + 263 aliases, meme/trend-focused: meme_net covered by TWO
web-grounded Fable 5 lenses (viral memes/expressions — "Ursul, băăă!", Dedeman-as-meme,
sigma/skibidi Gen-Alpha slang, AI-manele; and creators/platforms — Godină, DA BRAVO!),
plus trend briefs for the other five pop categories. Same verification rail as v18 (Opus
with web access; unverifiable post-2024 = block: 2 nodes, 9 edges, 15 aliases blocked;
1 cross-lens duplicate dropped at assembly, 3 more folded by the importer). Staying-power
rule (≥6 months) + strict ADR-0019 meme boundary in the briefs. Graph: **1,662 → 1,746
nodes, 6,966 → 7,237 edges** (pop shelf 804, meme_net 141); v18's three under-connected
nodes repaired (1 weak node remains — follow-up). No pack items retired this time
(764 = 591 approved unchanged, re-derived green); `kg_puzzles` + mobile snapshot
regenerated. Landed only — server remains on the v16 build (`473ee63`).

## Latest — v18 web-grounded pop-culture expansion (2026-07-13)

72 new pop-shelf concepts + 238 edges + 240 aliases across the 6 pop categories (muzica,
film_tv, meme_net, sport, viata_de_roman, gastronomie), authored by Fable 5 agents that
did LIVE WEB RESEARCH first (Romanian pop culture 2025-2026, staying-power filter) and
verified by Opus reviewers WITH web access — any post-2024 claim that could not be
verified against sources was blocked (13 nodes, 47 edges, 28 aliases blocked; importer
folded 5 more duplicate nodes, dropped 8 colliding aliases). Current-relevant content now
in the graph: Spotify Wrapped 2024/2025 toppers, the Babasha–Coldplay moment, Beach
Please at European-largest scale, Eurovision 2026, TikTok-viral hits, and equivalents in
the other pop categories. Graph: **1,590 → 1,662 nodes, 6,730 → 6,966 edges** (pop shelf
now 720 nodes); 3 v18 nodes sit below degree 3 after their edges were partially blocked —
follow-up candidate. Re-derivation retired one more approved normal Lanț board
(lt_viata_de_roman_164): pack now 764 = 591 approved + 173 pending, all green;
`kg_puzzles` + mobile snapshot regenerated. Landed only — server intentionally remains on
the v16 build (`473ee63`) per owner deploy policy.

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
