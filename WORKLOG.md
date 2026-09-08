# Work log

Valid until: the recorded verification run ends — then treat as history.

## V72 verification (2026-08-27)

Moved from STATUS to keep current truth concise; current gates and production state remain there.

| Date | Command | Result |
|---|---|---|
| 2026-08-27 | full backend `pytest -q` | 898/898 passed |
| 2026-08-27 | accounts-on suite, sessions, focused V72, combined V71/V72, pin propagation | 53/53, 16/16, 6/6, 13/13, 196/196 passed |
| 2026-08-27 | transaction dry-run + apply | zero topology or projection change |
| 2026-08-27 | `validate_fixture.py` · `validate_games_pack.py` | 0 errors · pack valid |
| 2026-08-27 | ranking + derived regeneration | 618 total / 448 eligible; 336 boards |
| 2026-08-27 | ruff, formatting, mirrors, hashes, stale-pin, JSON/digests, whitespace | green |

## V74 pre-candidate integration record

Valid until: final V74/V75 integration — then treat as history.

# Status — cat_de_roman_esti

Last verified: 2026-09-06 — V74 targeted reliability/accessibility gates green; integrated gates pending. Production last checked 2026-08-27.

## Current state

- V74: a failed fresh start keeps saved-round retry available; all six games pass the added desktop/mobile check.
- V74: scrolling status and Lanț history are keyboard-reachable; rendered intro/live/result audits and
  full desktop keyboard rounds pass across all six games (ADR-0103). Integrated V74 gates are pending.
- V73 baseline: real-backend browser journeys protect all six games on desktop and mobile emulation
  (ADR-0098). Public seed-38 snapshots protect deterministic selection before shared refactors.
- Product line: six-game arcade (Django BFF + React SPA) + terminal CLI, served offline from
  `cat_de_roman_esti/fixtures/kg_sample.json`, build `fixture-v72-romanian-dishes-and-pastries-morphology`:
  2,364 nodes / 9,217 edges / 8,450 aliases / 180 puzzles (verified against the fixture `meta.counts` 2026-09-05).
- `kg_real.json` is a thin real-corpus export (932 nodes / 135 edges / 13 puzzles, no aliases) — **not** the served
  build; pointing `CAT_KG_FIXTURE` at it silently empties every curated category (data.py:27,34-36).
- Landed: V72 fast-forwarded on `main` at `6ee8693`; the rollout record `02dba24` is also on `main`. Actions runs
  `33023808156`/`33024392655` green on Python 3.12/3.14 + frontend.
- ADR-0099 consolidates existing-session transactions; ADR-0101 adds safe resume retry and terminal recovery;
  ADR-0105 bounds and deduplicates local terminal score receipts across Web-Lock-capable tabs. Contexto
  giveup and Lanț undo keep terminal sessions immutable; ADR-0097 remains the newest vocabulary/build decision.
- V72 wave: 50 unanimously reviewed genitive/dative aliases for 25 gastronomie owners, zero rejections; the V71
  actionable-fuzzy deny set stays exactly `intrigii`, `intrigilor`; the 70-term nonaccepted ledger is unchanged.
  Evidence: `docs/reviews/v72-romanian-dishes-and-pastries-morphology/README.md`.

## Inventory and runtime invariants

| Game | Total | Approved | Pending | Runtime eligible/preferred |
|---|---:|---:|---:|---:|
| Conexiuni | 232 | 232 | 0 | 74 eligible |
| Cald sau Rece | 207 | 205 | 2 | 201 eligible |
| Lanțul Cuvintelor | 97 | 94 | 3 | 94 eligible |
| Alchimie | 82 | 79 | 3 | 79 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

Pack inventory remains **618 = 610 approved + 8 pending** across 14 categories; original
ranking remains 448 eligible, Contexto 201 eligible, and derived payload 336 boards.
V51–V72 reviewed inventories retain their owners; V49 retains 104 Lanț rejections.
Sessions retain the 7,200-second sliding TTL, 1,000-entry per-game cap, per-entry locks,
64 KiB request ceiling, deterministic selection, and server-private answers.

## Artifact pins (V72)
Build: fixture-v72-romanian-dishes-and-pastries-morphology; KG:
fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106;
pack: 05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed;
ranking: 45dfd81444dec14b4b639122fe30dea58f05ca76440003eb5280cc01bfcdc3e9;
derived: 8cff438c25deb5084c0311e808941bfef23e3c7bdbf93242a7a53348a6d2ef57;
mobile: 4c01361f94adbc50677bb63b5463063e38ccf2783b4627befc7c2c13d33a9e8e;
server manifest content: sha256:6a388f9bdb391ffca61ce4d51ab28255c00ed619142ded51cedd26c02bb9213d;
ledger: e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29.
Protected payload pins remain: nodes without aliases
c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0;
edges f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0;
puzzles 3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc;
ranking rows faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031;
derived boards 71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6;
mobile public content sha256:9e93479d2e417346dfabe7da8e5ffdc9078a0f75add14f11fc8cfc5ef87727ab.

## Production

- Anonymous production was upgraded from V68 `60c3fd5318a` to exact V72
  `6ee86935038744c0066cac6a50865f76eab93e37` on 2026-08-27. The healthy app image is
  sha256:30b39c0bba954074de6cdecd377a9742f627f4900caccbae8805d132f5c317bd,
  tagged release-6ee869350387, with zero restarts and zero error-log markers.
- `rollback-60c3fd5318a` preserves the prior V68 image sha256:7a9b6dbc5832; older V65/V61
  rollbacks remain retained. Caddy kept the same container/image and zero restarts.
- Production checkout is clean; accounts/debug are off; submissions return 503. No
  database, OAuth, worker, environment, DNS, TLS, Caddy, or infrastructure change occurred.
- Health, healthz, me, all 14 categories, Intrusul/Perechi, exact UI assets, and a V72
  Contexto alias smoke are green. Production reports the V72 manifest hash
  sha256:6a388f9bdb391ffca61ce4d51ab28255c00ed619142ded51cedd26c02bb9213d
  with counts 2,364 / 9,217 / 180.
