# V40 pilot-readiness refinement

V40 closes three bounded risks found while auditing the V39 six-game candidate. The
governing records are [ADR-0055](adr/0055-pilot-only-ranked-selection.md),
[ADR-0056](adr/0056-sticky-parental-consent-holds.md), and
[ADR-0057](adr/0057-actionable-local-daily-circuit.md).

## Player-facing changes

| Area | V40 behavior |
|---|---|
| Original games | A ranked bundled pack serves only zero-FAIL pilot boards |
| Repeat exhaustion | A safe eligible board repeats instead of exposing a known failed reserve |
| Daily circuit | Every unfinished row opens that game's intro with `Joacă →` |
| Completed daily | The retained score stays a non-action status row |
| Under-age account | Adult-year resubmission cannot clear the parental hold |

## Content boundary

The ranked original-game inventory remains 794 authored records and 572 approved records,
but runtime selection is bounded to the 486 `pilot_eligible` boards:

| Game | Approved | Runtime eligible | Known failed reserve |
|---|---:|---:|---:|
| Conexiuni | 209 | 123 | 86 |
| Cald sau Rece | 192 | 192 | 0 |
| Lanțul Cuvintelor | 94 | 94 | 0 |
| Alchimie | 77 | 77 | 0 |

Game/category/difficulty filters remain exact. Finished IDs are avoided while a new eligible
board remains; after shelf exhaustion, selection repeats only within that eligible shelf.
Shared dailies still require eight eligible boards and explicit categories require one.
Custom packs without a matching sidecar retain their neutral historical behavior.

The 336 Intrusul/Perechi boards are unchanged and remain bound to pilot-clean source boards.

## Account and interface boundary

Consent and ranking-profile writes now acquire the same database row lock. A stored minor
hold survives adult-year resubmission, creates no consent records, and continues to block
private score storage and ranking visibility. Profile writes update only nickname/visibility
fields, preventing stale consent state from being replayed.

The Home circuit still reads only the existing browser score document. Its unfinished rows
are native buttons to the existing game intro; completed rows stay status-only. It does not
start a session, call an API, or upload daily state.

## Reproduction

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest tests/test_wordgames_session_store.py -q
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
cd frontend && npm test && npm run lint && npm run build
```

The V40 candidate gate is 553 default backend tests, 53 accounts-on tests, 16 session-store
tests, and 21 frontend test files. The initial JS/CSS transfer is 119.15 KiB gzip against the
120 KiB limit. Deterministic ranking/catalog checks, migration dry-run, workflow syntax,
tracked bundle reproduction, and wheel contents are green.
