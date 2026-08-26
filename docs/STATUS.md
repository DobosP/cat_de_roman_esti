# Status — cat_de_roman_esti

_As of 2026-08-26. This file is the repository's current source of truth._

_Last verified: 2026-08-26 (complete local V71 backend, accounts, sessions, focused
resolver tests, validators, generators, Ruff, mirrors, hashes, JSON/digests, whitespace,
and diff checks are green; V71 feature CI has not run)._

## Current work — V71 applied snapshot

- The fixed 25-owner / 50-surface funnel produced 48 unanimously accepted aliases across
  24 existing literature-and-storytelling owners. Both reviewers rejected `intrigii` and
  `intrigilor`, with zero deferrals, projections, or quota.
- The local transaction applied exactly those 48 aliases. Build
  fixture-v71-literature-and-storytelling-morphology has 2,364 nodes / 9,217 edges / 8,400
  aliases / 180 puzzles; projections, topology, pack rows, and frozen boards are unchanged.
- Both rejected forms remain absent from exact/projection resolution and are the complete
  reviewed actionable-fuzzy deny set. Exact `intrigă` and advisory suggestions still work.
- V71 is intentionally uncommitted, unlanded, unpushed, and undeployed. All required local
  gates are green; feature CI has not run and is not claimed.
- ADR-0096 supersedes ADR-0095 only at its V70 build/count decision and records a narrow
  two-surface exception to ADR-0022/0062 fuzzy action. V69 Contexto selection,
  navigation, sessions, privacy, and all other fuzzy behavior remain unchanged.

## V71 artifact pins

Build: fixture-v71-literature-and-storytelling-morphology; KG:
9134f057be13538cf9c4f48b50d41e06a1e6bfb36f26a5cb59cd925f9b900640;
pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed;
ranking: f9c114570006938ec6602e9318e49a145bedd378be16120cacb4b6c9a2107a51;
derived: 37ddf1a45ad04eeaf115589112269bc6cf3a2e19e61576a15c0acc426d168662;
mobile: a627e1234e88ccd174369ec19e58d912faaf526025c3955305c6c6c79ae2595e;
server manifest content: sha256:130e1a14a3331a89e3418858d8737c66b0817fc994efed05fc4c124d1509ac0f;
ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
Protected payload pins remain: nodes without aliases
c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0;
edges f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0;
puzzles 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc;
ranking rows faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031;
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6.

## V71 local verification

- Complete backend passed 892/892; accounts-on 53/53, sessions 16/16, V71 7/7, combined
  V71/Contexto/Lanț fuzzy 20/20, and current-pin propagation 189/189 passed.
- Fixture validator reported 0 errors; games-pack validation passed. Ranking regeneration
  checked 618 total / 448 eligible records; derived regeneration checked 336 boards.
- Repo-wide Ruff lint, V71 scripts/test formatting, mirrors, hashes, stale-pin scan,
  JSON/digests, whitespace, and git diff checks are green.

## Preserved inventory and runtime

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
V51–V71 reviewed inventories retain their owners; V49 retains 104 Lanț rejections.
Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game cap, per-entry locks,
64 KiB request ceiling, deterministic selection, and server-private answers.

## Documented main and production

- The documented main baseline is exact 2d1b7b975eb3f8cbcdb7d6e623b55e31c372ebc8;
  its deployed application ancestor is exact 60c3fd5318a483b0e4001481d036358a855a7961.
- V70 exact feature/main CI 32935538976/32936248214 are green at 2d1b7b9. No V71 commit,
  push, feature CI, main merge, or deployment exists.
- Anonymous production remains healthy at 60c3fd5318a on image
  sha256:7a9b6dbc5832aa9d3601a7216114499e0a56453bf83b9cd34cc266eb8c3da955,
  tagged release-60c3fd5318a, with zero restarts and zero error-log markers.
- Retained rollbacks are V65 sha256:71f3e2cc / rollback-aefcc2c64fed and V61
  sha256:efa179af / rollback-1c42de0. Caddy remains retained.
- Production checkout is clean; accounts/debug are off; submissions return 503. No
  database, OAuth, worker, environment, DNS, TLS, or infrastructure change occurred.
- Health, healthz, me, Intrusul/Perechi, exact UI assets, and V69 Contexto refren rank-170
  smokes remain green. Production still reports V68 manifest hash
  sha256:54f4d41b3ca4bea0d3160ea81364c68940a5bdeef1e4c2f67f263c1e29fe4002
  with counts 2,364 / 9,217 / 180.
- Rollout risk remains five high npm advisories; react-router/react-router-dom 7.18.1 carry
  GHSA-qwww-vcr4-c8h2, fixed in 7.18.2. V65 had the same lock and rollback does not reduce
  exposure; dependency remediation is separate.

## Next verified work

- Review and commit the green local snapshot, require exact feature CI, then land and
  deploy only as separately requested steps.
