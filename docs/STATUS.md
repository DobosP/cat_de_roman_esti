# Status — cat_de_roman_esti

_As of 2026-07-30. This file is the repository's current source of truth._

_Last verified: 2026-07-30 (V43: backend 679/679, accounts 53/53, session store
16/16, frontend 152/152, Ruff, ESLint, typecheck, production build at
118.03/120 KiB, rankings/derived/pack/KG validators, and `git diff --check` green)._

## Current outcome — V43 strict board release (ADR-0067)

- The Fable 5 replay audited all 67 original reserve boards and 268 groups, the full
  approved/pending inventory, every replacement, and both derived-game creation paths.
  Direct quad reuse is banned; rejected material remains digest-bound novelty debt.
- The release funnel used exact deterministic, factual, play-quality, and real-ID
  analyst/verifier gates with no shelf quota. Of 66 original proposals, only
  `cx_stiinta_356` remains selectable; the strict replacement rebuild shipped no new
  selected board.
- Eight more approved boards moved to the reserve sidecar. It now has 75 IDs; 43 rejected
  boards/172 groups live in durable tombstones. Ten empty Conexiuni shelves stay hidden.
- Invalid or unreadable derived catalogs now make Intrusul/Perechi return controlled
  Romanian 503 responses. Regenerated healthy catalogs serve normally; the frozen
  336-board payload stayed byte-identical.
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

## Content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 311 | 232 | 79 | 74 eligible |
| Cald sau Rece | 217 | 202 | 15 | 202 eligible |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 eligible |
| Alchimie | 99 | 78 | 21 | 78 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **828 = 606 approved + 222 pending**, across 14 categories. The ranked original-game
runtime serves **448 zero-FAIL boards**. The strict derived catalog remains **336** boards
from the frozen V38 source snapshot; its `boards` payload hash is
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
Bundled KG: **2,364 nodes / 9,217 edges / 7,440 aliases / 180 puzzles**
(`fixture-v42-pegas-colind-damigeana`).

ADR-0067 supersedes ADR-0023. The full evidence, exact rejection reasons, source links,
bindings, and closure census are in `docs/reviews/v43-release-board-rebuild.md` and
`v43-release-funnel.json`. Ranking scores remain editorial pre-playtest estimates, not
measured fun or knowledge.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode can upload validated completed-score rows privately but does not download,
  restore, or merge them. Public records remain server-authored and consent-gated.
- Repository landing and production deployment remain separate operations; the last
  recorded live probe (2026-07-23) reported V32 `fixture-v32-face-workshop-garden`.

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

- Any future Conexiuni authoring starts from the ten hidden shelves and the durable
  demotion/rejection evidence; never force a quota or reuse a banned quad.
- Deferred Lanț/Conexiuni pending-pool re-gate requires fresh exact dossiers.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion (ADR-0054; generator now pins the V38 source snapshot).
- Keep accounts off until the compliance checklist is complete.