- Current local lock audit reports six high npm advisories; react-router/react-router-dom 7.18.1 carry
  GHSA-qwww-vcr4-c8h2, fixed in 7.18.2. V65 had the same lock and rollback does not reduce
  exposure; dependency remediation is separate.

## Verification record

| Date | Command | Result |
|---|---|---|
| 2026-09-06 | V74 rendered access/keyboard and failed-action recovery browser checks | 12 + 12 passed, desktop/mobile |
| 2026-09-06 | `npm run test:e2e` + strengthened progress/snapshot checks | 48/48 passed against integrated refactors; frozen starts unchanged |
| 2026-09-05 | `pytest tests/test_wordgames_session_store.py -q` | 16 passed |
| 2026-09-05 | `pytest tests/test_app_pack_contract.py tests/test_data_client.py -q` | 23 passed |
| 2026-09-06 | `ruff check`, docs, whitespace | all green |
| 2026-09-06 | `scripts/validate_fixture.py` | GREEN: fixture is valid (0 errors) |
| 2026-09-06 | `scripts/validate_games_pack.py` | games pack GREEN |
| 2026-09-06 | integrated accounts-on `pytest -q tests/accounts` | 53 passed |
| 2026-09-05 | alchimie sparse-recipes test alone at load ≈ 39 | failed: 49.0 s vs the 45 s budget (timing only) |
| 2026-09-06 | integrated full backend `pytest -q` | 922 passed in 270.26 s |
| 2026-09-06 | V74 frontend resume implementation + browser recovery | 165 native + 30 browser passed; lint/build green; 118.17 KiB gzip |
| 2026-09-06 | V74 local terminal-score receipt regression | 172 native + 17 desktop browser passed; lint/build green; 118.66 KiB gzip |
| 2026-09-05 | `python3 ~/work/agent-ops/scripts/check_docs.py .` | `files=29 dead_links=0 stale_terms=0 retired_verbs=0 orphans=0` |
| 2026-09-05 | `check_project_contexts.py --work-root ~/work` | row `ok`, thin pointer yes (reads the shared checkout) |
| 2026-09-06 | session/store + six game suites; request limits; ruff, docs, whitespace | 264 + 9 passed; all green |
| 2026-09-06 | Contexto/Lanț terminal + shared session/request-limit tests | 156 + 9 passed |

2026-09-05/06 runs used `~/work/cat_de_roman_esti/.venv/bin/python` with `PYTHONPATH=.` from the docs worktree.
V73 full-suite load was ≈ 5; the unchanged Alchimie timing gate passed. Historical timing sensitivity remains
documented in `docs/agent-testing.md`. Python 3.14 CI and production have not been run for V73.

## Next actions

- Keep `rollback-60c3fd5318a` through the next successful rollout.
- Complete the refactor-first anonymous-beta quality goal; remaining gates and playtest protocol:
  `docs/BETA_CANDIDATE.md`. V74 targets reliability/UX; V75 prepares a reviewed playable-content wave.
- V74 clean npm install/audit reports zero vulnerabilities. Local runtime evidence, including 100 Contexto sessions:
  `docs/reviews/v74-runtime-measurements/README.md`.

## Open gates

- Accounts-stack go-live: the `docs/DEPLOY.md` go-live checklist plus `docs/compliance/` lawyer review
  (DEPLOY.md:35-40). Production runs anonymous mode until both are satisfied.

## Doc map

- `README.md` / `AGENTS.md` — orientation and contract; `docs/agent-map.md` / `docs/agent-testing.md` — routes and gates.
- `docs/adr/` (newest ADR-0103), `docs/reviews/`, `docs/handoffs/`, and `docs/archive/` — decisions and history.


## V77 — bounded flour routes, 2026-09-06

Valid until: the next relevant content wave — then treat as history.

Continued from local V76 `9ef9dc7`. V77 accepts Făină→Cozonac and Făină→Clătite;
the factually valid bread link was deferred after it made flour warm for Stiloul
cu rezervor. Fixed generated edge-ID allocation so retired gaps remain absent.
The final KG has 2,364 nodes, 9,219 edges, 8,450 aliases and 180 unchanged puzzles.
All 620 pack/ranking rows and 336 frozen derived boards remain exact. Historical
review files remain untouched; current test pins were refreshed and V77 separately
reconstructs the exact prior KG. No game candidates were promoted.

Both Python 3.12.3/3.14.6 full suites passed 983 tests, plus 53 accounts tests each.
Frontend: 173 native tests and 108 final-fixture desktop/mobile checks passed;
clean install/audit zero findings, lint/typecheck and retained 118.73 KiB budget GREEN.
Independent factual, impact, implementation and docs reviews complete; validators,
Ruff/docs/whitespace GREEN. ADR-0108 and `docs/reviews/v77-flour-associations/` hold
bounded acceptance, rejected-bread evidence, hashes, reproduction and exact results.
Landing is local only; production/feedback/player/device/legal verification gates
remain as recorded in BETA_CANDIDATE. Next: fresh Cozonac/Clătite target reviews.


## V78 — fresh dessert-target screening, 2026-09-06

Valid until: the next relevant food-feedback or target wave — then treat as history.

V77 was already on clean local main at `9abbc52`. Re-reviewed the two existing
Cozonac/Clătite candidates using a new exact two-row batch, independent factual
screening, an ordinary-player quality screen and adversarial diagnosis. All 68
fixed-target API probes were reproduced byte-exact by a second executor of the
same runner. Flour now works, but Nucă remains cold for Cozonac and Gem remains
frozen for Clătite while Dulceață is hot. Both targets are dropped before staging;
no pending IDs or promotions were created. Gem and Nucă currently borrow Miere
in Contexto's projection table. ADR-0109 and the V78 review archive preserve the
negative result and the bounded next Gem-feedback hypothesis.

All nine generated/ledger artifacts remain byte-identical to V77; runtime,
frontend assets, existing content and session limits are untouched. Fresh checks:
91 focused tests on each of Python 3.12.3/3.14.6, both content validators,
read-only batch preflight, 173 native frontend tests, clean npm install/audit,
lint/typecheck and bundle budget. V77's full backend/accounts/browser evidence
remains prior evidence; those suites were not rerun for documentation-only V78.
Ruff, docs and whitespace checks are recorded in the V78 verification file.
No push, deployment or human-playtest claim. The next wave should assess Gem's
feedback anchor with distinct projection identity and exact-win/privacy guards,
then review effects across current targets before any change or promotion.


