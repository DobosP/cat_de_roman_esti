# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V89 landed locally; V90 started; local loop active. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V89 is merged at `143bfdb`, following V88 `000b0a2` and its landing record `b614bfe`.
  V90 starts on `feat/v90-household-discovery-and-critique-gates`; the local loop
  continues until stopped (ADR-0127).
- Conexiuni reconciles lost guess/clue responses with one owned GET. Earned clues,
  solved groups and wins/losses recover without replaying a mutation. Failed verification
  retains a visible read-only retry and locks board actions; stale replies cannot adopt
  another saved game. A lost first clue now preserves a 150-point finish instead of 50.
- One new easy Cald sau Rece round: Mop (`ct_viata_de_roman_353`). The two independently
  reviewed gate judgments reject staged Făraș352/Aspirator354: each has only three
  recognizable incoming neighbors, below the five required by ADR-0071. Mop has five.
  Initial screens incorrectly used combined incoming/outgoing counts; corrections and
  original evidence remain archived. The rejected IDs remain consumed, with dossiers kept.
- Tort Diplomat→Frișcă now gives rank2/hot, nonwinning feedback through one exact native
  pair. Praf gets the same related feedback only for Făraș, Mop and Aspirator; its public
  identity, Pământ fallback and all other scopes remain. Valid feedback does not approve
  a hidden target. No graph concepts, directed links, forms, synonyms or projection rows added.
- Served KG remains `fixture-v88-cross-game-quality`: 2,413 nodes / 9,442 edges /
  8,631 aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served graph.
  V88's truthful fermented/sweet/whipped-cream distinctions remain intact.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 234 | 234 | 0 | 76 eligible |
| Cald sau Rece | 242 | 240 | 2 | 236 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **659 = 651 approved + 8 pending**; original four-game ranking **489 eligible**.
No new Conexiuni, Alchimie, Lanț, Intrusul or Perechi round is claimed in V89.
All 658 old pack records, 83 Alchimie books/profiles, 100 Lanț profiles/menus and 336
derived rows/payloads remain exact. All 465 projection rows / 26 domains,
71 scorer proxies, native owners and graph bytes remain exact. Native exact feedback
pairs grow 10→11; four preexisting projected neighborhoods gain the one closed Praf entry.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, locks, 64 KiB requests and
bounded histories/caches. No scoring formula, backend session shape or shared action-helper change.

## Current artifact pins

- `games_pack.json`: `c8b310f56f3983dc8f4e6a523a85a9af79a3cf244d770474f6db6ac8266e0f04`
- `board_rankings_v37.json`: `ea207d65a1846d2f9bb2945ca9320a8e5e7bdc5e9fe8c31113aaf4f749fdc3d6`
- `derived_catalog_v38.json`: `4bd3cd515d21627fe42d07149bdf78951164ebfaa30df52fd1259ce26b8470d9`
- `kg_sample.json`: `2964951e3f68be7b49abb7f727b97d700a42d7e3527b117ef8b6c2830103f9fc`
- `cat_mobile_app_pack_contract.json`: `d2fbb9f550a05b6b128431ee55787b2b156846887f0bc8ce1908f09e6683b951`

Server KG content: `sha256:b8205c055288f2d2697076d0fac2d4852b6c690089ac373507e325979952b2b2`.
Mobile content: `sha256:f8f5c13f2cb302338f35adf38e311906856d24cb04f58592c77783a519a61fd3`.

## Verification

- Exact independent recovery/feedback reviews accept the bounded implementation.
  All three deterministic dossiers have zero FAIL/WARN; final human-style agent judgment
  still rejects two by directed C3. Supported import/artifact/promotion transactions pass.
- Feedback: 15 focused tests pass. Independent whole-module AST comparison confirms just
  one native pair and one projected-neighborhood entry. Eleven separate BFF probes pass;
  author evidence independently confirms 253/256 responses and 81/84 controls unchanged.
- Conexiuni lane: 193 native tests, lint/build and 26 desktop/mobile browser cases pass,
  plus two stronger settled screenshot checks. Bundle is 118.92/120 KiB.
- Initial lane checks: seven stale native source-shape assertions and eight browser locators
  failed; exact original failures remain archived. Stronger screenshot assertions resolve
  a blank mocked-animation capture. Three wrong-directory npm attempts ran no checks.
- The focused history/content set passes 266 tests. Final impact: 7,169/7,170 old-round
  observations unchanged; only Diplomat→Frișcă improves. All seeded start payloads stay exact.
- Full frontend is green: **193 native /214 browser checks**, no retries; lint/typecheck/
  build/bundle pass. Fixture/pack/pending/Ruff/docs/whitespace pass.
- First full backend: **1,530 pass /one historical-scope failure**. The V44 pre-V88 sink
  assertion included new Mop. The exact test-only correction passes 110 focused cases;
  final full backends pass **1,531 tests each on Python 3.12.3 /3.14.6**, plus
  **53 accounts tests each**. All 407 integration input hashes remain unchanged.
  Final independent audit accepts all 16 receipts and 407 input hashes. The final
  candidate manifest binds 237 present/deleted files, including its audit snapshot/pair.
  Evidence is sealed by implementation commit `143bfdb`; later status notes are docs only.
  `docs/reviews/v89-feedback-and-conexiuni-recovery/`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; health/config/assets and alias smoke passed. No production check,
  push or deployment occurred in V89. Preserve `rollback-60c3fd5318a` for the next rollout.
- Local Python3.12.3, fresh constrained Python3.14.6 and Node24 dependencies are available.

## Remaining gates

- V90 starts household vocabulary and truthful directed-discovery work, a necessary
  incoming-neighbor critique floor, and an all-six-game review. Alchimie lost-action
  behavior requires actual reproduction before choosing a fix. Its fresh kickoff binds
  eight directed profiles, 19 unknown inputs and 10 private BFF probes. No V90 promotion yet.
- The household screen finds 19/33 deliberately broad tested surfaces unrecognized,
  including murdărie/firimituri/pardoseală. This is a stress sample, not a player-frequency
  estimate. Electricitate→Aspirator remains cold378 while Apă is hot9; broader semantic
  work remains. True Zacuscă→Bucătărie→Frigider→Frișcă remains warm24.
- Cremșnit/Pișcot→Frișcă remain cold; their variant/indirect associations were not granted
  the exact Diplomat pair. Brioșă/Pandișpan hidden targets and Diplomat Alchimie stay held.
- Romanian-player sessions, real-device checks, feedback contact and operator/legal-page
  verification remain unrun. Rollout requires separate authorization and live smoke/rollback
  checks. Keep accounts out until the DEPLOY go-live checklist passes; see BETA_CANDIDATE.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0133), `docs/reviews/`, WORKLOG: decisions, evidence and history.
