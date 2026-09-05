# Status — cat_de_roman_esti

Last verified: 2026-09-06 — saved-game resume refactor; frontend gates re-run on this host. Production smokes last run 2026-08-27, not re-run.

## Current state

- Product line: six-game arcade (Django BFF + React SPA) + terminal CLI, served offline from
  `cat_de_roman_esti/fixtures/kg_sample.json`, build `fixture-v72-romanian-dishes-and-pastries-morphology`:
  2,364 nodes / 9,217 edges / 8,450 aliases / 180 puzzles (verified against the fixture `meta.counts` 2026-09-05).
- `kg_real.json` is a thin real-corpus export (932 nodes / 135 edges / 13 puzzles, no aliases) — **not** the served
  build; pointing `CAT_KG_FIXTURE` at it silently empties every curated category (data.py:27,34-36).
- Landed: V72 fast-forwarded on `main` at `6ee8693`; the rollout record `02dba24` is also on `main`. Actions runs
  `33023808156`/`33024392655` green on Python 3.12/3.14 + frontend.
- Newest decision: ADR-0100 extracts the six saved-game resume flows without changing their distinct
  terminal/error policies; ADR-0097 remains the newest vocabulary/build decision.
- V72 wave: 50 unanimously reviewed genitive/dative aliases for 25 gastronomie owners, zero rejections; the V71
  actionable-fuzzy deny set stays exactly `intrigii`, `intrigilor`; the 70-term nonaccepted ledger is unchanged.
  Evidence: `docs/reviews/v72-romanian-dishes-and-pastries-morphology/README.md`.

## Inventory and runtime invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 201 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories; original
ranking remains 448 eligible, Contexto 201 eligible, and derived payload 336 boards.
V51–V72 reviewed inventories retain their owners; V49 retains 104 Lanț rejections.
Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game cap, per-entry locks,
64 KiB request ceiling, deterministic selection, and server-private answers.

## Artifact pins (V72)

Build: fixture-v72-romanian-dishes-and-pastries-morphology; KG:
fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106;
pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed;
ranking: 45dfd81444dec14b4b639122fe30dea58f05ca76440003eb5280cc01bfcdc3e9;
derived: 8cff438c25deb5084c0311e808941bfef23e3c7bdbf93242a7a53348a6d2ef57;
mobile: 4c01361f94adbc50677bb63b5463063e38ccf2783b4627befc7c2c13d33a9e8e;
server manifest content: sha256:6a388f9bdb391ffca61ce4d51ab28255c00ed619142ded51cedd26c02bb9213d;
ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
Protected payload pins remain: nodes without aliases
c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0;
edges f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0;
puzzles 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc;
ranking rows faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031;
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6;
mobile public content sha256:9e93479d2e417346dfabe7da8e5ffdc9078a0f75add14f11fc8cfc5ef87727ab.

## Production

- Anonymous production was upgraded from V68 `60c3fd5318a` to exact V72
  `6ee86935038744c0066cac6a50865f76eab93e37` on 2026-08-27. The healthy app image is
  sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd,
  tagged release-6ee869350387, with zero restarts and zero error-log markers.
- `rollback-60c3fd5318a` preserves the prior V68 image sha256:7a9b6dbc5832; older V65/V61
  rollbacks remain retained. Caddy kept the same container/image and zero restarts.
- Production checkout is clean; accounts/debug are off; submissions return 503. No
  database, OAuth, worker, environment, DNS, TLS, Caddy, or infrastructure change occurred.
- Health, healthz, me, all 14 categories, Intrusul/Perechi, exact UI assets, and a V72
  Contexto alias smoke are green. Production reports the V72 manifest hash
  sha256:6a388f9bdb391ffca61ce4d51ab28255c00ed619142ded51cedd26c02bb9213d
  with counts 2,364 / 9,217 / 180.
- Rollout risk remains five high npm advisories; react-router/react-router-dom 7.18.1 carry
  GHSA-qwww-vcr4-c8h2, fixed in 7.18.2. V65 had the same lock and rollback does not reduce
  exposure; dependency remediation is separate.

## Verification record

| Date | Command | Result |
|---|---|---|
| 2026-08-27 | full backend `pytest -q` | 898/898 passed |
| 2026-08-27 | accounts-on suite, sessions, focused V72, combined V71/V72, pin propagation | 53/53, 16/16, 6/6, 13/13, 196/196 passed |
| 2026-08-27 | transaction dry-run + apply | zero topology or projection change |
| 2026-08-27 | `validate_fixture.py` · `validate_games_pack.py` | 0 errors · pack valid |
| 2026-08-27 | ranking + derived regeneration | 618 total / 448 eligible; 336 boards |
| 2026-08-27 | ruff, formatting, mirrors, hashes, stale-pin, JSON/digests, whitespace | green |
| 2026-09-05 | `pytest tests/test_wordgames_session_store.py -q` | 16 passed |
| 2026-09-05 | `pytest tests/test_app_pack_contract.py tests/test_data_client.py -q` | 23 passed |
| 2026-09-05 | `ruff check` | All checks passed! |
| 2026-09-05 | `scripts/validate_fixture.py` | GREEN: fixture is valid (0 errors) |
| 2026-09-05 | `scripts/validate_games_pack.py` | games pack GREEN |
| 2026-09-05 | accounts-on `pytest -q tests/accounts` | 53 passed |
| 2026-09-05 | alchimie sparse-recipes test alone at load ≈ 39 | failed: 49.0 s vs the 45 s budget (timing only) |
| 2026-09-05 | full backend `pytest -q` | 898 passed in 399.96 s (6m40s) |
| 2026-09-06 | frontend `npm ci && npm test && npm run lint && npm run build` | 163 passed; lint/build green |
| 2026-09-05 | `python3 ~/work/agent-ops/scripts/check_docs.py .` | `files=29 dead_links=0 stale_terms=0 retired_verbs=0 orphans=0` |
| 2026-09-05 | `check_project_contexts.py --work-root ~/work` | row `ok`, thin pointer yes (reads the shared checkout) |

2026-09-05 runs used `~/work/cat_de_roman_esti/.venv/bin/python` with `PYTHONPATH=.` from the docs worktree.
The full suite was green at host load average ≈ 28; the same alchimie test fails on its own at load ≈ 39, so the
45 s budget is load-sensitive, not a behavior regression.

## Next actions

- Keep `rollback-60c3fd5318a` through the next successful rollout.
- Start a later bounded vocabulary wave from documented `main` only when requested.
- npm advisory remediation (react-router 7.18.1 → 7.18.2) is a separate task.
- Decide whether the 45 s wall-clock budget at `tests/test_alchimie_sparse_recipes.py:211` should tolerate host
  load (green in the full run at load ≈ 28, red alone at load ≈ 39 on 2026-09-05).

## Open gates

- Accounts-stack go-live: the `docs/DEPLOY.md` go-live checklist plus `docs/compliance/` lawyer review
  (DEPLOY.md:35-40). Production runs anonymous mode until both are satisfied.

## Doc map

- `README.md` — orientation + the full doc index. `AGENTS.md` — operating contract (Claude Code and Codex).
- `docs/agent-map.md` — entry points and task routes. `docs/agent-testing.md` — gate commands + expected output.
- `docs/adr/` — decisions (newest ADR-0100). `docs/reviews/<wave>/` — per-wave evidence.
- `docs/handoffs/` — dated records. `docs/archive/` — superseded snapshots.
