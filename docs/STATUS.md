# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V86 full integration GREEN; landed locally; V87 starts next. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V86 is merged into local main at `7d8b177`, following V85 and its record `14e8895`.
  V87 starts from this verified content. No push or deployment.
- V86 adds nine preparation concepts, 30 accepted forms and 41 directed links; no removals.
  Frișcă, Albuș, Gălbenuș, Zahăr pudră, Lapte praf, Amidon alimentar, Cremă de vanilie,
  Congelator and qualified Mixer de bucătărie provide specific preparation/cooling cues.
- Congelator replaces its approximate Frigider projection and is hot for Înghețată.
  Two exact feedback pairs repair Ecler→Cremă de vanilie and Savarină→Frișcă while
  retaining guess identities, exact wins and every graph direction (ADR-0123).
- Five new Contexto rounds: Brânză, Lapte, Savarină, Frișcă and Cremă de vanilie.
  Lanț gains Frigider→Înghețată through chilled Frișcă or a Congelator compartment.
- Lanț reserves two existing corridor slots for available shortest alternatives, keeping
  a third exploratory slot and the six-choice maximum. On unchanged V85 content, 59/96
  eligible menus improve alternative coverage; no start misses two available short hops.
- New-game failures persist across all six games. Replay errors sit beside retry actions;
  failed replacement preserves options, prior progress/results and scores (ADR-0124).
  Long-result/intro placement and held replacement behavior pass browser checks.
- Served KG: `fixture-v86-preparation-and-route-quality`, 2,397 nodes / 9,360 edges /
  8,572 aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 235 | 233 | 2 | 229 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **649 = 641 approved + 8 pending**; original four-game ranking **479 eligible**.
All 643 old pack records and 336 derived rows remain exact. All old native owners/forms,
9,319 retained edges and 180 legacy puzzles remain exact; only 21 old node degrees change.
Projection vocabulary is 468 rows across 26 domains; retained rows, 71 legacy proxies and
four prior native-audit tuples stay exact. The freezer domain retains 18 synthetic rows.
The four prior exact feedback pairs remain; exactly two reviewed target-specific pairs join them.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, locks, 64 KiB requests,
bounded histories/caches and private answers. No new server-session fields or scoring formula.

## Current artifact pins

- `games_pack.json`: `b9c8771294abbb2242ca006f64b8bb8dd5e4ae175345383c608c53455015b25d`
- `board_rankings_v37.json`: `7e46c05207ef102aa7ff877d019235dede5d5e78c0afb19bd005fa413bd384cf`
- `derived_catalog_v38.json`: `55cfcd131f91e5f712c4fcf6b6324a167d0aaca24b59301b86c79a1462d7f68e`
- `kg_sample.json`: `b612eda1fb8712fb57f1e16ca2a4fed3e5f6cec847c977ab45ee420c575ffa1a`
- `cat_mobile_app_pack_contract.json`: `2222e09de934f8428bd90c5857b49d514587bf5fa2c44ecd4c3c0cec0cf09e3c`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:2ee5f5391548547df66d7d8ee74cf53b4105882c926c7597f5e518978c3bb46d`.
Mobile content: `sha256:bd2ccd079148398fc7732f9ade2ca6e0259d1613d3a7e5a8f97c791f746e9c82`.

## Verification

- Exact independent graph review and 324-word/41-link preflight pass. Both validators
  pass through the graph/import/promotion transactions. Six complete dossiers: zero FAIL,
  two explicitly justified salience WARNs; separate bound judges promote all six.
- All 45 preparation tests pass, including native forms, 41 directed moves, rejected reverse
  moves, two earned Alchimie outputs, sense exclusions, exact history and seven public journeys.
- Lanț policy: 65 existing/new checks pass; isolated before/after menus cover all 96 old
  eligible rounds. All 82 old Alchimie and 99 Lanț profiles stay exact; 9,120 first guesses
  per checkout cover 228 old approved records/40 inputs; 128 compatibility checks pass.
- Full backend: **1,353 passed on Python 3.12.3 and 3.14.4**; accounts: **53 passed each**.
  Frontend: **177 native and 148 desktop/mobile browser checks passed**; no skips/retries
  in the final browser run. Lint/typecheck/build/bundle pass at 118.87/120 KiB.
- Final validators, pending gate, Ruff/docs/whitespace pass. Initial focused UI failures and
  four updated source-shape assertions remain disclosed in the actual verification receipt.
- Seed-38 snapshot reflects Contexto reachability 2,312→2,321 and the new Lanț selection.
- Full evidence and actual receipts: `docs/reviews/v86-preparation-and-route-quality/`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for V86.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; see `docs/DEPLOY.md`.
- Fresh Node24 install/audit reports zero vulnerabilities; deployed V72 remains unchanged.

## Remaining gates

- V87 continues reviewed snack/ingredient feedback, playable content and action quality.
  Its final implementation and integration are not yet complete.
- Indirect Sarmale/oven/yeast feedback and some butter/dairy cues remain noisy. Bare
  temperature/cream/starch words retain their explicit boundaries. Frigider can colloquially
  mean a fridge-freezer; the new route counts distinct authored preparation/storage links.
- Biscuit is deferred because common ingredient/dessert guesses remain weak. Other investigated
  routes with plausible missing direct ingredients are deferred. Human enjoyment remains unmeasured.
- Owner feedback contact, Romanian-player and real-device checks remain unrun. Reverify operator,
  contact configuration and legal pages per DEPLOY before public anonymous rollout.
- Rollout requires explicit authorization and live smoke/rollback checks. Keep accounts out
  until the DEPLOY go-live checklist and compliance review pass. See `docs/BETA_CANDIDATE.md`.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0124), `docs/reviews/`, WORKLOG: decisions, evidence and history.
