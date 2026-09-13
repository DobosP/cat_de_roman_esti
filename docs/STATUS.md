# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 interfaces are green locally across all six games; ready for owner playtesting.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- V92 continues on `feat/v92-alchimie-gui`. The owner explicitly expanded the interface
  review to all five other games after the Alchimie correction. This pass starts from
  `f57162d`; no V93 or recurring version loop is started (ADR-0143).
- Intrusul keeps one-tap answers and Perechi two-tap matching. Compact instructions
  and balanced grids prioritize the board. Retapping cancels a Perechi selection;
  redundant Golește is removed. Solved pairs follow remaining tiles. Locked hint states
  are text; available hints show their 150-point cost and retain earned feedback.
- Conexiuni keeps four columns on phones and places shuffle/clear/check below the board.
  Checking stays explicit because mistakes are limited. The fourth selected tile never
  submits automatically. Lives, selection count, one-away feedback and earned clues
  remain visible; available clues show the existing 100-point cost.
- Cald sau Rece prioritizes the guess field, inline rank meaning and ranked words.
  Input focus supports repeated guesses while respecting navigation elsewhere. Options
  contain reveal, ordering and a clearly named new-round action. Reveal still needs
  confirmation, with safe cancel focused and reachable. Hint cost remains 120 points.
- Lanț puts current word, target and legal next choices together. Exact earned hint
  choices now take one tap; uncertain spelling suggestions remain edit-only. History
  and the original-start optimal benchmark move into options, with no invented distance.
  Undo stays available. Owned action focus follows consumed choices without stealing it.
- All five games use closed optional rules/tools; configurable setup choices are
  optional. Consumed quick-game hints restore lost keyboard focus to an eligible word,
  while deliberate focus moves and passive saved-hint restoration remain untouched.
- Alchimie direct crafting from `f57162d` is unchanged: two word taps combine, a sole
  useful result carries forward, failed attempts keep the first word, drag/keyboard
  use the same guarded path. Its previous three-tap seed-38 win remains baseline evidence.
- References: NYT Connections, official Contexto, Wikispeedia, Wordwall and Sporcle.
  Details and inspection limits: [ADR-0143](adr/0143-simplify-the-five-other-games.md).

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

- Node 24.19.0: **195 native checks**, ESLint, typecheck/build and **119.18/120 KiB**
  initial gzip budget pass. New styles/components load through the game screens.
- Focused interface/accessibility gate: **50 passed**. Consumed-hint focus follow-up:
  **18 passed**, covering both quick games, keyboard restoration and no focus stealing.
  Final complete six-game gate: **414 passed**, four workers, zero retries.
  Commands and fingerprints: [verification](reviews/v92-other-interfaces/verification.json).
- The first focused run had 42 passes and four test-only casing mismatches; assertions
  now follow server-authored labels. Review also reproduced/fixed lost or stolen focus
  and made reveal confirmation reachable on short screens. Two stale replay fixtures
  were corrected to exercise genuinely scrolled compact results; final focused/full gates pass.
- Backend, API wrappers, content and Alchimie source have no diff from `f57162d`.
  Prior **1652 backend/53 accounts** tests and validators remain baseline evidence;
  this GUI-only pass uses new real BFF browser journeys rather than rerunning those suites.
- Content delta from `f57162d`: zero concept/connection/form/puzzle/round/approval/
  eligibility/derived-board changes. Human playtesting and physical-device acceptance
  remain unrun. Current review: [other interfaces](reviews/v92-other-interfaces/README.md).

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
- `docs/adr/` (newest 0143), `docs/reviews/`, WORKLOG: decisions, evidence and history.
