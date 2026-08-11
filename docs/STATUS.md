# Status — cat_de_roman_esti

_As of 2026-08-11. This file is the repository's current source of truth._

_Last verified: 2026-08-11 (V49 backend 748/748, accounts 53/53, sessions 16/16, artifact validators, Ruff, workflow syntax, and whitespace green; frontend unchanged; production probes remain V48)._

## Current outcome — V49 durable Lanț rejection debt (ADR-0073)

- A non-runtime ledger now retains exactly the 104 V45 Lanț rejections as 104 unique
  directed start/target pairs. Each entry binds its rejected record, pair, exact dossier,
  and complete V45 gate; the initial ID set and source commit/pack are pinned.
- Import canonicalizes aliases and fails before mutation on ledger reuse. Pending critique
  checks the full current Lanț inventory plus the ledger, excluding only the row itself.
  Future rejects append with the pack transaction and roll back on any validation failure.
- Reverse pairs are distinct; broader corridor similarity remains D1–D5 human evidence.
  The three V45 repair holds are excluded and unchanged. No owner disposition was inferred.
- Pack, KG, rubric, rankings, derived catalog, statuses, selection, frontend, and sessions are unchanged. V49 did not deploy.
- V48 remains: Alchimie has 79 approved/selectable + 3 alcohol A5 holds; its source-bound
  private recipes are bounded and the complete one-promote/17-reject archive is retained.
- V47 remains: Cald sau Rece has 205 approved / 2 pending / 202 selectable unique targets;
  `Mâncare` is served and `Shitpost`/`Industrie` remain A5 owner holds.
- V46 remains: Conexiuni has 232 approved / 74 selectable / 0 pending and a durable
  rejection ledger of 122 boards / 488 groups. V45 leaves Lanț at 94 selectable boards
  and three pending repair holds.
- V44's repair/projection remains unchanged; so does the frozen 336-board derived payload.
- The six-game tap-first lobby remains Alchimie → Intrusul → Perechi → Conexiuni → Cald sau
  Rece → Lanț. Mobile stays one card per row; wide screens use three columns.
- Alchimie help still starts after two distinct barren experiments, reveals only bounded
  strategy, preserves the selected theme/difficulty on another board, and caps experiment
  memory at 496 pairs. Other game help, scoring, and hidden-answer behavior are unchanged.
- A category-scoped curated daily needs four selectable exact-shelf records; the shared
  daily needs eight. Thin shelves mine inside the requested theme or return themed 503.

## Content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 202 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **618 = 610 approved + 8 pending**, across 14 categories. The ranked original-game
runtime serves **449 zero-FAIL boards**. The strict derived catalog remains **336** boards
from the frozen V38 source snapshot; its `boards` payload hash is
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
Bundled KG: **2,364 nodes / 9,217 edges / 7,452 aliases / 180 puzzles**
(`fixture-v44-contexto-common-words`).

ADR-0073's seed audit is under `docs/reviews/v49-lant-rejection-ledger/`. V45's exact
Lanț gate and V48's live-projection gate remain their immutable source evidence; rankings
remain estimates.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode can upload validated completed-score rows privately but does not download,
  restore, or merge them. Public records remain server-authored and consent-gated.
- Anonymous production runs V48 at `d59caed` since 2026-08-01. Exact runtime hashes/counts,
  accounts-off and submissions-off boundaries, 14 categories, frontend/health/manifest,
  Făt-Frumos, and create/resume privacy contracts for all six games passed publicly.
  The single app process is healthy with zero restarts and no unexpected post-smoke errors.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
PYTHONPATH=. .venv/bin/ruff check --no-cache .
cd frontend && npm test && npm run lint && npm run typecheck && npm run build
git diff --check
```

## Next verified work

- Resolve the three Alchimie alcohol holds only through explicit owner disposition and a
  fresh source-bound live-recipe gate. Consult the V48 archive before any repair; never
  re-add one of the 17 rejected source records unchanged or fill the shelf by quota.
- Any future Conexiuni authoring starts materially fresh from the ten hidden shelves and
  durable rejection evidence; never force a quota or reuse a banned quad.
- Census the full Lanț pack and durable ledger before authoring/import. Repair the three
  holds only after their named blocker changes, then generate fresh exact dossiers.
- Resolve the two Cald sau Rece A5 holds explicitly. Repair Morcov, Familie, Farmacie,
  Ploaie, Frigider, or Creion only through a separately bound feedback change and fresh
  C1-C6 gate; never re-add the archived exact record unchanged.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion (ADR-0054; generator now pins the V38 source snapshot).
- Track the React Router high-severity advisory in a separate compatibility upgrade. Its
  primary advisory limits impact to unstable RSC APIs, which this BrowserRouter SPA does
  not use: <https://github.com/advisories/GHSA-qwww-vcr4-c8h2>.
- Keep accounts off until the compliance checklist is complete.
