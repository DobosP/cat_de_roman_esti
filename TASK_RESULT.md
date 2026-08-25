# Task Result — V68/V69/navigation production rollout

## Result

- V68, V69, and the persistent-navigation change are landed and pushed in the integrated
  main release at exact 60c3fd5318a483b0e4001481d036358a855a7961.
- Exact CI is green: V68 feature/main 32907211185 / 32907879041, V69 feature/main
  32908368059 / 32909044614, and navigation feature/main
  32908981966 / 32909756110.
- Anonymous production was deployed on 2026-08-26 at exact 60c3fd5318a and passed generic,
  UI-asset, derived-game, and V69 Contexto diagnostics.

## Delivered behavior

- V68 adds 48 reviewed Romanian-language and grammar aliases across 24 bounded existing
  owners. It retains 2,364 nodes / 9,217 edges / 8,306 aliases / 180 puzzles and changes no
  topology, board payload, session, account, or frontend behavior.
  Its frozen 50-surface review digest is
  ff4cee7a4ac2f39601a19efd3aad2a305e85303e282451ba606fe1c8b68b3377; punctului and
  punctelor remain rejected.
- V69 reserves ct_muzica_163 from selection and ranks each requested Contexto shelf with
  deterministic positive quintile tickets. It retains 201 eligible Contexto targets,
  618 total / 448 eligible original-game boards, and the exact frozen 336 derived boards.
- GameShell navigation remains visible below the mobile safe area and uses Ieși. Explicit
  Conexiuni exit removes only its own resume pointer and replaces browser history, while
  page refresh resumes and Escape/Backspace still clears selection.
- Intrusul is the sole Începe aici recommendation. Conexiuni explains all three difficulty
  tiers, keeps only its next-move coach sticky, and leaves feedback/clues in document flow.
- The ADR sequence is V68 ADR-0092, V69 ADR-0093, and navigation ADR-0094. ADR-0091 remains
  superseded by ADR-0092; ADR-0094 changes only ADR-0052's lobby recommendation.

## Final artifact evidence

- KG: ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128.
- Games pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed.
- Ranking: c32b648885cf9d0aad718bda9c1dcbd86f49ddda6819ceb14a7c372e32ddb424.
- Derived: 9199f60c41d334f620403ca68926790b57292d71761175a470ba7385af52da91.
- Mobile: 1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae.
- V49 ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
- Protected nodes-without-aliases:
  c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0.
- Protected edges: f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0.
- Protected puzzles: 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc.
- Ranking rows: faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031.
- Derived boards: 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6.

## Verification

- Frontend 29/29, ESLint, typecheck/build, 472-module Vite build, tracked-static byte parity,
  manifest graph, and 118.17/120 KiB initial bundle gate passed.
- Backend preservation tests, V68/V69 focused tests, ranking/derived tests and generators,
  fixture/pack validators, Ruff, mirrors, and whitespace passed.
- Chrome at maximum scroll on 390 × 620, 360 × 430, and 375 × 330 kept a 44 px exit visible
  with zero sticky overlap; the 360 × 430 header/coach gap was 7 px. Refresh retained the
  Conexiuni board, explicit exit cleared only its token, and Back remained at the lobby.
- CI run pairs 32907211185/32907879041, 32908368059/32909044614, and
  32908981966/32909756110 all completed successfully.

## Production evidence

- Active image
  sha256:7a9b6dbc5832aa9d3601a7216114499e0a56453bf83b9cd34cc266eb8c3da955
  is tagged release-60c3fd5318a. The production checkout is clean, and the container is
  healthy with zero restarts and zero error-log markers.
- Retained rollback images are V65 sha256:71f3e2cc tagged rollback-aefcc2c64fed and V61
  sha256:efa179af tagged rollback-1c42de0.
- Caddy was retained. Accounts/debug are off, submissions return HTTP 503, and no database,
  OAuth, worker, environment, DNS, TLS, or infrastructure change occurred.
- Public health, healthz, me, Intrusul, and Perechi smokes passed across 14 categories.
  The public manifest reports V68 hash
  sha256:54f4d41b3ca4bea0d3160ea81364c68940a5bdeef1e4c2f67f263c1e29fe4002
  with 2,364 / 9,217 / 180 counts.
- Production served exact files assets/index-DNdfJLWK.js, assets/index-DiCPhhaT.css,
  assets/Alchimie-L2bxBlOx.js, and assets/Conexiuni-BF-X6jR1.js exactly. The V69 Contexto
  refren diagnostic returned rank 170.
- Rollout risk: npm audit now reports five high advisories. Two are shipped
  react-router/react-router-dom 7.18.1 issues fixed by 7.18.2
  (GHSA-qwww-vcr4-c8h2). Exact V65 already used 7.18.1, and this BrowserRouter-only SPA
  does not use RSC/actions, so rollback does not reduce exposure. No dependency was changed
  in this evidence-only commit.

## Next action

Start V70 social-and-civic-life morphology from the final documented main. V70 has not
started.
