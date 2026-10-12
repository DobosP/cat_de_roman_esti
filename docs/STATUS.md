# Status — cat_de_roman_esti

Last verified: 2026-10-12 — V1.12 qualified locally on main a27477d; V1.7 remains parked ([ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md)); four native rails and content gates pass ([ADR-0189](adr/0189-behaviour-bound-installed-content-authorities.md)); GUI review branch integrates it ([ADR-0196](adr/0196-integrate-reviewed-v19-v110-with-gui-history.md)), combined unit/full NOT RUN. Actual full at e042587 (GUI4f36+main3f327c, ADR0194) failed only active route-JS budgets + aggregate exit.

- **GUI Linux current:** Core1.6 released; UI0.3 active/UI1.0.6 staged. Full at 6b10d47 (2026-10-12, canonical distroless image, main a27477d integrated): 900/900 browser, 16/16 baselines, CSP enforced 0; red only E3 route-JS (Home115016 vs40960) plus the procedural owner-coordinator journey and its knock-ons; unit 6b10d47 budget-only red (KIT_BUMP evidence, E6). Committed `scripts/gui-full-runner.py` attaches the real same-full legacy coordinator and verifies owned cleanup; baseline verification installs missing locked quality deps in the managed runner, preserving exact versions and baselines; full not rerun. Next: M1-close full; roedu-ui `docs/GUI_COMPLETION_LOOP.md`; decisions [ADR-0195](adr/0195-owner-decisions-review-m1-image-test-loop.md), roedu-ui E5/E6.
- **GitHub Actions:** [ADR-0164](adr/0164-manual-github-actions.md), checked2026-10-05; required Go/Node dispatch, references opt-in, no hosted run.

## Current state

- Package **1.0.1** (lobby **V1.0.1**) hardens owner-requested mixed-age V1 on phones/desktop;
  independent review/decision [ADR-0159](adr/0159-v1-0-1-testing-hardening.md).
- 1.0.1: a 0-point loss is never a record; circuit daily intent is single-use (one resume
  notice; Intrusul/Perechi results offer the pending daily); Conexiuni/Intrusul/Perechi
  boards step 4/2/1 columns only; Lanț stacks its route on phones and Alchimie keeps long
  words whole on enlarged text. Lanț has "Începe alt lanț", an announced position and
  "salturi"; Cald sau Rece shows "Arată răspunsul" and rules below play.
- 1.0.1: a failed optional AccountBar renders nothing instead of a game error; the reserve
  loads at startup and reserve drift returns the game's JSON 503; `/` revalidates on
  every load; `/api/health` reports `version`. Quick-game tiles are display-capitalised
  (reviewed lowercase allowlist); server copy has diacritics and correct plurals.
- Ghiozdan→Capra cu trei iezi has reviewed approval/captions; both routes win; all120captions exact.
- A finite reviewed reserve excludes 20 pack rounds and three quick boards from new
  bundled selection. Archived records remain unchanged. Custom development overrides
  retain their previous unranked compatibility scope under ADR-0158.
- All 256 historical rejections/seven pending boards, V99 twelve research proposals
  (eight researched/four held) and V98 three recipe ideas retain their prior state.
- [Content skill](../.agents/skills/romanian-game-content/SKILL.md): refinement/discovery with independent gates.
- Decision/evidence: [ADR-0158](adr/0158-v1-testing-release.md),
  [release review](reviews/v1-testing-release/README.md), [Romanian tester guide](TESTARE_V1.md).
- **V1.12 qualified locally on main a27477d:** 38 reviewed new concepts, including postal and garden vocabulary;
  +38 nodes/+164 links/+168 exact forms, zero new curated rounds or hidden-target approvals.
  All 206 added headwords/forms resolve into 38 real slots; foreign Piersic plurals preserve Piersică.
  [Review](reviews/v1-12-post-and-garden/README.md) and [pool](content-pool/v1-12-post-and-garden/pool.json).
  Four exact native rails; owner-approved Cald assertions, HTTP1207 and API206 pass.
  Full native race has no new red versus main; managed SPA baseline failures remain unchanged. Main-only V1.8–V1.12 results do not qualify the combined GUI source (ADR0194/ADR0196).
## Inventory and invariants

| Game | Total | Approved | Pending | New-round pool |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 83 eligible |
| Cald sau Rece | 265 | 263 | 2 | 255 eligible |
| Lanțul Cuvintelor | 123 | 121 | 2 | 121 eligible |
| Alchimie | 83 | 80 | 3 | 68 eligible |
| Intrusul | 228 | 228 | 0 | 226 selectable / 188 preferred |
| Perechi | 193 | 193 | 0 | 192 selectable / 153 preferred |

Pack **716 = 709 approved + 7 pending**,527 eligible; quick421/418,341 preferred, starter62/61. The85 authored/336 frozen payloads stay exact.
Pool counts describe curated records; existing on-demand fallback generators remain.
Qualified V1.12 KG: `fixture-v1-12-post-and-garden`, 2543 nodes/9974 links/9332 forms/180 exact puzzles.
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration has **252 concepts/352 recipes/148 discoveries**, 96 supplies, 12 tiers,
32 goals, ten historical books and 1156 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current qualified V1.12 pins

