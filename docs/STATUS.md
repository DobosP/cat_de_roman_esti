# Status — cat_de_roman_esti

Last verified: 2026-09-15 — V92 vocabulary session 03; all local integration gates green.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner requested another vocabulary/interface session. This bounded V92 pass uses
  `feat/v92-entry-creation-03`, based on completed `0b51e03`; no automatic fourth session.
- **11 new rounds/targets, four Alchimie words and six recipes**: Conexiuni +1, Cald sau
  Rece +2, Lanț +2, Intrusul +3 and Perechi +3. New boards use six words absent from the
  previous Conexiuni pack, ten from Intrusul and twenty from Perechi’s fixed catalogs.
- Conexiuni adds scoarță wordplay with concrete anchors. New targets are Ion Creangă and
  Alba Iulia; Lanț connects Poarta Sărutului→Oltenia and Ștefan cel Mare→Bucovina.
  One proposed Ateneul route was rejected for an unsupported displayed definition.
- All five pack additions passed raw review, pending staging, actual dossiers and
  independent analyst/verifier promotion. The six quick boards pass original graph and
  rating gates; five qualify for starter selection. No graph vocabulary was changed.
- Alchimie now has **225 concepts, 294 recipes and 121 craftable discoveries**. New words:
  Mere coapte, Ardei copți, Pilaf de legume and Dovleac copt. Roasted peppers and baked
  pumpkin have onward recipes. Eight starters, 96 later supplies, 12 tiers and 32 goals remain.
  Crafted intermediates grow 50→52; terminal results become 69; alternative-result count stays 77.
- The world has 174 KG identities and 51 reviewed world-local definitions. All 221 previous
  concept records and 288 recipes remain exact, including preparation references.
  Four saved-book generations (75/111/221-with285/221-with288 recipes) remain supported.
  Completed old 221 collections retain 117 journal entries and open four new discoveries.
- Twelve exact edge-bound Lanț captions now describe creator, place, foundation and
  regional relationships. The previous 68 remain exact; 80 total. Both traversal directions
  and changed-snapshot fallback were verified without changing topology or weights.
- Alchimie has a visible one-action search reset even with tools closed. It preserves
  selection, filter and save with no request. Completed worlds display every earned word
  and journal guidance, with no misleading crafting prompt or hidden all-words checkbox.
- Conexiuni status uses explicit columns and a separate mobile mistakes row, fixing the
  selection/mistake overlap at 320px and enlarged text. Contexto/Lanț controls now meet 44px.
  Intrusul/Perechi keep their efficient tap loops. Previous focus/ownership guards remain.
- Decision/evidence: [ADR-0150](adr/0150-expand-vocabulary-and-clarify-game-controls.md),
  [vocabulary/interface review](reviews/v92-session 03-vocabulary-and-interface/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 240 | 240 | 0 | 82 eligible |
| Cald sau Rece | 257 | 255 | 2 | 251 eligible |
| Lanțul Cuvintelor | 116 | 113 | 3 | 113 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 214 | 214 | 0 | 175 preferred |
| Perechi | 179 | 179 | 0 | 139 preferred |

Pack **696 = 688 approved + 8 pending**, with **526 eligible** four-game records.
All 691 previous pack records, 336 core quick boards and 51 prior authored payloads/scores
remain exact. The authored supplement now has 57 boards; 38 private competition ranks update.
Quick starter shelves are 49 Intrusul / 47 Perechi. KG/mobile content remains
`fixture-v90-household-discovery`: **2416 nodes/9459 links/8641 forms/180 puzzles**.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains <=256 concepts/512 recipes/256 saved crafts. Quick
supplements remain <=256 boards/2 MiB. Private recipes, routes, hidden answers and source IDs
stay server-controlled. Both catalogs still require exact final live-audit reviews.

## Current artifact pins

- Discovery world: `b9ff7122f6499d4eea365cc6292249744e34c6576f5f16ca694d9644c19c327f`
- Recipe extensions: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- Quick supplement: `9fdcd45bca05d94077465c300851d18bcc487a7b82af3b69863e3d57534766ad`
- `games_pack.json`: `02b966eacaa851a9b20c4f36e0ee50c217e49670553da462313b16830b2c13e6`
- `board_rankings_v37.json`: `e467823999d6b20bd0abeb6a41ceb239faaf7c600afe7d9df3adfc65daad3b12`
- `derived_catalog_v38.json`: `de2f46a72c23e5ecbd496d3a4314a48f0d4f636b71aa5ba4662bccc837298449`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Python 3.12 backend **1968 pass**, browser **480 pass**, frontend native **212 pass**,
  accounts **53 pass**. Ruff, whitespace, docs, both content validators and frontend
  lint/typecheck/build GREEN at **119.22/120 KiB** initial gzip. Python 3.14 not rerun.
- Historical/world focused checks **173 pass**. The exact five-artifact inverse preserves
  original historical hashes and assertions. New-world checks cover all four saved books,
  retained journals, repeat/resume behavior and rejection of forged historical recipes.
- Independent quick reviews replay all 57 natural rounds; all six additions also pass
  wrong/repeat/hint/GET/completion checks. World audit exhausts 294 recipes across 33 runs
  and 39/58/117/117 saved prefixes; independent BFF checks create all six new recipe pairs.
- Independent GUI review verifies local search recovery, completed 225 words/121 journal
  entries, keyboard/deferred-response ownership, 320px/200% status layout and 44px controls.
  Long words still wrap at 320px/200%; no remaining blocker was reproduced. This is browser
  evidence, not human enjoyment or physical-device acceptance.
- [Final verification](reviews/v92-session03-vocabulary-and-interface/verification.json)
  binds the current artifacts. Preview uses **8150**, preserving the previous browser origin.

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work stays in its task worktree.
- Owner playtesting, physical-device acceptance and broader calibration remain. Further
  specific captions, stronger target neighborhoods and dish reuse remain editorial work.
- The prior 17-entry queue remains linked as unapproved history; overlaps are not counted
  again. Existing museum/Dem/Ateneul definition debt, Neagu labels, thin neighborhoods,
  unknown household forms and hidden-target/A5 holds remain. Cross-device synchronization
  and HSTS follow-up are outside this pass. Keep accounts out until DEPLOY gates pass.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0150), `docs/reviews/`, WORKLOG: decisions, evidence and history.
