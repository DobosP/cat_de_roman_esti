# Status — cat_de_roman_esti

Last verified: 2026-09-07 — V83 integration complete, with documented timing retry. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V82 landed locally at `e5f7d96`; landing record `38f0d62`. V83 candidate branch:
  `feat/v83-food-input-and-feedback`, ready for its next landing request. No push or deployment occurred.
- ADR-0113 governs complete player-outcome batches and honest concept/edge/form/round counts.
- V83 adds five reviewed Contexto rounds: Cornulețe, Gogoși, Telemea, Cartofi prăjiți and
  Ardei umpluți. All five are runtime selectable after complete independent promotion review.
- V83 adds 24 reviewed grammatical/qualified forms across eight existing food concepts.
  All 13,180 older authored surface owners and 11 excluded forms' resolution/suggestion
  behavior remain exact; these forms are not new concepts or synonyms (ADR-0117).
- Six exact-target feedback repairs make Gem useful for Cornulețe/Gogoși, Ulei for Gogoși/
  Cartofi prăjiți, Sare for Telemea and Ardei for Ardei umpluți. They remain nonwinning,
  keep submitted identity/private answers, and do not spread through target neighbors.
- Current test hashes/counts use one manually authored immutable snapshot; historical evidence
  remains separate. Named-round journeys find bounded current seeds and still use real APIs
  (ADR-0116). The refactor avoids repeated current-pin edits without weakening old constraints.
- V82 Alchimie pair reuse, V73/V74 reliability/accessibility and V76 input-sense guards remain.
- Served KG: `fixture-v83-food-input-and-feedback`, 2,365 nodes / 9,223 edges / 8,475 aliases /
  180 puzzles. `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 223 | 221 | 2 | 217 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **634 = 626 approved + 8 pending**; original four-game ranking **464 eligible**.
All 629 old pack records, 336 frozen boards, graph edges and 180 puzzles remain exact.
Only 24 aliases and KG build metadata change; four Contexto weight bands and insertion ranks
change as stock grows. Full baseline KG/pack/ranking/derived hashes reconstruct exactly.
All 472 projection rows, 71 legacy proxies and existing Nucă/Burtă policies remain intact;
Gem retains its old six-member neighborhood in addition to the two explicitly reviewed targets.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, per-entry locks, 64 KiB requests,
bounded histories/caches and private answers. Prior rejection/word-resolution safeguards remain.

## Current artifact pins

- `games_pack.json`: `78e680f3849f9a9de2a2675cbe7349ba23c8165f415cfc89a7533121bc34399c`
- `board_rankings_v37.json`: `f80397b3fc1dbfb58c9b4daf1e74fcebc43b698a5e290660333dad71a5d8dfb2`
- `derived_catalog_v38.json`: `e406f182bbc8629b05dac9f2d58b51de45113f2917b8beeb078f8ddccf2a66af`
- `kg_sample.json`: `4ce12d15ec247ebcaba3e119caed91f8d2624b09fa5568a8d7ece728f76a8a5e`
- `cat_mobile_app_pack_contract.json`: `ea2fe6b05df3104f674905c971f506fdf41168c6c9760bab7b2a780fcaae93a0`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:bb2ab1ce02ba2f197b1d824ae7b102524b2ac7e4deec161324f6500e700db4b6`.
Mobile content: `sha256:5ea700a00708cf799a4cad8dcc99c54cb6595f0e99c217b5d890b9a829195918`;
its data payload is unchanged, with refreshed build metadata.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for this local V83 candidate.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; procedure: `docs/DEPLOY.md`.
- Clean local Node24 install/audit reports zero vulnerabilities. Frontend app sources/assets
  remain at their prior version; production's V72 dependency lock is unpatched by this work.

## Verification

- Independent lexical review: 24 accepted; factual/quality screens: five raw references covered.
  Strict pending critique: five/zero flags; independent bound judges promote all five; apply GREEN.
- Separate-checkout API comparison: 884 canonical observations over 216 old approved records plus
  five candidates (218 distinct targets), exactly six changes/878 exact; 60 extra controls exact.
- New forms, excluded inputs, privacy, repeats, resume, clues and exact wins pass focused checks.
  Whole-KG target-boundary tests pass; all old authored surface owners remain exact.
- Broad focused integration: 156 passed across V75–V83 history, feedback and public journeys.
  Independent implementation/history review: 53 passed, no blockers. Current-pin checks pass.
- Selection repeats across 100 seeds/30 September dates; other curated games and eight reviewed
  fixed-date observations match. Contexto remapping is disclosed. Seed-38 start snapshots exact.
- Python 3.12: 1,115 passed; Python 3.14: 1,114 passed, sole load-sensitive Alchimie timing
  case passed on retry (21.96s against unchanged 45s limit). Accounts: 53 passed on each.
- Frontend: 173 native and 108 desktop/mobile browser checks passed; lint/typecheck/build and
  118.73/120 KiB bundle pass. Reload checks now bind to the new document's state request;
  rebuilt application assets remain byte-identical. Validators, pending gate, Ruff/docs/whitespace pass.
  Commands, initial failures and retries: `docs/reviews/v83-food-input-and-feedback/verification.json`.

## Remaining gates

- V83 is ready on its task branch; its next landing request can merge the verified candidate.
- Next coherent feedback work: broad Drojdie approximation and false-hot food/holiday routes;
  the remaining grain, biscuit/apple, whey, oven/pan inputs and V82 candidate dispositions.
- Owner selects feedback contact; Romanian-player and real-device checks remain unrun. Reverify
  legal operator/contact configuration and legal pages per DEPLOY before public rollout.
- Public rollout requires explicit authorization and live smoke/rollback verification. Keep accounts
  outside the anonymous beta until DEPLOY's go-live checklist and compliance review pass.
- Release protocol/external evidence: `docs/BETA_CANDIDATE.md`; agent reviews are not playtests.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0117), `docs/reviews/`, WORKLOG: decisions, evidence and history.
