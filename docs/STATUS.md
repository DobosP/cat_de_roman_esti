# Status — cat_de_roman_esti

_As of 2026-08-27. This file is the repository's current source of truth._

_Last verified: 2026-08-27 (complete local V72 gates, exact feature and landed-main CI,
and anonymous production identity, health, gameplay, account-mode, asset, and log smokes
are green)._

## Current work — V72 applied snapshot

- Two independent reviews unanimously accepted 50 normalized-unique genitive/dative aliases
  for 25 existing Romanian dishes-and-pastries owners, with zero rejections, deferrals, or
  projections. Qualified bulz and gogoși forms avoid unsafe bare polysemes.
- The rollback-safe transaction applied exactly those 50 aliases. Build
  fixture-v72-romanian-dishes-and-pastries-morphology has 2,364 nodes / 9,217 edges / 8,450
  aliases / 180 puzzles; projections, topology, pack rows, and frozen boards are unchanged.
- All owners are gastronomie concepts with 4–23 legal non-distractor incoming Lanț
  predecessors. Pre-apply fuzzy results were 20 intended, 30 unresolved, and zero wrong.
- V71's reviewed actionable-fuzzy deny set remains exactly `intrigii` and `intrigilor`;
  the inherited 70-term cumulative nonaccepted ledger is unchanged.
- V72 is committed, pushed, and fast-forward landed at exact
  `6ee86935038744c0066cac6a50865f76eab93e37`; feature/main Actions runs
  `33023808156`/`33024392655` passed frontend and Python 3.12/3.14 on attempt 1.
- ADR-0097 supersedes ADR-0096 only at its V71 build/count decision. Contexto selection,
  navigation, sessions, privacy, frontend, and all other fuzzy behavior remain unchanged.

## V72 artifact pins

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
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6.

## V72 local verification

- Complete backend passed 898/898; accounts-on 53/53, sessions 16/16, focused V72 6/6,
  combined V71/V72 13/13, and historical/current-pin propagation 196/196 passed.
- The transaction dry-run and apply completed with zero topology or projection changes.
  Fixture validation reported 0 errors; games-pack validation passed. Ranking regeneration
  checked 618 total / 448 eligible records; derived regeneration checked 336 boards.
- Repo-wide Ruff lint, touched-file formatting, mirrors, hashes, stale-pin scan,
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
V51–V72 reviewed inventories retain their owners; V49 retains 104 Lanț rejections.
Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game cap, per-entry locks,
64 KiB request ceiling, deterministic selection, and server-private answers.

## Documented main and production

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

## Next verified work

- Gate this docs-only rollout record through exact feature and main CI before landing.
- Keep rollback-60c3fd5318a through the next successful rollout; start a later bounded
  vocabulary wave from final documented main only when requested.