## V79 — bounded Gem feedback, 2026-09-06

Valid until: the relevant projection, Contexto routes or bound content changes — then treat as history.

Continued from clean local V78 `010cfd1`. The first global Gem→Dulceață trial
repaired Clătite but made unrelated savory targets warm; the 207-target impact
review rejected it despite green local tests. A one-hop-only simulation also
included weak seasonal Socată. The accepted policy retains every original term
and Gem's Miere default, borrowing Dulceață only for self or a reviewed directed
non-distractor edge at strength >=0.60. Both guesses and suggestions use the
same private helper. Exactly six graph concepts qualify, with an explicit
regression guard. Gem remains distinct and nonwinning; exact answers still win.

Of 207 approved targets (203 eligible), only Papanași changes: rank 1291/very cold
to rank 13/hot. Fixed Clătite improves rank 1699/frozen to rank 8/hot. All other
206 approved responses, all 473 projection rows and all content artifacts remain
exact; selection, score rules and session bounds remain intact.
Cozonac/Clătite remain deferred targets; no promotion or topology edit occurred.

Final full suites: 996 passed on Python 3.12.3 (278.39 s) and 3.14.6 (247.49 s), plus
53 accounts tests each. Focused 13 passed; independent V79/V44 25 passed. Node 24.19.0
and npm 11.17.0: clean install/audit zero, 173 native, lint/typecheck/bundle and
108 desktop/mobile checks passed. Both content validators, Ruff/docs/whitespace
and independent factual, impact/implementation reviews are green. ADR-0110 and
the V79 archive bind final source/tests/results and preserve the rejected global
trial. The full matrix was repeated after adding the six-node guard; no runtime
changed between runs. Next: fresh Clătite content review. No push, deployment or
human-playtest claim.


## V80 — reviewed Clătite target, 2026-09-06

Valid until: the bound candidate, content or relevant runtime changes — then treat as history.

V79 was already landed at `9c208a9`. A fresh one-row Clătite candidate passed
independent factual and quality screening, strict pending critique and unanimous
dossier-bound analyst/verifier review. The supported importer staged one pending
row; the V2 applier promoted `ct_gastronomie_320` in gastronomie/usor. Reviewers
retained the cold fat/honey/nut and missing chocolate/dough limitations explicitly.
The repaired flour/egg/milk/jam/dairy paths now support a coherent easy round.

Pack stock is 621 = 613 approved + eight existing holds; Contexto has 204 eligible
targets. Every old pack row, score/status/eligibility and all 336 frozen boards
remain exact. Generated ranking/derived bindings and the trusted catalog digest
advance; KG, mobile, aliases, puzzles and game logic do not change. The receipt
records 158 old Contexto ordinal shifts, one global and two filtered weight changes.
The other five games retain all sampled selections; repeated current-artifact
selection is deterministic. Public seed 20 selects the new hidden, warm, winnable
round; current Mici smoke moves to seed 19 while Salată de boeuf retains seed 6.

Both full suites pass 1,006 tests (Python 3.12.3: 294.27 s; 3.14.6: 255.22 s), plus
53 accounts tests each. Thirty historical/new content cases and 35 independent
ranking/derived cases pass. Node 24.19.0/npm 11.17.0: clean install/audit zero,
173 native, lint/typecheck/bundle and 108 desktop/mobile checks pass. Validators,
Ruff/docs/whitespace and stale-reapply refusal are green. Historical SHA assertions
remain meaningful through exact pre-V80 reconstruction; raw review history is
untouched. ADR-0111 and the V80 archive bind acceptance and the final evidence.
Next: independently investigate honest nut feedback for Cozonac; bread remains
deferred. No push, deployment or human-playtest claim.


## V81 — real walnut input with bounded feedback, 2026-09-06

Valid until: the bound word, topology, policies or game content changes — then treat as history.

V80 was already merged at `dbbcf6e`. V81 adds one Nucă concept, sole alias nucile,
and four source-backed outgoing recipe links through the existing V24 transaction.
The ordinary density guard stays intact; ADR-0112 narrowly permits four outgoing
links for this new node and partially supersedes ADR-0033's cap. Naive graph
simulations were rejected for savory/regional/history warmth. The accepted native
Contexto rule uses only self or strong direct ingredient links; Miere remains the
penalized fallback elsewhere. Other 472 projection rows, 71 legacy proxies and
Gem policy remain exact. Ambiguous tree forms and part/whole aliases are deferred.

Actual graph: 2,365 nodes, 9,223 edges, 8,451 aliases. All 621 pack records, 336
frozen boards and 180 puzzles stay exact. Only Baclava gets newly hot Nucă feedback
among 208 approved targets; Cozonac/Colivă/Cornulețe fixed recipe probes are hot.
Across 491,712 old-node scores, old distances stay exact; 222,582 ranks move +1
and 121 marginal tier crossings are documented. Baclava's private estimate rises
one point and four adjacent ordinals shift; no weights/eligibility/status change.
All-six-game profiles and bounded seed/date samples remain stable.

Final serial gates: 1,024 tests on Python 3.12.3 (443.33 s) and 3.14.6 (620.63 s),
53 accounts each, 173 frontend native checks and 108 browser checks (5.3 min).
Validators, Ruff/docs/whitespace, semantic/implementation/impact reviews and
already-applied refusal pass. Earlier parallel runs exposed stale expected counts
and the documented timing sensitivity; neither the 45-second gate nor behavior
was relaxed. The browser-start snapshot was regenerated for reachable_count +1.
No frontend app source/assets or dependencies changed. Historical graph/ranking,
projection and 13,177-word-resolution proofs remain intact through exact inverses.
Evidence: ADR-0112 and docs/reviews/v81-nuca-feedback/. Next: fresh Cozonac target
review; bread and other approximate vocabulary remain deferred. Land means merge
into main; no push, deployment or human-playtest claim.


## V82 — playable food batch and bounded generation reuse, 2026-09-06

Valid until: the bound content, scoring policies or generation implementation changes — then treat as history.

