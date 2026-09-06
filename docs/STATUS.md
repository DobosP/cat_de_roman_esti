# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V80 Clătite target verified locally. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V75 landed at `d127abb`; V76 at `9ef9dc7`; V77 at `9abbc52`, all locally.
  V78 at `010cfd1` deferred both dessert candidates; V79 at `9c208a9` repaired bounded Gem feedback.
  V80 promotes the freshly reviewed Clătite target; Cozonac and bread remain deferred.
  Technical candidate complete; public rollout remains subject to the external gates below.
- V73 shared session transactions and saved-game lifecycle landed locally at `f75a75c` (ADRs 0098–0100).
- V74 restores transiently unavailable rounds, rejects stale resume responses, recovers terminal results,
  retains retry after failed fresh creation, and preserves terminal Contexto/Lanț state (ADR-0101).
- Scrolling HUD/history are keyboard-reachable; all six intro/live/result states pass rendered audits and
  full desktop keyboard rounds (ADR-0103). Scores/receipts persist atomically; terminal IDs remain recoverable
  until recording settles, including options/exits and reloads (ADR-0105).
- V75 adds two reviewed Contexto food targets after dropping three weak candidates. Reusable pack-only
  import/review tools and bound evidence: ADRs 0102/0104/0106; `docs/reviews/v75-contexto-food/README.md`.
- V76 prevents accented `Paște`/`Paștele` from playing the unrelated pasta concept in Contexto/Lanț.
  Ordinary `paste`/`pastele`, compounds and all 13,177 existing surface mappings remain intact (ADR-0107).
  No content or frontend artifact changes; evidence: `docs/reviews/v76-romanian-input-senses/README.md`.
- V77 adds two directed flour ingredient links; bread is deferred after a misleading warm-guess route.
  The generator preserves retired edge-ID gaps. No pack records or aliases change (ADR-0108);
  evidence: `docs/reviews/v77-flour-associations/README.md`.
- V78 re-reviews Cozonac/Clătite using 68 ordinary API probes: cold Nucă and frozen Gem
  still contradict obvious filling guesses. Both raw candidates are dropped before staging (ADR-0109);
  evidence: `docs/reviews/v78-dessert-targets/README.md`. No IDs, rows, mappings or artifacts change.
- V79 gives Gem an authored strong, direct Dulceață neighborhood while retaining its Miere fallback.
  Papanași improves; the other 206 approved targets stay exact. All 473 terms remain unchanged;
  same helper protects scoring/suggestions and exact wins (ADR-0110). No target is promoted.
- V80 adds only `ct_gastronomie_320` (Clătite), gastronomie/usor, through fresh unanimous
  dossier-bound review. All 620 prior records and 336 frozen boards remain exact (ADR-0111).
  Evidence: `docs/reviews/v80-clatite-target/README.md`; no graph/runtime game-logic change.
- Served KG is `fixture-v77-flour-associations`: 2,364 nodes / 9,219 edges /
  8,450 aliases / 180 puzzles. `kg_real.json` is a thin export and is not the served fixture.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 210 | 208 | 2 | 204 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **621 = 613 approved + 8 pending**; original four-game ranking **451 eligible**.
V80 preserves all 620 old pack records, their scores/status/eligibility and all 336 frozen boards.
158 old Contexto ordinals move +1; one global weight and two existing filtered-shelf weights change.
KG, mobile payload, aliases, puzzles and holds stay exact. Only generated catalog bindings advance.
Sessions retain 7,200-second sliding TTL, 1,000 entries per game, per-entry locks, 64 KiB requests,
bounded histories/caches and server-private answers. V49 retains 104 Lanț rejections; the 70-term
nonaccepted ledger and V71 `intrigii`/`intrigilor` actionable-fuzzy deny remain intact.

## Current artifact pins

