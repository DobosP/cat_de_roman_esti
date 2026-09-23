# Status — cat_de_roman_esti

Last verified: 2026-09-23 — origin reconciled; V99 first refinement/discovery batch verified locally.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- Origin/main `b25c949` includes verified V97 and the V98 kickoff. Local reconciliation
  `af5981a` preserves both that history and the repository content skill under ADR-0156.
  Published ADR-0155 remains intact; the previously unpublished skill decision is ADR-0156.
- The owner requested V99 using the [Romanian game content skill](../.agents/skills/romanian-game-content/SKILL.md).
  Its first bounded batch follows both refinement and experimental discovery tracks.
- Four independently accepted Lanț captions explain Cacao→Lapte through Înghețată or
  Chec: cocoa variants, milk-based ice cream and cake served with milk. All 113 older
  captions remain exact; 117 now have reviewed text. Five supported traversal directions
  retain truthful wording; three absent reverse directions remain unavailable.
- Existing hint selection can now show a meaningful direction hint from an already visible
  opening choice. No hidden continuation, route answer or edge digest becomes public.
- The [discovery pool](content-pool/v99-everyday-spaces/pool.json) records 12 proposed new
  shared concepts: eight researched and four held. None is selected, approved or installed.
  Intrare, Sticlă, Masă de bucătărie and Ac de cusut need further sense/input work.
  Masă retains its meal sense; bare ac still belongs to the existing AC air-conditioner alias.
- V99 changes no graph, forms, rounds, recipe, ranking, frontend bundle or session limits.
  The first batch is complete; broader V99 expansion remains open.
  The V98 kickoff remains historical input, not a completed V98 implementation.
- Decisions/evidence: [ADR-0157](adr/0157-start-v99-refinement-and-discovery.md),
  [V99 review](reviews/v99-refinement-and-discovery/README.md),
  [V97 review](reviews/v97-discovery-continuity-and-new-words/README.md),
  [V98 kickoff](reviews/v98-meaningful-connections/README.md).

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---|
| Conexiuni | 245 | 245 | 0 | 87 eligible |
| Cald sau Rece | 265 | 263 | 2 | 259 eligible |
| Lanțul Cuvintelor | 123 | 120 | 3 | 120 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 228 | 228 | 0 | 189 preferred |
| Perechi | 193 | 193 | 0 | 153 preferred |

Pack **716 = 708 approved + 8 pending**, 546 eligible. Every baseline record remains exact.
Quick supplement 85; 336 frozen core boards remain exact. All 105 Lanț rejections remain.
KG: `fixture-v90-household-discovery`, 2416 nodes/9459 links/8641 forms/180 puzzles.
Alchimie exploration: **251 concepts/351 recipes/147 discoveries**, 96 supplies, 12 tiers,
32 goals, nine retained historical books. Both server/browser allow sixteen histories with
pre-write 2 MiB bounds under ADR-0155; all earlier earned collections remain supported.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks and 64 KiB requests.
Exploration stays ≤256 concepts/512 recipes/256 saved crafts and 128 observed empty pairs;
quick supplements ≤256 boards/2 MiB. Recipes/routes/answers stay private.

## Current artifact pins

- alchimie_discovery_world_v92.json: `0b3fea2c30b4c729cbe8398bc467e5a4f7e6a443ff886023a07d9bf0e40e9f44`
- alchimie_recipe_extensions_v92.json: `ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`
- quick_games_v92.json: `804fcf446487e9925158598c4663f0d61f4508574ad14b2fc4e93a5ba8fe6803`
- games_pack.json: `4162c8db2205ac4f250e29e6e94ec1e0212036d6c38de5660991a8bd010204de`
- board_rankings_v37.json: `23421501b0e4bc391a62d25a577ed9d08c935a9eb48a550ab0e5b2f0e8367acb`
- derived_catalog_v38.json: `fe88e7265c68a79884eabb257912630722980dccd7238f3a834c6796aa65b400`
- lant_rejection_tombstones.json: `01811f415e93e885a12de76b1a38ec2e9e2055b68b12675c67d0c5c266ca611d`
- kg_sample.json: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- cat_mobile_app_pack_contract.json: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`

## Verification

- V99: **2345 backend / 53 accounts on WSL Python 3.14.4** and 173 targeted
  checks on native Python 3.12.14 pass. Four focused Edge journeys pass at desktop and
  320px/200% text; fourteen geometry checks and six reload recoveries pass.
- Both content validators, whole-repo Ruff, skill, docs and whitespace gates pass.
  Exact commands, logs and bindings: [verification](reviews/v99-refinement-and-discovery/verification.json).
- Independent factual/quality reviewers accepted the exact four captions. A separate
  implementation audit verifies historical preservation, digest guards and hint privacy.
  The discovery audit checks research boundaries and three source classes, without promotion.
- Native Windows full-suite collection fails on the pre-existing Unix-only `resource` import;
  the unchanged complete suite passes in WSL. The initial failure remains in the archive.
- Inherited V97 evidence: 2329 backend/53 accounts on Python 3.12 and 3.14,
  214 frontend/552 browser checks. These are V97 results, not fresh V99 matrix claims.
- Human enjoyment and physical-device acceptance remain unrun.

## Production and next work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`.
  No push, deployment or recurring loop restart is part of this V99 request.
- Select a small, exact revision set from the pool for independent graph and game-specific
  review. Research states alone grant no approval; all new playable concepts still need gates.
  Ușă still lacks intrare/toc/balama/lemn. Alchimie has five spare concept slots; its two V97
  dishes remain terminal and the three V98 continuation ideas remain unreviewed.
- Earlier Caraiman/museum/Dem/Ateneul descriptions, Neagu labels and pending A5 holds stay
  open. Accounts stay off until DEPLOY gates; human playtesting remains outstanding.

## Doc map

- README/AGENTS: orientation; agent-map/agent-testing: routes/gates.
- ADRs (newest 0157), reviews and WORKLOG: decisions, evidence and history.
