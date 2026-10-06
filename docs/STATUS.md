# Status — cat_de_roman_esti

Last verified: 2026-10-06 — V1.5 i07 source screen independently accepted with adoption held; discovery active; native held; V1.4 retained.

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
- **V1.2 landed locally17f7da1:** four reviewed synonym families (ascensor, tomată, scripcă, prăvălie),
  22 distinct forms and Cărare↔Potecă; zero new concepts/curated rounds. Old records,
  recipe cores/histories/pools persist. [Review](reviews/v1-2-content-growth/README.md),
  [ADR-0170](adr/0170-v1-2-reviewed-content-growth.md), [pool](content-pool/v1-2-synonyms-and-links/pool.json).
- V1.2 baseline authority reconstructs all four rails exactly; source/export/mobile/rank/derive,
  independent Python export,1207 current HTTP, history68 and new synonym/hop race checks pass.
  Full native/shared race/vet,smoke151/assets28/docs and assembled review GREEN; old content heartbeat PAUSED.
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
Task KG: `fixture-v1-4-time-links`, 2419 nodes/9473 links/8677 forms/180 exact puzzles.
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration remains **251 concepts/351 recipes/147 discoveries**, 96 supplies, 12 tiers,
32 goals, nine historical books and 1009 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current artifact pins

- alchimie_discovery_world_v92.json: `0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef`
- alchimie_recipe_extensions_v92.json: `1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7`
- quick_games_v92.json: `a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef`
- derived_catalog_v38.json: `25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6`
- cat_mobile_app_pack_contract.json: `2f756c7d71f65a1367648d477c67d6d1af0bd19411149667b77f3cf77a6153b8`
## Verification

- 1.0.1 (2026-09-23): **2466 backend / 53 accounts**, **240 frontend**, lint/typecheck/build
  (119.78/120 KiB gzip), validators, reserve builder, docs and whitespace; **622/622** browser
  cases (Edge desktop/Pixel 7, no retries), plus 200 repeated Lanț recovery cases pass.
  V1 receipts: [1.0.0](reviews/v1-testing-release/verification.json), [1.0.1](reviews/v1-0-1-hardening/README.md).

## Selected Go backend

- [ADR-0162](adr/0162-select-go-production-backend.md): owner-selected Go-only production runtime;
  six games/mining, exploration/restores, metadata/OpenAPI, legal pages and SPA are native Go.
  Canonical launcher/Docker/anonymous profile have no Python serving process or fallback.
- Serving qualification: **1207 HTTP responses/runtime** match Django; all games and nine histories
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
  Source3/allfour authority/source/export/native+shared race/vet/HTTP1207/history305/frontend242 GREEN; assembled ACCEPT95f94e3; locally landed082ba99; [V1.4](reviews/v1-4-time-links-and-predicates/README.md) graph0nodes/2forms/2links accepted/applied; Source4/current4authority/native+shared race/vet/export+Python/HTTP1207/history394/smoke151+28/docs GREEN; assembled ACCEPT672d656; locally landedfd09b3b; [pool3integrated/3held](content-pool/v1-4-time-links-and-predicates/pool.json); [V1.5](reviews/v1-5-small-objects/README.md) r3 remains2researched/6held,0selected/installed; [i01](reviews/v1-5-small-objects/iterations/i01/README.md) Breloc1/1/Pâlnie4/1 held; [i02](reviews/v1-5-small-objects/iterations/i02/README.md) two existing-direction hypotheses source-reviewed,2held/0selected/installed;136 exact bindings/89 named-test definitions/docs/budgets/default whitespace PASS, all actual native/play/installation gates NOT RUN; WAITING_NATIVE_WINDOW; loop ACTIVE per [ADR-0173](adr/0173-resume-bounded-content-version-loop.md); [i03](reviews/v1-5-small-objects/iterations/i03/README.md)21raw/8deep/9held/11ideas/1rejected/0selected/installed,35 source bindings; b02casting screen held; independent factual/quality source-only acceptance; discovery continues per [ADR-0174](adr/0174-continue-discovery-during-qualification-holds.md). [i04](reviews/v1-5-small-objects/iterations/i04/README.md):12records/11new/1follow-up/5deep/0selected/installed; Ciocolată caldă researched, other10held/1rejected; r1 preserved; bound r2 factual/quality source acceptance; native/gameplay/history NOT RUN; discovery ACTIVE. [i05](reviews/v1-5-small-objects/iterations/i05/README.md):6records/1known-input exclusion/5deep/3researched/2held/1rejected/0ready/selected/installed; recipe and label research only, exact frozen reviews; discovery ACTIVE. [i06](reviews/v1-5-small-objects/iterations/i06/README.md):1material beverage refinement/4fresh hypotheses/2deep/1researched/4held/0ready/selected/installed;19 frozen bindings; independent factual/quality source acceptance only; native restore/new-service gap NOT RUN; prior turn cap failed and preserved. [i07](reviews/v1-5-small-objects/iterations/i07/README.md):R2 six fresh held/three directions/three deep investigations/four sourced records/zero ready/selected/installed;R1 incorrect novelty preserved,35bindings; independent factual/quality source acceptance; resource wait resumed only above16GiB.
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859); forced fallback Societate/Secundă and mixed Personalități predicates.
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds
  (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and five spare concept slots remain.
## Doc map

- README/AGENTS: orientation; agent-map/testing: routes/gates; ADRs (newest 0174), reviews/WORKLOG: history.
