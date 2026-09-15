# Status — cat_de_roman_esti

Last verified: 2026-09-16 — V95 landed; V96 drafting session started.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V95 is landed and pushed on main at `1457786` (implementation `085e792`).
  [GitHub CI 35026423470](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35026423470)
  passed, along with all local integration gates. Its verified branch/worktree/scratch
  were cleaned after both preview origins moved to main.
- V96 starts from that commit in `feat/v96-words-and-input-clarity`, with fresh drafts
  for all six games and an input/focus critique. New candidates remain unapproved;
  the served inventory below is landed V95. No V96 runtime or fixture changes are installed.
- V95 added
  **13 new rounds/targets, five Alchimie words and ten recipes**: Conexiuni +1,
  Cald sau Rece +2, Lanț +2, Intrusul +4 and Perechi +4. Per-game fresh word exposures:
  nine Conexiuni, ten Intrusul and twenty-three Perechi; shared KG remains unchanged.
- New targets are Penar and Clește. Lanț connects oven→crumb through bread or biscuit,
  and powdered sugar→Tort Diplomat through whipped cream or ladyfinger.
  Conexiuni combines boiled grains, bread spreads, light sources and meanings of coadă.
- Final selection review found that the beginner preference hid both new Lanț rounds.
  Casual easy play now retains one in four initially picked eligible narrow rounds;
  other picks continue through the wider-route preference. Daily selection is unchanged.
  Strict two-route content floors, exclusions and deterministic seeded play remain.
- Alchimie has **247 concepts, 342 recipes and 143 craftable discoveries**. New words:
  Budincă de paste, Cremă de zahăr ars, Negresă, Pavlova and Profiterol, each with two
  routes. Bezea and Paste cu brânză gain onward uses; the five new results are terminal.
  Alternative-result count grows 92→97, intermediates 61→63.
- All 242 old concepts and 332 recipes remain exact. Seven saved-book generations retain
  earned progress, including all 138 V94 entries. Eight starters, 96 later supplies,
  twelve tiers and 32 goals remain exact; vocabulary is 174 KG identities + 73 local words.
- Alchimie marks attempted empty pairs and acknowledges immediate retries without a
  request or save write. Server memory is bounded to 128 unordered observed pairs.
  Local freshness lasts 30 seconds; recipe-book changes and restored/new sessions clear
  observations. Save ownership, request locks and keyboard focus remain guarded.
- Decision/evidence: [ADR-0153](adr/0153-expand-discovery-and-remember-attempted-pairs.md),
  [V95 review](reviews/v95-discovery-and-game-quality/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 243 | 243 | 0 | 85 eligible |
| Cald sau Rece | 263 | 261 | 2 | 257 eligible |
| Lanțul Cuvintelor | 121 | 118 | 3 | 118 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 226 | 226 | 0 | 187 preferred |
| Perechi | 191 | 191 | 0 | 151 preferred |

Pack **710 = 702 approved + 8 pending**, with **540 eligible** four-game records.
All 705 earlier pack records, 336 core quick boards and 73 authored payloads/scores stay exact.
The authored supplement now has 81 boards; seven of eight additions qualify as starters.
Starter shelves are 60 Intrusul / 59 Perechi. Tableware remains outside the starter shelf.
Private ranking metadata recomputes; 105 rejection tombstones and 101 custom Lanț captions stay exact.
KG/mobile: `fixture-v90-household-discovery`, **2416 nodes/9459 links/8641 forms/180 puzzles**.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Exploration retains ≤256 concepts/512 recipes/256 saved crafts; quick
supplements ≤256 boards/2 MiB. Answers, private recipes/routes and source IDs remain server-controlled.
Both catalogs require exact final live-audit reviews before installation.

## Current artifact pins

- alchimie_discovery_world_v92.json: `22137b51f6ba642704e1ca3eeee75fa466c70bd983977269dede09d8ce2f31bd`
- alchimie_recipe_extensions_v92.json: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- quick_games_v92.json: `b166aa76e2746c5c2f1382889ede528cce25536fb5480c9d21b027cf65c5d319`
- games_pack.json: `27b1dba81a2e02d1e2616a1ad4e6eceefe12d189a86a0913c3655adee99bb3cf`
- board_rankings_v37.json: `b4c32d0ff65e024e4bd2e292c03e5382f0927c7c388367bf1f80bd7a3c09a831`
- derived_catalog_v38.json: `5e27495fcc34980ced41a7bbd5c0b61d703c459489d08d6b7322dac197fd7e96`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- cat_mobile_app_pack_contract.json: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- manifest.json: `d7b6fb1545efcdd13d96856cd0c0a3e75eca3d9071d60f4be0e7da7e1bf930b7`

## Verification

- Python 3.12 and 3.14 each pass **2191 backend/53 account tests**; browser **528 pass**,
  native frontend **212 pass**. Both validators, Ruff, frontend lint/typecheck/build, docs
  and whitespace pass; initial gzip **119.23/120 KiB**.
- [Final integration receipt](reviews/v95-discovery-and-game-quality/verification.json)
  binds exact tested inputs, installed artifacts, final reviews and original failures.
- Installed-world tests 20 pass. The live audit exhausts 342 recipes, 33 free/goal runs
  and seven historical save generations. Independent quick audits win all 81 authored
  boards and verify wrong/repeat/hint/GET recovery for all eight additions.
- Five new pack records serve and win through public category/difficulty/seed requests;
  both routes win for each Lanț round. Daily behavior matches 56 previous-policy cases;
  deterministic 1024-seed sampling retains 982 wider picks while reaching both additions.
- Independent Alchimie GUI review passes seven fresh scenarios plus six focus controls; 18 new desktop/mobile
  cases cover repeated pairs, reload, transport recovery, save ownership and narrow screens.
- Strict inverses restore exact five-core-artifact baseline bytes; all 261 old Contexto
  profiles remain exact. Browser seed changes affect only Conexiuni and Lanț.
- [Preview checks](reviews/v95-discovery-and-game-quality/preview-check.json): 8150 serves
  V95's 247/342 world before landing; both origins now serve landed V95 from main.
  [V95 landing receipt](reviews/v95-discovery-and-game-quality/landing.json).

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`.
  V95 is on main. V96 drafting remains local; production deployment remains separate.
- V96 session: [initial review queue](reviews/v96-words-and-input-clarity/README.md).
- Owner playtesting and physical-device acceptance remain. Clește has strong tool/material
  openers but unealtă, fier and scule are unknown; new Lanț captions remain mostly generic.
- Existing Crucea Caraiman, museum/Dem/Ateneul description debt, Neagu labels, thin neighborhoods,
  unknown household forms and hidden-target/A5 holds remain. Prior queues stay historical.
  Broader target calibration, cross-device synchronization and HSTS are separate.
  Accounts stay disabled until the DEPLOY gates pass.

## Doc map

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0153), reviews and WORKLOG: decisions, evidence and history.
