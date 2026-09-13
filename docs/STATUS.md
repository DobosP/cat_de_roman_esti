# Status — cat_de_roman_esti

Last verified: 2026-09-13 — larger V92 vocabulary; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner again requested more Alchimie concepts. V92 continues on
  `feat/v92-alchimie-gui` from `8f97bd9`; no V93, recurrence, publication or deployment.
- **Bucătăria românească** now has **221 concepts (+110)**, **285 recipes (+169)** and
  **32 optional goals (+13)**. Craftable discoveries grow **58→117**; later pantry
  supplies grow **45→96**. Eight starters remain. All twelve supply tiers are reachable.
- The book contains **174 KG identities and 47 reviewed world-local definitions**.
  The shared KG remains unchanged. New foundations include mayonnaise, choux pastry,
  laminated pastry, caramel, sauces, vegetable purées, chickpeas and aubergines.
- Original 111 concept records, 116 recipes, six supply tiers, starters and 19 goals
  remain exact. Recipe outcomes remain consistent across optional goals and input order.
  Both previous saved-collection formats (75/111 concepts) upgrade without losing progress.
- Reusable crafted concepts grow **23→47**; results with alternative recipes **40→77**.
  Seventy crafted dishes remain terminal. Productive initial pairs grow **7→9 of 28**.
  Direct crafting, free hints, searchable collection and recipe journal remain available.
- Definitions may now be authored inside the exploration catalog under `alw_food_` IDs,
  with original text, primary references and exact provenance snapshots. Runtime rejects
  KG identity/alias shadowing, indistinguishable labels, missing sources and altered metadata.
- Both independent semantic reviews cover all 285 recipes AND all 221 concept digests.
  Exact prior records inherit explicit reviewed judgments; every new definition is checked.
  Two final reviews bind exact catalog bytes and the live replay audit before package write.
- Bounded capacity is now **256 concepts / 256 saved crafts / 96 later supplies / 12 tiers**.
  Per-tier supplies stay <=12; limits remain 512 recipes, 32 goals, eight historical books
  and a 2 MiB catalog. Browser saves enforce their existing 64 KiB limit as UTF-8 bytes.
- The generator carries the previous book's reviewed compatibility history forward.
  Unknown versions and new recipes claimed under old authority still fail. Live sessions
  upgrade atomically; browser unions retain the newer compatible book.
- Scored **Provocări**, earlier challenge content, daily routing and the other five games
  remain unchanged. Decision/evidence: [ADR-0147](adr/0147-grow-alchimie-with-reviewed-vocabulary.md).

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
has a separate 285-recipe world, including 47 authored definitions outside the shared graph.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration has its own capped store and <=256 concepts/512 recipes/256-craft
checkpoints. Private recipes, routes and unearned target IDs remain server-controlled.

## Current artifact pins

- Discovery world: `baafc2fc656dfe501dbe5be03ce2bd536e086b71f1711d0cf8c77ed56a03e1df`
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

- Final Python 3.12 backend **1837 pass**, accounts **53 pass**, focused API/catalog/mobile
  **143 pass**. Ruff, whitespace and fixture/pack validators are GREEN. Python 3.14 was not rerun.
- Frontend native **212 pass**, browser **446 pass**, lint/typecheck/build GREEN at
  **119.23/120 KiB** initial gzip. Exploration focus **24 pass**; four workers, zero retries.
- Tests restore a synthetic 256-concept collection with more than 128 earned crafts and
  reject excessive saves, forged provenance and ambiguous labels. Both real historical
  collections migrate in browser tests; the local preview retained its existing discovery.
- Serving audit exhausts all 285 recipes for free play and 32 goals, then all 39/58 historical
  prefixes. Independent factual replay passed 50 complete worlds, 50 current restores,
  100 historical migrations and 100 live-session upgrades. No human playtest is claimed.
- Evidence: [large vocabulary review](reviews/v92-alchimie-large-concepts/README.md),
  exact candidate, provenance, semantic/final judgments, live audit and verification receipt.

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
- `docs/adr/` (newest 0147), `docs/reviews/`, WORKLOG: decisions, evidence and history.
