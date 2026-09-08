# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V90 landed locally; V91 started; local loop active. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V90 is merged through `13a78fd`, including implementation `0039b1e`; it follows V89.
  V91 starts on `feat/v91-recovery-and-mobile-clarity`; the local loop remains active
  until stopped (ADR-0127).
- V90 adds Praf, Firimitură and Scamă: three concepts, 17 directed links, ten grammatical
  forms and zero synonyms. Thirteen old node degree fields regenerate; every old semantic
  field, owner, stored form, edge and all 180 CLI puzzles remain unchanged.
- Praf becomes native, retiring its synthetic ID/Pământ fallback and unused three-target
  neighborhood. Other 464 projection rows, 26 domains, 71 scorer proxies, 11 native exact
  pairs and four audit-only native tuples remain unchanged. Exact forms share one attempt;
  dust remains nonwinning against tool targets. No scoring formula changes (ADR-0135).
- Two new easy Cald sau Rece rounds are approved: Făraș355 and Aspirator356. Both final
  independent judgments pass full C1–C6 on exact dossiers, with five/eight incoming cues.
  V89 rejected IDs352/354 remain history. Burete is dropped before staging for weak dish
  cues despite six incoming neighbors; the investigated Conexiuni/Lanț rounds stay held.
- The plate→sponge edge de8797 opens exactly seven old kitchen nodes to the wider graph:
  Oală, Tigaie, Cană, Castron, Farfurie, Furculiță and Lingură. Removing it restores the
  six previously connected cleaning proxies; other sink boundaries remain. Reachability
  grows 2343→2353 through three new/seven old nodes; the proxy mapping stays exact.
- C3 now fails pending targets with fewer than five unique valid incoming neighbors and
  warns on approved stock. Numerical counts do not certify recognition. Four approved
  warnings leave existing scores/eligibility unchanged; A5 holds remain (ADR-0134).
- Alchimie recovers uncertain combine/hint/reset/win responses through one owned GET.
  A failed read retains a visible read-only retry and locks mutations. One already-paid
  public clue survives GET/resume; new unique combines/reset clear it. Stale or cross-tab
  responses cannot adopt another game or record an old result (ADR-0136).
- Served KG: `fixture-v90-household-discovery`, 2,416 nodes / 9,459 edges /
  8,641 stored aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served KG.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 234 | 234 | 0 | 76 eligible |
| Cald sau Rece | 244 | 242 | 2 | 238 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **661 = 653 approved + 8 pending**; original four-game ranking **491 eligible**.
All 659 old pack records, 83 complete Alchimie books/profiles, 100 Lanț route profiles
and 336 complete derived rows/payloads remain exact. One nonshortest water menu choice
changes Aluat→Burete on lt_stiinta_216; all 206 shown shortest first hops remain.
Sessions retain 7,200-second sliding TTL, 1,000 entries/game, locks, 64 KiB requests and
bounded histories/caches. The new Alchimie cue is one bounded public object, not a history.

## Current artifact pins

- `games_pack.json`: `e32139529aacc88e2f453ac1cee1d8cd9a2cd1b16f3ee0551a5a76779192391e`
- `board_rankings_v37.json`: `b5beb978b911c952ef2632cb2d93bc695be19f226b4a4661d77e26b335413fab`
- `derived_catalog_v38.json`: `6ac090bc2186bf00209913d1123ba3f54de9f7b02f9fa2a781f2dfcccbbf58a9`
- `kg_sample.json`: `d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109`
- `cat_mobile_app_pack_contract.json`: `5832ca01b97e949e3cf8cd0ecaf2a27b6be58a8a6fc2e9e1426f338f22272f7f`
- Rubric: `3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101`

Server KG content: `sha256:b005b9d24b9b7df0bd1869f8ade38ec62fd9080b2332444924dd40ad82a50486`.
Mobile content: `sha256:83cab839a30b48eeb2ef33b3089e31dae8ec3a82e3d6d9e2e4d5c2a24ea61de3`.

## Verification

- Independent graph factual/quality, Praf implementation, topology, Alchimie and final
  content/history reviews accept the bounded changes. Graph preflight: 324 beginner and
  17 direct-link probes. Supported serial application/import/two promotions are GREEN.
- Critique: 166 focused tests and all 242 pregraph profiles pass; no score/eligibility loss.
  History/migration: 367 tests, including 53 new cases, pass; five artifact inverses and
  normal/exception cache teardown restore exact V89 history and current V90 behavior.
- Alchimie: 74 focused backend, 32 browser and two independent repeated-read-failure
  cases pass. Source-shape/locator/stale-rubric and reviewer-harness failures are archived.
- Full frontend is GREEN: **193 native /246 browser checks**, no retries; lint/typecheck/
  build/bundle pass at **118.88/120 KiB**. Full Python3.12: **1,608 backend /53 accounts pass**.
- Python3.14 also passes **1,608 backend /53 accounts**. Its first process ended143
  without a summary and remains archived/excluded; cause unestablished. The same command
  passed separately with periodic progress output. All 16 final gates are GREEN.
- Final impact: 240 old approved records ×70 words, 16,800 fresh requests on each side.
  **11,120 selected feedback observations are exact; 5,680 change**, including 2,880 newly
  recognized inputs and 240 Praf identity migrations. This is not full HTTP-body equality.
  No compared win flag changes; 17 new direct-link wins pass. Only Contexto's seeded start
  changes reachability; the other five are byte-identical. Full raw hashes/logs are retained.
- Final independent audits accept all 16 receipts, 1,635 frozen inputs and 340 final
  present/deleted-file bindings. An earlier verifier note was preserved byte-for-byte
  inside the review folder. Candidate evidence is sealed by `13a78fd`; later status notes
  are documentation only. Evidence: `docs/reviews/v90-household-discovery-and-critique-gates/`.

## Production — last observed 2026-08-27

- Last documented deployment: anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off. No production check, push, deployment or external contact
  occurred in V90. Preserve `rollback-60c3fd5318a` for the next separately authorized rollout.

## Remaining gates and costs

- V91 starts remaining Intrusul/Perechi recovery reproduction, shared mobile HUD/notice
  clarity and existing easy-content review, including al_sport_083 and four C3 warnings.
  No V91 implementation or promotion yet; human/player/device acceptance remains unrun.
- Praf loses its broad earth approximation: 227 old-target ranks rise and 13 fall; Mop2→6
  remains hot. Other changed same-rank observations include closeness and 20 temperature
  shifts. The eight lower-rank existing-identity changes all concern Mop, not universal gains.
- Seventeen stress words remain unknown, including murdărie/pardoseală/curățenie/gunoi.
  Burete's plate proxy and generic floor cues remain weak; truthful links do not approve it.
- The four thin approved C3 warnings, earlier hidden-target holds, operator/legal checks,
  feedback contact and rollout remain open. Keep accounts out until DEPLOY's checklist passes.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0136), `docs/reviews/`, WORKLOG: decisions, evidence and history.
