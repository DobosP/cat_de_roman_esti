# Status — cat_de_roman_esti

Last verified: 2026-09-14 — V92 entry session 02 and GUI critique; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner requested new entries/levels and a GUI critique. This bounded V92 session uses
  `feat/v92-entry-creation-02`, based on completed `c0ead5e`; no V93 or automatic recurrence.
- **11 new rounds/targets plus three recipe alternatives**: Conexiuni +1, Cald sau Rece
  +3, Lanț +1, Intrusul +3, Perechi +3; Alchimie recipes 285→288.
- New targets are Chitară, Brașov and Nadia Comăneci. The literary route connects Capra cu
  trei iezi to Amintiri din copilărie. Conexiuni adds functional groups; quick games add
  school/kitchen/transport predicates and twelve previously unused practical pairs.
- Two proposed personality Lanț routes were rejected for generic genre/discipline bridges.
  Raw quick labels were corrected to distinguish an airport from a terminal and respect
  the exact botanical flower sense. Independent reviews bind all accepted final bytes.
- Alchimie retains **221 concepts, 117 craftable discoveries, 32 optional goals, eight
  starters, 96 later supplies and twelve tiers**. Omelette, boiled egg and baked potatoes
  gain useful recipe paths. Reusable crafted concepts grow 47→50; terminal results 70→67.
  All 285 previous recipe records and 221 concept records remain exact.
- All three saved-world generations (75/111/221 concepts) restore without lost discoveries.
  A completed 221 collection stays complete and retains its 117-entry journal. Per-recipe
  primary preparation sources now survive candidate generation as well as factual review.
- Fresh GUI critique covered all six games at 390px and 320px. Alchimie optional goals and
  search/filter controls now start collapsed, with selected goal/filter state in summaries.
  All eight starters fit both tested 844px-high phone views; controls remain at least 44px.
- The exploration workbench stays visible while browsing a long collection when it fits
  within 35% of a visual viewport at least 480px high. Short/large-content views use normal
  flow. Keyboard crafting brings restored focus onscreen; pointer browsing stays in place
  and deliberate focus changes during a request remain respected.
- Lanț skips a generic `legătură directă` first hint and immediately shows useful options.
  The same 20-round audit improves 13 such cases; seven specific direction hints stay exact.
  Help remains free, capped at level 3, and persistent across GET/move/undo as appropriate.
- Intrusul, Perechi, Conexiuni and Cald sau Rece retain their existing efficient controls;
  their remaining priorities are content clarity and useful associations.
- Decision/evidence: [ADR-0149](adr/0149-review-new-levels-and-keep-crafting-feedback-visible.md),
  [session review and critique](reviews/v92-entry-creation-and-gui/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 239 | 239 | 0 | 81 eligible |
| Cald sau Rece | 255 | 253 | 2 | 249 eligible |
| Lanțul Cuvintelor | 114 | 111 | 3 | 111 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 211 | 211 | 0 | 172 preferred |
| Perechi | 176 | 176 | 0 | 136 preferred |

Pack **691 = 683 approved +8 pending**, with **521 eligible** four-game records.
All 686 previous pack records, 336 core quick boards and 45 previous authored payloads/scores
remain exact. The supplement now has 51 boards; 38 private competition ranks recompute.
Quick starter shelves are 46 Intrusul / 45 Perechi. The KG/mobile content remains
`fixture-v90-household-discovery`: **2416 nodes/9459 links/8641 forms/180 puzzles**.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains <=256 concepts/512 recipes/256 saved crafts. Quick
supplements remain <=256 boards/2 MiB. Private recipes, routes, hidden answers and source IDs
stay server-controlled. Both content pipelines still require exact final live-audit reviews.

## Current artifact pins

- Discovery world: `c2bfc524e31115be3283b9dfd8e1bb1853c7082bc153716b5db368596ac5f672`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- Quick supplement: `361387e01ef512d1e31bfe65a333af54c24a1a5a1040ba0d8b3a19d20936c741`
- `games_pack.json`: `9c0a8fde33742ad5230d1697fe7617eabfc8a257a6409562e3b0357c0b8fc77b`
- `board_rankings_v37.json`: `cdc148bfc95c9791b8b941b7c537a04b72d8d21398e1b258cf8e743ac9bdbde5`
- `derived_catalog_v38.json`: `931278ac590aa1d4904e15d4a30990a349fe82af09cbbb1b9c1a3e3c1461671a`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Python 3.12 backend **1948 pass**, browser **458 pass**, frontend native **212 pass**,
  accounts **53 pass**. Ruff, whitespace, docs, both content validators and frontend
  lint/typecheck/build GREEN; initial gzip **119.23/120 KiB**. Python 3.14 not rerun.
- Historical inverse and migration checks **65 pass**; corrected selection/hint regression
  suites **99 pass**. All final browser checks include the keyboard-focus correction.
- Independent reviews replay all 51 quick rounds; new six also pass wrong/repeat/hint/GET/win
  checks. World audit exhausts 288 recipes across 33 free/goal runs and restores 39/58/117
  historical prefixes. Independent BFF checks craft all three new recipes from starters.
- Independent GUI review covers deep keyboard focus, retained-origin growth, pointer
  continuity, delayed-response focus ownership, short viewports and 200% text. No remaining
  GUI blocker was reproduced. These are automated/browser checks, not human playtesting.
- Exact final checks: [verification](reviews/v92-entry-creation-and-gui/verification.json).
  Current local preview runs on port **8150**.

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work stays in its task worktree.
- Owner playtesting and physical-device acceptance remain. More specific Lanț captions,
  deeper Contexto neighborhoods and terminal-dish reuse remain editorial follow-ups.
  Cross-device synchronization and HSTS follow-up remain outside this delivery.
- The earlier 17-entry authoring queue is preserved as unapproved backlog; overlapping
  entries are not counted again. Existing museum/Dem graph debt, proposed Neagu labels,
  thin Contexto neighborhoods, unknown household forms and hidden-target/A5 holds remain.
  Keep accounts out until DEPLOY gates pass. No next automatic creation session is active.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0149), `docs/reviews/`, WORKLOG: decisions, evidence and history.