V81 was already merged into local main at `9533919`. V82 records the owner's expanded
version objectives in ADR-0113: coherent playable batches with enabling fixes and honest
baseline-to-candidate counts. The new report tool distinguishes graph concepts, connections,
forms, approvals, runtime-ranked eligibility and frozen boards; aliases are not inferred
synonyms. Agent-map and the pack-only workflow point future versions to these objectives.

Twenty-three food targets were screened with 764 fixed-session probes. Eight received
complete independent factual/quality screens and unanimous dossier-bound analyst/verifier
promotion: Cozonac, Pască, Muștar, Mujdei, Ciorbă de burtă, Urdă, Friptură and Bulz. The
supported importer/serializer/applier added `ct_gastronomie_321`–`328`. Contexto selectable
stock grows 204→212; pack stock is 629 = 621 approved + eight original pending holds.
No graph concept, edge, form, genuine synonym, other-game record or frozen board is added.

The defining `burtă` guess was cold for the soup. ADR-0114 adds explicit target-only
projection feedback: rank434/Rece becomes rank2/Fierbinte without winning; all 472 original
projection rows remain exact and other targets keep body feedback. Exactly 1 of 764 repeated
probes changes. All 621 prior pack records, all 336 frozen boards, the KG/mobile/puzzles and
old quality/status/eligibility remain exact. Nine global Contexto weight bands change;
selection remains deterministic, with daily/seed changes recorded. Complete V81 artifact
hashes reconstruct through a compact inverse receipt. Fifteen omitted targets and ordinary
cold/unknown ingredient/form gaps remain documented rather than implicitly approved.

The initial full gate exposed stale current-inventory/profile expectations and the known
Alchimie timing failure: 52.73 s versus 45 s at host load 75. Profiling found 20,606,576 graph queries
in twelve mined sessions. ADR-0115 uses a local 4,096-pair memo with uncached fallback after
capacity; query count falls 88.89% to 2,288,987. Complete dataclasses for all 82 curated
projections and twelve mined sessions remain exact, including recipes/routes/par/private
quality. The unchanged timing test passes at 29.96 s. Later stale daily/policy expectations
were fixed, and a seed-dependent typo skip became a deterministic real-target regression.
No test threshold, session bound or search limit was relaxed.

Final full gates: **1,057 passed on Python 3.12.3 in 641.60 s and Python 3.14.6 in 588.88 s**, with
zero skips; accounts 53 passed on each. Frontend 173 native tests, lint/typecheck and retained
118.73/120 KiB bundle pass; **108 desktop/mobile browser checks passed in 7.7 min**. Clean Node 24
install/audit reports zero vulnerabilities. Validators, strict pending gate, Ruff, docs and
whitespace pass. Frontend application/assets and regenerated seed-38 starting snapshots are
unchanged. Backend starts were staggered past their timing checks, then independent gates
overlapped. Exact commands, source bindings and intermediate failures are in the V82 archive.

V82 is a committed local candidate on `feat/v82-playable-content-batch`; no push, deployment,
real-device check or human playtest is claimed. The next landing request can merge this
verified batch. Further content work should combine relevant feedback/vocabulary repairs
with fresh playable candidates under ADR-0113. Public anonymous-beta external gates remain.


## V82 local landing and V83 start, 2026-09-06

Valid until: the next landing or version changes these facts — then treat as history.

Verified the complete V82 source/review manifest and green gate receipts, then fast-forwarded
local main to `e5f7d96`. Removed its merged local branch, worktree and scratch; no origin
branch existed, and no push or deployment occurred. V83 starts on
`feat/v83-food-input-and-feedback` under ADR-0113, combining ordinary food-input/feedback
repairs with a reviewed playable batch and less repetitive artifact-pin maintenance.

## V83 food input and feedback candidate, 2026-09-07

Valid until: the reviewed content, policies or validation bindings change — then treat as history.

V83 adds five independently reviewed Contexto rounds (Cornulețe, Gogoși, Telemea, Cartofi
prăjiți and Ardei umpluți), increasing eligibility 212→217. It accepts 24 grammatical or
qualified forms across eight existing concepts and repairs six exact-target ingredient/filling
feedback pairs. New concepts, shared KG edges and genuine synonyms: zero. All 629 old pack
records, 336 frozen boards, 180 puzzles, older surface owners and excluded-input behavior
remain exact. Independent review, full baseline inverses, 884 before/after observations
(six intended changes) and 60 extra controls support the bounded change. Known false-hot
Sarmale/Drojdie feedback and missing production/utensil vocabulary remain follow-ups.

ADR-0116 centralizes manually authored current test expectations while retaining historical
pins and uses bounded named-round seed lookup for API journeys. It also repairs a proven
old-document response race in browser reload assertions. ADR-0117 records the forms and
explicit feedback pairs; ADR-0110 is partially superseded for Gem's two additional targets.
Runtime scoring, answer privacy, session TTL/size limits and test thresholds remain unchanged.

Python 3.12 passed all 1,115 tests in 751.83s. Python 3.14 passed 1,114 with only the known
Alchimie timing case over its unchanged 45s ceiling (50.30s); that case passed on retry at
21.96s. Accounts passed 53 on each runtime. Frontend passed 173 native tests and all 108
browser checks after fixing the reload race; the earlier browser run's nine failures and
host-pressure observations remain disclosed. Lint/typecheck/build/bundle, both validators,
pending gate, Ruff/docs/whitespace pass. Rebuilt application assets are byte-identical.
The V83 archive binds exact commands, source bytes, independent reviews and artifact hashes.

V82 is merged into local main at `e5f7d96`, followed by landing record `38f0d62`; V83 remains
on `feat/v83-food-input-and-feedback`, ready for its next landing request. No push, deployment,
real-device acceptance or human playtest occurred. Anonymous public-beta external gates remain.


## V84 six-game guidance and culinary graph quality, 2026-09-07

Valid until: the reviewed content, behavior or validation bindings change — then treat as history.

