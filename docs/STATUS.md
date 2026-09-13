# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 direct crafting is green locally; ready for owner playtesting.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V92 continues on `feat/v92-alchimie-gui`. The owner clarified that the primary problem
  was too many buttons/actions. This revision supersedes the first GUI candidate `e609de6`
  with direct crafting informed by the official Infinite Craft and Little Alchemy 2 interfaces.
  The automatic version loop remains stopped; this is still V92 (ADR-0142).
- Tap a word, then another: the second tap immediately combines them. Desktop dragging
  one owned word onto another invokes the same guarded action. There is no Combine button,
  two-slot form, Golește button or mandatory use-result step. Tapping the active word cancels.
- The sole useful new discovery automatically stays selected for the next combination.
  A failed attempt keeps the first word; a different partner takes one tap. An unchanged
  failed pair is blocked locally. Multiple useful discoveries require an explicit choice.
- Default play exposes three controls outside word tiles: exit, search and options.
  Filters, history, rules and round actions begin collapsed. Intro difficulty/category
  settings are optional. The target, active word, result and inventory occupy one compact area.
- Available hints still show their 150-point penalty. Pair hints select only the first
  suggested word and highlight both; neither hints nor resume cause an automatic mutation.
  Lost replies retain GET-only recovery, ownership checks and paid-cue persistence.
- Keyboard crafting uses native Enter/Space. If a discovery removes the focused word,
  focus follows the carried word or inventory panel, preserving deliberate navigation
  elsewhere during the request. Carried selection is announced; terminal focus stays owned.
- Real seed-38 phone journey: **3 word taps / 2 combinations / 1000 points**, versus six
  actions for the first candidate. The first word starts at **y=367.91** at 390×844
  (first candidate: 613.75); six words fit. These are emulated-browser measurements,
  not human playtesting. Decision: [ADR-0142](adr/0142-direct-alchimie-crafting.md).

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
V92 changes no content: all concepts, links, forms, puzzles, curated rounds, approvals,
eligibility and the 336 frozen derived boards match baseline `6208eae` exactly.
Sessions retain 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Private recipes, routes and target IDs remain server-controlled.

## Current artifact pins

- `games_pack.json`: `6bf27de5da270258290ecb4ed41c3ef60a609e3e153855f38b7556a7f2aedeca`
- `board_rankings_v37.json`: `01fc906e390b8d3135f1856930458aa86873a525049b419eceb8652c72f717f8`
- `derived_catalog_v38.json`: `53fb3e4555205179072bd54a45f5b1b185de064625893dcf288902574a075e64`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Node 24.19.0: **195 native checks**, ESLint, typecheck/build and **119.09/120 KiB**
  initial gzip budget pass. Styles remain scoped to the lazy Alchimie screen.
- **368 final browser checks pass**, four workers, zero retries; **26 focused workbench
  checks pass** with actual touchscreen taps, native drag, three-tap completion, retries,
  passive paid hints, keyboard focus restoration, no focus stealing and 320px/200% text.
  Commands and fingerprints: [verification](reviews/v92-direct-crafting/verification.json).
- A first focused run found duplicate replay-failure notices (108 pass/2 fail); the
  correction passed both regression cases. A pre-focus-fix full run passed 364 cases;
  independent review then reproduced lost keyboard focus after a submitting word vanished.
- Backend and content are unchanged from `e609de6`. Its **1652 backend/53 accounts**
  tests and both content validators remain baseline evidence; they were not rerun for
  this further GUI-only correction. New browser tests exercise the real BFF contracts.
- Content delta from `e609de6`: zero concept, connection, form, puzzle, round, approval,
  eligibility and derived-board changes. API wrappers and backend source have no diff.
- Previous V92 layout evidence remains historical in `reviews/v92-alchimie-gui/`.
  Current evidence: [direct-crafting review](reviews/v92-direct-crafting/README.md).

## Production and remaining work

- Production remains anonymous V91 `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`, deployed
  2026-09-09. V92 has not been pushed or deployed; current work is isolated on its task branch.
- Last documented production smoke: health 200, accounts off, 2416 concepts, 14/14
  categories available and real Intrusul/Perechi seed-38 boards. HSTS follow-up remains open.
- Next: review the V92 play feel with the owner, then integrate the candidate. Physical
  device/player acceptance remains unrun. Recurring iteration remains stopped.
- Existing content follow-ups remain: three proposed Neagu past-tense labels, four thin
  Contexto neighborhoods, 17 unknown household surfaces and earlier hidden-target/A5 holds.
  Keep accounts out until the DEPLOY checklist passes.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0142), `docs/reviews/`, WORKLOG: decisions, evidence and history.
