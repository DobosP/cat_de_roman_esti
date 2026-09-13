# Status — cat_de_roman_esti

Last verified: 2026-09-13 — V92 Alchimie GUI candidate is green locally; ready for owner playtesting.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
- The owner explicitly requested V92 on 2026-09-13, focused on rebuilding the confusing
  Alchimie interface. Candidate branch: `feat/v92-alchimie-gui`, baseline `6208eae`.
  The automatic version loop remains stopped; this request covers V92 only (ADR-0141).
- Alchimie now has a compact target and one workbench: mixing controls beside the
  inventory on desktop, stacked in normal flow on phones. The target carries theme,
  difficulty and daily date; the header keeps the combination count. Help and discovery
  history follow the main play area. Numbered slots and larger word tiles wrap full labels.
- Two selections stay stable when a third word is chosen. A clear message explains
  replacement; removing a slot returns focus to its inventory button or panel. Editing
  the pair clears stale selection guidance. Existing empty-pair retry blocking remains.
- Successful combines preserve the inventory filter. Feedback and immediate use buttons
  appear inside the bench; earned discoveries remain reusable from their history.
  Filters clear search; an empty search offers a clear button. Ready labels explain that
  a suitable partner exists, without suggesting every marked pair will produce a result.
- Available hints show their 150-point penalty before use. Paid cues and uncertain-action
  GET recovery retain their existing ownership and charging rules. Other games are unchanged.
- At 390×844, real seed-38 measurement moves the first word from y=744 to y=613.75.
  Six starting words fit completely (V91: four). This is browser emulation, not player
  acceptance. GUI-only scope adds no content. Decision: [ADR-0141](adr/0141-rebuild-alchimie-workbench.md).

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

- Node 24.19.0: clean `npm ci`, **193 native tests**, ESLint, typecheck/build/bundle pass.
  Initial JS/CSS is **119.09/120 KiB gzip**; Alchimie CSS stays in its lazy game chunk.
- Final full browser gate: **356 passed**, four workers, zero retries. The focused
  workbench/header gate also passes **16 checks** (320px, 200% text, long Romanian
  labels, short viewport, selection recovery, search and immediate earned-result use).
- Python 3.12: **1652 backend/53 accounts tests** pass; both content validators, Ruff,
  documentation checks and whitespace pass. Python 3.14 was not rerun for this GUI-only change.
- First full browser run had 352 passes and two stressed-header overflow failures.
  The wrapping fix passes both focused and final full gates; original failures are not
  counted as passing evidence. Independent review found no substantive new regressions.
- Evidence: [V92 review](reviews/v92-alchimie-gui/README.md), screenshots, geometry,
  content delta and [verification receipt](reviews/v92-alchimie-gui/verification.json).
- Content delta against `6208eae`: zero additions, removals or revisions in every
  concept/connection/form/puzzle/round/approval/eligibility/derived-board category.
- Earlier V91 verification is archived in WORKLOG and its original review directory.

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
- `docs/adr/` (newest 0141), `docs/reviews/`, WORKLOG: decisions, evidence and history.