Started from V83 already on local main at `8353880`. V84 adds native in-round Romanian
help to all six games, including safe Enter behavior, and earned Alchimie explanations
with actual oriented graph relations retained after resume. It adds 15 culinary concepts,
42 forms and 57 specific links, and removes one false Telemea/Poale-n brâu cheese edge.
One lexical equivalent is explicitly reviewed; the remaining forms are not counted as
synonyms. Only 25 old node degree fields change; all old aliases and retained edges stay exact.

Independent bound review promotes three Contexto rounds (Plăcintă cu mere, Salam de biscuiți,
generic Pâine) and one Lanț route (Făină→Cornulețe). Eligibility grows 217→220 and 94→95.
All 634 old pack records, 336 frozen boards and 180 legacy puzzles stay exact. All 82 old playable
Alchimie projections and 97 old Lanț profiles stay exact; broader theoretical crafting closure
changes are measured separately. Six false-hot yeast/meat-or-cheese associations cool;
cinnamon/bread, cocoa/oven and other remaining feedback noise are explicitly disclosed.

Source and exact-edge removal reviews pass, including an independently found duplicate-ID
helper flaw fixed before content mutation. Full baseline inverses, 3,757 observations per
checkout, 67 new directed-link journeys and four real public journeys support the change.
Five stale historical test expectations surfaced in the initial integration run; original
values remain checked on restored V83 data and current assertions bind the reviewed delta.

Fresh full gates: **1,207 passed on Python 3.12.3 in 767.72s and Python 3.14.6
in 667.85s**, 53 accounts each, 177 native frontend and 122 browser checks. No skips,
browser retries or relaxed thresholds. Build/bundle 118.87/120 KiB, both validators, pending
gate, lint/typecheck, Ruff/docs/whitespace and independent reviews pass. Actual built desktop
and mobile screenshots were inspected. Initial failures and interrupted diagnostic runs
are retained in the verification receipt; all final source/review bytes are manifest-bound.

V84 is a committed local candidate on `feat/v84-six-game-graph-quality`, ready for its next
landing request. Shared main remains at V83. No push, deployment, real-device acceptance or
human playtest occurred. Public anonymous-beta external gates remain in BETA_CANDIDATE/DEPLOY.


## V84 local landing and V85 start, 2026-09-07

Valid until: the next landing or version changes these facts — then treat as history.

Verified all 109 V84 source/artifact/review manifest entries and 15 final green gate
receipts, including 1,207 backend tests and 53 accounts tests on both Python versions,
177 native frontend tests and 122 browser checks. Landed `eb4155c` into local main with
this documentation update. V85 continues with ingredients/feedback and board clarity,
new concepts, specific graph links and reviewed playable content. No push or deployment.


## V85 ingredient feedback and board clarity, 2026-09-08

Valid until: the reviewed content, behavior or validation bindings change — then treat as history.

V84 landed at `eb4155c`, followed by local landing record `39b64cb`. V85 adds eight native
culinary concepts, 25 accepted forms and 40 specific links, plus one corrected Mucenici/Moldova
description. The latter preserves the relation's endpoints, strength and directions; physical
edge changes are 41 added IDs and one retired ID. Forms are not counted as synonyms.

Native cinnamon and cocoa remove known food/coffee approximations. Cinnamon cools from
hot to cold for bread/Sarmale and becomes hot for apple pie; butter and cocoa gain appropriate
direct dessert cues. ADR-0120 explicitly changes the domain audit from synthetic-only to
accepted words including four exact native migrations. All 469 retained projection rows and
71 legacy proxies remain exact; the metadata does not participate in scoring.

Independent review promotes Ecler, Amandină, Halva and Înghețată Contexto rounds plus
Stafide→Brânză in Lanț, with real routes through Pască and Poale-n brâu. Contexto eligibility
grows 220→224 and Lanț 95→96. Four salience warnings are explicitly justified; all eight prior
pending holds remain. The pack now contains 643 records, 635 approved and eight pending.

Two exact source labels are repaired. One served Intrusul clue now says “Produse lactate”.
The shared builder/runtime policy preserves all 336 derived identities, partitions, choices
and ranks, while rejecting stale or partial changes. No new Conexiuni/Perechi/Alchimie rounds
are claimed. All 82 prior Alchimie projections, 98 Lanț profiles and 180 legacy puzzles remain
exact. Indirect oven/yeast noise, weak cold clues and limited initial route suggestions remain.

Final gates: 1,299 backend tests on both Python 3.12.3 and 3.14.6, 53 accounts tests each,
177 native frontend tests and 122 browser checks pass. Validators, pending gate, Ruff,
docs/whitespace and lint/typecheck/build/bundle pass. Application assets remain byte-identical;
initial transfer is 118.87/120 KiB. Seventy-seven focused checks and 5,376 first guesses per
checkout support the reviewed delta. Seven stale Clătite rank expectations were corrected
with old observations retained on restored graphs; both full matrices pass without retries.
The actual corrected Intrusul clue was inspected at 390×844 in browser emulation.

V85 is ready on `feat/v85-ingredient-feedback-and-board-clarity` for its next landing request.
Shared main remains at `39b64cb`. No push, deployment, real-device acceptance or human playtest
occurred. Exact reviews, receipts and file bindings are in the V85 review archive.


## V85 local landing and V86 start, 2026-09-08

Valid until: the next landing or version changes these facts — then treat as history.

Verified all 82 V85 manifest bindings at `317ae7d` and all 15 actual final green gate
receipts, including 1,299 backend tests and 53 accounts tests on each Python version,
177 native frontend tests and 122 browser checks. Landed that candidate into local main
with this documentation record. V86 begins another batch of player-visible fixes,
reviewed concepts/links and playable content; remaining preparation/cooling feedback and
Lanț suggestion coverage are initial investigation candidates. No push or deployment.


## V86 preparation, route and replay quality, 2026-09-08

Valid until: the reviewed content, behavior or validation bindings change — then treat as history.

V85 landed at `317ae7d`, followed by local landing record `14e8895`. V86 adds nine native
preparation concepts, 30 accepted forms and 41 one-way links, with no removals. Existing
owners/forms, 9,319 edge records and all 180 puzzles remain exact; only 21 old node degrees
change. Congelator replaces its approximate Frigider projection, while qualified kitchen
mixer and starch keep their sense boundaries. Forms are not counted as synonyms.

