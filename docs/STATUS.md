# Status — cat_de_roman_esti

Last verified: 2026-09-17 — V96 landed; V97 compatibility and content drafting started.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V95 landed on main `1457786`; [GitHub CI 35026423470 passed](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35026423470).
- V96 is landed and pushed on main `36db143` (implementation `57d5bcc`).
  [GitHub CI 35155920107](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35155920107)
  passed both backend jobs; one of 540 browser cases hit a test-interception race.
  A V96 correction is being verified separately. Its original verified worktree was cleaned.
- V97 starts locally in `feat/v97-discovery-continuity-and-new-words`. Saved-book
  compatibility design, fresh content and twelve earned-caption drafts are recorded.
  All new proposals remain unapproved; the served inventory below remains landed V96.
- **Five new rounds/targets, two Alchimie concepts and five recipes**: one each for
  Conexiuni, Cald sau Rece, Lanț, Intrusul and Perechi. Fresh per-game exposures are
  seven Conexiuni words, three Intrusul words and four Perechi words; shared KG is exact.
- New Conexiuni groups cover parents/grandparents, drinks, opening for passage and
  sharpening. Covor has useful floor/home/vacuum-cleaner openers. Lanț connects
  Vanilie→Brânză through Poale-n brâu or Pască with a wide beginner corridor.
- Alchimie: **249 concepts, 347 recipes, 145 discoveries**. Ostropel and Salată de fructe
  each have two recipes; Chiftele de legume gains an onward Sandviș route. Alternatives
  grow 97→99, intermediates 63→64. Both new results are terminal.
- Every prior 247 concept/342 recipe record is exact. Eight starters, 96 supplies, twelve tiers
  and 32 goals remain exact. Eight historical saved books preserve all earned progress.
  The existing eight-book limit is now full: settle compatibility before further recipes.
- Unsupported Cald sau Rece input explicitly costs no attempt. Advisory spelling uses
  conservative displayed-label checks; Nuci/Prafzz help remains, while fier→fluier and
  reparație→pârâu are withheld. Exact/fuzzy resolution, projections, scoring and privacy
  stay unchanged; this adds no synonyms or missing vocabulary.
- Alchimie lost-response GET recovery restores a usable activated word or collection
  fallback, respecting focus moved elsewhere, save ownership and generation checks.
  Mutations are never replayed; cached retries retain V95's synchronous focus handling.
- Decision/evidence: [ADR-0154](adr/0154-expand-content-and-clarify-input-recovery.md),
  [V96 final review](reviews/v96-words-and-input-clarity/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 244 | 244 | 0 | 86 eligible |
| Cald sau Rece | 264 | 262 | 2 | 258 eligible |
| Lanțul Cuvintelor | 122 | 119 | 3 | 119 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 227 | 227 | 0 | 188 preferred |
| Perechi | 192 | 192 | 0 | 152 preferred |

Pack **713 = 705 approved + 8 pending**, with 543 eligible records. All 710 prior pack records,
336 core quick boards and 81 authored payloads/scores stay exact. The supplement now has 83
boards; both additions qualify as starters. Starter shelves: 61 Intrusul/60 Perechi.
All 105 Lanț rejection records and 101 custom captions remain exact; ranking metadata recomputes.
KG/mobile: `fixture-v90-household-discovery`, **2416 nodes/9459 links/8641 forms/180 puzzles**.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration stays ≤256 concepts/512 recipes/256 saved crafts, with 128 observed
empty pairs per session; quick supplements ≤256 boards/2 MiB. Recipes/routes/answers stay private.

## Current artifact pins

- alchimie_discovery_world_v92.json: `356270c25d61f16cac3fdb59efa1e0399b18606ee796d498f132a92ad3c9d5c4`
- alchimie_recipe_extensions_v92.json: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- quick_games_v92.json: `75e052c7cb1595bc77a6181bed734893f3d1dc6b0c6fa6c7bb05a91a6a1119d7`
- games_pack.json: `f2538a91726da87a519f8efac5d3a9993a8a23445879af817f08bdabd478e307`
- board_rankings_v37.json: `bee608938a113922842ec987bf44269ae086f45aaeb9c54f68e39c8f160bd9d3`
- derived_catalog_v38.json: `9c46598b19acd30e82cf7bf542c82b8fcfe5039f607bc689ef27a98e78e3d76c`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- cat_mobile_app_pack_contract.json: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- manifest.json: `ec5724d7afb7f49ae6ad367648676a071f0d0751b82d27ae39278e98fde0004d`

## Verification

- Python 3.12 and 3.14 each pass **2236 backend/53 account tests**; browser **540 pass**,
  native frontend **212 pass**. Both validators, Ruff, frontend lint/typecheck/build, docs
  and whitespace pass. Initial gzip **119.23/120 KiB**.
- [Final integration receipt](reviews/v96-words-and-input-clarity/integration/verification.json)
  binds assembled inputs, exact artifacts, final approvals and preserved initial failures.
- World lane: 36 wave/history and 136 catalog/exploration checks pass; final audit covers
  all 347 recipes, 33 free/goal runs and eight historical books. Old 247/342 records are exact.
- Quick: 83 natural winning replays plus both new recovery/starter journeys pass; all 81
  prior authored payloads/scores and 336 core boards remain exact.
- All three pack additions select and win through public requests, including both Lanț
  routes and wrong/repeat/hint/GET recovery. The strict five-artifact inverse restores
  exact 1457786 bytes; all 263 previous target profiles remain exact. Only Lanț's browser
  seeded start changes.
- Input review: 174 focused feedback cases, independent 60-case backend pass and 12 fresh
  desktop/mobile focus/input journeys pass. Independent closure binds artifacts and code.
- Both preview origins now serve V96's 249/347 world from landed main. [Landing receipt](reviews/v96-words-and-input-clarity/landing.json).

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`.
  V96 is on main; V97 preparation remains local. Deployment is separate.
- [V97 session](reviews/v97-discovery-continuity-and-new-words/README.md) must settle saved-book
  compatibility before further Alchimie recipe changes.
  More specific earned Lanț captions, missing common words and target calibration remain.
- Existing Caraiman/museum/Dem/Ateneul description debt, Neagu labels and pending A5
  holds remain. No earlier queue is silently approved. Human playtesting and device
  acceptance remain; accounts stay off until DEPLOY gates pass.

## Doc map

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0154), reviews and WORKLOG: decisions, evidence and history.
