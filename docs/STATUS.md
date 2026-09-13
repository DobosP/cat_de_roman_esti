# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 persistent Alchimie world; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner authorized the remaining shared Alchimie discovery world on 2026-09-13.
  V92 continues on `feat/v92-alchimie-gui` from `c0f3945`; no V93, recurrence or deployment.
- New default **Explorează** mode: **Bucătăria românească**, a persistent collection of
  **75 concepts**, **57 canonical recipes**, **39 crafted discoveries**, **9 optional goals**.
  Eight starters and 28 later pantry supplies are distinct from crafted discoveries.
- Four pantry milestones unlock automatically after **3/8/16/24** crafted results.
  Every concept is reachable. Eighteen results have alternate recipes; twelve crafted
  results are reusable intermediates and 27 are terminal dishes. Initial coverage is 7/28.
- Pair results are identical across all exploration goals; goals never stop crafting.
  Empty/repeated experiments and progressive hints are free. Exploration creates no
  score, ranking or account record. Existing scored challenges remain under **Provocări**;
  daily-circuit links and existing challenge saves retain their challenge flow.
- Two taps/drag craft immediately. Usable results carry forward, fresh dishes stay visible,
  and search, the full collection and recipe journal remain available. Free hints first
  name a reachable result, then reveal its owned pair. Optional goals require no setup.
- Browser checkpoints preserve successful recipes and goals, including server-expiry
  restoration. World ID plus recipe fingerprint prevent silent changes to saved results;
  copy edits remain compatible. Concurrent-tab merges and uncertain-action GET recovery
  preserve earned discoveries. Invalid saves remain intact; storage limitations are visible.
- The generator accepted complete independent factual/quality reviews for all 57 recipes,
  then two final reviews bound exact catalog bytes and the runtime replay audit before apply.
  Full KG snapshots/provenance remain intact; four world-local descriptions were corrected.
- Thirty exploration results never appeared as crafted outputs in the old challenge books;
  48 concepts and 54 canonical recipe triples were absent from all 80 old live books.
  All IDs already existed in the unchanged KG. This adds playable content, not KG vocabulary.
- The prior 50 reviewed challenge recipes and free-miss scoring remain unchanged.
  Those short challenges still have 19 single-ending-pair rounds and scoped recipe differences.
  The earlier V92 six-game GUI work remains; decision/evidence: [ADR-0145](adr/0145-persistent-alchimie-discovery-world.md).

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
has a separate 57-recipe world.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration has its own capped store and <=128 concepts/512 recipes/128-craft
checkpoints. Private recipes, routes and unearned target IDs remain server-controlled.

## Current artifact pins

- Discovery world: `fd3f5547e2a771b8d6d6caae7cf2d18335ce97d512a37446daa3062acb638a8c`
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

- Final Python 3.12 backend **1787 pass**, accounts **53 pass**; fixture/pack validators
  GREEN, Ruff and whitespace pass. Focused API/catalog/mobile **93 pass**, generator **61 pass**.
- Frontend native **204 pass**, browser **442 pass**, lint/typecheck/build GREEN at
  **119.22/120 KiB** initial gzip. Browser run used four workers and zero retries.
- Python 3.14 was not rerun. Desktop/mobile preview screenshots were inspected; no human
  playtest or physical-device acceptance is claimed.
- Independent final replay covers every recipe under free exploration and all nine goals,
  plus 100 randomized goal-switching complete playthroughs. Every run reaches all 75 items.
- Evidence: [discovery world review](reviews/v92-alchimie-discovery-world/README.md),
  exact candidate, semantic/final judgments, runtime fingerprints, comparison and verification.

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
- `docs/adr/` (newest 0145), `docs/reviews/`, WORKLOG: decisions, evidence and history.
