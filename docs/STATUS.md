# Status — cat_de_roman_esti

Last verified: 2026-10-05 — native toolchain qualified locally; production remains anonymous V1.0.1.

- **GitHub Actions (Last verified: 2026-10-04):** owner-requested on-demand policy,
  [ADR-0164](adr/0164-manual-github-actions.md). Workflows use `workflow_dispatch`; automatic
  push/PR/label/schedule runs are removed. Existing jobs, inputs, and safety gates
  remain. Workflow YAML, manual inputs, job dependencies, and permission preservation
  were checked; this configuration edit does not refresh application test results.

## Current state

- The owner requested internal V100 as a testing release named **V1** for mixed ages on
  phones and desktop. Package **1.0.1** (lobby badge **V1.0.1**) hardens the V1 1.0.0
  release `2ba8a8b` after an independent review; decision [ADR-0159](adr/0159-v1-0-1-testing-hardening.md).
- 1.0.1: a 0-point loss is never a record; circuit daily intent is single-use (one resume
  notice; Intrusul/Perechi results offer the pending daily); Conexiuni/Intrusul/Perechi
  boards step 4/2/1 columns only; Lanț stacks its route on phones and Alchimie keeps long
  words whole on enlarged text. Lanț has "Începe alt lanț", an announced position and
  "salturi"; Cald sau Rece shows "Arată răspunsul" and rules below play.
- 1.0.1: a failed optional AccountBar renders nothing instead of a game error; the reserve
  loads at startup and reserve drift returns the game's JSON 503; `/` revalidates on
  every load; `/api/health` reports `version`. Quick-game tiles are display-capitalised
  (reviewed lowercase allowlist); server copy has diacritics and correct plurals.
- Three reviewed captions explain the held Ghiozdan→Capra cu trei iezi board. Fresh
  independent analyst/verifier gates promote that single board; both natural routes win.
  All 117 earlier captions remain exact; 120 caption entries now have reviewed text.
- A finite reviewed reserve excludes 20 pack rounds and three quick boards from new
  bundled selection. Archived records remain unchanged. Custom development overrides
  retain their previous unranked compatibility scope under ADR-0158.
- Reconsideration retains all 256 historical rejections and seven other pending boards.
  The V99 pool remains 12 research proposals (eight researched/four held), none installed;
  the three V98 recipe continuation ideas remain research. Quality gates were not lowered.
- The repository [content skill](../.agents/skills/romanian-game-content/SKILL.md) retains
  conservative refinement and experimental discovery as separate tracks.
- Decision/evidence: [ADR-0158](adr/0158-v1-testing-release.md),
  [release review](reviews/v1-testing-release/README.md), [ADR-0159](adr/0159-v1-0-1-testing-hardening.md),
  [Romanian tester guide](TESTARE_V1.md) (now with a same-Wi-Fi phone setup and known limits).
## Inventory and invariants

| Game | Total | Approved | Pending | New-round pool |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 83 eligible |
| Cald sau Rece | 265 | 263 | 2 | 255 eligible |
| Lanțul Cuvintelor | 123 | 121 | 2 | 121 eligible |
| Alchimie | 83 | 80 | 3 | 68 eligible |
| Intrusul | 228 | 228 | 0 | 226 selectable / 188 preferred |
| Perechi | 193 | 193 | 0 | 192 selectable / 153 preferred |

Pack **716 = 709 approved + 7 pending**, 527 eligible. Quick **421 stored / 418 selectable**;
341 preferred, starter pools 62/61. The 85 authored and 336 frozen quick payloads stay exact.
Pool counts describe curated records; existing on-demand fallback generators remain.
KG: `fixture-v1-reviewed-content`, 2416 nodes/9458 links/8641 forms/180 puzzles.
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books retain
521 recipes, routes and par. One former addition belongs to a reserved board.
Exploration remains **251 concepts/351 recipes/147 discoveries**, 96 supplies, 12 tiers,
32 goals, nine historical books and 1009 verified saved prefixes.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts/128 observed empty pairs;
sixteen histories and 2 MiB pre-write bounds remain. Quick supplements ≤256 boards/2 MiB.
Unrevealed answers, recipe maps and routes stay private.
## Current artifact pins

- alchimie_discovery_world_v92.json: `0b3fea2c30b4c729cbe8398bc467e5a4f7e6a443ff886023a07d9bf0e40e9f44`
- alchimie_recipe_extensions_v92.json: `c52035abbbf08f6a1d4c1b50d8048bc5efcf3c7a4f2c9daca0096cb3444c9661`
- quick_games_v92.json: `85c89ec82d27a19ba619604ed3c47b09e3bb18e1718343db6d56c03b0999761c`
- games_pack.json: `e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8`
- board_rankings_v37.json: `bf7a88448ce7cb8d21d95defc745517d97c8542f582d66eadbfb92ef54bd4adc`
- derived_catalog_v38.json: `bea0732aefeb0af59e99c926f893bc9f6bb54bae3bb371eace238872470ac2a4`
- release_reserve_v1.json: `fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `1c74e5fe387b20ed196f76588d1ef96658743776817532c09a17ab9dd0a39b64`
- cat_mobile_app_pack_contract.json: `82304733284ca62245e0d2ac0abb7b81c991ed1857ca904c990116c5bce280b4`
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
- Native source/tooling stage [ADR-0165](adr/0165-native-source-build-and-qualification.md):
  exact eight-source export, 180 terminal paths, 32 neutral body cases and 1009 saved prefixes pass.
  Native compiled parity 1207/1207, synthetic smoke151/28asset proofs, REST/mobile/docs race/vet pass.
  Native operators/builders/tagged input and neutral release coupling (optional legacy) pass.
- [ADR-0166](adr/0166-native-content-operators-and-builder-rails.md): independent review/rollback/v2 rails pass.
  [ADR-0167](adr/0167-close-unread-bodies-on-early-refusal.md):13 TCP gates/32 body/1207 parity and strict scalar envelopes pass; auth unchanged.
  [ADR-0168](adr/0168-qualify-complete-native-toolchain.md): clean native Go/PG/Node242/browser622 GREEN.
  Accepted origin4fcf manual policy is integrated; native Go/Node gates default, references opt-in.
- Next: same-Wi-Fi phone/desktop testing, iPhone (Safari/WebKit untested), Android and enlarged text.
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859).
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds
  (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and five spare concept slots remain.
## Doc map

- README/AGENTS: orientation; agent-map/testing: routes/gates; ADRs (newest 0168), reviews/WORKLOG: history.
