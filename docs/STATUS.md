# Status — cat_de_roman_esti

Last verified: 2026-09-09 — V91 landed locally and deployed to production `13e49b2`; automatic iteration is stopped.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V91 is locally landed at `48cd5b8`, following V90 baseline `e2e0363`.
  This is the final authorized version. Automatic recurrence is paused; the loop is
  stopped and V92 was not started (ADR-0137).
- Intrusul and Perechi now retain visible verification after failed recovery reads.
  Mutations stay locked; each retry reads once. Original saved-pointer ownership survives
  retries, including another tab removing its pointer. Successful replies also require
  matching game identity and ownership. Owned 404 returns to setup; changed ownership
  offers the current round. Animated Exit/Back departure invalidates stale replies,
  scoring and pending Perechi focus before passive effects (ADR-0138).
- Both games already preserved paid clues and capped hints at one. No backend clue or
  second-charge fix is claimed. Actual unmount was safe; the reproduced departure race
  occurred while the animation kept a screen mounted.
- Shared mobile headers display full titles and wrapping status badges. Notices occupy
  their own row above the scrollable screen. Measured header height positions sticky
  controls; short viewports retain normal flow. Long headings wrap at 200% text size.
  Toast announcements, dismissal, lifetime and package visuals remain (ADR-0139).
- Existing easy Sport Alchimie 083 now starts with Neagu, Echipă națională, Dinamo,
  Rapid, FCSB and CFR Cluj. Six useful seeds replace a start with three depleted items.
  Four productive pairs represent two ideas; six recipes/four routes retain par 2.
  ID, target, difficulty, source and approval stay unchanged (ADR-0140).
- V91 adds zero concepts, links, forms, synonyms or rounds; one round is revised.
  The exact approved-stock writer requires two bound independent accepts, reconstructs
  the dossier and live private book, and validates/rolls back both pack mirrors.
  Target salience 0.4323 remains an editorially accepted warning, not measured recognition.

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
All KG/mobile bytes, the other 660 pack records and 336 complete derived boards stay exact.
The other 82 Alchimie books remain exact; all100 Lanț records are unchanged.
Sport 083's heuristic score rises67→70 (familiarity 49→60, play quality 93→85), rank 38→23
and weight 3→4. Fifteen other Alchimie ordinal ranks shift; al_limba_042 weight 4→3.
No other score, eligibility or approval changes. Only Alchimie's seeded start changes.
Sessions keep 7200-second sliding TTL, 1000 entries/game, locks, 64 KiB requests and bounded
histories/caches. Projection 464/26 domains, 71 proxies, 11 native pairs and 4 audit tuples remain.

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

- All 16 final local gates are GREEN. Python 3.12 and 3.14 each pass **1652 backend/53
  accounts tests**. Frontend passes **193 native/342 browser checks**, lint/typecheck/
  build/bundle, with two isolated browser workers and zero retries at **119.08/120KiB**.
- Independent factual/quality judges accept the exact Sport revision. The writer's 37
  guard/transaction tests and real serial application pass. Independent migration/history
  audit passes 85 tests; all 83 live books match the exact reviewed candidate.
- Four fresh public seed 38 Sport journeys all win at par 2/1000 points: 16 actual BFF
  requests, four sessions deleted. Only Alchimie's six-game seeded start changes.
- Recovery passes 80 focused browser cases and 26 native checks; independent review adds
  four Back and two removed-pointer checks. Six archives retain 199 exact raw entries.
  Mobile passes 14 focused browser/10 native checks with 255 verified raw/decoded bindings.
- Two stale backend expectations were corrected while preserving complete V87/V90 checks.
  The first red run was deliberately interrupted after 1265 passes/two failures; it is
  excluded. Both subsequent complete Python matrices pass. Current approved books have
  554 recipes/76 two-result recipes/median 0.68; V90 retains 555/77/0.67 in history.
- Initial full browser 338 pass/two failures exposed old hint setup after Sport's new opener.
  The test-only correction preserves all six original solution fields and explicitly
  covers output/pair/category clues: 34 focused and 342 final full checks pass.
- Original failures, non-reproductions, traces, intermediate catalog-pin 503 and earlier
  recovery-run 143 are retained with precise scope. Separate freeze receipts account for
  the two test-only amendments; serving runtime/data and final UI assets stayed exact.
- Evidence: `docs/reviews/v91-recovery-and-mobile-clarity/verification.json`, immutable
  review inputs, independent audits and final file ledger. Human/player/device acceptance
  remains unrun. The candidate ledger is sealed at `48cd5b8`; later landing notes are
  documentation only. V90 evidence stays in its historical review folder.

## Production and remaining work

- Last documented deployment: anonymous **V91** `13e49b2c1148bb0aab35cc1e3b023b5bd29c142d`
 (2026-09-09), image `sha256:91d425c6d14065be7413762608309f8d924a86611e9e2e4a2072ce59abb041b9`,
 tagged `release-13e49b2c1148`. Fast-forwarded from V72 `6ee8693` (74 commits); compose,
 Dockerfile and dependencies were unchanged, so only code and content shipped.
 Rollback: `cat-de-roman-esti:rollback-6ee869350387` retained on the host, plus the older
 `rollback-60c3fd5318a`. Accounts stayed out of scope (`accounts_enabled: false` verified live).
- Post-deploy smoke GREEN (2026-09-09): `/healthz` 200; `/api/me` accounts off; `/api/health`
 `concepts=2416` equal to `/api/manifest` `counts.nodes=2416`; `/api/categories` 14/14 with
 availability and zero empty categories; both mandatory Intrusul/Perechi `seed=38` POSTs 200
 with real boards. `CAT_KG_FIXTURE` confirmed on `kg_sample.json`. HSTS still 0 (open follow-up).
- V91 is landed locally and the loop is stopped. No further version is authorized.
 Human/player/device acceptance, operator/legal checks, feedback contact and rollout remain.
- Three Neagu edge labels have a factually reviewed past-tense proposal, unapplied in V91.
 Four thin approved Contexto neighborhoods and 17 unknown household surfaces remain open.
 Earlier hidden-target/A5 holds are unchanged; no automatic demotion or approval occurred.
 Keep accounts out until the DEPLOY checklist passes.

## Doc map

- `README.md`/`AGENTS.md`: orientation; `docs/agent-map.md`/`docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0140), `docs/reviews/`, WORKLOG: decisions, evidence and history.
