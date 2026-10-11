# Status — cat_de_roman_esti

Last verified: 2026-10-11 — actual full at e042587 (= GUI4f36 + main3f327c merge, ADR0194) failed only active route-JS budgets + aggregate exit; review branch `fix/gui-review-20261011` (ADR-0195) unit/full NOT RUN. Historical fd336 E3 proof and main V1.8 local qualification remain source-scoped.

- **GUI Linux current:** Core1.6 released; UI0.3 active/UI1.0.6 staged. Latest actual full at e042587 (2026-10-11, enforced CSP 0 violations, 37/39 checks) failed only the 10 active route-JS rows (Home115016 vs40960) plus aggregate exit; contentrails race used 1,385 of 1,800 s. Review branch `fix/gui-review-20261011` (local) adds fail-fast/fresh content tests, the canonical distroless M1 image (container port 8080) and no-behaviour test speedups; owner decisions 2026-10-11 (budget-only-red KIT_BUMP, Teacher/Social prep) in [ADR-0195](adr/0195-owner-decisions-review-m1-image-test-loop.md)/PROGRAM E5. Next: Paul trust pin → unit/full on that branch; combine local main V1.9/V1.10 with one full; KIT_BUMP core-v1.6 under E5. Samsung device checkpoint UNMET; budgets.json §4.7 vs E3 open. E3 preliminary only, no GREEN/M0/M1/M2 adoption. Earlier fd336 full, [focused d8](reviews/gui-normalized-react/frozen-baseline-focused-d8-checkpoint.json), [CLS erratum](reviews/gui-normalized-react/full-b03-cls-description-erratum.json) and old failures stay historical; ADR0194 integration and [handoff](GUI_MIGRATION_HANDOFF.md) carry detail.
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
- **V1.8 qualified locally on main3f327c (historical):** 30 reviewed items: 23 new concepts, six existing-owner input
  families and one directional link; +23 nodes/+93 links/+136 forms, zero new curated rounds.
  Leafă→Salariu; ogradă→Curte is a regional input; full non-colliding paradigms preserve owners.
  [Review](reviews/v1-8-everyday-core/README.md) and [pool](content-pool/v1-8-everyday-core/pool.json).
  Four native rails reconstruct exactly; owner-approved Cald assertions, HTTP1207 and API51 pass.
  Those main-only results do not qualify this combined GUI source; all fresh integration gates remain pending.
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
Qualified V1.8 KG: `fixture-v1-8-everyday-core`, 2442 nodes/9566 links/8815 forms/180 exact puzzles.
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration has **252 concepts/352 recipes/148 discoveries**, 96 supplies, 12 tiers,
32 goals, ten historical books and 1156 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current qualified V1.8 pins

- alchimie_discovery_world_v92.json: `dc0fd8737d3ed187c18f2ba246af524cb20ef2c9e0be35ed282b844decd7528a`
- alchimie_recipe_extensions_v92.json: `ff14ada7e6a048012fc774fcbe8e4fbd57ed4ed2981d236eabc0ddd82964f063`
- quick_games_v92.json: `d3a50586c0983cb6f2f291f1b042041840b7403fabc330554977575f7866791b`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `538cf0db0e9141c3bbb4676404f136ab1faab0f06023dee86d207a0ee775c99c`
- derived_catalog_v38.json: `e4535a059c253fbf07911ec04e476a4e9725b52aa025faa4967ffbaa936adb7e`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `da14c34310eac3a03c2b5438c18043a2a7da682af9e0d991eb105c0639696c8f`
- cat_mobile_app_pack_contract.json: `e753434dcc19cab6dd9f69b8349db431bed12807a7a0464fb2140d1db721dcbf`
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
- **V1.7 parked** ([ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md)): `codex/content-v1-7` (local 3377a68, origin fba9498) and `codex/content-v1-7-qualification` are not merged; zero integrated growth. V1.8 is the qualified content; [ADR-0186](adr/0186-go-authoritative-content-validation.md) keeps Go/native JSON authoritative. Outcome: [pool](content-pool/v1-7-recognizable-content/pool.json); leafă was independently integrated via V1.8 as a full-paradigm Salariu input.
- **Main3f327c V1.8 contentrails GREEN history** (verified 2026-10-11; combined NOT RUN): all four rails reconstruct exactly and re-audit under the current binary; contentrails/contentbuild race tests pass.
  Main records approved Cald assertions/content passes and known `TestManagedSPA*` failures; no combined result is inferred. [Procedure](CONTENT_LOOP.md), [ADR-0189](adr/0189-behaviour-bound-installed-content-authorities.md).
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859); forced fallback Societate/Secundă and mixed Personalități predicates.
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and four spare concept slots remain.
## Doc map
- README/AGENTS: orientation; agent-map/testing: gates; [ADR0194](adr/0194-integrate-reviewed-v18-with-gui-history.md) records current integration and full-filename0185/0186/0188/0189 collisions; [content loop](CONTENT_LOOP.md), WORKLOG and [GUI handover](GUI_MIGRATION_HANDOFF.md) preserve source-scoped history. Motion preparation remains provisional, not a named-gate qualification.
