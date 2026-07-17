# Status — cat_de_roman_esti

_As of 2026-07-17. This file is the repository's current source of truth._
_Last verified: 2026-07-17 (local v25 gate: backend 345; session-store 11; semantic/alias quality 9; exact critique 33; Ruff; both validators; mobile rollback transaction; workflow syntax; `git diff --check`. Production remains release `2746be3`, smoke-verified 2026-07-16.)_

## Current outcome — critique gate completed (ADR-0023 through ADR-0026)

The critique layer now fails closed from generation through promotion:

- `critique_pack.py` validates explicit IDs, cross-board reuse, projected member overuse, and directed Contexto dossiers with live degree.
- Gate mode verifies every item adversarially; only clean approved-stock sweeps may sample 1-in-4, and returned IDs must match requested IDs.
- Lanț and Alchimie have explicit branch/craft judge criteria; all four games have game-specific review.
- Version-2 artifacts bind the exact batch, dossiers, and rubric; apply rebuilds and reruns them before writing.
- Re-review/demotion validates identity and verdict, restoring both pack copies on any red or exception.
- Imports enter `pending`; persistent per-game high-water marks prevent retired ID reuse.

## Current outcome — browser recovery (ADR-0027 through ADR-0029)

Lanț renders server-authored recovery in a polite status; bounded spelling and path
choices fill but never submit. Conexiuni retains nonterminal one-away selections for
one-tile swaps and blocks the unchanged set without inferring hidden membership.
Cald sau Rece renders target-filtered typo suggestions as fill-only buttons and preserves
accepted correction messages, including wins. All three remain server-authoritative;
score, secrecy, TTL, and the 1,000-session caps are unchanged.

## Current outcome — beginner mobile interface (ADR-0031)

All four games now default to `Ușor`, teach their loop with three terse actions, and show
one live `ACUM` cue instead of repeating rules. Mobile gets 44 px targets, scrollable
status/theme rails, readable long labels, reachable primary actions, visible rank meaning,
and safe keyboard shortcuts; desktop retains the same focused play column.

## Current outcome — beginner vocabulary waves (ADR-0030, ADR-0032, ADR-0033)

V23 retains 22 childhood/story nodes, 78 owned edges, and seven pending items. V24 adds
**150 everyday nodes, 511 edges, 276 aliases, and 26 pending items**: four Conexiuni,
eight Cald sau Rece, eight Lanț, and six Alchimie. V25 adds **168 collision-safe aliases
and 25 concrete semantic links** without new boards or nodes. Exact intended resolution is
**219/234 (93.6%)**; all 33 affected pending dossiers are deterministically clean and all
572 approved records remain unchanged. No new boards are served before bound review;
the alias and semantic-link corrections apply to the existing graph immediately.

## Product and deployment

The Romanian arcade has four server-authoritative games: Alchimie, Cald sau Rece, Lanțul
Cuvintelor, and Conexiuni, using Django 5.2/DRF and React 19/Vite 8 over the offline KG.

Anonymous v1 at <https://cat-de-roman-esti.dobolabs.ro> runs release `2746be3`, deployed
and smoke-verified on 2026-07-16. Accounts/rankings remain staging-only: scores are
client-authored and visibility needs opt-in by default.

## Shipped content

| Game | Total | Approved | Pending | Runtime source |
|---|---:|---:|---:|---|
| Conexiuni | 288 | 209 | 79 | curated first; mixed-board miner fallback |
| Cald sau Rece | 207 | 192 | 15 | curated first; category miner fallback |
| Lanțul Cuvintelor | 201 | 94 | 107 | curated first; branch-aware miner fallback |
| Alchimie | 98 | 77 | 21 | curated first; category closure fallback |

Pack: **794 items = 572 approved + 222 pending**, across 14 categories.
Bundled KG: **2,184 nodes / 8,792 edges / 7,033 aliases / 180 legacy puzzles**.
Both fixture copies and both pack copies are byte-identical and validator-green.

## Runtime contracts and safety

- Sessions use a validated two-hour sliding TTL and 1,000-entry LRU cap per game; cleanup
  is lazy, lock-protected, monotonic, and deterministic.
- Request bodies default to a 64 KiB Caddy plus ASGI receive ceiling.
- Hidden-answer boundaries remain pinned: Contexto hides its target until terminal;
  Alchimie hides target ID; Lanț reveals played/hinted hops; Conexiuni withholds unsolved
  membership and the full solution until terminal.
- Curated submissions are opt-in through `CAT_SUBMISSIONS_DIR`; only approved records
  are served. Import candidates remain pending until the critique gate promotes them.
- Mobile fixture/OpenAPI contracts and curated-first seeded selection remain test-pinned.

## Quality gate

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/ruff check .
PYTHONPATH=. .venv/bin/python scripts/validate_games_pack.py
PYTHONPATH=. .venv/bin/python scripts/validate_fixture.py
node --check .claude/workflows/critique-games.js
git diff --check
```

Run frontend lint/typecheck/test/build only when frontend files change. The shared
session-store target remains `tests/test_wordgames_session_store.py` (11 tests).

## Next verified work

- Playtest the beginner UI at 320–390 px and Lanț recovery; measure first action, invalid
  moves, hint reuse, undo, completion, and abandonment.
- Run bound subjective review over the exact 33 v23/v24 pending IDs; inspect Contexto
  ordering after v25, route meaning, Conexiuni predicates, and Alchimie recipe intuition.
- Work the approved-stock critique/A7 queues; generic regional KG edges remain a cleanup
  inventory, while owner demotions stay explicit proposals.
- Make ranking scores server-authored, bound retained score history, and default ranking
  visibility off before enabling public accounts.
