# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V82 complete local integration GREEN. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V81 is merged into local main at `9533919`. V82 candidate: `feat/v82-playable-content-batch`.
- New version objectives are ADR-0113: coherent playable batches with enabling fixes, explicit
  baseline/outcomes, focused development checks and required final integration gates. Report
  concepts, connections, forms, synonyms, rounds, eligibility and visible fixes separately.
- V82 adds eight reviewed Contexto rounds: Cozonac, Pască, Muștar, Mujdei, Ciorbă de burtă,
  Urdă, Friptură and Bulz; four easy and four normal. All eight are runtime selectable.
- V82 makes the defining `burtă` guess hot/nonwinning for exactly Ciorbă de burtă, keeping its
  original body meaning elsewhere. Gem/Nucă policies and all 472 projection rows remain exact
  (ADR-0114; `docs/reviews/v82-playable-content-batch/README.md`).
- V82 adds reusable `scripts/report_content_delta.py`. Actual gains: eight rounds and one
  feedback repair; zero concepts/edges/forms/synonyms. No new boards in the other five games.
- V82 removes repeated Alchimie graph queries using a 4,096-pair memo local to one cold build
  (ADR-0115). All 82 curated projections and 12 mined sessions remain exact; graph queries in
  the mined sample fall 88.89%. The existing 45-second timing gate passes at 29.96 seconds.
- V73/V74 session/resume/recovery, keyboard accessibility and atomic terminal recording remain
  protected (ADRs 0098–0105). V76 preserves accented Paște/Paștele input senses (ADR-0107).
- Served KG: `fixture-v81-nuca-feedback`, 2,365 nodes / 9,223 edges / 8,451 aliases / 180 puzzles.
  `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 218 | 216 | 2 | 212 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **629 = 621 approved + 8 pending**; original four-game ranking **459 eligible**.
All 621 previous pack records, 336 frozen boards and 180 puzzles remain exact. KG, aliases,
mobile, old semantic distances, scores/status/eligibility, 71 legacy proxies and prior holds
are unchanged. Nine Contexto weight bands and insertion ordinals change as stock grows.
The receipt reconstructs complete pre-V82 pack/ranking/derived artifacts by original hash.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, per-entry locks, 64 KiB requests,
bounded histories/caches and private answers. Prior word-resolution/ledger safeguards remain.

## Current artifact pins

- `games_pack.json`: `26d61a029a6c706a02a15991730725a3421dfa1f9b36537032291828a44ab070`
- `board_rankings_v37.json`: `fc31646b058bf2caaaf63a90ac172e504fd2bd89c4028102c4570d054f9a40a8`
- `derived_catalog_v38.json`: `cf9ed7cba4bc82025297907a5131df7c7f61c06ac43722d22d591790e6facf9a`
- `kg_sample.json`: `fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331`
- `cat_mobile_app_pack_contract.json`: `9012a0e6c6f48397a94ff8bfcbf297ea58e357ac283c978e4e9542ea66ae77b1`
- `lant_rejection_tombstones.json`: `e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29`
- `contexto_impact_reserve_v69.json`: `4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612`

Server KG content: `sha256:11b2d0e96d9f66ccfb239d21b1b6dd12e6616f1bfacf9522611fdfd08d90c6d2`.
Mobile content: `sha256:5ea700a00708cf799a4cad8dcc99c54cb6595f0e99c217b5d890b9a829195918`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; submissions unavailable; health/config/assets and alias smoke passed.
  No production check, push or deployment was performed for this local V82 candidate.
- Preserve `rollback-60c3fd5318a` through the next successful rollout; procedure: `docs/DEPLOY.md`.
- Local clean Node24 install/audit reports zero vulnerabilities. Production's V72 lock remains
  unpatched by this local work. Frontend app sources/assets remain at their prior version.

## Verification

- Independent factual/quality screens: eight raw candidates covered; strict critique eight/zero
  flags; independent bound analyst/verifier both promote all eight; supported V2 apply GREEN.
- Fresh API evidence: 764 guesses across 23 sampled food targets. Exactly one observation changes
  after the feedback fix; 763 remain exact. Every KG target is covered by the policy-boundary test.
- Full backend: 1,057 passed on Python 3.12.3 (641.60 s) and 3.14.6 (588.88 s); accounts
  53 passed on each (7.57/7.71 s). No skipped tests in either final backend run.
- Frontend: 173 native tests, lint/typecheck and 118.73/120 KiB bundle check passed; all
  108 desktop/mobile browser checks passed (7.7 min). App sources/assets remain unchanged.
- Focused and independent content, history, projection-equivalence and memo checks passed.
  Both validators, strict pending gate, Ruff/docs/whitespace GREEN. Exact commands/results:
  `docs/reviews/v82-playable-content-batch/verification.json`.
- Public seed-38 starting snapshots regenerate unchanged. Selection samples repeat exactly over
  100 seeds/30 September dates; other curated games match, Contexto changes are disclosed.
- Initial full run exposed two stale current-inventory/profile expectations and the existing
  Alchimie timing failure at host load 75. Expectations were corrected with old-profile proof;
  the measured generator optimization retains exact games and the original timing ceiling.
  Later stale daily/policy expectations were corrected, and a seed-dependent typo skip was
  replaced by an always-exercised fixed-target test. The final complete runs are green.

## Remaining gates

- V82 is committed as a ready local candidate; the next landing request can merge its branch.
- Next batch candidates: deficient whey/grain/oven/pan and ingredient forms; over-warm soup/polenta
  feedback; the 15 named food dispositions and prior bread findings. Use ADR-0113 to choose scope.
- Owner selects feedback contact; Romanian-player and real-device checks remain unrun. Reverify
  legal operator/contact configuration and legal pages per DEPLOY before public rollout.
- Public rollout requires explicit authorization and live smoke/rollback verification. Keep accounts
  outside the anonymous beta until DEPLOY's go-live checklist and compliance review pass.
- Release protocol and external evidence: `docs/BETA_CANDIDATE.md`; agent reviews are not playtests.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0115), `docs/reviews/`, WORKLOG: decisions, evidence and history.
