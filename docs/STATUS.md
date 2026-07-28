# Status — cat_de_roman_esti

_As of 2026-07-29. This file is the repository's current source of truth._

_Last verified: 2026-07-29 (V42 main landing: backend 577/577, accounts 53/53,
frontend 27/27, session store 16/16; Ruff/lint/typecheck/build/wheel/content/fixture gates
green; initial JS/CSS 117.81/120 KiB)._

## Current outcome — V42 on main (ADR-0062–ADR-0064)

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
- A category-scoped curated daily now needs four selectable exact-shelf records; the shared
  daily still needs eight. Thin shelves mine inside the requested theme or return themed 503,
  never an off-theme board carrying the requested label.
- The browser keeps one bounded daily streak outside portable history. A zero-score daily
  completion counts; import cannot create or overwrite the streak. The 6/6 diploma is derived
  from the browser score document and only copies a share string.

## Content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 288 | 209 | 79 | 123 eligible |
| Cald sau Rece | 207 | 192 | 15 | 192 eligible |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 eligible |
| Alchimie | 98 | 77 | 21 | 77 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **794 = 572 approved + 222 pending**, across 14 categories. The ranked original-game
runtime serves **486 zero-FAIL pilot boards**; the derived strict catalog contains **336**
boards. Bundled KG: **2,287 nodes / 9,122 edges / 7,400 aliases / 180 puzzles**. V23–V33
vocabulary probes remain **322/322**.

Nine pending beginner candidates passed the deterministic local critique with zero failures,
but promotion remains blocked until ADR-0023/0025's independent analyst/verifier review is
authorized. No pack, ranking sidecar, fixture, KG, catalog, or board count changes in V42.
Ranking scores remain editorial pre-playtest estimates, not measured fun or knowledge.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode can upload validated completed-score rows privately but does not download,
  restore, or merge them. Public records remain server-authored and consent-gated.
- The canonical vendored `/v1` client remains generated from the producer and stamped by
  `scripts/sync_roedu_client.py`; never edit `_roedu_client_core.py` directly.
- V42 is the current canonical `main` release. The landing reproduced candidate-tree identity,
  26 focused backend integration passes, the required 16-session suite, all 27 frontend test
  files, Ruff, and the bundle gate. The last live probe (2026-07-23) reported V32
  `fixture-v32-face-workshop-garden`; landing source does not deploy production.

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

- Obtain explicit authorization for the independent nine-candidate content review, then
  promote only if both artifacts and regenerated sidecars stay green.
- Run the larger anonymous six-game pilot before a seventh mode or score recalibration.
- Deploy V42 only on explicit instruction; keep accounts off until the compliance checklist
  is complete.
