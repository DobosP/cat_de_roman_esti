# Status — cat_de_roman_esti

Last verified: 2026-09-14 — V92 all-game content expansion; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner requested comparable content growth across all games, with quality preserved.
  V92 continues on `feat/v92-alchimie-gui` from `75584bf`; no V93 or automatic recurrence.
- **70 new rounds/targets**: Conexiuni +4, Cald sau Rece +8, Lanț +13, Intrusul +25,
  Perechi +20. The accepted additions use familiar words, practical associations and
  Romanian culture. Twelve weaker pack proposals were excluded after independent review.
- Conexiuni adds precise functional groups and wordplay; Contexto adds Televizor, Florin
  Piersic, Amza Pellea, Sare, Usturoi, Minge, Cheie and Ghiozdan. Lanț adds routes with
  alternative bridges through geography, literature, history, sport, film and food.
- Intrusul and Perechi gain a separate authored supplement, with exact predicates, sources,
  independent factual/quality reviews and final reviews of live API replay. Original
  336 board records remain exact. Starter shelves grow 24→43 and 26→42 respectively.
- New quick-game content exposes 92 previously unseen concepts in Intrusul and 130 in
  Perechi; 73 of 80 intended pairs are new to Perechi. No new shared KG concept is claimed.
  Existing graph gates, score formulas, source balancing, hints and repeat rules remain.
- Lanț captions now describe connections consistently in either supported direction.
  Sixty-eight exact edge snapshots have specific reviewed captions; unmapped edges use
  neutral relation-type wording. Choices, hints, moves and saved paths use the same text.
  This prevents reversed verbs from asserting false relationships; graph topology is exact.
- Alchimie's **Bucătăria românească** retains **221 concepts, 285 recipes, 32 optional
  goals and 117 craftable discoveries**, with eight starters and 96 later supplies.
  All twelve tiers remain reachable; 47 crafted concepts are reusable, 77 results have
  alternative recipes. The 75/111-concept collection migrations remain supported.
- V92's direct crafting, free exploration hints, searchable collection, recipe journal
  and simplified interfaces for the other five games remain. Scored Alchimie challenges
  and its exploration/recipe artifacts are unchanged by this wave.
- Decision/evidence: [ADR-0148](adr/0148-expand-all-game-content-with-independent-review.md),
  [all-game review](reviews/v92-all-games-content/README.md). Kitchen history: ADR-0147.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 238 | 238 | 0 | 80 eligible |
| Cald sau Rece | 252 | 250 | 2 | 246 eligible |
| Lanțul Cuvintelor | 113 | 110 | 3 | 110 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 208 | 208 | 0 | 169 preferred |
| Perechi | 173 | 173 | 0 | 133 preferred |

Pack **686 = 678 approved + 8 pending**, with **516 eligible** four-game records.
All 661 previous pack records and all 336 original quick-game board records remain exact.
KG remains `fixture-v90-household-discovery`: **2416 nodes/9459 links/8641 forms/180 puzzles**.
The authored supplement adds 45 boards; Alchimie retains 47 world-local definitions.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains <=256 concepts/512 recipes/256 saved crafts. Quick
supplements are capped at 256 boards/2 MiB and fail closed on bound-source or artifact drift.
Private recipes, routes, hidden answers and source/catalog IDs remain server-controlled.

## Current artifact pins

- Discovery world: `baafc2fc656dfe501dbe5be03ce2bd536e086b71f1711d0cf8c77ed56a03e1df`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- Quick supplement: `36f5fc575ed5ae36735d792dd71df5860d917dba1b3b58090f792afd4f3b0d39`
- `games_pack.json`: `62c1eaaa7bb72674cf59a66f9b543d911749d52973155f6b201d796d97d6ea4a`
- `board_rankings_v37.json`: `6f2662615b686a492b41f2d689a7ba6b380b62d7b8cecc5e7a3c9788d1dce641`
- `derived_catalog_v38.json`: `09e6b1caa3ed586264a85d3d9807f0173384c02c80102dae072d14665432f2aa`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Python 3.12 backend **1934 pass**, accounts **53 pass**, browser **446 pass**, frontend
  native **212 pass**. Ruff, lint/typecheck, whitespace, docs and fixture/pack validators
  GREEN. Frontend product sources/static assets are unchanged; Python 3.14 was not rerun.
- Focused quick-game/API tests **120 pass**; new runtime integrity checks **23 pass**;
  historical reconstruction and caption checks **124 pass**, further Lanț checks **213 pass**.
- Independent quick reviews replay all 45 natural-seed rounds, hidden answers, correct
  wins and terminal GETs; additional replays verify free repeats and earned hints.
  Lanț review solves all 34 representative paths/68 moves of the 13 new rounds.
- Historical assertions retain original hashes by reconstructing exact predecessor bytes.
  Automated correctness and editorial review do not establish human enjoyment or device acceptance.
- Exact checks and source pins: [verification](reviews/v92-all-games-content/verification.json).
  Local preview is on port **8144**; all six lobby entries and health are available.

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work is isolated on its task branch.
- Last documented production smoke: health 200, accounts off, 2416 concepts, 14/14
  categories available and real Intrusul/Perechi seed-38 boards. HSTS follow-up remains open.
- Next: owner playtesting of the expanded arcade, then local integration. More specific
  Lanț captions, deeper Contexto neighborhoods and more reuse for terminal kitchen dishes
  remain content follow-ups. Cross-device synchronization remains outside this delivery.
- Existing KG debt includes the excluded museum description and Dem/Monstrul association,
  three proposed Neagu labels, four thin Contexto neighborhoods and 17 unknown household
  surfaces. Earlier hidden-target/A5 holds remain. Keep accounts out until DEPLOY gates pass.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0148), `docs/reviews/`, WORKLOG: decisions, evidence and history.
