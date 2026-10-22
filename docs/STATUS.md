# Status — cat_de_roman_esti

Last verified: 2026-10-21 — KIT_BUMP core-v1.13 ([ADR-0209](adr/0209-kit-bump-core-v1-13.md)), product ce04b124: unit27, full37 (937/0 skip-unexpected-flaky, CSP enforced 0), image2; release image Trivy exit 0 ([record](reviews/kit-bump-core-v113/README.md)); before that go1.27.3 security release builders ([ADR-0208](adr/0208-go-1-27-3-security-release-builders.md)) plus an Alchimie resume-race fix (Cald sau Rece keeps the same latent race: follow-up), product 99f507f4: unit27, full37 on the second full after one failed browser case (937/0 skip-retry-flaky), image2 ([record](reviews/go-1-27-3-security/README.md)); publication-review follow-ups KFA-1/EQ-1/EQ-2/DCR-1 on product 20dab663: unit27/full37 (937 browser) and independent review pass ([record](reviews/gui-publication-followups/README.md)); before that `main` fb829aaa was published (Paul-authorized, [ADR-0206](adr/0206-owner-authorized-main-publication.md), [review](reviews/gui-main-publication/README.md)). Production/accounts remain owner-only.

- **Historical GUI M2 accepted on `main` c9017b5b (2026-10-13; [ADR-0198](adr/0198-owner-lands-m2-before-device-checkpoint.md), [ADR-0199](adr/0199-owner-no-device-checkpoint-agent-lands-m3-m4.md)):** UI1 active on core-v1.9 (`@roedu/ui` 1.0.9 / web-kit 0.1.9), Preact 11 + preact-iso shell; `/`, `/intrusul`, `/perechi`, `/conexiuni` ported (kit Presence, Conexiuni per-tile `variant`) and served by the current bundle, every other route by the frozen legacy bundle (ADR-0197). Unit 26/26 (route JS gz `/` 26,641, `/intrusul` 38,088, `/perechi` 38,915, `/conexiuni` 40,377 ≤ 40,960); full 37/37: browser 933/933, nine exact PNGs, axe, vitals, CSP enforced 0/0 (4 current + 5 frozen pages), PG, parity. REQ-9/REQ-10 workarounds were replaced by the later core-v1.10 landing below. [Bindings and findings](reviews/gui-m2-activation/bindings.md). **GUI Linux previous:** [M1-close b3f5f61](reviews/gui-normalized-react/m1-close-b3f5f61.json): 37/39, only E3 route-JS rows + aggregate red.
- **GitHub Actions:** [ADR-0164](adr/0164-manual-github-actions.md), checked2026-10-05; required Go/Node dispatch, references opt-in, no hosted run.

