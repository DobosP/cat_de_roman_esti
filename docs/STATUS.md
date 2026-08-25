# Status — cat_de_roman_esti

_As of 2026-08-26. This file is the repository's current source of truth._

_Last verified: 2026-08-26 (six exact feature/landed-main CI runs, frontend and backend
gates, real-browser acceptance, production smokes, container health, and rollout evidence
are green)._

## Current release — V68, V69, and persistent navigation

- The integrated V68/V69/navigation release is landed and pushed on clean main at exact
  60c3fd5318a483b0e4001481d036358a855a7961.
- V68 adds 48 bounded Romanian-language and grammar aliases across 24 existing owners,
  retains 2,364 nodes / 9,217 edges / 8,306 aliases / 180 puzzles, and changes no topology.
- V69 keeps ct_muzica_163 as provenance but removes it from Contexto selection, then applies
  deterministic positive quintile tickets within the filtered shelf. Contexto has 201
  eligible targets; original-game ranking has 618 total / 448 eligible boards; the frozen
  derived payload remains 336 boards.
- Shared game navigation stays reachable below the mobile safe area and uses Ieși. Explicit
  Conexiuni exit clears only its active pointer and replaces history; refresh resume and
  Escape/Backspace selection clearing remain intact.
- Intrusul is the sole Începe aici recommendation. Conexiuni has plain-language hints for
  all three difficulty tiers; its sticky coach no longer contains feedback or clues.
- ADR order is V68 ADR-0092, V69 ADR-0093, and navigation ADR-0094. ADR-0091 remains
  superseded by ADR-0092; ADR-0094 supersedes only ADR-0052's lobby-recommendation clause
  and preserves its derived-game contracts.

## Preserved inventory

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 201 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories. V51–V69
accepted inventories and owners remain intact; V49 retains 104 Lanț rejections.

## Final artifact pins

Bundled KG: ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128;
pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed;
ranking: c32b648885cf9d0aad718bda9c1dcbd86f49ddda6819ceb14a7c372e32ddb424;
derived: 9199f60c41d334f620403ca68926790b57292d71761175a470ba7385af52da91;
mobile: 1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae;
ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
Protected payload pins: nodes without aliases c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0;
edges f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0;
puzzles 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc;
ranking rows faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031;
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6.

## Verification and CI

- V68 feature/main CI 32907211185 / 32907879041: green.
- V69 feature/main CI 32908368059 / 32909044614: green.
- Navigation feature/main CI 32908981966 / 32909756110: green.
- Frontend 29/29, ESLint, typecheck/build, 118.17/120 KiB bundle gate, manifest graph,
  tracked-static byte parity, backend preservation, generators, validators, Ruff, mirrors,
  and whitespace passed.
- Chrome at 390 × 620, 360 × 430, and 375 × 330 kept the 44 px exit visible at maximum
  scroll with zero overlap; the 360 × 430 header/coach gap was 7 px. Refresh preserved the
  board, explicit exit cleared only Conexiuni state, and browser Back stayed home.

## Production rollout

- Anonymous production was deployed on 2026-08-26 at exact 60c3fd5318a. Image
  sha256:7a9b6dbc5832aa9d3601a7216114499e0a56453bf83b9cd34cc266eb8c3da955
  is tagged release-60c3fd5318a; the container is healthy with zero restarts and zero
  error-log markers.
- Rollbacks retained: V65 image
  sha256:71f3e2cc tagged rollback-aefcc2c64fed and V61 image
  sha256:efa179af tagged rollback-1c42de0.
- The production checkout is clean. Caddy was retained; accounts and debug are off;
  submissions return HTTP 503. No database, OAuth, worker, environment, DNS, TLS, or
  infrastructure change occurred.
- Public health, healthz, me, Intrusul, and Perechi smokes passed across all 14 categories.
  The public manifest reports V68 hash
  sha256:54f4d41b3ca4bea0d3160ea81364c68940a5bdeef1e4c2f67f263c1e29fe4002
  and counts 2,364 / 9,217 / 180.
- Production served exact files assets/index-DNdfJLWK.js,
  assets/index-DiCPhhaT.css, assets/Alchimie-L2bxBlOx.js, and
  assets/Conexiuni-BF-X6jR1.js. The V69 Contexto refren rank-170 diagnostic passed.
- Rollout risk: npm audit reports five high advisories. Two affect shipped
  react-router/react-router-dom 7.18.1 and are fixed in 7.18.2
  (GHSA-qwww-vcr4-c8h2). V65 already locked 7.18.1, and this SPA uses BrowserRouter without
  RSC/actions, so rollback does not reduce exposure; dependency remediation is separate.
- Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game LRU cap, per-entry
  locks, 64 KiB request ceiling, deterministic selection, and server-private answers.

## Next verified work

- Start V70 social-and-civic-life morphology from final documented main; it has not started.
