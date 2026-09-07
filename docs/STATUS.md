# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V85 full integration GREEN; candidate ready for local landing. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V84 landed locally at `eb4155c`, followed by landing record `39b64cb`.
  V85 candidate: `feat/v85-ingredient-feedback-and-board-clarity`. No push or deployment.
- V85 adds eight culinary concepts, 25 accepted forms and 40 new specific links.
  One existing Mucenici/Moldova relation is relabelled correctly as the baked variant,
  preserving its endpoints, strength and directions (41 added edge IDs / one retired ID).
- Native Scorțișoară/Cacao replace their approximate food/coffee projections. Cinnamon is
  now hot for apple pie and cold for bread/Sarmale; cocoa and butter gain direct dessert cues.
- Four reviewed Contexto rounds are added: Ecler, Amandină, Halva and Înghețată.
  Lanț gains Stafide→Brânză, with real routes through Pască or Poale-n brâu.
- Two source labels in `cx_gastronomie_171` are corrected. One served Intrusul clue now
  says “Produse lactate”; all 336 derived IDs, choices, partitions and ranks stay exact.
  The Conexiuni source is not pilot-eligible; no new served Conexiuni/Perechi round is claimed.
- ADR-0120 audits at least 14 accepted words/domain, including four exact native migrations.
  Synthetic ingredient entries are now 13; this is an explicit audit-policy change.
  Metadata creates no scoring proxy. Historical synthetic coverage remains tested.
- V84 in-round help and earned Alchimie explanations remain; prior session/input guards hold.
- Served KG: `fixture-v85-ingredient-feedback-and-board-clarity`, 2,388 nodes / 9,319 edges /
  8,542 aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 230 | 228 | 2 | 224 eligible |
| Lanțul Cuvintelor | 99 | 96 | 3 | 96 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **643 = 635 approved + 8 pending**; original four-game ranking **473 eligible**.
All old native owners and 8,517 aliases remain exact. Only 22 old node degrees change;
9,278 retained old edges and 180 legacy puzzles remain exact. Of 638 old pack records,
637 are unchanged and one has exactly two corrected labels. Of 336 derived payloads,
335 remain exact and one label changes. All 82 prior Alchimie projections and 98 prior
Lanț route profiles remain exact. Old ranking changes are recorded separately from stock.
Projection vocabulary is 469 rows across 26 domains; every retained row and 71 legacy proxies
remain exact. Two retired projection words now resolve to their native IDs.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, locks, 64 KiB requests,
bounded histories/caches and private answers. No new session fields or scoring formula.

## Current artifact pins

- `games_pack.json`: `835937cc369918a0070a8d09a35f3982f21f74275476f061aa6c05242d270b4d`
- `board_rankings_v37.json`: `21ff49faabb631e2a62cd07e15a6f1de69b7cb9ad04f900344771b7fefeeac0b`
- `derived_catalog_v38.json`: `66f4aebe9d64f638cfc8d48d51692b27a0f846d56e072a9a028a33b72d6e1ec7`
- `kg_sample.json`: `b7d28b990d37164d8e41a93965a5824162ded56b2907ac03388fee717eb144b2`
- `cat_mobile_app_pack_contract.json`: `d1f5808af8e0e5188b84ad4591891aa029e7f6e59fdb0c7cc14d7dd6775d2d09`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:af0c1c9647501cb93b8c990f983ff44a226f715e5fa7d97b9bcffdca2e386923`.
Mobile content: `sha256:39da1d1b2ed32509d4ce6974251304454aa8d5b84976f9e475bd381626571c2c`.

## Verification

- Exact independent graph and label reviews pass. Five fresh dossiers: zero FAIL and four
  explicitly justified familiarity/salience WARNs; separate bound judges promote all five.
- 77 focused ingredient/board checks pass, including all five public rounds, both Lanț
  routes, repeat/resume/clues/exact wins, sense exclusions and identity-preserving label repair.
- Six-game comparison: 5,376 first guesses per checkout over 224 old approved records and
  24 inputs; all 45 new directed journeys work and all old eligible pools remain available.
- Broad compatibility: 599 cases; seven stale Clătite rank expectations corrected while
  preserving V83/V84 observations. The 48-case follow-up passes; full historical inverses pass.
- Full backend: **1,299 passed on Python 3.12.3 and 3.14.6**; accounts: **53 passed each**.
  Frontend: **177 native and 122 browser checks passed**, no skips or browser retries.
- Validators, pending gate, Ruff, docs, whitespace, lint/typecheck/build/bundle pass.
  Initial transfer remains 118.87/120 KiB; rebuilt application assets are byte-identical.
  Seed-38 snapshots reflect current Contexto reachability and intended Lanț selection change.
- Full evidence and actual receipts: `docs/reviews/v85-ingredient-feedback-and-board-clarity/`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for V85.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; see `docs/DEPLOY.md`.
- Clean Node24 install/audit reports zero vulnerabilities; this does not patch deployed V72.

## Remaining gates

- V85 is ready on its task branch for its next landing request.
- Indirect oven/yeast feedback remains too warm for some desserts; refrigerator is weak for
  Înghețată and bare “rece” is not accepted. The legal Poale-n brâu route is not shown among
  the initial three Lanț suggestions. Human fairness and enjoyment remain unmeasured.
- Owner feedback contact, Romanian-player and real-device checks remain unrun. Reverify legal
  operator/contact configuration and pages per DEPLOY before public anonymous rollout.
- Rollout requires explicit authorization and live smoke/rollback checks. Keep accounts out
  until the DEPLOY go-live checklist and compliance review pass. See `docs/BETA_CANDIDATE.md`.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0121), `docs/reviews/`, WORKLOG: decisions, evidence and history.