## Current state
- **S1 M3/M4 accepted and published:** M3 source9c44d01f and final M4 source16733891 complete all current Preact11/core-v1.11 routes and both Alchimie modes through managed Go delivery. Final unit27/full38/image2 and independent review pass:570Node+6actualVitest,1930backend identity union/28auth; freshPG12/301 closes17DSN obligations, parity1206,933browser/0skip-retry-flaky,9byte-exact originals/Axe/Home/five-run vitals/CSP0/legacy/cleanup. CSS16,043≤16,093 includes21gzip bytes from the protected empty sheet (actual level-9 vs original level-6 gzip; like-for-like headroom 3 B, [ADR-0205 erratum](adr/0205-canonical-game-css-and-browser-contracts.md)); HomeJS28,879/30,720 target, Challenge40,714/40,960; all10caps pass. Warm unit7.12min/full20.07min retain strict reuse policy. Full/release images differ but actual26,042,528B app payload is byte-identical. [Qualification](reviews/gui-m4/qualification.json), [independent acceptance](reviews/gui-m4/independent-acceptance.json), [completion report](execplans/gui-game-renovation.md). Published on `origin/main` fb829aaa (2026-10-21); production and accounts remain owner-only. Review follow-ups (product 20dab663, unit27/full37, [record](reviews/gui-publication-followups/README.md)): KFA-1 Conexiuni Esc/Backspace and Lanț live-region e2e, mutation-proven (937 browser cases); DCR-1 cat-server refuses to serve an unadmitted managed UI ([ADR-0207](adr/0207-fail-fast-on-unavailable-managed-ui.md)); EQ-1/EQ-2 record corrections. Open low items: GSP-1, KFA-2, DCR-2 (owner), DCR-5, DCR-6.
- **Core-v1.10 adopted on local `main` f8c00f80:** UI1.0.10/web-kit0.1.10; canonical CSS order, kit-bound frozen CSP, full bootstrap closure/lock refresh and retired planner refusals. Clean unit27/full37 (548 unit cases,933 browser cases,nine exact PNGs,CSP9/0) and independent review pass. Full19.15min exceeds15min aspiration ([ADR-0201](adr/0201-core-v110-consumer-contracts.md), [qualification](reviews/gui-core-v110-adoption/qualification.json)).
- **Lighter GUI gates qualified:** `fix/gui-cat-lighter-gates` d98fe50e: cold unit27, full37 (933 cases/nine exact PNGs/CSP0), warm unit27. Full13.64min vs34.44; warm5.42min vs~21 (five-minute target missed by25s). Independent review verifies retained historical assertions and fresh GUI/API coverage ([ADR-0200](adr/0200-bound-gate-evidence-reuse.md), [qualification](reviews/gui-lighter-gates/qualification.json)).
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
- **V1.13 qualified locally:** 43 reviewed items:41 new weather/landscape concepts and two input families;
  +41 nodes/+167 links/+188 exact forms, zero new curated rounds or hidden-target approvals.
  All229 added headwords/forms resolve into43 real slots in315 API requests; protected owners remain.
  [Review](reviews/v1-13-weather-and-landscape/README.md) and [pool](content-pool/v1-13-weather-and-landscape/pool.json); nine legacy HopGame puzzles regenerated.
  Four exact native rails; owner-approved Cald expectations and V1.13 HTTP1206 pass.
  Full native race has only the two unchanged main managed-SPA failures; all content gates pass.
## Inventory and invariants

| Game | Total | Approved | Pending | New-round pool |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 83 eligible |
| Cald sau Rece | 265 | 263 | 2 | 255 eligible |
| Lanțul Cuvintelor | 123 | 121 | 2 | 121 eligible |
| Alchimie | 83 | 80 | 3 | 68 eligible |
| Intrusul | 228 | 228 | 0 | 226 selectable / 188 preferred |
| Perechi | 193 | 193 | 0 | 192 selectable / 153 preferred |

Pack **716 = 709 approved + 7 pending**,527 eligible; quick421/418,341 preferred, starter62/61. The85 authored/336 frozen payloads stay exact. Pool counts describe curated records; existing on-demand fallback generators remain.
Qualified V1.13 KG: `fixture-v1-13-weather-and-landscape`, 2584 nodes/10141 links/9520 forms/180 puzzle IDs (nine regenerated).
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration has **252 concepts/352 recipes/148 discoveries**, 96 supplies, 12 tiers,
32 goals, ten historical books and 1156 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current qualified V1.13 pins