- `games_pack.json`: `27ce95294b7a8ea39aedc3f22e125650d0f06d9ecbcf0fb7af4bc6966d59cb29`
- `board_rankings_v37.json`: `823c5f302bd36c833283038affb1125dc434a1d34fba635e71c06b721cda4cec`
- `derived_catalog_v38.json`: `0787a4325c84753c739e7900f174cc99f46e9a4d3fbd8ce1e035cdf84c9b6ae2`
- `kg_sample.json`: `c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370`
- `cat_mobile_app_pack_contract.json`: `869499abccc3e6b5befe5d889a0e24c4d3bd67096c4d0a69c58d925680612a28`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

The V77 artifact-delta receipt records before/after pins and preserved payloads. Server KG manifest:
`sha256:d45e82150eea141c92d09125a64ec74f6c536d3876a8bc417814ad6bbd8a31a8`;
mobile public content: `sha256:7e90ec33dfddf74723dcea1ffc0e787c58ee8ae1f457b71528678db0918788ba`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and V72 alias smoke passed.
  Those observations were not rerun for this local candidate. No push or deployment was performed.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; detailed earlier record is in WORKLOG.
- The candidate's clean npm install/audit reports zero vulnerabilities. The deployed V72 lock has not
  been patched by this local work. Deployment/rollback procedure: `docs/DEPLOY.md`.

## Verification

V80 exact commands and source/artifact bindings: `docs/reviews/v80-clatite-target/verification.json`.
V79 verification remains historical evidence for the bounded Gem policy.

| Scope | Verified result |
|---|---|
| V80 focused / independent review | 30 V75/V77/V80 cases passed; independent ranking/derived 35 passed; fresh factual, quality, verifier and implementation reviews accepted |
| V80 backend Python 3.12.3 | 1006 passed in 294.27 s; accounts 53 passed in 2.59 s |
| V80 backend Python 3.14.6 | 1006 passed in 255.22 s; accounts 53 passed in 3.50 s |
| V80 frontend, Node 24.19.0 / npm 11.17.0 | clean install; 173 native passed; lint/typecheck GREEN; npm audit zero findings |
| V80 real-BFF browser run | 108 desktop/mobile checks passed in 4.2 min against final content |
| V80 content gates | Both validators GREEN; all package/test mirrors exact; 620 prior pack rows and 336 frozen boards exact |
| V80 selection / public API | Repeated 100-seed and September daily samples deterministic; other five games unchanged; new target hidden, warm and winnable through public create seeds 20/46 |
| Unchanged frontend build | V75 assets retained; typecheck/bundle GREEN, 118.73/120 KiB initial gzip; no frontend source changed |
| Final integration | Current pins refreshed; historical hashes reconstructed and raw reviews preserved; Ruff, docs and whitespace GREEN |

The new target has hot flour/egg/jam and warm milk/cheese paths. Reviewers retained the
cold butter/oil/honey/nut and unknown chocolate/dough findings as limits, not silent passes.
The V80 receipt records 158 ordinal changes, one global and two filtered weight changes.
No session, scoring or graph logic changed. Commands/runtime paths: `docs/agent-testing.md`.
Historical verification and measured runtime limits remain in WORKLOG and their review archives.

## Remaining gates

- Next bounded investigation: honest nut feedback for Cozonac; no mapping or promotion is implied.
  Cozonac and bread remain deferred. Widening local feedback needs new semantic/impact review.
  Release protocol and external evidence checklist: `docs/BETA_CANDIDATE.md`.
- Owner selects feedback contact; player and real-device checks remain unrun. Reverify legal operator/contact
  configuration and legal pages per DEPLOY; independent content judgments here are from Codex agents.
- Public rollout requires explicit authorization and live smoke/rollback verification. Technical candidate
  status does not establish enjoyment or permission to publish.
- Accounts remain outside the anonymous beta scope until DEPLOY's go-live checklist and compliance review pass.

## Doc map

- `README.md` / `AGENTS.md`: orientation/contract; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0111), `docs/reviews/`, WORKLOG: decisions/evidence/history.
