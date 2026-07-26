# Status — cat_de_roman_esti

_As of 2026-07-26. This file is the repository's current source of truth._

**Client (2026-07-25):** `cat_de_roman_esti/roedu_client.py` is now a thin re-export of
`_roedu_client_core.py`, a generated, stamped copy of the canonical `/v1` client the producer
owns (romania_scraper ADR-0069, `scripts/sync_roedu_client.py`; local ADR-0060). Never edit
`_roedu_client_core.py` here — edit the canonical file and re-run the sync script;
`tests/test_roedu_client_vendored.py` fails on a local edit via the `VENDORED_SHA256` stamp.
Adopting it **fixed a real defect**: this app's private `iter()` had no repeated-cursor guard,
so a server echoing one cursor looped forever. Iteration now raises `RoeduContractError`.
The public import path (`from cat_de_roman_esti.roedu_client import RoeduClient`) is unchanged.
_Last verified: 2026-07-26 (V38-V41 chain landed on top of the vendored-client adoption; backend 560/560, frontend 114/114. Baseline before this merge was backend 482/482. The V40 line this replaced read: _As of 2026-07-24. This file is the repository's current source of truth._ _Last verified: 2026-07-24 (V40: backend 553, accounts 53, frontend 21, session store 16; lint/build/content/migration/wheel green, bundle 119.15/120 KiB; live V32, V38–V40 local.)_)_

## Current outcome — local V40 release candidate (ADR-0055–ADR-0057)

- The six-game, tap-first lobby remains in fun-first order: Alchimie → Intrusul → Perechi →
  Conexiuni → Cald sau Rece → Lanț. A seventh mode still waits for player evidence.
- The digest-ranked bundled runtime now serves only its **486 zero-FAIL pilot boards**:
  Conexiuni 123, Cald sau Rece 192, Lanț 94, and Alchimie 77. Its 86 approved
  non-eligible Conexiuni reserves are never selected.
- Game/category/difficulty filters remain exact. Finished eligible IDs are avoided while a
  new one remains, then selection repeats only inside the safe shelf. Daily floors apply to
  eligible stock; zero/thin shelves use the existing mined fallback or themed 503. A custom
  pack without a matching sidecar keeps neutral historical selection.
- Intrusul and Perechi remain strict catalog-only games over **336 boards**: 183 from 66
  sources and 153 from 51. Runtime prefers standard-score ≥55 boards (144/113) and falls
  back only inside the same pilot-clean filtered catalog.
- Home's local-only daily circuit keeps zero-score completion and a bounded 0–6,000 total.
  An unfinished 44 px row now opens that game's intro with `Joacă →`; a completed row stays
  status-only. No daily aggregate, board identity, action trail, API call, or telemetry exists.
- Accounts-on staging keeps server-verified per-game records. An under-age hold is sticky:
  adult-year resubmission cannot clear it, create consent, save scores, or enable ranking.
  Consent/profile writers share a row lock and profile edits update only intended fields.
- Public rows still require current consent, an explicit nickname, and opt-in; ties use
  competition ranks and a bounded personal row can sit below the top 50. Browser-authored
  history remains private and cannot feed public ranking.

## Retained beginner play and vocabulary

- Every original game defaults to `Ușor`, teaches three terse actions, shows one live `ACUM`
  cue, and keeps mobile actions at least 44 px. Conexiuni centralizes recovery feedback;
  Lanț has direction, free undo, and a 64-hop cap; Alchimie remembers at most 496
  experiments and projects at most 24 useful pairs.
- Derived starters balance category → source → variant and persist until a non-daily win or
  three non-daily completions. Daily play does not graduate them. Free replay retains one
  opaque session ID per derived game, never content or answers.
- Cald sau Rece accepts **444 screened guesses across 26 domains** through 89 KG anchors.
  Targets, hidden routes, and recipes stay private in all games.
- V23–V33 vocabulary probes remain **322/322**. All 794 curated records pass envelope/schema
  validation and all 572 approved records pass playability validation. Rankings remain
  editorial pre-playtest estimates, not measured fun or Romanian-knowledge ratings.

## Product and deployment

The arcade uses Django 5.2/DRF and React 19/Vite 8 over the offline KG. On 2026-07-23,
<https://cat-de-roman-esti.dobolabs.ro/api/manifest> still reported
`fixture-v32-face-workshop-garden` and four live games. Shared `main` remains V37 `18400f9`;
V38–V40 and accounts/player rankings remain local only.

## Content baseline

| Game | Total | Approved | Pending | Runtime eligible/preferred | Runtime source |
|---|---:|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | 123 eligible | pilot-only curated; mixed-board miner |
| Cald sau Rece | 207 | 192 | 15 | 192 eligible | pilot-only curated; category miner |
| Lanțul Cuvintelor | 201 | 94 | 107 | 94 eligible | pilot-only curated; branch-aware miner |
| Alchimie | 98 | 77 | 21 | 77 eligible | pilot-only curated; sparse miner |
| Intrusul | 183 | 183 | 0 | 144 preferred | strict derived catalog only |
| Perechi | 153 | 153 | 0 | 113 preferred | strict derived catalog only |

Pack: **794 = 572 approved + 222 pending**, across 14 categories. Bundled KG:
**2,287 nodes / 9,122 edges / 7,400 aliases / 180 puzzles**; all mirrors are byte-identical.

## Runtime contracts and quality gate

- Sessions retain the validated 7,200-second sliding TTL and 1,000-entry per-game LRU cap.
  Per-entry locks serialize one session; all-borrowed capacity returns 503. Request bodies
  retain the 64 KiB Caddy and ASGI ceiling.
- Account history is capped at 500 rows per user; public records are capped at one for each
  of the exact six game keys. Current consent is checked under the shared profile lock.
- Curated submissions require `CAT_SUBMISSIONS_DIR`; hidden answers remain server-private.
  Mobile fixture/OpenAPI contracts and deterministic seeded/daily selection stay pinned.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
CAT_ACCOUNTS_ENABLED=1 CAT_DEBUG=1 PYTHONPATH=. .venv/bin/python -m pytest tests/accounts -q
PYTHONPATH=. .venv/bin/python scripts/build_derived_catalog_v38.py
PYTHONPATH=. .venv/bin/python scripts/rank_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
node --check .claude/workflows/critique-games.js
git diff --check
```

Frontend: **21/21**, lint/build green, **119.15 KiB**. Session-store target: **16/16**.

## Next verified work

- Run a larger anonymous six-game pilot before adding a seventh game or changing scores.
- Merge/deploy V38–V40 only on explicit instruction. Keep accounts off until the compliance
  checklist is complete; analytics still requires a separate privacy/retention decision.
