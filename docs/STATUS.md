# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 concept expansion; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner requested more Alchimie concepts. V92 continues on `feat/v92-alchimie-gui`
  from `2257766`; no V93, recurring iteration, publication or deployment.
- **Bucătăria românească** now has **111 concepts (+36)**, **116 recipes (+59)** and
  **19 optional goals (+10)**. The additions are **19 crafted discoveries + 17 pantry supplies**.
  Total crafted results: **58**; initial starters: **8**; later supplies: **45**.
- The original 75 concept records, 57 recipe records, starters, four pantry tiers and
  nine goals remain exact. New pantry tiers unlock at **30/36** crafted discoveries;
  original thresholds **3/8/16/24** remain. Previously completed collections can continue.
- Reusable crafted concepts grow **12→23**, and results with alternative recipes **18→40**.
  Seven old terminal discoveries gain uses: bread, roast meat, bean spread, salad, garlic
  sauce, pasta and jam. Thirty-five crafted dishes remain terminal. All 111 items are reachable.
- New discoveries include sandvișuri, clătite, pizza, șnițele, zacuscă, urdă, mucenici,
  cornulețe, halva and plăcinte. All IDs already existed in the unchanged KG. New world
  definitions are reviewed; original source snapshots/provenance remain intact.
- Reviewed historical mechanics allow old checkpoints to upgrade without losing earned
  concepts, recipes or goals. Live sessions upgrade before reads and mutations. Unknown
  versions still fail; an old fingerprint cannot claim newly added recipes.
- State adds bounded `compatible_recipe_hashes`; browser saves merge across versions only
  along explicit server compatibility and retain the newer book. No client guesses which
  recipes remain valid. Existing same-version recovery and saved collections remain supported.
- Both semantic reviews cover all 116 recipes: 57 byte-matched inherited judgments plus
  59 new reviews, with 36 new concept descriptions checked. Two final reviews bind the
  exact catalog and runtime replay before the generator's atomic package write.
- Direct two-tap/drag input, free hints, automatic supplies, optional goals, search and
  collection/journal remain. Goals never change pair results or stop exploration.
- Scored **Provocări**, daily routing, earlier 50 challenge additions and other games
  remain unchanged. Challenge books retain their scoped rules. Decision/evidence:
  [ADR-0146](adr/0146-expand-alchimie-and-preserve-collections.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 234 | 234 | 0 | 76 eligible |
| Cald sau Rece | 244 | 242 | 2 | 238 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **661 = 653 approved + 8 pending**, with **491 eligible** original four-game records.
KG remains `fixture-v90-household-discovery`: **2416 nodes/9459 links/8641 forms/180 puzzles**.
Graph/pack concepts, links, forms, puzzles, rounds, approvals, eligibility and the 336
frozen derived boards remain exact. The earlier challenge catalog adds 50 rules; exploration
has a separate 116-recipe world.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration has its own capped store and <=128 concepts/512 recipes/128-craft
checkpoints. Private recipes, routes and unearned target IDs remain server-controlled.

## Current artifact pins

- Discovery world: `2ca7f281c801a4c2e044134c94dfcb29ff5e51a9c2d4982ba3076818f1040a6d`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- `games_pack.json`: `6bf27de5da270258290ecb4ed41c3ef60a609e3e153855f38b7556a7f2aedeca`
- `board_rankings_v37.json`: `01fc906e390b8d3135f1856930458aa86873a525049b419eceb8652c72f717f8`
- `derived_catalog_v38.json`: `53fb3e4555205179072bd54a45f5b1b185de064625893dcf288902574a075e64`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Final Python 3.12 backend **1805 pass**, accounts **53 pass**, focused API/catalog/mobile
  **111 pass**. Ruff, whitespace and fixture/pack validators are GREEN. Python 3.14 was not rerun.
- Frontend native **209 pass**, lint/typecheck/build GREEN at **119.23/120 KiB** initial gzip.
  Full browser **444 pass** (four workers, zero retries); exploration focus **22 pass**,
  including actual original-checkpoint migration. Local preview restored its existing collection.
- Serving audit exhausts all recipes for free play and 19 goals and preserves every one
  of 39 historical save prefixes. Independent migration review covered 780 randomized
  prefixes; factual review covered 100 complete new runs, current restores and old migrations.
- Evidence: [concept expansion review](reviews/v92-alchimie-more-concepts/README.md),
  exact candidate, editorial delta, semantic/final reviews, live audit and verification receipt.

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work is isolated on its task branch.
- Last documented production smoke: health 200, accounts off, 2416 concepts, 14/14
  categories available and real Intrusul/Perechi seed-38 boards. HSTS follow-up remains open.
- Next: owner playtesting of the finite kitchen world, then local integration. Further themes
  and more reuse for terminal dishes are content follow-ups. Cross-device synchronization,
  human playtesting and physical-device acceptance are not part of this delivery.
- Existing content follow-ups remain: three proposed Neagu past-tense labels, four thin
  Contexto neighborhoods, 17 unknown household surfaces and earlier hidden-target/A5 holds.
  Keep accounts out until the DEPLOY checklist passes.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0146), `docs/reviews/`, WORKLOG: decisions, evidence and history.