Five Contexto rounds (Brânză, Lapte, Savarină, Frișcă, Cremă de vanilie) and one Lanț round
(Frigider→Înghețată) receive complete independent bound promotion reviews. Two salience
warnings are explicitly justified; all eight prior pending holds remain. Eligibility grows
224→229 and 96→97. Two closed feedback pairs repair natural Ecler/vanilla-cream and
Savarină/whipped-cream guesses without winning or reversing graph directions.

Lanț reserves two available shortest continuations within its old menu limits. Among 96 old
approved rounds, 59 menus improve; visible shortest first hops total 107→198, starts showing
none fall 32→0, and all 96 show at least two. No previously shown shortest option disappears.
All 643 old source records, 336 derived rows, 82 Alchimie projections and 99 Lanț profiles
remain exact. The 9,120-observation comparison per checkout separates stock and rank changes.

All six games persist creation errors beside retry actions and retain selected options,
old results/progress and scores. Existing intro/round DOM stays mounted during creation;
synchronous flight guards and disabled/inert controls prevent old-game mutations or duplicate
starts. Shared ResultCard and the live Alchimie footer reserve responsive notice space so
retry does not move outside a short viewport. Saved-game recovery remains separate.

Full gates pass: 1,353 backend tests on Python 3.12.3 (666.27s) and 3.14.4 (515.00s),
53 accounts tests each, 177 native frontend tests and 148 browser checks (8.6m).
Validators, pending gate, Ruff, docs/whitespace and frontend lint/typecheck/build/bundle pass;
initial transfer is 118.87/120 KiB. Focused evidence includes 45 preparation checks,
65 Lanț checks and 128 compatibility checks. Desktop/mobile screenshots were inspected.

Initial UI review/testing caught offscreen error placement, intro remount scroll loss and
retry-button displacement; those were repaired. Sticky/partially visible rules caused two
incorrect setup assumptions, corrected with strict notice/button viewport checks retained.
Four old native source-shape assertions were updated to require stronger creating/flight
guards while retaining the original behavior checks. Exact initial and final receipts remain
in the V86 archive; neither full Python matrix nor the final browser run required a retry.

V86 is ready on `feat/v86-preparation-and-route-quality` for its next landing request.
Shared main remains at `14e8895`. No push, deployment, real-device acceptance or human
playtest occurred. Indirect oven/yeast/Sarmale and some butter/dairy feedback remain noisy;
Biscuit and less defensible routes are deferred. Public-beta external gates remain.


## V86 local landing and V87 start, 2026-09-08

Valid until: the next landing or version changes these facts — then treat as history.

Verified all 144 V86 manifest bindings at `7d8b177`, including 12 removed build paths,
all seven lossless evidence archives and 16 actual final green receipts. These include
1,353 backend tests and 53 accounts tests on each Python version, 177 native frontend
tests and 148 browser checks. Landed that candidate into local main with this record.
V87 begins a coherent batch of snack/ingredient feedback, reviewed playable content and
action quality. Candidate quantities do not override the critique rubric. No push or deployment.

## V87 snack and action quality (2026-09-08)

Valid until: the source/artifact bindings change — then treat as history.

V86 `7d8b177` was merged into local main, with landing record `daae025`; its verified-merged
branch/worktree/scratch were removed. V87 starts from `daae025` and finishes on
`feat/v87-snack-and-action-quality`, ready for a later local landing. No push/deployment.

V87 adds nine concepts, 50 directed links and 31 forms (30 grammatical/qualified, one
regional Cremșnit/cremeș equivalent), and promotes six new Contexto rounds: Biscuit, Chec,
Cremșnit, Tort Diplomat, Pișcot and Ciocolată. Contexto eligibility grows 229→235. Native
Chec/Brioșă replace broad projections, generic tort is recognized, and five exact
nonwinning feedback repairs retain identities and isolate projected/native exceptions.

Contexto reconciles lost guess/clue/giveup responses with one owned GET. Failed reads keep
a visible read-only retry; no lost win, repeated paid clue or stale-tab adoption in the
added tests. All 649 old pack records, 82 Alchimie / 100 Lanț profiles and 336 derived rows remain
exact. All 9,087 before/after observations and semantic costs are recorded: Brioșă→Pâine
becomes too cold while false Zacuscă affinities cool; eight old-native warm→lukewarm
boundaries preserve distances. No claim that every one of 6,941 changed observations improves.

Full gates: 1,409 backend tests on each Python 3.12.3/3.14.4, 53 accounts each, 193 native
frontend and 168 desktop/mobile browser checks; validators/pending/Ruff/docs/whitespace
and lint/typecheck/build/bundle GREEN, 118.90/120 KiB. Original 189/192 native and 196/197
compatibility runs are preserved; stale assertions were corrected with stronger exact
historical/owned-action checks. Both full backend matrices reran after one stale projection test correction; no relaxed threshold.

Evidence: `docs/reviews/v87-snack-and-action-quality/README.md`; current truth is STATUS.
Human/player/device acceptance and production rollout remain pending.

## V87 landing and V88 loop start (2026-09-08)

Valid until: the next version landing — then treat as history.

Verified V87 `fa8cffd4bc100eb867c992d346b4b93551a76bdd` against all 167 recorded
file/deletion bindings and 16 actual green gate receipts, then fast-forwarded local
main. Its final tests remain 1,409 backend per Python runtime, 53 accounts each,
193 native frontend and 168 browser checks. No runtime/content edits or test reruns
were required for this landing. A stale V87 summary-table phrase was corrected to
reflect its already recorded full integration result.

The owner authorized recurring local versions until stopped. ADR-0127 records the
work/verify/review/land/start-next protocol and unchanged publication boundaries.
The native recurring task was created and confirmed active. V88 begins on
`feat/v88-cross-game-quality`, initially investigating breadth beyond Contexto,
bread-family feedback, and concrete content-extension/reliability obstacles.
Its first implementation and full integration are pending. No push or deployment.

## V88 baseline checkpoint (2026-09-08)

Valid until: V88 implementation changes the bound baseline — then treat as history.

