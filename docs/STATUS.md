# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V78 candidate review verified locally. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V75 landed at `d127abb`; V76 at `9ef9dc7`; V77 at `9abbc52`, all locally.
  V78 completes fresh dessert-target screening with two drops and no served-content change.
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
- Served KG is `fixture-v77-flour-associations`: 2,364 nodes / 9,219 edges /
  8,450 aliases / 180 puzzles. `kg_real.json` is a thin export and is not the served fixture.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 209 | 207 | 2 | 203 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **620 = 612 approved + 8 pending**; original ranking **450 eligible**, +2 Contexto targets.
V77 preserves all 620 pack/ranking rows, 336 frozen boards, 180 puzzles and all aliases/holds.
Two directed ingredient edges and three node degrees change; mobile and metadata are regenerated.
Contexto flour/sugar paths and ordinal guess ranks change; board eligibility and weights stay exact.
Sessions retain 7,200-second sliding TTL, 1,000 entries per game, per-entry locks, 64 KiB requests,
bounded histories/caches and server-private answers. V49 retains 104 Lanț rejections; the 70-term
nonaccepted ledger and V71 `intrigii`/`intrigilor` actionable-fuzzy deny remain intact.

## Current artifact pins

- `games_pack.json`: `9f559e33eac688868dfdf562f62022a3df629c9cb389b957dda0896d7cec70b5`
- `board_rankings_v37.json`: `53c2542b845d2560a900712381ab4c28cb1b9789beaae9690639647871e905d3`
- `derived_catalog_v38.json`: `84aaa772746dac0eb4e1366738f467afad86c543c7430cb67810475d5a296878`
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

V78: 68 API probes independently reproduce byte-exact; 91 focused Contexto/V76/V77 tests pass
on Python 3.12.3 and 3.14.6. Both validators and bound raw-candidate preflight pass; all nine
served/derived/ledger artifacts match V77 exactly. The frontend clean install, 173 native tests,
lint/typecheck and retained bundle check pass (Node 24.19.0/npm 11.17.0; zero audit findings).
Ruff, docs and whitespace pass. V78 changes only review/status documentation; no full backend,
accounts or browser suite was rerun. Exact V78 checks: `docs/reviews/v78-dessert-targets/verification.json`.
The unchanged runtime retains the V77 integration evidence below.

| Scope | Verified result |
|---|---|
| V77 targeted / independent review | 19 ingredient/allocator/V43 checks passed independently; factual, impact, implementation and docs reviews complete |
| V77 backend Python 3.12.3 | 983 passed in 233.94 s; accounts 53 passed in 1.98 s |
| V77 backend Python 3.14.6 | 983 passed in 204.06 s; accounts 53 passed in 1.81 s |
| V77 frontend, Node 24.20.0 / npm 11.19.0 | clean install; 173 native passed; lint/typecheck GREEN; npm audit zero findings |
| V77 real-BFF browser run | 108 desktop/mobile checks passed in 4.2 min against the final two-edge fixture |
| Unchanged frontend build | V75 assets retained; typecheck/bundle check GREEN, 118.73/120 KiB initial gzip; backend-only V77 did not rebuild them |
| V77 content preservation | 620 pack/ranking rows, 336 frozen boards, 180 puzzles exact; both validators GREEN; repeated apply fails without mutation |
| Dependency/runtime | Prior bounded offline latency/RSS evidence retained; no new runtime/session code or dependencies |
| Final integration | No remaining review findings; Ruff, docs and whitespace GREEN; current pins corrected without rewriting historical evidence |

Exact commands, reviewed scope, intermediate findings and final results:
`docs/reviews/v77-flour-associations/verification.json`. V76 verification is preserved at `9ef9dc7`.
Commands and runtime paths: `docs/agent-testing.md`. Historical timing sensitivity and full prior
verification records remain in WORKLOG. The local runtime sample includes 100 Contexto sessions /
1,000 distinct guesses; its load, process-RSS limitations and latency data are in
`docs/reviews/v74-runtime-measurements/README.md`.

## Remaining gates

- Technical gates retain V77 evidence. Next: review the Gem projection’s honey anchor and measure
  a distinct Dulceață-based feedback alternative; no future mapping/promotion is approved.
  Cozonac’s nut route and bread remain deferred.
  Release protocol and external evidence checklist: `docs/BETA_CANDIDATE.md`.
- Owner selects feedback contact; player and real-device checks remain unrun. Reverify legal operator/contact
  configuration and legal pages per DEPLOY; independent content judgments here are from Codex agents.
- Public rollout requires explicit authorization and live smoke/rollback verification. Technical candidate
  status does not establish enjoyment or permission to publish.
- Accounts remain outside the anonymous beta scope until DEPLOY's go-live checklist and compliance review pass.

## Doc map

- `README.md` / `AGENTS.md`: orientation/contract; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0109), `docs/reviews/`, WORKLOG: decisions/evidence/history.
