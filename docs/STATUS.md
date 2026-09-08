# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V87 landed locally; V88 started; recurring local version loop active. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V87 is merged into local main at `fa8cffd`, following V86 and its record `daae025`.
  V88 starts on `feat/v88-cross-game-quality`; no push or deployment.
  Owner-authorized recurring local iteration continues until stopped (ADR-0127).
- V87 adds nine snack/preparation concepts, 31 accepted forms and 50 directed links;
  no removals. Chec, Pandișpan, Cremșnit, Tort Diplomat, Pișcot, Brioșă, Praf de copt,
  Bicarbonat de sodiu alimentar and Gelatină alimentară gain specific recipe/type cues.
  One form is the sourced Cremșnit/cremeș lexical equivalent; 30 are grammatical/qualified.
- Chec and Brioșă replace their approximate Pâine projections. A new nonwinning “tort”
  cue recognizes the broad dessert. Three native and two projected exact feedback repairs
  improve cake/biscuit/chocolate families without reversing graph edges (ADR-0125).
  Projected guesses cannot inherit an exact native exception through their fallback anchor.
- Six new easy Contexto rounds are approved and selectable: Biscuit, Chec, Cremșnit,
  Tort Diplomat, Pișcot and Ciocolată. Pandișpan/Brioșă remain inputs, with targets deferred.
- A lost Contexto guess/clue/giveup response triggers one owned read of actual server state.
  Failed verification keeps a visible read-only retry; no mutation replay or second clue
  charge. Stale/unmounted/other-tab responses cannot replace the current game (ADR-0126).
- V86's visible Lanț alternatives and all-six-game creation/replay recovery remain covered.
- Served KG: `fixture-v87-snack-and-action-quality`, 2,406 nodes / 9,410 edges /
  8,603 aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 241 | 239 | 2 | 235 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **655 = 647 approved + 8 pending**; original four-game ranking **485 eligible**.
All 649 old pack records and 336 derived rows remain exact. All old native owners/forms,
9,360 retained edges and 180 puzzles remain exact; only 28 old node degrees change.
Projection vocabulary is 467 rows across 26 domains: 466 old rows retained, two retired,
one added. The 71 legacy proxies and four prior native-audit tuples stay exact.
Native exact feedback pairs grow 6→9; projected exact neighborhoods grow 2→4.
The audit-only domain representative becomes Chiflă; its other 25 examples stay exact.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, locks, 64 KiB requests,
bounded histories/caches and private answers. No new server-session fields or scoring formula.

## Current artifact pins

- `games_pack.json`: `536036f6d030be4e8750fb104325b67a9363535506d453ef8a0e0a824a3b63ab`
- `board_rankings_v37.json`: `53defb36ab442aee1135ae3dd0522559abe27234048f9accdfbd5c9fe75eccc3`
- `derived_catalog_v38.json`: `f4e16944845311eeba231f866c5578a4f1de9ee40e08857cca575930a2bf1278`
- `kg_sample.json`: `96d50f8b724b9d1d1ff5d02b5a9a206445d7d9edead778d6db173f00ac094bfa`
- `cat_mobile_app_pack_contract.json`: `f0c346bff24fc821d56be1d41d15c7fca57c4473b637006679f712238a965ecf`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:4955a96a884a685e93b0f38966f0d0d94b34a9db5a726d6470c64c93d2621716`.
Mobile content: `sha256:7473bfe7d42189a28cf933032705b288ff2933fd8eeaf30c65a2dba3be4e79d4`.

## Verification

- Independent exact graph review and 324-word/50-link preflight pass. Both validators
  pass through graph/import/promotion transactions. Six complete dossiers: zero FAIL/WARN;
  separate bound judges promote all six. Public journeys cover clues/resume/repeats/wins.
- All **56 new content tests pass**. Final capture covers 9,087 first guesses over 233
  old approved records/39 words; all 82 Alchimie/100 Lanț profiles and 336 derived rows
  stay exact. No old eligible stock or shortest-menu choice is lost; one menu gains Chec.
- Frontend: **193 native and 168 desktop/mobile browser checks pass**; no final retries.
  Lint/typecheck/build/bundle pass at 118.90/120 KiB. Backend: **1,409 passed on Python
  3.12.3 and 3.14.4**; accounts **53 each**.
- Historical compatibility: 196/197 initially pass; the stale V85 Tort inventory loop is
  repaired against reconstructed historical rows. All 57 affected-module cases then pass.
- Both initial full backends passed 1,408/1,409. One test still expected retired pastry
  projections; retained inputs preserve its rank/repeat assertions. Both full reruns pass.
- Final validators, pending gate, Ruff/docs/whitespace pass; actual logs are hash-bound.
- Seed-38 snapshot changes only Contexto reachable count 2,321→2,330; other starts exact.
- Full evidence and actual receipts: `docs/reviews/v87-snack-and-action-quality/`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for V86 or V87.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; see `docs/DEPLOY.md`.
- Fresh Node24 install/audit reports zero vulnerabilities; deployed V72 remains unchanged.

## Remaining gates

- V88 starts a cross-game batch: investigate bread-family feedback, broaden playable
  content beyond Contexto and remove concrete content/reliability obstacles. Its new
  implementation and full integration are not yet complete.
- Pandișpan/Chec overlap and Brioșă's brioche/muffin meanings hold the two hidden targets.
  Native Brioșă→Pâine falls from rank 2/hot to 424/cold after its broad projection retires;
  former false Zacuscă affinities cool. Generic pastry, optional butter/dairy, reciprocal
  Pișcot→Biscuit and indirect Sarmale/oven/yeast feedback retain noise. No broad scoring rewrite or new derived boards.
- Owner feedback contact, Romanian-player and real-device checks remain unrun. Reverify
  operator/contact configuration and legal pages per DEPLOY before public anonymous rollout.
- Rollout requires explicit authorization and live smoke/rollback checks. Keep accounts out
  until the DEPLOY go-live checklist and compliance review pass. See `docs/BETA_CANDIDATE.md`.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0127), `docs/reviews/`, WORKLOG: decisions, evidence and history.
