# Status — cat_de_roman_esti

Last verified: 2026-10-01 — Go Intrusul pilot qualified locally; anonymous production remains V1.0.1.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
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
- V1 1.0.0 put game choices first, exposed rules directly, removed empty options and made
  replay primary; guarded storage reads and one persisted reload marker keep startup usable.
- Seven independently reviewed factual repairs correct Caraiman, Village Museum,
  Athenaeum, three Neagu labels and one false Operațiunea Monstrul–Dem Rădulescu edge.
  Every original KG puzzle, concept and accepted form remains.
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
Alchimie challenge refresh: 49 existing additions across 27 books; all 68 selectable books
retain their 521 recipes, routes and par. One former addition belongs to a reserved board.
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
- Isolated 3.12.13 wheel: version/health 1.0.1, 30 static files exact, six creates/resumes.
  V1 receipts: [1.0.0](reviews/v1-testing-release/verification.json), [1.0.1](reviews/v1-0-1-hardening/README.md).
- Physical devices and Safari/WebKit remain untested; Windows full suite requires WSL.

## Go migration pilot

- [ADR-0160](adr/0160-start-go-backend-with-native-intrusul.md): native Intrusul; other games Python.
  Pinned private content, deterministic selection, TTL/LRU/atomic actions, 64 KiB; loopback gateway.
- Local 2026-10-01: **2838 HTTP responses** matched Django; 1269 seeded/235 daily vectors,
  Go race/vet, Unicode-15 checks, **2466 existing backend + 2 export / 53 accounts**, validators,
  Ruff/docs/whitespace pass. Real local gateway: SPA + all six game creates 200; no deployment.
- Pilot peak RSS **16.0 MiB Go / 100.9 MiB Python**; different retained data/test harnesses,
  not full-port savings. [Guide and receipt](GO_BACKEND.md); hosted Go CI is not claimed.

## Production and next work

- Production: anonymous V1.0.1 `e29fb0f63df8f3fe4678b1ae8882b6712ba993be`, deployed
  2026-09-26 at the owner's request (GitHub CI green on that commit). Image tag
  `release-e29fb0f63df8`; rollback image `rollback-13e49b2c1148` (V91) stays on the host.
  Build 54 s while V91 served; recreate gave ~3 s of 502s (7/126 polls), then 200s.
- Post-deploy smoke: `/api/health` 1.0.1/2416 concepts, manifest
  `fixture-v1-reviewed-content` 2416/9458/180, accounts off, 14 categories, all six game
  starts 200, `/` `max-age=0`, legal pages filled; container healthy, 0 restarts, no 5xx.
- Origin `main` was published on 2026-09-23 at the owner's request: a fast-forward from
  `b25c949` through V99, V1 and V1.0.1 (merge `8e66ec0`). Accounts activation and
  recurring loop restart remain outside V1/1.0.1.
- Next: a same-Wi-Fi phone/desktop session with the tester guide, including an iPhone
  (Safari/WebKit is untested), an Android phone and enlarged text. Accounts stay off.
- Deferred to one reviewed content wave (each re-pins KG/pack/ranking digests): missing
  diacritics in some descriptions ("roman"/"român"), the false Toma Caragiu–Reconstituirea
  casting edge, generic-only Lanț `lt_personalitati_186`, off-theme single-board Conexiuni
  Limbă/Geografie Greu shelves, label spellings (Herta Müller, Mica Unire 1859).
- Known limits: Alchimie Greu starts on shelves without a curated board can take seconds
  (a time cap would break deterministic dailies); older stored score details keep ISO dates
  but display as dd.mm.yyyy. The held Familie gradient and five spare concept slots remain.

## Doc map

- README/AGENTS: orientation; agent-map/testing: routes/gates; ADRs (newest 0160), reviews/WORKLOG: history.
