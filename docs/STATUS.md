# Status — cat_de_roman_esti

Last verified: 2026-09-15 — V94 integrated on main; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V93 landed and was pushed to main at `c971846`; GitHub CI run 35011658720 passed.
  Its verified task branch/worktree/scratch were cleaned after preview relocation.
- V94 implementation `b75d68e` is integrated on main; the owner authorized its
  publication and a fresh V95 content/game-quality session.
  **12 new rounds/targets, seven Alchimie words and 17 recipes**: Conexiuni +1,
  Cald sau Rece +2, Lanț +1, Intrusul +4 and Perechi +4. New boards expose twelve
  previously unused Conexiuni words, sixteen Intrusul words and twenty-three Perechi words.
  These are per-game exposures; shared KG vocabulary remains unchanged.
- New targets are Ciorbă de perișoare and Temă pentru acasă. The new Lanț round connects
  Ciorbă de perișoare→Sarmale through either meat or rice. Conexiuni uses household
  preparation/cleaning wordplay, printed publications, lower-limb parts and calendar units.
- Four pack entries pass independent raw/allocated-ID review and strict promotion.
  The proposed Sfinx→Crucea Caraiman round was rejected: its existing target description
  is publicly visible and conflicts with the monument owner's location account. ID 242
  remains reserved; the exact rejection becomes the 105th durable Lanț tombstone.
- Alchimie has **242 concepts, 332 recipes and 138 craftable discoveries**. New words:
  Cartofi gratinați, Chiftele de pește, Crochete de cartofi, Jeleu de fructe, Paste cu pesto,
  Piure de dovleac and Tzatziki. Compot and Sos de iaurt gain onward uses; new jelly/purée
  feed existing preparations. Alternative-result count grows 86→92; intermediates 57→61.
- All 235 old concept records and 315 recipes remain exact. Six saved-book generations
  preserve earned progress; completed V93 collections retain all 131 recipe entries.
  Eight starters, 96 later supplies, twelve tiers and 32 optional goals remain exact.
  World vocabulary comprises 174 KG identities and 68 reviewed world-local definitions.
- Twenty-one reviewed, exact-edge-bound Lanț captions clarify membership, publication,
  locations and ingredients in both directions. All eighty previous captions remain exact.
  One initial plateau phrase was corrected against the monument owner's source.
- Earned Lanț paths and captions now wrap inside the viewport, removing the hidden
  horizontal scrolling needed at 320px/200% text. Keyboard focus and game actions remain.
- Decision/evidence: [ADR-0152](adr/0152-expand-reviewed-rounds-and-explain-lant-connections.md),
  [V94 review](reviews/v94-words-and-clearer-connections/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 242 | 242 | 0 | 84 eligible |
| Cald sau Rece | 261 | 259 | 2 | 255 eligible |
| Lanțul Cuvintelor | 119 | 116 | 3 | 116 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 222 | 222 | 0 | 183 preferred |
| Perechi | 187 | 187 | 0 | 147 preferred |

Pack **705 = 697 approved + 8 pending**, with **535 eligible** four-game records.
All 701 prior pack records, 336 core quick boards and 65 authored payloads/scores remain
exact; the authored supplement now has 73 boards. All eight additions qualify as starters;
starter shelves are 57 Intrusul / 55 Perechi. Private ranking metadata recomputes.
KG/mobile: `fixture-v90-household-discovery`, **2416 nodes/9459 links/8641 forms/180 puzzles**.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains <=256 concepts/512 recipes/256 saved crafts; quick
supplements <=256 boards/2 MiB. Answers, private recipes/routes and source IDs remain
server-controlled. Both catalogs require exact final live-audit reviews before installation.

## Current artifact pins

- Discovery world: `8b174e16edf6ad279f9fa6cc0328776cba033be0b177c849ad77d81ec603da89`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- Quick supplement: `6ca48cc452d33a150bad949ef09d5e624df349b5d19a2eeeb253a2d123cf4042`
- games_pack.json: `7d28b9df887fe561150bc582f390df0dde4f8c292e5550055bbe84e9e8d90990`
- board_rankings_v37.json: `82f128edb3ccdd8208d41c43b7eb77df1e8d528d2aaea1fed5972712047255ed`
- derived_catalog_v38.json: `4088402b80b78946e6f9cb7ee5379c9c3f32438801611008f266101625bb428d`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- cat_mobile_app_pack_contract.json: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Python 3.12 and 3.14 each pass **2133 backend/53 account tests**; browser **510 pass**,
  native frontend **212 pass**. Both validators, Ruff, frontend lint/typecheck/build, docs
  and whitespace pass; initial gzip **119.23/120 KiB**.
- [Final integration receipt](reviews/v94-words-and-clearer-connections/verification.json)
  binds 69 changed inputs and the final logs. Pesto focus expectations now reflect its
  onward recipe; a separate terminal case preserves collection-fallback coverage.
- Installed new-world tests 26 pass. Independent world audit exhausts 332 recipes, 33 free/goal
  runs and six historical save generations. Old 235→242 restoration preserves all 131 entries.
- All four new pack entries naturally serve and win through the BFF. All 73 authored quick
  boards have natural-seed winning replays; eight additions also pass wrong/repeat/hint/GET
  recovery. Rejected 242 is absent from served pools and fails reimport.
- Caption checks 68 pass; scoped browser checks 22 pass. Separate independent GUI review
  verifies wrapping, keyboard focus, reload, undo and read-only interactions in three journeys.
- Strict inverses preserve all five original core artifacts and the original 104-entry ledger;
  focused history checks 111 and historical-ledger checks 21 pass. Current target profiles add
  exactly two rows while all 259 old profiles remain exact; only Lanț's seed 38 snapshot changes.
- Preview origin **8150** is retained, supporting restoration of earlier collections.
  [V94 landing receipt](reviews/v94-words-and-clearer-connections/landing.json).

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V94 is integrated on main; production deployment is outside this landing.
- Owner playtesting and physical-device acceptance remain. Existing Crucea Caraiman,
  museum/Dem/Ateneul description debt, Neagu labels, thin neighborhoods, unknown household
  forms and hidden-target/A5 holds stay explicit. New captions do not approve bad descriptions.
- Prior unapproved queues remain historical. Broader target calibration, cross-device
  synchronization and HSTS follow-up are separate. Keep accounts out until DEPLOY gates pass.

## Doc map

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0152), reviews and WORKLOG: decisions, evidence and history.
