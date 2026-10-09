# Status — cat_de_roman_esti

Last verified: 2026-10-09 — content loop resumed in this chat. Source6 live; V1.7 uninstalled.

- **GUI checkpoint:** core1.2 released; native7/current+candidate andfocusedMotion14 PASS; exact15 accepted/unapplied; deps64ea PASS. Fullnormalized replay/Node3/lint/unit/CSP/device/KIT_BUMP pending. Linuxsupervisor/worker paused.
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
- Historical V1.2 growth and qualification: [review](reviews/v1-2-content-growth/README.md); exact prior status retained in WORKLOG.
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
Qualified Source6 KG: `fixture-v1-6-everyday-inputs`, 2419 nodes/9473 links/8679 forms/180 exact puzzles.
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration has **252 concepts/352 recipes/148 discoveries**, 96 supplies, 12 tiers,
32 goals, ten historical books and 1156 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current qualified V1.6 pins

- alchimie_discovery_world_v92.json: `8f013a8f6b54a97a768a34c42e669addc4f5ab9823302befbe15ad811cae77ad`
- alchimie_recipe_extensions_v92.json: `d94647e78f8c2bd375b961f0aab52f3f7207024e60bed745b78c4a3d052d0bfc`
- quick_games_v92.json: `0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31`
- derived_catalog_v38.json: `fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf`
- cat_mobile_app_pack_contract.json: `282f18f6d81c623be004f28d4c5634bfbbbdf2294e466d842a9192123bc06fae`
Historical verification receipts: [WORKLOG](../WORKLOG.md), [V1.0.1](reviews/v1-0-1-hardening/README.md), [V1.2](reviews/v1-2-content-growth/README.md).

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
- **Source6 live; V1.7 uninstalled, zero integrated growth.** [ADR-0186](adr/0186-go-authoritative-content-validation.md): Go/native JSON authoritative; Python/Rust optional.
- Exact candidate I1200 preserves all1198 prior members and adds2 Go contract tests. [71 executions](reviews/v1-7-recognizable-content/go-source7-input-contracts-results.json) pass ordinary leafă→Salary/shared-slot/private-clue/Progress plus69 held-input cases; no new69-response HTTP corpus claim.
- Linux Extensions49, sealed candidate, ops840c/rail0724/check and backend389objects/38packages/27testdirs metadata persist; never replay completed content work or failed optional full-module inventory.
- Owner recovered disk/resumed this chat. Exact Go1.27.1 SDK restored once; [authcore inventory](reviews/v1-7-recognizable-content/go-source7-windows-authcore-metadata-inventory-r2.json) accepted242objects/1package/5source/3testfiles.
- [Fresh authcore race compilation](reviews/v1-7-recognizable-content/go-source7-windows-authcore-race-compile-results-r2.json) independently accepted: complete19010pre/post pins, binary06e480bc/16962965B,459763712B sampled parent peak, owned-group closure. Original reserve/scanner failures remain FAILED.
- [Authcore native gate](reviews/v1-7-recognizable-content/go-source7-windows-authcore-tests-results-r1.json) independently accepted: exact15-case listing, all15+13 race executions and full standalone vet; six19013pre/post checks,1008447488B parent peak, cleanup confirmed.
- [Five pinned web modules](reviews/v1-7-recognizable-content/go-source7-windows-five-module-acquisition-results-r1.json) genuinely acquired/Go-validated:1871files/23852260B, complete19023pre/post and both-host fingerprint, independently accepted. First offline rail build FAILED cumulative growth; exact failure/cleanup retained, no artifact. [Current rail build](reviews/v1-7-recognizable-content/go-source7-windows-current-rail-build-results-r3.json) independently accepted:e702a52c/34667895B, complete20915pre/post,800423936B peak/227532057B native growth/cleanup. Original growth/dispatch/collector failures retained. Next new Quick proposal/audit/same-role finals.
- All85 Quick boards freshly reassessed by actual current factual/quality roles using exact inherited stable evidence; fresh supported proposal/audit85boards/460requests/same-role finals remain required. Old runtime130/110 finals are stale; current runtime131 is static expectation.
- Full native/shared/Webkit coverage, independent Source7HTTP1207 corpus/selector, current/frozen assets, installed source/history/inverse/authority and exact assembled acceptance remain required. [Current continuation](reviews/v1-7-recognizable-content/README.md).
- Loop runs here, no new chats; GUI/perf separate, PG/provider/remote actions paused. No V1.8 before nonempty independently accepted all-green V1.7 local landing.
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859); forced fallback Societate/Secundă and mixed Personalități predicates.
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds
  (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and four spare concept slots remain.
## Doc map
- README/AGENTS: orientation; agent-map/testing: gates; ADRs (newest 0186), WORKLOG: history; [GUI motion preparation](reviews/gui-motion-baseline/README.md):29 provisional preview/69 focused checks;48 future cases UNEXECUTED; named-gate placement blocked.
