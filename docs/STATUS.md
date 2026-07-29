# Status — cat_de_roman_esti

_As of 2026-07-30. This file is the repository's current source of truth._

_Last verified: 2026-07-30 (V42 plus stale lazy-route recovery: full backend suite,
web/static 18/18, derived-game 36/36, session store 16/16, frontend 28/28, lint, typecheck,
production build at 118.03/120 KiB, browser click-through, and `git diff --check` green)._

## Current outcome — V42 release (ADR-0062–ADR-0065)

- The six-game, tap-first lobby stays in its tested fun-first order: Alchimie → Intrusul →
  Perechi → Conexiuni → Cald sau Rece → Lanț. Mobile remains one card per row; wide screens
  balance the six cards in three columns.
- Alchimie offers help after two consecutive distinct barren experiments, appends only
  generic strategy after a longer dry history, and can request another board with the
  authoritative theme and difficulty. Experiment memory remains bounded at 496 pairs.
- Conexiuni offers at most two redacted, penalized clues after mistakes two and three. Cald
  sau Rece has seven temperature bands and asks before spending a confident non-target fuzzy
  correction. Lanț gives coarse direction on Ușor/Normal and retains one help stage counter,
  capped at three, across move/undo.
- Intrusul and Perechi explain their starter shelf before graduation and reveal clearer loss
  summaries only after terminal server state. Hidden answers and server-authored scores are
  unchanged.
- A browser tab kept open across a release reloads at most once when an obsolete lazy game
  chunk is requested. Missing `/assets/` hashes return 404 instead of the SPA HTML; current
  Intrusul and Perechi sessions, answers, scores, TTL, and caps are unchanged.
- A category-scoped curated daily now needs four selectable exact-shelf records; the shared
  daily still needs eight. Thin shelves mine inside the requested theme or return themed 503,
  never an off-theme board carrying the requested label.
- The browser keeps one bounded daily streak outside portable history. A zero-score daily
  completion counts; import cannot create or overwrite the streak. The 6/6 diploma is derived
  from the browser score document and only copies a share string.

## Content and ranking baseline (post ADR-0065/0066)

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 308 | 229 | 79 | 76 eligible |
| Cald sau Rece | 217 | 202 | 15 | 202 eligible |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 eligible |
| Alchimie | 99 | 78 | 21 | 78 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **825 = 603 approved + 222 pending**, across 14 categories. The ranked original-game
runtime serves **450 zero-FAIL boards** after the ADR-0066 owner wave (18 promotions; 67
structurally-killed boards demoted to never-selected reserves via
`board_demotions_v43.json`). Eleven Conexiuni shelves are empty and hidden pending the next
authoring wave (ADR-0066 lists them). The derived strict catalog stays at **336** boards
from the frozen V38 source snapshot (ADR-0054/0065; loader validates freeze-time semantics).
Bundled KG: **2,364 nodes / 9,219 edges / 7,440 aliases / 180 puzzles** (`fixture-v5-pop`).
V23–V33 vocabulary probes remain **322/322**.

The ADR-0023 gate ran end to end in V42 (Sonnet critique → adversarial Opus verify with live
Romanian web checks → orchestrator final judgment): **36 items promoted** (9+6 Contexto,
14+1 Alchimie, 6 Conexiuni) and **11 rejected**, including the authored wave of ADR-0065.
Each formerly empty Ușor Conexiuni shelf gained at least one eligible board; reaching the
eight-board daily-pool target additionally needs the owner's ADR-0019 call on the near-
duplicate-held boards listed in ADR-0065. Ranking scores remain editorial pre-playtest
estimates, not measured fun or knowledge.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode can upload validated completed-score rows privately but does not download,
  restore, or merge them. Public records remain server-authored and consent-gated.
- The canonical vendored `/v1` client remains generated from the producer and stamped by
  `scripts/sync_roedu_client.py`; never edit `_roedu_client_core.py` directly.
- Shared `main` and `origin/main` contain V42. The last recorded live probe (2026-07-23)
  reported V32 `fixture-v32-face-workshop-garden`; repository landing and production
  deployment remain separate operations.

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

- Author the next Conexiuni wave for the 11 empty shelves (ADR-0066) — the demoted
  clusters (Enescu, Caragiale, rivers/lakes, sport quads) need fresh, non-recycled boards.
- Deferred Lanț/Conexiuni pending-pool re-gate from fresh dossiers (ADR-0065).
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion (ADR-0054; generator now pins the V38 source snapshot).
- Keep accounts off until the compliance checklist is complete.