Created `feat/v88-cross-game-quality` from landing record `2878417`. Recorded nine
fresh actual-BFF first guesses and exact artifact/source hashes. Bread feedback,
Zacuscă negative controls, projection isolation and three Biscuit ingredient cues
match the V87 record. This is a started version, not a completed release candidate.
The initial scope includes cross-game content, Lanț action recovery and a possible
projection-bound Alchimie review-tool extension. No runtime/content edits or full
suite reruns in this checkpoint; documentation and whitespace checks pass.

## V88 completed candidate (2026-09-08)

Valid until: the final source/artifact bindings change — then treat as history.

V88 completes on `feat/v88-cross-game-quality` above baseline `2878417`. Seven new
concepts, 28 forms (25 grammatical + three qualified), 33 directed additions and one
removed false fermented-cream edge produce net 32 links. It promotes Cremșnit Alchimie
`al_gastronomie_107` and Conexiuni `cx_viata_de_roman_362/363`: 658 total, 650 approved,
488 eligible. No new Contexto/Lanț/derived rounds or lexical equivalents.

Lanț now recovers uncertain move/undo/hint responses and retained earned hints with one
owned read, without mutation replay. Alchimie portable reviews bind exact live sparse
projection evidence to distinct judges. Brioșă→Pâine gains one closed native hot cue;
Mătură/Taburet projections retire. Six cleaning nodes acquire real outgoing paths while
all 71 scorer mappings remain unchanged. Original cream/novelty/mechanical failures and
the root's rolled-back overlapping import are preserved, not counted as successes.

All 655 old pack records, 82 Alchimie books/profiles, 100 Lanț route profiles and 336 full
derived rows remain exact. All 206 previously shown shortest hops remain; one nonshortest
choice changes. The 11,233-observation impact records native-identity gains and semantic
costs, including weaker reverse pastry→Frișcă and household-context cues. Independent
supplemental review accepts these explicit limits for the local iteration.

Full gates: 1,508 backend tests on each Python 3.12.3/3.14.6, 53 accounts each, 193 native
frontend and 188 browser cases; validators/pending/Ruff/docs/whitespace and
lint/typecheck/build/bundle GREEN at 118.92/120 KiB. Initial full matrices had seven
historical/aggregate assertion failures, fixed without changing runtime/data/bounds.
A subsequent Python 3.12 runner exited 143 before completion; its partial log is retained
and excluded. The unchanged complete rerun passed. No push or deployment.

Complete evidence: `docs/reviews/v88-cross-game-quality/README.md`. The recurring local
loop remains active; human/device acceptance and production rollout are still separate.

## V88 landing and V89 start (2026-09-08)

Valid until: the next version landing — then treat as history.

V88 `000b0a25c25d48874e145fb3a8eebb1a38c791ba` was fast-forwarded into local main after
all 16 green integration gates and an independent final audit. The final manifest binds
297 present/deleted files, including the two final audit records and the earlier V88
kickoff commit. Full results are 1,508 backend tests per runtime, 53 accounts each,
193 native frontend and 188 browser cases. Initial failures and the interrupted run
remain separate, exact evidence. No push or deployment.

V89 starts `feat/v89-feedback-and-conexiuni-recovery`: reproduce Conexiuni lost paid
clue/group/terminal replies, review existing household Contexto targets, and assess the
remaining pastry/household feedback costs without restoring broad false affinities.
No V89 promotion or implementation is claimed by this start. The owner-authorized native
loop remains active until stopped. Clean up only the verified-merged V88 task artifacts.

## V89 baseline checkpoint (2026-09-08)

Valid until: V89 changes the bound baseline — then treat as history.

V89 starts above `b614bfe`, with eight source-bound household target profiles and seven
fresh private-BFF first guesses. A direct-neighbor screen narrows the first review set to
Făraș, Mop, Aspirator and Burete de vase; the other four remain held for missing-neighbor,
sense or cue issues. No V89 source/content edits or promotions yet. The kickoff prioritizes
Conexiuni response-loss recovery and bounded pastry/household feedback review. Docs and
whitespace checks pass; no full suite rerun for this documentation-only checkpoint.

## V89 implementation and directed review (2026-09-08)

Valid until: V89 lands — then treat this candidate record as history.

V89 implements owned Conexiuni action recovery, four bounded feedback scopes and one
new approved/selectable Mop round. All658 old pack records,83 Alchimie projections,
100 Lanț profiles/menus and336 derived boards remain exact. KG/mobile bytes and all
seeded starts remain exact. Pack659=651approved+8pending; Contexto236eligible.

The initial household screen used union adjacency rather than incoming neighbors.
Final dossiers show3/5/3 incoming cues; both judges reject Făraș352/Aspirator354 and
promote onlyMop353 under ADR-0071. Original raw evidence, corrections, three dossiers
and final portable gate remain preserved; no graph facts are invented to fill the gap.
Supported import/promotion and regeneration complete serially. Focused266 history/content
and15feedback checks pass. Final full integration passes1,531 backend tests on each
Python3.12.3/3.14.6,53 accounts each,193 native and214 desktop/mobile browser checks.
The first backend run passed1,530 and failed one historical V44 sink assertion that
included the new Mop target. Its original evidence is preserved; the narrow test-only
correction passes110 focused checks and both final full matrices. All16 final gates
are green and runtime/data remain exact. No V89 landing claimed by this candidate record.

## V89 landing and V90 start (2026-09-08)

Valid until: V90 completes — then treat this transition record as history.

V89 `143bfdb56dc3e8cd765fda30ca23fb6a0e30b55c` was fast-forwarded into local main after
16 green gates and independent content, recovery, feedback, historical-correction and
final integration audits. The final candidate manifest binds237 present/deleted files,
including the earlier committed kickoff, immutable audit input and final audit pair.
The407 input hashes remain exact after the sole historical-test correction; all runtime,
frontend and data bytes are the same as the reviewed/passing candidate. The original
1,530-pass/one-failure run remains archived. Candidate evidence refers to implementation
commit143bfdb; this landing record only updates living status documentation.

V90's task worktree exists on `feat/v90-household-discovery-and-critique-gates`. It starts
with ordinary household vocabulary, factual incoming discovery links, necessary C3
floor diagnostics and an all-six-game assessment. The held pending Contexto records
have8/13 incoming neighbors; no floor exception is needed, and their A5 holds remain.
Investigate any effect of approved warnings on ranking before implementing the check.
Alchimie lost-action behavior needs a real baseline reproduction before a recovery fix.
The local recurring loop remains ACTIVE. No push, deployment or external contact occurred.
Clean up only the verified-merged V89 branch/worktree/scratch after this record is merged.

