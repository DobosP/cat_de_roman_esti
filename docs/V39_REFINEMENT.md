# V39 six-game refinement

V39 refines the V38 six-game candidate without adding another mechanic. Its original
governing decisions were
[ADR-0053](adr/0053-verified-player-records-and-local-circuit.md), since superseded by
[ADR-0061](adr/0061-device-local-progress-and-upload-only-private-backup.md), and
[ADR-0054](adr/0054-refine-derived-pilot-before-expansion.md). The derived-catalog generation
and privacy boundary remain documented in [V38_DERIVED_GAMES.md](V38_DERIVED_GAMES.md).

## Player-facing changes

| Area | V39 behavior |
|---|---|
| Home | Compact local `Circuitul de azi`, `X/6`, best-per-game total, and `Azi ✓` cards |
| First play | Intrusul/Perechi starter shelf until one non-daily win or three completions |
| Free replay | Last completed non-daily Intrusul/Perechi session survives Home and reload |
| Intrusul | No inherited source-level badge; daily result offers `Joacă liber →` |
| Perechi | Solved tiles leave the active grid; solved stack and keyboard focus remain |
| Ranking | One selected game's verified 0–1,000 record; ties and a bounded personal row |

The circuit reads the existing browser score document only. A zero-score retained daily run
counts as complete. Each contribution is clamped to 0–1,000 and the six-game total to 6,000.
The circuit has no API, upload, model, telemetry, or public streak.

## Derived selection and continuity

The strict V38 catalog remains 183 Intrusul and 153 Perechi boards. Runtime filtering runs
before preference:

1. category, difficulty, repeat history, and starter state;
2. private standard-score preference at 55 or above;
3. strict filtered-shelf fallback only when the preferred shelf is empty.

An unscoped starter then balances category → source → variant. Explicit category play never
widens. Daily selection stays deterministic and does not alter the four V37 schedules.

The separate `cat_derived_replay_v1` browser document holds at most one opaque session ID
per derived game. It accepts no controls and no value longer than 128 characters. It contains
no source, catalog, board, score, rank, or answer field and is never consulted by daily play.
Expired sessions simply start without previous-source continuity.

Mastery remains in the bounded score document as a maximum-three completion counter plus a
monotonic non-daily-win flag. Import takes the maximum counter and logical OR, preventing an
older export from returning a graduated player to the starter shelf.

## Account and ranking boundary

`ScoreEntry` is a consent-gated, upload-only private backup of completed-score rows,
validated and pruned to the 500 newest server arrivals. The browser score document remains
the source of truth; the frontend does not download, restore, or merge account rows.
`ScoreEntry` never feeds the public ranking. `VerifiedBest` contains only user, exact game
key, a server-authored 0–1,000 best score, and update time; uniqueness limits it to six rows
per user.

Public visibility requires all of:

- current consent with no parental-consent hold;
- an explicit nickname unrelated to the Google fallback identity;
- explicit ranking opt-in;
- a terminal server-scored play for the selected game.

Public responses contain nickname, score, competition rank, and `is_me`. Board IDs, answers,
daily/category/difficulty fields, action trails, and private editorial ranks are absent.
Accounts remain disabled in the anonymous deployment profile.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
cd frontend
npm test
npm run lint
npm run build
```

The V39 candidate gate is 548 default backend tests, 52 accounts-on tests, 16 session-store
tests, and 21 frontend test files. The canonical initial JS/CSS transfer is 119.01 KiB gzip
against the 120 KiB limit.
