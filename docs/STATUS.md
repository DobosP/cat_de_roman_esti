# Status — cat_de_roman_esti

Last verified: 2026-09-23 — V1 hardened as local 1.0.1; physical-device and human testing next.

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

- 1.0.1 (2026-09-23): complete backend **2466 passed** + **53 accounts** (WSL, Python 3.14.4,
  constrained); frontend unit **240 passed**, lint, typecheck, build (initial gzip 119.78 of
  120.0 KiB); both validators, Ruff, reserve builder, docs check and whitespace pass.
- 1.0.1 browser: one all-green full Playwright run, **622/622** (desktop + Pixel 7 emulation,
  Microsoft Edge on Windows, 2 workers, no retries). An earlier full run's single Lanț
  late-404 failure did not recur in 200/200 repeated recovery cases (host under load).
- 1.0.1 isolated wheel (Python 3.12.13): version and `/api/health` 1.0.1, revalidated shell,
  all 30 static files exact, six games create and resume, curated counts unchanged.
- V1 1.0.0 gates (2446 backend, 224 frontend, 588 composed browser cases, factual audits,
  recipe and quick-board replays) stay in the [verification](reviews/v1-testing-release/verification.json) record.
- The complete suite needs WSL (Unix `resource` import); human enjoyment, physical devices
  and Safari/WebKit remain untested; browser emulation does not substitute for them.

## Production and next work

- Last recorded production: anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`
  (no live production recheck in this task).
  No push, deployment, accounts activation or recurring loop restart is part of V1/1.0.1.
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

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0159), reviews and WORKLOG: decisions, evidence and history.