## V90 baseline checkpoint (2026-09-08)

Valid until: V90 changes the bound baseline — then treat as history.

V90 starts above190d7fd with eight correctly directed household profiles,19 fresh
unknown-input lookups and10 private BFF first guesses. Only Mop is already an approved
Contexto target. The new source-bound kickoff separates necessary incoming counts from
union adjacency and quality approval. It scopes household meaning/discovery, a necessary
C3 diagnostic and actual Alchimie failure reproduction, with explicit all-six-game checks.
No V90 source/content change, new word, edge or promotion is claimed by this kickoff.

## V90 implemented candidate (2026-09-08)

Valid until: V90 lands — then treat this candidate record as history.

V90 adds3concepts/17links/10grammatical forms/0synonyms and promotes only Făraș355 and
Aspirator356. Pack661=653approved+8pending; Contexto238eligible. All659old pack records,
83Alchimie books,100Lanț route profiles,336derived rows and180CLI puzzles remain exact.
One nonshortest water menu changes Aluat→Burete; all206shown shortest hops remain.
The exact plate bridge opens7old kitchen nodes while the71proxy map stays unchanged.
Praf's native ownership retires its approximation; other464projection rows stay exact.

The C3 gate warns on4thin approved targets without score/eligibility changes. Alchimie
uses one ownedGET for uncertain actions and one bounded earned public cue. Independent
raw, final dossier, implementation, topology, UI and history/content reviews accept scope.
367focused tests include53new graph/migration cases. Full frontend193native/246browser
and Python3.12 1608backend/53accounts pass. One Python3.14 attempt ended143 incomplete;
its original evidence is preserved. The same command then passed separately with1608
backend/53accounts, completing all16 final gates. Only runner progress output changed.

Two complete16800-request captures compare selected feedback fields, not full HTTP bodies:
11120exact/5680changed, including2880newly accepted observations and240Praf identity
migrations. Costs and initial harness/locator/stale-rubric errors remain explicit. The
final receipt/manifest audit remains before local landing; no V90 merge is claimed yet.

## V90 landing and V91 start (2026-09-08)

Valid until: V91 completes — then treat this transition record as history.

V90 implementation0039b1e5c38d6b8bd4a59e99c600dea7da5ec440 and documentation cleanup
13a78fdd304e38c9b5e982784d94972b29977968 were fast-forwarded into local main after16green
gates, independent source/content/history/integration reviews and a narrow layout audit.
An early verifier Markdown draft had landed at repository root; its exact bytes were
moved into V90 evidence, preserving the distinct canonical final note and prior audit.
The final candidate manifest binds340 present/deleted files; all1635 frozen inputs and
both1608backend/53accounts matrices plus193native/246browser checks remain exact.
The first incomplete Python3.14 attempt remains excluded with its original logs/runner.

V91's worktree exists on `feat/v91-recovery-and-mobile-clarity`. The read-only scout
prioritizes remaining Intrusul/Perechi ownership failures for actual reproduction,
shared mobile HUD/resume-notice clarity and an existing-stock recognition/discovery
review. al_sport_083's easy seeds and three initially depleted entries are review
questions, not a preapproved revision. Four approved C3 warnings and17 unknown input
surfaces remain backlog; mined targets are distinct from curated approval.

The local loop remains active. No push, deployment, accounts rollout or external contact
occurred. Clean up only the verified-merged V90 branch/worktree/scratch after this record.
Candidate hashes refer to13a78fd; this transition changes living documentation only.

## Owner stopping point: complete V91 (2026-09-08)

Valid until: V91 lands or the owner changes the scope — then treat as history.

After V90 landed, the owner requested stopping the loop, then explicitly requested
landing V91 as well before stopping. Automatic recurrence is paused. Finish the existing
V91 worktree through independent review and green local merge; do not create V92.
ADR-0137 supersedes continuing-loop authority while retaining all landing/safety gates.
This is a direct bounded continuation, not permission to land unverified work.

## V91 bounded baseline checkpoint (2026-09-08)

Valid until: V91 changes the bound baseline — then treat as history.

V91 begins abovee2e0363 as the final authorized version. Fresh15-request BFF evidence
shows Intrusul/Perechi clues already surviveGET and repeated hints are rejected without
another charge. Browser uncertainty/ownership still needs reproduction. Existing Sport
record083 and four thin approved Contexto targets are review questions, not approved
changes. No V91 implementation is claimed; finish its green local landing, then stop.

## V91 verified candidate (2026-09-09)

Valid until: the verified candidate is locally landed — then treat as history.

Final version under ADR-0137: shared mobile titles/HUD/notices, owned Intrusul/Perechi
recovery with retry and animated departure protection, and one reviewed Sport083 seed
revision (ADR-0138–0140). Zero new concepts/links/forms/synonyms/rounds; all six seeds now
useful, four opening pairs/two ideas, six recipes/four routes/par 2. Graph/mobile and the
other 660 pack records/82 Alchimie books/336 derived boards remain exact. Ranking changes
and unresolved salience/label/household questions are explicit in STATUS and the review.

All 16 local gates pass: 1652 backend+53 accounts on Python 3.12 and 3.14; 193 frontend native
and 342 real-browser cases (two workers,zero retries); validators,lint,type/build/budget,
Ruff,docs and whitespace. Bundle 119.08/120KiB. Independent migration/history 85, recovery 80,
mobile 14 and corrected Alchimie 34 focused checks pass. The initial interrupted backend red
run (1265 pass/two stale expectations) and completed browser red run (338 pass/two old hint
setups) are retained. Exact historical snapshots and all three clue kinds stay covered.
Serving code/data/assets remain unchanged through these test-only amendments.

Evidence is under docs/reviews/v91-recovery-and-mobile-clarity/. Land locally, clean only
this verified worktree/branch/scratch, keep recurrence paused and do not start V92. No push,
deployment, accounts rollout or human/device acceptance is claimed.
