# Status — cat_de_roman_esti

_As of 2026-08-01. This file is the repository's current source of truth._

_Last verified: 2026-08-01 (V48 backend 726/726, accounts 53/53, sessions 16/16,
frontend 28/28 + lint/typecheck/build at 118.03/120 KiB, all artifact validators, and
production runtime/public/log probes green on exact commit `d59caed`)._

## Current outcome — V48 strict Alchimie live-recipe gate (ADR-0072)

- Fresh exact dossiers cover all 21 formerly pending Alchimie records. The broad-graph
  critique found 0 FAILs and 3 salience WARNs, but source-bound simulation of the private
  sparse recipe books found seven boards with only one live opening.
- Two independent E1–E5 reviews produced one unanimous promotion (`Făt-Frumos`), 17
  fail-closed rejections, and three mandatory ADR-0019 alcohol holds. No quota overrode
  legibility; all removed source rows remain in the replayable V48 audit.
- Alchimie is 79 approved/selectable + 3 pending. Its 79 live projections stay bounded;
  declared and exact par agree. No alias, node, edge, KG content, or new board was added.
- V47 remains: Cald sau Rece has 205 approved / 2 pending / 202 selectable unique targets;
  `Mâncare` is served and `Shitpost`/`Industrie` remain A5 owner holds.
- V46 remains: Conexiuni has 232 approved / 74 selectable / 0 pending and a durable
  rejection ledger of 122 boards / 488 groups. V45 leaves Lanț at 94 selectable boards
  and three pending repair holds.
- V44's 71-node Cald sau Rece repair, 453-term projection, 12 aliases, and 11 non-winning
  projections remain unchanged. The frozen 336-board Intrusul/Perechi payload is unchanged.
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

ADR-0072's exact dossiers, deterministic report, live-projection audit, and two-reviewer
verdicts are under `docs/reviews/v48-alchimie-pending-gate/`; rankings remain estimates.

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
- Repair the three Lanț holds only after their named blocker changes, then generate fresh
  exact dossiers; add a generic Lanț rejection ledger before another large import.
- Resolve the two Cald sau Rece A5 holds explicitly. Repair Morcov, Familie, Farmacie,
  Ploaie, Frigider, or Creion only through a separately bound feedback change and fresh
  C1-C6 gate; never re-add the archived exact record unchanged.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion (ADR-0054; generator now pins the V38 source snapshot).
- Track the React Router high-severity advisory in a separate compatibility upgrade. Its
  primary advisory limits impact to unstable RSC APIs, which this BrowserRouter SPA does
  not use: <https://github.com/advisories/GHSA-qwww-vcr4-c8h2>.
- Keep accounts off until the compliance checklist is complete.