- alchimie_discovery_world_v92.json: `2b4e18f8e5f231c0e94f30567366fe18a4d3677093f4fd590d0ecfebefb0cfff`
- alchimie_recipe_extensions_v92.json: `fe3265069003aaca36cd9d7d1a1a49f2768374f6872e19b0ea53516670192dcd`
- quick_games_v92.json: `36bed57411692dbb714fc4978b7d8193d3012cf1bb2a2bf4e48e14a01d29af31`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `7380a013c0ee14cd40c78b5469352346e945f42b90ca3a305fb17bc379cbad60`
- derived_catalog_v38.json: `6ede0ddfb44346bcd5595b08f4de7739aea64e0724f090ba6dd8d54059f525eb`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d8c7a8226e7b128ef613aeeebedbd6af8529e5dd1d56676c3a8b1a6b86c886fc`
- cat_mobile_app_pack_contract.json: `8201d8bde02881f36f4d832c863f4ff71fc44f9dc38161010287deedacb7d770`
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

- **Security hold (2026-10-21), resolved in source:** main fb829aaa had 14 reachable go1.27.1 standard-library vulnerabilities (govulncheck v1.8.0) and one Trivy HIGH (`golang.org/x/net` v0.59.0 CVE-2026-78669). [ADR-0208](adr/0208-go-1-27-3-security-release-builders.md) moved release/CI builders to go1.27.3; [ADR-0209](adr/0209-kit-bump-core-v1-13.md) (KIT_BUMP core-v1.13) moves x/net v0.60.0, the gate runner and the `go-backend` `go` line. Release image ce04b124: Trivy 0.75.0 exit 0; govulncheck v1.8.0 source 0, package 0, binary on the symbol-retaining same-source twin exit 0. The twin is `CGO_ENABLED=0 go build -trimpath ./cmd/cat-server` and its only difference affecting Go code from the release build is `-ldflags="-s -w"`. The stripped release binary exits 3 on GO-2026-5932 only, a documented non-actionable residual: x/crypto/openpgp, no fix, not linked ([record](reviews/kit-bump-core-v113/README.md)). Core-v1.12 stays published but unadopted (roedu-ui ADR-0036). The deployed V1.0.1 image is still go1.27.1 (11 HIGH/CRITICAL); redeploy is Paul's decision. Content loop: [V2 procedure draft](CONTENT_LOOP.md) ([ADR-0211](adr/0211-content-loop-v2-all-boards.md)) awaits Paul's review; all-board B1→C1→B2 and staged stock curation retain go1.27.3; old automation paused.
- Production: anonymous V1.0.1 **Go** `abe933779f04c46a32ff0194b5111e68086ba93f`, deployed
  2026-10-04 after all required [CI37208742166](https://github.com/DobosP/cat_de_roman_esti/actions/runs/37208742166) jobs passed.
  Native account/proposal code is shipped dormant; no Python serving runtime.
- Local **622/622 browser**,242 frontend assertions, account/game concurrency/race/vet and
  **1207 HTTP parity** pass. Candidate/public **151 requests each**, six games/exploration,
 28 asset/cache/HEAD proofs pass; current content/legal configuration and accountsoff verified.
- UID10001/read-only, healthy/zero restarts; fixedPCRE2 and zero fixableHIGH/CRITICAL image gate.
  Caddy/certificates/volumes preserved; previousGo+Python rollback profiles retained.
  [Complete rollout proof](reviews/go-completion/README.md). No provider/minor activation.
- Native source/tooling [ADR-0165](adr/0165-native-source-build-and-qualification.md): eight-source export, terminal180/body32/prefix1009/HTTP1207/smoke151/assets28 and operator/race/vet proofs pass; capture archived.
- [ADR-0166](adr/0166-native-content-operators-and-builder-rails.md): independent review/rollback/v2 rails pass.
  [ADR-0167](adr/0167-close-unread-bodies-on-early-refusal.md):13 TCP gates/32 body/1207 parity and strict scalar envelopes pass; auth unchanged.
  [ADR-0168](adr/0168-qualify-complete-native-toolchain.md): native qualification remains historical evidence.
- V1.3: [pool3integrated/5held](content-pool/v1-3-everyday-concepts/pool.json), [integration](reviews/v1-3-everyday-concepts/README.md); graph3/12/12 accepted/applied.
- **V1.7 parked** ([ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md)): `codex/content-v1-7` (local 3377a68, origin fba9498) and `codex/content-v1-7-qualification` are not merged; zero integrated growth. V1.13 is the qualified content; [ADR-0186](adr/0186-go-authoritative-content-validation.md) keeps Go/native JSON authoritative. Outcome: [pool](content-pool/v1-7-recognizable-content/pool.json); leafă was independently integrated via V1.8 as a full-paradigm Salariu input.
- **V1.13 contentrails GREEN** (verified 2026-10-12): all four rails reconstruct exactly and re-audit under the current binary; contentrails/contentbuild race tests pass.
  Owner-approved Cald assertions and all content gates pass; only known main `TestManagedSPA*` failures remain. [Procedure](CONTENT_LOOP.md), [ADR-0189](adr/0189-behaviour-bound-installed-content-authorities.md).
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859); forced fallback Societate/Secundă and mixed Personalități predicates.
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds (a time cap would break deterministic dailies); older stored score details keep ISO dates but display as dd.mm.yyyy. The held Familie gradient and four spare concept slots remain.
## Doc map
- README/AGENTS: orientation; agent-map/testing: gates; [ADR0194](adr/0194-integrate-reviewed-v18-with-gui-history.md)/[ADR0196](adr/0196-integrate-reviewed-v19-v110-with-gui-history.md) record the integrations and full-filename0185/0186/0188/0189 collisions; [content loop](CONTENT_LOOP.md), WORKLOG and [GUI handover](GUI_MIGRATION_HANDOFF.md) preserve source-scoped history. Motion preparation remains provisional, not a named-gate qualification.