- alchimie_discovery_world_v92.json: `c77c62cb28c6b4aae3b3e8c81aea50624cfd561b42d87b606b34f0b052922ad6`
- alchimie_recipe_extensions_v92.json: `034cf54261de0eb0046c1b6751637c03a610a95da34aeb2681195a13d73d60a5`
- quick_games_v92.json: `26bda43974c528aa9f04074541f4b248777550a7d6174bd75a17cc57665fd88a`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `d2e9d8c4193947c0dd821b2bd4cdbf5938732f4257a3ddb1841e4d3c11b85e97`
- derived_catalog_v38.json: `ae801b16fe240b218ab035296b5d895b37c915ce701efaa68e754ed30ca65d56`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `9b4c056e16e9a18100f4e376e7b6ae5dd0d82bb0408367e4d940fea0798bd9c6`
- cat_mobile_app_pack_contract.json: `62566db24792ffb2b8a3843186de3fa4ff1b781a1ecee3745760e882b110432f`
## Verification

- 1.0.1 (2026-09-23): **2466 backend / 53 accounts**, **240 frontend**, lint/typecheck/build
  (119.78/120 KiB gzip), validators, reserve builder, docs and whitespace; **622/622** browser
  cases (Edge desktop/Pixel 7, no retries), plus 200 repeated Lanț recovery cases pass.
  V1 receipts: [1.0.0](reviews/v1-testing-release/verification.json), [1.0.1](reviews/v1-0-1-hardening/README.md).

## Selected Go backend

- [ADR-0162](adr/0162-select-go-production-backend.md): owner-selected Go-only production runtime;
  six games/mining, exploration/restores, metadata/OpenAPI, legal pages and SPA are native Go.
  Canonical launcher/Docker/anonymous profile have no Python serving process or fallback.
- Serving qualification: **1207 HTTP responses/runtime** match Django; all games and ten histories
  match frozen references; prior Go race/vet and retained Rust **55 tests** pass (linked proof).
- Fixed a shared frontend score-receipt race found by the Go two-tab browser gate: transaction time
  is sampled after Web Lock acquisition. **241 frontend cases**, lint/typecheck/build pass (119.78 KiB).
- **622/622 browser cases per runtime** pass; same-CPU HTTP [receipts](reviews/native-backends/README.md).
  Build/run/CI: [guide](NATIVE_BACKENDS.md); Go production [proof](reviews/go-production/README.md) passes.
- [ADR-0163](adr/0163-complete-native-go-accounts.md): optional accounts/OAuth/consent/private
  progress/verified rankings/curated history/erasure and pending proposals are now native Go.
  Username/password and configured Google/Facebook adapters use the shared MIT auth core.
  Production flags remain off. Sources/world require rebuild; engine replicas still need affinity.

## Production and next work

- Production: anonymous V1.0.1 **Go** `abe933779f04c46a32ff0194b5111e68086ba93f`, deployed
  2026-10-04 after all required [CI37208742166](https://github.com/DobosP/cat_de_roman_esti/actions/runs/37208742166) jobs passed.
  Native account/proposal code is shipped dormant; no Python serving runtime.
- Local **622/622 browser**,242 frontend assertions, account/game concurrency/race/vet and
  **1207 HTTP parity** pass. Candidate/public **151 requests each**, six games/exploration,
 28 asset/cache/HEAD proofs pass; current content/legal configuration and accountsoff verified.
- UID10001/read-only, healthy/zero restarts; fixedPCRE2 and zero fixableHIGH/CRITICAL image gate.
  Caddy/certificates/volumes preserved; previousGo+Python rollback profiles retained.
  [Complete rollout proof](reviews/go-completion/README.md). No provider/minor activation.
- Native source/tooling [ADR-0165](adr/0165-native-source-build-and-qualification.md): eight-source export,
  terminal180/body32/prefix1009/HTTP1207/smoke151/assets28 and operator/race/vet proofs pass; capture archived.
- [ADR-0166](adr/0166-native-content-operators-and-builder-rails.md): independent review/rollback/v2 rails pass.
  [ADR-0167](adr/0167-close-unread-bodies-on-early-refusal.md):13 TCP gates/32 body/1207 parity and strict scalar envelopes pass; auth unchanged.
  [ADR-0168](adr/0168-qualify-complete-native-toolchain.md): native qualification remains historical evidence.
- V1.3: [pool3integrated/5held](content-pool/v1-3-everyday-concepts/pool.json), [integration](reviews/v1-3-everyday-concepts/README.md); graph3/12/12 accepted/applied.
- **V1.7 parked** ([ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md)): `codex/content-v1-7` (local 3377a68, origin fba9498) and `codex/content-v1-7-qualification` are not merged; zero integrated growth. V1.12 is the qualified content; [ADR-0186](adr/0186-go-authoritative-content-validation.md) keeps Go/native JSON authoritative. Outcome: [pool](content-pool/v1-7-recognizable-content/pool.json); leafă was independently integrated via V1.8 as a full-paradigm Salariu input.
- **Main a27477d V1.12 contentrails GREEN history** (verified 2026-10-12 on main; combined NOT RUN): all four rails reconstruct exactly and re-audit under the current binary; contentrails/contentbuild race tests pass.
  Owner-approved Cald assertions and all content gates pass on main; only known main `TestManagedSPA*` failures remain; no combined result is inferred. [Procedure](CONTENT_LOOP.md), [ADR-0189](adr/0189-behaviour-bound-installed-content-authorities.md).
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859); forced fallback Societate/Secundă and mixed Personalități predicates.
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and four spare concept slots remain.
## Doc map
- README/AGENTS: orientation; agent-map/testing: gates; [ADR0194](adr/0194-integrate-reviewed-v18-with-gui-history.md)/[ADR0196](adr/0196-integrate-reviewed-v19-v110-with-gui-history.md) record the integrations and full-filename0185/0186/0188/0189 collisions; [content loop](CONTENT_LOOP.md), WORKLOG and [GUI handover](GUI_MIGRATION_HANDOFF.md) preserve source-scoped history. Motion preparation remains provisional, not a named-gate qualification.
