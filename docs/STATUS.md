# Status — cat_de_roman_esti

_As of 2026-08-26. This file is the repository's current source of truth._

_Last verified: 2026-08-26 (complete local V70 tests, validators, generators, Ruff,
mirrors, hashes, stale-pin scan, JSON/digests, whitespace, and diff checks are green;
feature CI has not run)._

## Current work — V70 applied snapshot

- The fixed 25-owner / 50-surface funnel produced 46 unanimously accepted aliases across
  23 existing social-and-civic-life owners. Both reviewers rejected legii, legilor,
  băncii, and băncilor, with zero deferrals and no quota.
- The local transaction applied exactly those 46 aliases. Build
  fixture-v70-social-and-civic-life-morphology has 2,364 nodes / 9,217 edges / 8,352
  aliases / 180 puzzles; projections, topology, pack rows, and frozen boards are unchanged.
- The four rejected surfaces remain blocked from exact, projection, and fuzzy resolution.
- V70 is intentionally uncommitted, unlanded, unpushed, and undeployed. All required local
  gates are green; feature CI has not run and is not claimed.
- ADR-0095 supersedes ADR-0092 only at its V68 build/alias-count decision. ADR-0095
  preserves ADR-0092's bounded resolver contracts, ADR-0093's Contexto behavior, and
  ADR-0094's navigation behavior; ADR-0091 remains historically superseded by ADR-0092.

## V70 artifact pins

Build: fixture-v70-social-and-civic-life-morphology; KG:
76fc1f933000f56c0c0d46588f61eeb9c9e03af5608c950a3884550e5a3108b0;
pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed;
ranking: 3f90dc5162a2931967eef7a63c50707eb9e9a0f060684337f5638cfc4fe287fc;
derived: 7aa1596ca6dd55451c5e8da6b99a5852e319742f1893dd630c0c22795255b5a1;
mobile: c0f49ed6c084ecff0a76d24fb4153a25cd3b32e333ab4794a8a11140a343ee6d;
server manifest content: sha256:34320f0370381f756cc6e93503b26cb7af44eb6decd71fbdca5fecbb3b3a8774;
ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
Protected payload pins remain: nodes without aliases
c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0;
edges f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0;
puzzles 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc;
ranking rows faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031;
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6.

## V70 local verification

- Complete backend exited 0 over 885 collected tests; accounts-on 53/53, V70 6/6,
  sessions 16/16, and the pin-sensitive/preservation set 270/270 passed.
- Fixture validator reported 0 errors; games-pack validation passed. Ranking regeneration
  checked 618 total / 448 eligible records; derived regeneration checked 336 boards.
- Repo-wide Ruff, mirrors, hashes, stale-pin scan, JSON/digests, whitespace, and
  git diff checks are green.

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
V51–V70 reviewed inventories retain their owners; V49 retains 104 Lanț rejections.
Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game cap, per-entry locks,
64 KiB request ceiling, deterministic selection, and server-private answers.

## Documented main and production

- The documented main baseline is exact 047d3978175f4210698e44839ace3c9d8883dfe1;
  its deployed application ancestor is exact 60c3fd5318a483b0e4001481d036358a855a7961.
- V68 feature/main CI 32907211185/32907879041, V69 feature/main
  32908368059/32909044614, and navigation feature/main
  32908981966/32909756110 remain green. No V70 feature CI exists yet.
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

- Commit the green local snapshot, require exact feature CI, then land and deploy
  separately.
