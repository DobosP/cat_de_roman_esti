# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V73–V76 technical candidate verified locally. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V75 landed locally at `d127abb`; V76 completes its reviewed input-sense follow-up.
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
- Served KG remains `fixture-v72-romanian-dishes-and-pastries-morphology`: 2,364 nodes / 9,217 edges /
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
All prior 618 pack rows and 336 frozen derived boards remain exact. Four Contexto weight bands and
its ordinal ranks change; selection remains deterministic within an artifact set. Other games' sampled
seeded/daily selections are unchanged. KG topology, aliases, mobile content and editorial holds are unchanged.
Sessions retain 7,200-second sliding TTL, 1,000 entries per game, per-entry locks, 64 KiB requests,
bounded histories/caches and server-private answers. V49 retains 104 Lanț rejections; the 70-term
nonaccepted ledger and V71 `intrigii`/`intrigilor` actionable-fuzzy deny remain intact.

## Current artifact pins

- `games_pack.json`: `9f559e33eac688868dfdf562f62022a3df629c9cb389b957dda0896d7cec70b5`
- `board_rankings_v37.json`: `118d8561a329fd6a4646524ee9b033302735708a66d8a5921245942d5616eb74`
- `derived_catalog_v38.json`: `2839606ad82ae781cd57c8c265b636871f9326733881240855a3c95f3dd94f1c`
- `kg_sample.json`: `fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106`
- `cat_mobile_app_pack_contract.json`: `4c01361f94adbc50677bb63b5463063e38ccf2783b4627befc7c2c13d33a9e8e`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

The V75 allocation receipt records before/after pins and exact preserved payloads. Server KG manifest:
`sha256:6a388f9bdb391ffca61ce4d51ab28255c00ed619142ded51cedd26c02bb9213d`;
mobile public content: `sha256:9e93479d2e417346dfabe7da8e5ffdc9078a0f75add14f11fc8cfc5ef87727ab`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and V72 alias smoke passed.
  Those observations were not rerun for this local candidate. No push or deployment was performed.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; detailed earlier record is in WORKLOG.
- The candidate's clean npm install/audit reports zero vulnerabilities. The deployed V72 lock has not
  been patched by this local work. Deployment/rollback procedure: `docs/DEPLOY.md`.

## Verification

| Scope | Verified result |
|---|---|
| V76 targeted / independent review | 137 alias/Contexto/Lanț tests passed; independent 17-case regression rerun GREEN; evidence/scope audit found no issues |
| V76 backend Python 3.12.3 | 968 passed in 276.99 s; accounts 53 passed |
| V76 backend Python 3.14.6 | 968 passed in 228.06 s; accounts 53 passed |
| V76 frontend, Node 24.20.0 / npm 11.19.0 | clean install; 173 native passed; lint GREEN; npm audit zero findings |
| V76 real-BFF browser run | 108 desktop/mobile checks passed in 4.3 min; direct holiday rejection/pasta acceptance/reload check passed |
| Unchanged frontend build | V75 typecheck/build GREEN; identical assets retained, 118.73/120 KiB initial gzip; backend-only V76 did not rebuild them |
| V75 review/tooling/content | 52 checks passed; validators GREEN; public warm-guess/win paths confirmed |
| Dependency/runtime | npm audit 0 findings; bounded offline latency/RSS evidence archived, including integrated V75 sample |
| Final integration | independent reviews found no remaining actionable issues; both validators, Ruff, docs and whitespace GREEN |

V76 code was verified at `3ad960e`; final status updates are documentation only.
Earlier V75 verification remains in the status snapshot at `d127abb`.
Commands and runtime paths: `docs/agent-testing.md`. Historical timing sensitivity and full prior
verification records remain in WORKLOG. The local runtime sample includes 100 Contexto sessions /
1,000 distinct guesses; its load, process-RSS limitations and latency data are in
`docs/reviews/v74-runtime-measurements/README.md`.

## Remaining gates

- Technical gates are complete; release protocol and external evidence checklist: `docs/BETA_CANDIDATE.md`.
- Owner selects feedback contact; player and real-device checks remain unrun. Reverify legal operator/contact
  configuration and legal pages per DEPLOY; independent content judgments here are from Codex agents.
- Public rollout requires explicit authorization and live smoke/rollback verification. Technical candidate
  status does not establish enjoyment or permission to publish.
- Accounts remain outside the anonymous beta scope until DEPLOY's go-live checklist and compliance review pass.

## Doc map

- `README.md` / `AGENTS.md`: orientation/contract; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0107), `docs/reviews/`, WORKLOG: decisions/evidence/history.
