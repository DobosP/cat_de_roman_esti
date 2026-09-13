# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 reviewed Alchimie recipe additions and free misses are green locally.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner extended V92 from interface work into Alchimie recipe quality and the balance
  between exploration and targets. Work continues on `feat/v92-alchimie-gui` from `e46bf3d`.
  Automatic iteration remains stopped; no V93 or deployment is authorized (ADR-0144).
- Alchimie now has **50 independently reviewed recipe additions across 28 rounds**,
  generated into a separate bound catalog. All 80 original recipe cores, routes, seeds,
  targets and exact pars remain intact. Other games' content and behavior are unchanged.
- Live recipes increase **554→604**. Productive pairs among initially selectable words
  rise **190/476 (39.9%)→223/502 (44.4%)**; raw all-seed coverage is 15.5%→18.2% and
  includes sidelined words. Median openings rise 2→3; single-opening rounds fall 16→12.
- Single productive winning-sequence rounds fall **5→3**. Nineteen rounds still have
  one final pair; median discoverable concepts stays 4.5. This remains short target
  challenges, with no new free-play world, side discoveries or automatic AI generation.
- The easy seed-38 Sport round accepts every football-club pairing: **4/15→7/15**
  productive openings. It still has three discoveries and two final approaches.
- Empty and repeated experiments cost **0 points**. Extra successful crafts beyond par
  still cost 120 and hints 150; the floor stays 100. The client separates the new scoring
  basis from older local puzzle records. Feedback distinguishes missing recipes from
  results already owned. Target/session/privacy gates remain server-authoritative.
- Two semantic and two final bound reviews accepted the exact catalog and live audit.
  Serving matches exact core and graph metadata, and never automatically enables an
  arbitrary graph triangle. Pending-board gates bind the new loader/catalog; old reviews
  retain historical core reconstruction and original hashes (ADR-0144).
- The earlier V92 direct Alchimie input and five-game GUI improvements remain; their
  historical evidence is under `reviews/v92-direct-crafting/` and `reviews/v92-other-interfaces/`.
- Design direction: a future curated, target-independent discovery world with optional
  goals. Reference evidence and the limits of this first pass are in
  [ADR-0144](adr/0144-reviewed-alchimie-recipe-freedom.md).

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
frozen derived boards remain exact. The separate recipe catalog adds 50 serving rules.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Private recipes, routes and target IDs remain server-controlled.

## Current artifact pins

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

- Final Python 3.12 gates: **1702 backend / 53 accounts tests pass**. Fixture and pack
  validators are GREEN, Ruff and whitespace pass. Python 3.14 was not rerun in this pass.
- Frontend Node 24.19.0: **195 native / 422 browser checks pass**, lint/typecheck/build
  GREEN, initial JS/CSS **119.19/120 KiB gzip**. Browser run uses four workers, zero retries.
- Targeted recipe/action/history gates pass 145 checks; the generator/loader covers
  45 guard tests. V91 migration history passes 38 with exact frozen source bytes and
  explicit rejection of the newer runtime; old hashes and review files are unchanged.
- Both reviewers independently reproduced all 80 final serving books and current source
  hashes. Private target IDs stay hidden; concepts/core recipes/routes/par and bounds
  remain exact. The final catalog is byte-identical to the approved proposal.
- Earlier full Python run: 1671 pass / 30 old-source fixture failures. The historical
  setup fix retains the migration's original hash gates; the complete final run passes.
- Evidence: [recipe freedom review](reviews/v92-alchimie-recipe-freedom/README.md),
  exact before/after inventories, candidate judgments, live audit and verification receipt.

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work is isolated on its task branch.
- Last documented production smoke: health 200, accounts off, 2416 concepts, 14/14
  categories available and real Intrusul/Perechi seed-38 boards. HSTS follow-up remains open.
- Next: owner playtesting, then local integration. A broader persistent discovery world
  remains design/content work; no such mode is claimed here. Device/player acceptance is unrun.
- Existing content follow-ups remain: three proposed Neagu past-tense labels, four thin
  Contexto neighborhoods, 17 unknown household surfaces and earlier hidden-target/A5 holds.
  Keep accounts out until the DEPLOY checklist passes.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0144), `docs/reviews/`, WORKLOG: decisions, evidence and history.
