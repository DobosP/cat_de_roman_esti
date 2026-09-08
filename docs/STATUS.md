# Status — cat_de_roman_esti

Last verified: 2026-09-08 — V88 full integration GREEN; ready for local landing. Production last checked 2026-08-27.

## Current state

- Six-game anonymous Romanian arcade, Django BFF + React SPA; terminal CLI retained.
  V87 is merged at `fa8cffd`, with landing record `2878417`. V88 remains on
  `feat/v88-cross-game-quality`; the owner-authorized local loop continues (ADR-0127).
- V88 adds Compas, Echer, Raportor, Mătură, Taburet, Cratiță and qualified Smântână dulce
  pentru frișcă: seven concepts, 28 forms (25 grammatical + three qualified), zero synonyms.
  It adds 33 directed links and removes exactly the unsupported fermented-cream→Frișcă
  edge de8676 (net32). Ordinary Smântână keeps its fermented owner and aliases (ADR-0131).
- Three new approved/selectable rounds: Alchimie Cremșnit (`al_gastronomie_107`, three
  actions, four useful openings) and two everyday Conexiuni boards (`cx_viata_de_roman_362/363`).
  Diplomat is held after the correct cream link made its old seeds a one-pair shortcut;
  alternative seeds were weak. No new Contexto, Lanț or derived rounds are claimed.
- Brioșă→Pâine now gives hot, nonwinning feedback through one exact native scope;
  all 238 other captured approved-record responses stay exact on unchanged graph bytes.
  Native Mătură/Taburet retire their approximate projections; vocabulary is 465 (ADR-0130/0131).
- Lanț reconciles uncertain move/undo/hint responses through one owned GET. Failed reads
  retain a visible read-only retry. One bounded earned hint survives resume without another
  consumed stage; actual position changes clear it. Stale replies cannot replace a new game.
  Shared action ownership retains Contexto behavior (ADR-0128).
- Portable Alchimie reviews now carry exact projection-audit bytes and two independent
  judge hashes; missing/stale/tampered or mixed-game audit batches fail closed (ADR-0129).
- Served KG: `fixture-v88-cross-game-quality`, 2,413 nodes / 9,442 edges /
  8,631 aliases / 180 puzzles. `kg_real.json` remains a thin export, not the served graph.

## Inventory and invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 234 | 234 | 0 | 76 eligible |
| Cald sau Rece | 241 | 239 | 2 | 235 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack **658 = 650 approved + 8 pending**; original four-game ranking **488 eligible**.
All 655 old pack records, 82 Alchimie books/profiles, 100 Lanț route profiles and 336
complete derived rows remain exact. No old eligible/preferred/starter stock is lost.
One nonshortest Lanț suggestion changes Saramură→Găleată; all 206 shown shortest hops remain.
All old native owners/forms, 9,409 retained edges and 180 puzzles remain exact.
Six formerly isolated cleaning nodes gain real paths via Făraș→Mătură→Podea; other old
beginner meshes remain isolated. All 71 scorer proxies and four prior native-audit tuples stay exact.
Projection domains remain 26; only the cleaning audit example changes Mătură→Pămătuf.
Native exact feedback pairs grow 9→10. Sessions retain 7,200-second sliding TTL,
1,000 entries/game, locks, 64 KiB requests and bounded histories/caches. No scoring formula change.

## Current artifact pins

- `games_pack.json`: `4c7030bd86e966162f4ac51ef00cf3bb649ff7a9d59c8c34e180cb7ff53e1636`
- `board_rankings_v37.json`: `b19a53983a1b4555c700f717033bb61b66aea9ea2dce643a7df0cf1a31e2c764`
- `derived_catalog_v38.json`: `1c1613cd4f1e59c2b8d68ded9b071b1f812198f50aca528a3785fef34fad90b8`
- `kg_sample.json`: `2964951e3f68be7b49abb7f727b97d700a42d7e3527b117ef8b6c2830103f9fc`
- `cat_mobile_app_pack_contract.json`: `d2fbb9f550a05b6b128431ee55787b2b156846887f0bc8ce1908f09e6683b951`

Server KG content: `sha256:b8205c055288f2d2697076d0fac2d4852b6c690089ac373507e325979952b2b2`.
Mobile content: `sha256:f8f5c13f2cb302338f35adf38e311906856d24cb04f58592c77783a519a61fd3`.

## Verification

- Exact independent graph, tooling, recovery, feedback and supplemental reviews accept the
  bounded scope. Actual preflight: 324 declared beginner entries (322 eligible) / 33 links.
  Supported graph/import/promotion gates pass; all three dossiers have zero FAIL/WARN.
- All 59 new graph/history/public cases pass; eight bread cases and 80 targeted Lanț/session
  checks pass. Tooling: 45 focused and 102 existing critique checks pass.
- Frontend: **193 native / 188 desktop-mobile browser checks pass**, with no full-run retries.
  Lint/typecheck/build/bundle pass at 118.92/120 KiB. Backend: **1,508 pass on each Python 3.12.3/3.14.6; accounts 53 each**.
- Both first full backends: 1,501 passed / seven historical-aggregate/topology failures.
  Exact historical/current assertions now pass all seven focused checks; bounds stay unchanged.
- Final impact: 11,233 fresh observations over 239 old approved records / 47 words. Complete
  baseline ancestry, failed proposals and raw logs survive in lossless hash-bound archives.
- Seed38 changes Alchimie to Liga Campionilor la handbal and Contexto reachability to 2,343;
  other four initial payloads remain exact. Tests do not establish human enjoyment.
- One later Python 3.12 attempt ended with signal 143 before completion; its partial log
  is preserved and excluded from success counts. The unchanged complete rerun passed.
- Final validators, pending, Ruff/docs/whitespace pass. All actual receipts and failure
  evidence: `docs/reviews/v88-cross-game-quality/`.

## Production — last observed 2026-08-27

- Last documented deployment remains anonymous V72 `6ee86935038744c0066cac6a50865f76eab93e37`,
  image `sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd`.
- Accounts/debug were off; health/config/assets and alias smoke passed. No production check,
  push or deployment occurred in V88. Preserve `rollback-60c3fd5318a` for the next rollout.
- Fresh local Python3.14.6 and Node24 dependencies are installed; deployed V72 is unchanged.

## Remaining gates

- V88 is green on its task branch. Local landing and the next version follow the active loop.
- Facts improved without universal rank improvement: reverse pastry guesses toward Frișcă and
  some native household-context guesses cool. Smântână remains warm for Frișcă; qualified
  whipping cream is hot. No semantic quality claim follows from the 8,540 changed observations.
- Brioșă/Pandișpan hidden targets and the investigated Diplomat Alchimie round remain held.
- Romanian-player sessions, real-device checks, feedback contact and operator/legal-page
  verification remain unrun. Rollout requires separate authorization and live smoke/rollback
  checks. Keep accounts out until the DEPLOY go-live checklist passes; see BETA_CANDIDATE.

## Doc map

- `README.md` / `AGENTS.md`: orientation; `docs/agent-map.md` / `docs/agent-testing.md`: routes/gates.
- `docs/adr/` (newest 0131), `docs/reviews/`, WORKLOG: decisions, evidence and history.
