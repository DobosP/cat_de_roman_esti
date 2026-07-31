# Status — cat_de_roman_esti

_As of 2026-08-01. This file is the repository's current source of truth._

_Last verified: 2026-08-01 (V47 backend 717/717, accounts 53/53, sessions 16/16,
targeted Contexto 187/187, derived games 82/82, Ruff and all artifact validators green)._

## Current outcome — V47 strict Cald sau Rece target gate (ADR-0071)

- Fresh exact dossiers cover all 13 formerly pending Cald sau Rece records. Deterministic
  review found no failure and one Sonicitate salience warning; live C1-C6 gameplay and
  inventory review still rejected ten misleading or too-thin targets.
- `Mâncare` is the one unanimous promotion. `Shitpost` and `Industrie` remain unserved A5
  owner holds; Familie was rejected because core kin guesses are frozen while generic
  abstractions are hot. No common-word quota overrode the feedback-quality bar.
- Cald sau Rece is 205 approved / 2 pending / 202 selectable unique targets. The lexical
  review added nothing: existing forms cover Mâncare, and `ploaia` belongs to a served song.
- V46's Conexiuni cleanup remains: 232 approved / 74 selectable / 0 pending and a durable
  rejection ledger of 122 boards / 488 groups.
- V45's strict Lanț cleanup remains: 94 selectable boards and three pending repair holds.
- V44's 71-node Cald sau Rece feedback repair, 453-term projection, 12 aliases, 11
  non-winning projections, and two earlier promoted targets remain unchanged.
- V43's 75-board general reserve, 43 rejected boards/172 rejected groups, hidden weak
  shelves, and unanimous future gate remain in force. The frozen 336-board
  Intrusul/Perechi payload remains unchanged after metadata regeneration.
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

## Content and ranking baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 202 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 99 | 78 | 21 | 78 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack: **635 = 609 approved + 26 pending**, across 14 categories. The ranked original-game
runtime serves **448 zero-FAIL boards**. The strict derived catalog remains **336** boards
from the frozen V38 source snapshot; its `boards` payload hash is
`71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6`.
Bundled KG: **2,364 nodes / 9,217 edges / 7,452 aliases / 180 puzzles**
(`fixture-v44-contexto-common-words`).

ADR-0071's exact dossiers, report, verdicts, and audit are under
`docs/reviews/v47-contexto-pending-gate/`; ranking scores remain pre-playtest estimates.

## Runtime, accounts, and deployment

- Sessions keep the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry locks,
  64 KiB request ceiling, deterministic seeded/daily selection, and server-private answers.
- Browser history, records, derived mastery, circuit, and streak remain device-authored.
  Account mode can upload validated completed-score rows privately but does not download,
  restore, or merge them. Public records remain server-authored and consent-gated.
- Anonymous production runs V43 at `38da2f4`; its 2026-07-30 six-game live probes passed.

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

- Any future Conexiuni authoring starts materially fresh from the ten hidden shelves and
  the durable demotion/rejection evidence; never force a quota or reuse a banned quad.
- Repair the three Lanț holds only after their named blocker changes, then generate fresh
  exact dossiers; add a generic Lanț rejection ledger before another large import.
- Resolve the two Cald sau Rece A5 holds explicitly. Repair Morcov, Familie, Farmacie,
  Ploaie, Frigider, or Creion only through a separately bound feedback change and fresh
  C1-C6 gate; never re-add the archived exact record unchanged.
- Re-gate the remaining 21 Alchimie pending records with fresh exact evidence.
- Run the larger anonymous six-game pilot before a seventh mode, score recalibration, or
  derived-catalog expansion (ADR-0054; generator now pins the V38 source snapshot).
- Keep accounts off until the compliance checklist is complete.
