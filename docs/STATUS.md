# Status — cat_de_roman_esti

_As of 2026-07-10. Update whenever `main` or the test baseline moves._
_Last verified: 2026-07-10 (v13: full 235-test pytest suite + ruff +
`validate_games_pack.py` + `validate_fixture.py` green; frontend test/build/lint green.)_

## Latest — v13 play-loop foundation

Ordinary no-category starts now use the reviewed curated pack in all four games. This
fixes a routing gap that made default play bypass all 642 v12-approved instances.
Selection is seeded and deterministic; signed-in avoid-repeats applies; the existing
bounded miner remains the fallback when a matching curated pool is empty. Daily
rendezvous hashing and explicit category filters are unchanged (ADR-0011).

Conexiuni now exposes an authored label and four tiles only after that group is solved,
so correct groups persist as colored locked rows while every unsolved group stays hidden.
Re-submitting the same unordered four-tile set returns 409 without consuming a life or
advancing the clue. The SPA applies the authoritative guess response directly instead of
issuing a follow-up GET. ADR-0014 supersedes ADR-0010's terminal-only solved-group rule.

## Product phase

**v1.3 — Romanian text word-game arcade over an offline knowledge graph.** The web
product has four server-authoritative games: Alchimie (category-scoped Infinite Craft),
Cald sau Rece (Contexto-style ranked proximity), Lanțul Cuvintelor (semantic word
ladder), and Conexiuni (four authored groups). Each supports difficulty, seeded daily
play, score/share output, categories, and bounded local history. The old graph SPA was
removed; no graph UI unless the owner reopens ADR-0001.

Backend: Django 5.2 + DRF, stateless by default, WhiteNoise SPA serving, uvicorn ASGI.
Frontend: React 18 + Vite + TypeScript, shared game shell/HUD/result components,
animations and Web-Audio feedback. Optional accounts add Google sign-in, saved completed
puzzle ids, public ranking handles, leaderboard scores, and donations.

## Shipped content

| Game | Approved | Pending | Runtime source |
|---|---:|---:|---|
| Conexiuni | 195 | 90 | curated first; mixed-board miner fallback only |
| Cald sau Rece | 185 | 4 | curated first; category-scoped miner fallback |
| Lanțul Cuvintelor | 187 | 8 | curated first; branch-aware miner fallback |
| Alchimie | 75 | 16 | curated first; category-scoped closure fallback |

Pack total: **760 instances = 642 approved + 118 pending**, across 14 categories.
Bundled KG: **1,459 nodes / 5,656 edges / 4,688 aliases / 180 legacy puzzles**;
both fixture copies and both pack copies are byte-identical. V12 removed 101 duplicates
or broken games, adversarially rechecked high-stakes verdicts, then v12.1 completed
difficulty, member, label, description, and Romanian-diacritics fixes. Its dated handoff
is expired history.

The curated fixture path is the delivered content source. The `romania_scraper →
ro_data_server` corpus path remains blocked by restricted processed-data access; live
pull stays optional and fail-soft. `kg_puzzles` powers only the legacy terminal HopGame.

## Runtime contracts and safety

- Sessions use a 6-hour sliding TTL and a 10,000-entry LRU cap **per game**. Cleanup is
  lazy, lock-protected, monotonic-clock based, and deterministic under injected clocks.
- Contexto withholds target id/label/description until win or give-up. Alchimie withholds
  target id until crafted. Lanț reveals only played/hinted hops. Conexiuni reveals solved
  groups as earned but withholds all unsolved membership and full solution until terminal.
- Conexiuni clues remain one redacted label pattern after two distinct mistakes. Contexto
  exposes one broad category clue after three counted guesses. Both retain score penalties.
- `GET /api/manifest`, stable OpenAPI operationIds, the public mobile app-pack fixture,
  and hidden-answer boundaries are pinned by `docs/MOBILE_CONTRACT.md` and tests.
- Curated submissions remain opt-in through `CAT_SUBMISSIONS_DIR`; only approved records
  are served. Validators reuse the same runtime playability functions as the server.

## Quality gate

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
cd frontend && npm test && npm run build && npm run lint
git diff --check
```

The shared session-only command remains:
`PYTHONPATH=. /home/dobo/work/romania_scraper/.venv/bin/python -m pytest
tests/test_wordgames_session_store.py -q` (10 passed). Do not commit generated SPA assets.

## Verified v13 follow-up candidates

These are audit findings, not accepted decisions:

- Repair the v11 enrichment tail: 183 nodes currently have non-distractor degree ≤2
  (157 are `n_v11*`), below the play-density direction in ADR-0012.
- Close curated/mined mechanics drift before expanding content: 98/187 approved Lanț
  pairs miss the miner's branch-width floor; Alchimie's stored closure generation is not
  always the true minimum action count; category-scoped importer depth needs its missing
  category argument restored.
- Improve Contexto's compressed BFS feedback (approved targets have only 6–9 non-win
  distance buckets) without weakening its target reveal boundary.
- Build the visible replay loop: home daily progress, consistent same-filter replay, and
  Romanian-first onboarding/mobile copy. Remove stale hard-coded content counts in README/UI.
