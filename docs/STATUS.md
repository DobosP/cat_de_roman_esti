# Status — cat_de_roman_esti

Last verified: 2026-09-15 — V93 integrated on main; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V93 implementation `ba28be6` is integrated on main after `bf9d814`;
  the owner authorized its publication and a fresh V94 content/game-quality session.
- **13 new rounds/targets, ten Alchimie words and 21 recipes**: Conexiuni +1,
  Cald sau Rece +2, Lanț +2, Intrusul +4 and Perechi +4. New boards expose eleven
  previously unused Conexiuni words, fifteen Intrusul words and thirty Perechi words.
  These are per-game exposures; the shared KG vocabulary stays unchanged.
- Conexiuni combines female kinship, crown wordplay, absorbent household objects and
  atmospheric water. Cald sau Rece adds Aluat and Cașcaval. Lanț adds Cluj-Napoca→Munții
  Apuseni and Mihai Eminescu→Titu Maiorescu, with three shortest routes each.
- All five pack additions pass independent raw review, pending staging, exact allocated
  dossiers, analyst/verifier judgments and strict promotion. All eight quick additions
  pass original mechanics, novelty, rating and final artifact/audit reviews; all are starters.
- Alchimie has **235 concepts, 315 recipes and 131 craftable discoveries**. New words:
  Ouă umplute, Musaca, Clătite gratinate, Găluște cu prune, Milkshake, Bruschete,
  Salată de paste, Budincă de pâine, Pesmet and Supă cu tăiței.
- Crutoane, Legume la grătar, Clătite and Înghețată gain onward recipes. Pesmet leads to
  existing Șnițel. Alternative-result count grows 77→86; crafted intermediates 52→57.
  Eight starters, 96 later supplies, twelve tiers and 32 optional goals remain exact.
- The world has 174 KG identities and 61 reviewed world-local definitions. All 225 old
  concept records and 294 recipes remain exact. Five saved-book generations are supported;
  completed old 225 collections retain all 121 earned entries and open ten discoveries.
- Earned Alchimie recipes can be searched by result or ingredient, ignoring accents/case.
  Filtering/reset/Escape preserve selection and save without API calls. Closed journals
  show a two-line query preview; the editable input keeps the full query. Source controls
  reach 44px. Cald sau Rece describes harder associations instead of rarer concepts.
- Decision/evidence: [ADR-0151](adr/0151-expand-game-vocabulary-and-search-earned-recipes.md),
  [V93 words and game-quality review](reviews/v93-words-and-game-quality/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 241 | 241 | 0 | 83 eligible |
| Cald sau Rece | 259 | 257 | 2 | 253 eligible |
| Lanțul Cuvintelor | 118 | 115 | 3 | 115 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 218 | 218 | 0 | 179 preferred |
| Perechi | 183 | 183 | 0 | 143 preferred |

Pack **701 = 693 approved + 8 pending**, with **531 eligible** four-game records.
All 696 previous pack records, 336 core quick boards and 57 old authored payloads/scores
remain exact. The authored supplement now has 65 boards. Of 498 changed private ranking
rows, six change selection weight; the others change rank only. Another 48 quick rows
change private rank fields, retaining payloads/scores. Quick starter shelves
are 53 Intrusul / 51 Perechi. KG/mobile: `fixture-v90-household-discovery`,
**2416 nodes/9459 links/8641 forms/180 puzzles**. The previous 80 Lanț captions remain exact.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains <=256 concepts/512 recipes/256 saved crafts. Quick
supplements remain <=256 boards/2 MiB. Hidden answers/recipes/routes and source IDs remain
server-controlled. Both catalogs require exact final live-audit reviews before installation.

## Current artifact pins

- Discovery world: `14475e29c1c40888a762c1302170f658577ec58ea7e6db2b6fc2ac833c8f5e38`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- Quick supplement: `04622c7dc0e7d38f68d949c03be349f716a99222d344eb60db6b96d560a6dc21`
- `games_pack.json`: `573e921cbe54cb482535584a22e55183c4b7add9b0a9a92a1400f9dae4fd01d8`
- `board_rankings_v37.json`: `5e29e48a7d684d23d5532f38d80fb996c92d3474744b20a0159111ac7b41bc76`
- `derived_catalog_v38.json`: `46360ac6a77fff6cdab2f86500dcadc348243f71bab71eea01111e76bf80f2c4`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Python 3.12 and 3.14 each pass **2017 backend/53 accounts tests**; browser **486 pass**,
  frontend native **212 pass**. Both validators, Ruff, frontend lint/typecheck/build, docs
  and whitespace are GREEN. Initial gzip is **119.22/120 KiB**.
- [Final integration receipt](reviews/v93-words-and-game-quality/verification.json) binds
  the exact inputs and logs. Two stale current snapshots were corrected with explicit
  before/after evidence; all older profile and historical assertions remain intact.
- Installed new-world tests **29 pass**. Independent audit exhausts 315 recipes in 33
  free/goal runs and five historical save prefixes; completed 225→235 restoration retains
  every old earned recipe. The exact five-artifact inverse preserves all older pins/counts.
- All five new pack entries are naturally selectable and complete through the BFF. All 65
  authored quick boards have natural-seed winning replays; eight additions also pass
  wrong/repeat/hint/GET/completion checks. Answers and unearned metadata remain private.
- Independent GUI checks cover 320px/200% text, 117 earned recipes, ingredient/result search,
  zero API/save changes, selection/focus, long queries, empty recovery and 44px controls.
  No unresolved finding remains in that bounded review; human enjoyment is unmeasured.
- Preview origin **8150** is retained, supporting restoration of earlier Alchimie
  collections. [V93 landing receipt](reviews/v93-words-and-game-quality/landing.json).

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V93 is integrated on main; production deployment is outside this landing.
- Owner playtesting and physical-device acceptance remain. Aluat's bread approach is still
  lukewarm despite five strong direct ingredient/tool approaches. Further specific route
  captions and broader target-neighborhood calibration remain editorial work.
- Prior unapproved queues stay historical; duplicates and ambiguous candidates are excluded.
  Existing museum/Dem/Ateneul definition debt, Neagu labels, thin neighborhoods, unknown
  household forms and hidden-target/A5 holds remain. Cross-device synchronization and HSTS
  follow-up are separate. Keep accounts out until DEPLOY gates pass.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0151), `docs/reviews/`, WORKLOG: decisions, evidence and history.
