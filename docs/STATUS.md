# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V81 walnut wave checked locally. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V80 merged into local main at `dbbcf6e`; V81 adds real walnut input with bounded feedback.
  Local technical candidate work does not authorize the public rollout below.
- V73/V74 share session/resume machinery, preserve recoverable rounds after transient failures,
  protect terminal recording across tabs and retain keyboard-accessible game states (ADRs 0098–0105).
- V75 and V80 add independently reviewed Mici, Salată de boeuf and Clătite targets through
  the strict pack-only pipeline. Prior Cozonac/bread rejections remain review history (ADRs 0102/0104/0106/0111).
- V76 preserves accented Paște/Paștele as unresolved holidays instead of pasta, while retaining
  the original 13,177 authored KG surface mappings (ADR-0107).
- V77 adds directed flour routes; V79 bounds Gem's direct preserve feedback. Bread remains
  deferred after its misleading Stilou route (ADRs 0108/0110).
- V81 adds Nucă with only `nucile`, plus four outgoing recipe edges. A shared native-ingredient
  policy uses direct reviewed links and retains the prior Miere approximation elsewhere.
  Tree/fruit-ambiguous forms are not aliases; exact-self, fuzzy, suggestion and clue privacy
  remain protected. No target is promoted (ADR-0112; `docs/reviews/v81-nuca-feedback/README.md`).
- Served KG: `fixture-v81-nuca-feedback`, 2,365 nodes / 9,223 edges / 8,451 aliases / 180 puzzles.
  `kg_real.json` remains a thin export, not the served graph.

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
All pack records, 336 frozen boards and 180 puzzles remain exact. No old semantic distance changes.
The remaining 472 projection rows, all 71 legacy proxies and Gem policy stay exact.
Only Baclava gets newly hot Nucă feedback among 208 approved targets; 207 retain fallback distances
and temperatures. One added reachable word causes 222,582 +1 ranks and 121 marginal temperature
crossings across 491,712 old-node/target scores. Baclava's private rank estimate improves;
four adjacent ordinals move, without changing weights, approval or eligibility.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, per-entry locks, 64 KiB requests,
bounded histories/caches and private answers. V49's 104 Lanț rejections, the 70-term
nonaccepted ledger and V71's actionable-fuzzy deny remain intact.

## Current artifact pins

- `games_pack.json`: `27ce95294b7a8ea39aedc3f22e125650d0f06d9ecbcf0fb7af4bc6966d59cb29`
- `board_rankings_v37.json`: `fa1094a6c51e6d51cdafc5fecd302ef43bd3f44ff0e5aa7b36b7397a8ef7b546`
- `derived_catalog_v38.json`: `f66624bfe2e5ef434c9d47eb21b128d569637ac941b85834b2c0a5a196de7a6a`
- `kg_sample.json`: `fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331`
- `cat_mobile_app_pack_contract.json`: `9012a0e6c6f48397a94ff8bfcbf297ea58e357ac283c978e4e9542ea66ae77b1`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:11b2d0e96d9f66ccfb239d21b1b6dd12e6616f1bfacf9522611fdfd08d90c6d2`.
Mobile content: `sha256:5ea700a00708cf799a4cad8dcc99c54cb6595f0e99c217b5d890b9a829195918`.
The V81 receipt reconstructs the complete pre-wave KG, rankings and derived artifacts by hash.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and V72 alias smoke passed.
  Those observations were not rerun for this local candidate. No push or deployment was performed.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; detailed earlier record is in WORKLOG.
- The candidate's clean npm install/audit reports zero vulnerabilities. The deployed V72 lock has not
  been patched by this local work. Deployment/rollback procedure: `docs/DEPLOY.md`.

## Verification

Exact commands, source bindings and intermediate findings: `docs/reviews/v81-nuca-feedback/verification.json`.

| Scope | Verified result |
|---|---|
| V81 focused / independent review | 14 behavior tests; 4 baseline reconstructions; independent 45-case V81/V77/V79 gate passed; factual and impact reviews accepted |
| V81 backend Python 3.12.3 | 1024 passed in 443.33 s; accounts 53 passed in 5.43 s |
| V81 backend Python 3.14.6 | 1024 passed in 620.63 s; accounts 53 passed in 6.85 s |
| V81 browser | 108 desktop/mobile checks passed in 5.3 min against regenerated start snapshot |
| Frontend application | 173 native checks, clean install/audit zero, lint/typecheck and retained 118.73/120 KiB bundle passed; app sources/assets unchanged |
| Content / game impact | Validators GREEN; eight pending items lint clean; 232 Conexiuni, 97 Lanț, 82 Alchimie profiles and 336 derived boards exact |
| Selection / history | All-six and Contexto shelf samples repeat and match across 100 seeds/30 September dates; old KG/ranking/projection/word-resolution history reconstructs exactly |
| Final integration | Current pins and generated browser snapshot corrected; full serial gates, Ruff/docs/whitespace GREEN |

Initial parallel runs hit stale count/hash assertions and a load-sensitive generation timing limit.
Corrected expected values preserve exact semantic assertions; the 45-second ceiling was not relaxed.
No broad UI refactor, dependency change, new game row or wider alias policy is part of V81.

## Remaining gates

- Next content step: freshly review Cozonac after its nut route improves; no promotion is implied.
  Bread and remaining approximate/unknown vocabulary need their own reviews.
- Owner selects feedback contact; Romanian-player and real-device checks remain unrun. Reverify
  legal operator/contact configuration and legal pages per DEPLOY before public rollout.
- Public rollout requires explicit authorization and live smoke/rollback verification. Keep accounts
  outside the anonymous beta until DEPLOY's go-live checklist and compliance review pass.
- Release protocol and external evidence: `docs/BETA_CANDIDATE.md`; these agent reviews are not playtests.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes and gates.
- `docs/adr/` (newest 0112), `docs/reviews/`, WORKLOG: decisions, evidence and history.
