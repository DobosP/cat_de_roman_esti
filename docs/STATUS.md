# Status — cat_de_roman_esti

Last verified: 2026-09-07 — V84 full integration GREEN; committed candidate ready for landing. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V83 is on local main at `8353880`. V84 candidate: `feat/v84-six-game-graph-quality`.
  No push or deployment was performed in this version.
- V84 adds in-round Romanian rules, feedback interpretation and recovery help to all six
  games. Keyboard/touch disclosure preserves progress and selection; Enter cannot submit it.
- Alchimie now explains earned discoveries with up to two actual, oriented graph relations,
  retained after resume and in the winning recap. Only already visible concepts are exposed.
- V84 adds 15 real culinary concepts and 42 accepted forms, plus 57 specific graph links.
  The false Telemea→Poale-n brâu cheese-category edge is removed through an exact-record
  rollback-protected transaction. Existing aliases remain exact (ADR-0118).
- Drojdie is a native concept; its broad food projection is retired. Six former false-hot
  meat/cheese targets cool. Biscuit/apple, whey/urdă and brine/telemea now have direct feedback.
- Four independently reviewed rounds are promoted: Contexto Plăcintă cu mere, Salam de
  biscuiți and Pâine; Lanț Făină→Cornulețe, with routes via Aluat or Cozonac.
- Served KG: `fixture-v84-six-game-graph-quality`, 2,380 nodes / 9,279 edges / 8,517 aliases /
  180 puzzles. `kg_real.json` is a thin export, not the served graph.
- Prior V73/V74 reliability/accessibility, V76 input guards and V82 bounded pair reuse remain.
  Current expectations remain literal and immutable; historical artifacts reconstruct exactly.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 226 | 224 | 2 | 220 eligible |
| Lanțul Cuvintelor | 98 | 95 | 3 | 95 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **638 = 630 approved + 8 pending**; original four-game ranking **468 eligible**.
All 634 old pack records, 336 frozen boards, 180 puzzles and 8,475 old aliases remain exact.
All 82 prior Alchimie recipe projections and 97 prior Lanț route profiles remain exact.
Only 25 old node degree fields change; 9,222 retained edge records stay exact. Of old ranking
rows, 292 change after graph/stock updates. No extra Conexiuni/Alchimie/derived boards are claimed.
Projection vocabulary is 471 rows across 26 domains; all 71 legacy proxies remain unchanged.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, per-entry locks, 64 KiB requests,
bounded histories/caches and private answers. New Alchimie explanations add no session fields.

## Current artifact pins

- `games_pack.json`: `c843705d565770d6916567be8b7c627c16bfdcf9dd8368e6a333f0f222484b57`
- `board_rankings_v37.json`: `67a7a3274f24485d45ab75191a9701482c0959be4029e29e47c7c576360a6075`
- `derived_catalog_v38.json`: `579128d90d34a57a093202e54babe76b1ceb6840a36e332c9ecc540a8fb5251a`
- `kg_sample.json`: `3fb0f97c5b4c813eb72d8fd3589c4ce92f724d0565db840c1bc3909458a60ab0`
- `cat_mobile_app_pack_contract.json`: `43e18a0b84b81196573bca0c5643c117def93535c38fa67b52adf5da63fd3166`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:0fda97f4ab1c80aaf31c46bf638f75301156eb3029a6505486ab512c8b80d131`.
Mobile content: `sha256:10984193d18dd817029c5972fe84e39bb490c4ef819399408cd54c299c67ed00`.

## Verification

- Exact independent graph review accepts 15 nodes / 42 forms / 57 links / one removal.
  Duplicate baseline IDs, stale removals and interrupted writes fail closed; rollback tests pass.
- Strict pending critique: four checked, zero FAIL, one justified salience WARN. Separate bound
  analyst/verifier promote all four through the supported serializer/applier; validators pass.
- Independent six-game impact: 3,757 first-guess API observations per checkout over all 221
  old approved Contexto records; 67 newly valid directed-link journeys pass. All old eligible
  pools retained. Rank/acceptance changes are measured, not counted as thousands of repairs.
- Every new form has typed API coverage; actual dough/brine recipes expose earned explanations.
  Independent runtime/UI/history review finds no blockers; complete V83 artifacts reconstruct.
- Frontend build passes at 118.87/120 KiB. New seed-38 snapshots include Alchimie empty links,
  the larger Contexto reachable count and intended Lanț selection change.
- Full backend: 1,207 passed on each of Python 3.12.3/3.14.6; accounts: 53 passed each.
- Frontend: 177 native and 122 desktop/mobile browser checks passed; no skips/retries.
- Validators, pending gate, lint/typecheck/build, Ruff/docs/whitespace pass. Initial stale
  test expectations and final fresh green runs: `docs/reviews/v84-six-game-graph-quality/verification.json`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for V84.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; see `docs/DEPLOY.md`.
- Clean Node24 install/audit reports zero vulnerabilities; this does not patch deployed V72.

## Remaining gates

- V84 is ready on its task branch; its next landing request can merge the verified candidate.
- Remaining food feedback: Scorțișoară is too hot for Pâine; oven is too warm for the no-bake
  biscuit dessert and outranks cocoa; butter/apple-pie and other production inputs remain noisy.
  Directed input-only concepts are not automatically eligible targets or new curated boards.
- Owner feedback contact, Romanian-player and real-device checks remain unrun. Reverify legal
  operator/contact configuration and pages per DEPLOY before public anonymous rollout.
- Rollout requires explicit authorization and live smoke/rollback verification. Keep accounts
  outside anonymous beta until the DEPLOY go-live checklist and compliance review pass.
- Release evidence: `docs/BETA_CANDIDATE.md`; agent reviews are not human playtests.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0119), `docs/reviews/`, WORKLOG: decisions, evidence and history.
