# V42 fun and clarity refinement

V42 makes all six pilot games easier to understand when a player is stuck, without widening
their hidden answer space. The governing decisions are
[ADR-0062](adr/0062-bounded-recovery-and-player-state-clarity.md),
[ADR-0063](adr/0063-four-board-category-daily-floor.md), and
[ADR-0064](adr/0064-device-local-daily-streak-and-derived-diploma.md).

## Player-facing changes

| Area | V42 behavior |
|---|---|
| Alchimie | Hint after two consecutive distinct barren experiments; later dead pairs get a short generic strategy line; `Alt joc` keeps the server-echoed theme and difficulty |
| Conexiuni | Up to two redacted clues at mistakes two and three; the disabled mobile action shows its unlock countdown |
| Cald sau Rece | A seventh, `Foarte rece`, band separates far from frozen; fuzzy non-target corrections ask before costing an attempt; rank help is one tap |
| Lanț | Coarse direction also plays on Normal; three help stages persist through moves/undo; a short rules disclosure explains detours and free undo |
| Intrusul / Perechi | Starter status is visible before graduation; a loss names the terminal answer and earned progress only after the server reveals it |
| Home | Same-device daily streak, a 6/6 diploma/share moment, clearer Romanian range, and a balanced mobile/desktop six-card grid |

## Recovery and secrecy

An Alchimie repeated pair remains free and advances no counter. Consecutive distinct barren
combines unlock the paid hint after two; after four total barren combines, only a
deterministic, generic strategy sentence is added. It never names a recipe, output, or
target.

Conexiuni keeps both clues as label patterns. Each uses the existing 100-point penalty. A
clue payload contains no category key, exact label, tile IDs, or membership. The second clue
advances deterministically to another unsolved category when possible.

Contexto exact labels, aliases, and diacritic-insensitive matches still play immediately. A
confident non-target fuzzy interpretation returns `ok: false` with a game-bound opaque handle
and no attempt mutation. Echoing the handle accepts it; a stale handle asks again. A fuzzy
target remains a legitimate direct win and cannot leak in a non-win response.

Lanț sends automatic coarse progress only on Ușor and Normal; Greu omits that object but
keeps voluntary help and automatic dead-end recovery. The help stage is one capped session
scalar, but its direction/alternatives/hop content is recomputed at the current node. The
two-move recommended-undo highlight remains Ușor-only.

## Category daily boundary

The unscoped curated daily still needs eight records. An explicit category daily now needs
four records inside the exact game/category/difficulty shelf. Ranked inventory counts only
pilot-eligible records. A thinner shelf returns no curated record: Alchimie, Contexto, and
Lanț mine deterministically inside the requested theme; Conexiuni returns its themed 503.
The server never borrows an unscoped record while echoing the requested category.

## Local motivation boundary

One valid daily completion, including a zero-score loss, advances the same-device streak at
most once per day. Consecutive days increment it; a gap restarts it. The `_streak` record is
bounded, excluded from export and account upload, preserved across history import, and
removed with local history.

The diploma is not stored. It renders when the current browser score document has all six
daily rows and its share action only copies text. A manual score-history import can
reconstruct 6/6 because daily rows are intentionally portable; there is still no automatic
account restore, aggregate upload, telemetry event, or diploma API.

## Content gate

V42 does not change the shipped pack, KG, or catalog counts. A deterministic audit found nine
existing pending beginner candidates with zero local critique failures, but ADR-0023/0025
also require independent external analyst/verifier artifacts before promotion. That review
needs separate authorization to send the private dossiers to its configured service, so the
pack remains fail-closed rather than claiming unreviewed quantity growth.

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
```

The exact measured gate and bundle size are recorded in `docs/STATUS.md`.
