# V41 beginner-path and account-truth refinement

V41 removes two small mobile dead ends and corrects the account-history promise without
adding a game or widening content selection. The governing records are
[ADR-0058](adr/0058-difficulty-aware-playable-category-availability.md),
[ADR-0059](adr/0059-recoverable-ranking-states.md), and
[ADR-0060](adr/0060-device-local-progress-and-upload-only-private-backup.md).

## Player-facing changes

| Area | V41 behavior |
|---|---|
| Category choice | Chips match the selected game's exact difficulty |
| Difficulty change | An invalid selected theme clears silently; `Toate temele` remains |
| Ranking load | A centered live status announces progress |
| Ranking unavailable | Accounts-off 404 offers `Acasă →` |
| Ranking outage | A transient failure offers `Reîncearcă` for the same game |
| Account gate | Short copy says progress stays on the device and completed scores upload privately |

## Availability and content boundary

`/api/categories` now separates raw approved inventory from runtime playability. The
additive `available_by_difficulty.<game>.<difficulty>` matrix follows the active ranked
pack's `pilot_eligible` boundary. The older `available` field remains the any-difficulty
summary; Contexto, Lanț, and Alchimie retain their existing category node-floor mining
proxy.

At `Ușor`, Conexiuni no longer offers Gastronomie, Geografie, Știință, or Viața în România:
their approved records are known failed reserves and their safe ranked shelves are empty.
Direct explicit API requests keep the themed 503. No board is promoted, retiered, or made
eligible, so the 486-board original-game pilot inventory and the 336-board derived catalog
do not move.

The audit found two high-familiarity zero-FAIL pending boards, but either would create a
one-board shelf that repeats indefinitely. A later content wave should independently review
at least four boards per empty shelf for useful free-play variety; eight remains the shared
daily-pool target.

## Ranking and account boundary

Each ranking request clears stale rows before loading. Loading is a polite live status;
failures become an alert with one 44-pixel-or-larger action. Retry retains the selected
game. Ranking endpoints, verified-score authorship, public fields, consent, nickname,
visibility, and telemetry are unchanged.

The browser score document remains the source of truth for displayed history, records,
derived mastery, and the local daily circuit. With current consent and no parental hold,
the frontend can upload retained completed-score rows to a private `ScoreEntry` account
copy capped at 500. It does not download, restore, or merge that copy into another browser.
`PlayedPuzzle` repeat avoidance and server-authored `VerifiedBest` ranking rows remain
separate from both stores.

Automatic merging is deferred until account-scoped local storage, account-switch handling,
conflict rules, and strict isolation from daily/mastery state have a separate decision and
test contract.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
cd frontend && npm test && npm run lint && npm run typecheck && npm run build
```

The final measured gate and bundle size are recorded in `docs/STATUS.md`.
