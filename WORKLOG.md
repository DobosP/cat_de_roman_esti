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

## V91 local landing and loop stop (2026-09-09)

Valid until: a separately authorized version supersedes this landing — then treat as history.

V91 implementation/evidence `48cd5b81fa42b485c29fd22c39cb9f55be2224ce` is merged into local main following V90.
The independent closure audit accepted all480 original ledger bindings,2091 frozen
inputs and16 green gates. The final ledger adds only its three closure artifacts,
retaining all480 prior bindings unchanged (483 total, excluding the ledger itself).
A preserved unified diff was losslessly wrapped in gzip so its meaningful context
spaces do not fail the staged whitespace gate; its original decoded hash remains exact.
These landing notes change documentation only. The native heartbeat remains PAUSED;
no V92, push or deployment was started. Only this verified-merged task's branch,
worktree and scratch qualify for the required same-session cleanup.

## V91 verification archive (moved 2026-09-13)

Valid until: V92 integration — then treat as history.

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

## V92 main landing (2026-09-15)

Valid until: a later main landing changes these inputs — then treat as history.

The owner requested landing all completed work. Main fast-forwards from `6208eae`
through ten V92 implementation commits to `d52f4b4`, covering the Alchimie GUI/content
rebuild and two subsequent all-game entry/interface sessions. V92 adds 92 reviewed
rounds/targets across the other five games and a persistent Alchimie world with
225 concepts, 294 recipes, 121 craftable discoveries and 32 optional goals.

Python 3.12 and fresh constrained 3.14 each pass 1968 backend/53 account tests;
212 native frontend and 480 browser checks pass. Both validators, Ruff, frontend
lint/typecheck/build and the 119.22/120 KiB bundle gate are green. Independent audit
checks 400 current/archive bindings with zero mismatches. The exact Perechi privacy
log and 22 earlier verification-bound logs are preserved at their exact hashes before
scratch cleanup, and the broken status review link is fixed.
The closure changes documentation/evidence only. See
[main landing evidence](docs/reviews/v92-main-landing/README.md).

The authorized landing publishes main and cleans only the three verified V92 task
branches/worktrees/scratch directories after remote/ancestry checks. The existing
previews on ports 8150 and 8160 now run from main; route/asset smoke checks pass. Production remains anonymous V91; no deployment or
automatic fourth creation session is included. Remote CI follows the main push and
is not represented as already complete in this pre-push evidence receipt.

## V93 words and game quality (2026-09-15)

Valid until: the bound V93 inputs or integrated verification change — then treat as history.

The owner requested a fresh content/quality session after the green V92 main landing.
V93 starts from bf9d814 in feat/v93-words-and-game-quality and adds thirteen reviewed
rounds/targets across the other five games, plus ten new Alchimie words and 21 recipes.
The world reaches 235 concepts/315 recipes/131 discoveries with nine more results offering
alternate recipes, four formerly terminal discoveries gaining onward use, and all five
prior saved-book generations preserved. All 696 old pack records, 336 core quick boards and
57 prior authored quick payloads/scores remain exact. Shared KG vocabulary is unchanged.

The growing earned-recipe journal gains local result/ingredient search, visible reset,
keyboard recovery, a two-line closed query preview and 44px source controls. Selection,
saved progress and answer privacy remain intact. Cald sau Rece's hard-mode wording now
describes harder associations. Independent mobile/browser review accepted the final UI.

Five pack entries pass raw review, actual pending dossiers and separate analyst/verifier
promotion. All naturally serve through public seed/category/difficulty selection. Both
catalogs rebuild from their complete independent reviews and pass exact final live-audit
acceptances; 65 quick winning journeys plus eight added wrong/repeat/hint/GET journeys
pass. The questioned Maiorescu leadership relationship is supported by the journal's
own history; it is distinguished from a formal sole-editor title. Recipe references and
an already-cooked-noodle explanation were corrected before final approval.

The first full runs exposed current snapshots affected by catalog growth: both Python
versions passed 2016 tests with one outdated Contexto profile hash; browser passed 484 with
two Lanț initial-snapshot assertions. Exactly 257 old target profiles retain their original
hash; the two new targets account for the added profile rows. Only Lanț's current seed 38
snapshot changes among the six games, and its original fixture is archived. The focused
profile and ten Lanț lifecycle checks pass after test-only corrections. Final full-run
results are recorded in STATUS and the integration receipt, separately from these first runs.

The exact five-core-artifact inverse restores bf9d814 before every earlier historical
check. Original V92 world 225/294/121 assertions reconstruct the exact original catalog.
The review archive preserves candidates, exclusions, reviewer identities, source references,
GUI captures, original logs and encoded/decoded file hashes. See
[the V93 review](docs/reviews/v93-words-and-game-quality/README.md) and
[ADR-0151](docs/adr/0151-expand-game-vocabulary-and-search-earned-recipes.md).
Production remains anonymous V91; no main merge, push, deployment or automatic next session
is included. V93 preview uses 8150; main comparison uses 8160.

V93 final integration: Python 3.12 and 3.14 each pass 2017 backend/53 account tests;
486 browser and 212 native frontend checks pass. Validators, Ruff, frontend lint/build,
docs and whitespace are green; initial bundle 119.22/120 KiB. Final inputs, original
failed runs, corrected snapshots and full successful logs are bound by the V93 receipt.

## V93 main landing and V94 authorization (2026-09-15)

Valid until: later main integration changes these inputs — then treat as history.

The owner requested “land v93 start v94”. V93 implementation ba28be6 is fast-forwarded
from bf9d814 into local main. All 168 archived files, 43 changed gate inputs, nine
current artifacts and six final logs match the completed green integration receipt.
Landing notes change documentation only. The authorized main push is followed by
remote verification, relocation of the port 8150 preview and cleanup limited to the
verified V93 branch/worktree/scratch. Main then supplies the new V94 task baseline.
The original V93 integration receipt retains its pre-landing scope as historical fact.
Production remains anonymous V91; no deployment is included.

V93 landing audit checks 291 SHA bindings and all 168 archived scratch sources with zero
mismatches or missing reviewed keepers. Final build log rounds initial gzip to119.23KiB,
correcting the earlier119.22 figure in current STATUS/landing evidence; the original
sealed integration receipt is retained. The120KiB budget remains green.

## V94 words and clearer connections (2026-09-15)

Valid until: the bound V94 inputs or verification change — then treat as history.

The owner requested V93 landing and V94 continuation. V93 is published on main at
c971846 with GitHub CI 35011658720 green and its verified task worktree/branch/scratch
cleaned. V94 starts from that commit in its own task worktree.

V94 accepts twelve new rounds/targets across five games plus seven Alchimie words and
seventeen recipes. Conexiuni gains one household/wordplay board; Cald sau Rece adds
Ciorbă de perișoare and Temă pentru acasă; Lanț adds a food bridge via rice or meat;
Intrusul/Perechi gain four boards each. Alchimie reaches 242 concepts/332 recipes and 138
craftable discoveries, with six prior saved books supported. All old content records
and authored scores remain exact; shared KG vocabulary stays unchanged.

Twenty-one independently reviewed captions explain relationships in both directions.
Earned Lanț paths now wrap at 320px/200% text, preserving keyboard focus and actions.
A separate reviewer verified the implementation author's scoped browser evidence.
The proposed Sfinx→Crucea Caraiman level was rejected after actual GET/JSX verification
showed its inaccurate target description was public. The rejected ID 242 is reserved
and appended to the durable ledger; original 104 records and historical assertions stay
exact. Correct geographic edge captions are independently accepted and do not approve
that rejected round. Initial faulty assumptions and corrections remain in the archive.

Both Python versions pass 2133 backend/53 account tests. The initial full browser run
passed 506 and failed two old focus expectations: Pesto now has an onward recipe and
correctly retains focus. The test now checks Pesto continuation and a separate deeper
Lipie+Friptură→Șaorma terminal case to preserve collection-fallback coverage. All six
focused keyboard cases pass; only test expectations changed, with no runtime/data edit.
Final browser/full verification is recorded separately in STATUS and the integration receipt.

Evidence: docs/reviews/v94-words-and-clearer-connections/ and ADR-0152. V94 publication,
production deployment and another automatic version are outside this session.

V94 final integration is green: 2133 backend/53 accounts on each Python version,
510 browser and 212 native frontend checks, all validators/lint/build/docs/whitespace
gates. Initial bundle 119.23/120 KiB. Exact 69 input files,227 archived evidence records,
final 10 artifact pins and 12 final-evidence pins are bound by verification.json. The
preview now serves V94 on 8150 and landed V93 on 8160. No V94 publication or deployment.

## V94 main landing and V95 authorization (2026-09-15)

Valid until: a later main landing changes these inputs — then treat as history.

The owner requested landing V94 and starting V95. Main fast-forwards from c971846
through implementation b75d68e. All 227 archived files, 69 gate inputs, ten artifact
pins, twelve final-evidence pins and six final logs match the completed green receipt.
The final post-amendment frontend lint log is also preserved. Landing documentation
changes no runtime inputs. After the authorized push and remote proof, only the
verified V94 branch/worktree/scratch are cleaned; the preview moves off its worktree.
V95 starts in a new task worktree. Production remains anonymous V91.

## V95 discovery and game quality (2026-09-16)

Valid until: later content or runtime changes these bindings — then treat as history.

V94 landed at cf6b28b and GitHub CI 35018580589 passed. Its verified worktree and scratch
were cleaned. V95 starts from that main commit and adds thirteen reviewed rounds/targets,
five world-local Alchimie concepts and ten recipes. All 705 previous pack records,
242 world concepts, 332 recipes, 73 authored quick payloads/scores and 336 core boards
remain exact. Shared KG/mobile data, 105 rejection tombstones and 101 custom captions stay
unchanged. Seven historical Alchimie save generations preserve earned entries.

Alchimie now marks tried empty pairs and immediately acknowledges recent retries.
Memory holds at most 128 unordered confirmed failures per session. It stays out of saves,
clears on book upgrades/restoration, and local acknowledgments expire after 30 seconds.
Review first caught an indefinite-cache risk, then a stale deferred focus reference after
two identical retries followed by a lost response. Synchronous keyboard centering fixes
the latter without storing a deferred reference. The four new regression cases cover both
committed and uncommitted lost responses on desktop and mobile. The pre-existing lost-
response path can leave focus on the page body; the new backward jump is removed.

Final natural selection found both new Lanț rounds were hidden from anonymous players by
the strict wider-beginner preference. Casual selection now retains one in four initially
picked eligible narrow boards, otherwise applying the existing wider preference. Daily
selection and strict two-route approval remain unchanged. Independent sampling reaches
both additions, retains 982/1024 wider picks and preserves 56 daily comparisons. All five
new pack records and four Lanț routes complete through public BFF selection/actions.

Independent quick review wins all 81 authored boards and verifies all eight new recovery
journeys. Seven additions qualify as starters; the tableware board stays nonstarter.
Clește retains unknown generic tool-word debt despite useful hot alternative openers.
The new Lanț captions remain mostly generic; private edge text is not claimed displayed.

Both Python versions pass 2191 backend/53 account tests. Final frontend and browser
results, exact input hashes, preserved initial failures and review amendments belong in
[the V95 receipt](docs/reviews/v95-discovery-and-game-quality/verification.json).
Preview 8150 runs V95 and 8160 retains landed V94. The owner subsequently authorized
landing V95 and starting V96; production deployment remains outside that authorization.


## V95 main landing and V96 authorization (2026-09-16)

Valid until: a later main landing changes these inputs — then treat as history.

The owner requested landing V95 and starting the next version. Main fast-forwards from
cf6b28b to implementation 085e792. The final receipt verifies 253 archived records, 46
changed inputs, 15 removed assets, ten installed-artifact pins and twelve final-evidence
pins. All 528 browser checks pass on the final build; Python 3.12/3.14 each pass 2191
backend/53 accounts, and 212 native checks pass. The frontend-only focus correction is
independently bound without changing Python/data approvals. The landing record precedes
the authorized main push. After remote proof, previews move off the task worktree and
only verified-landed V95 work is cleaned. V96 starts separately; production stays V91.


## V96 creation and critique kickoff (2026-09-16)

Valid until: draft content or baseline bindings change — then repeat affected checks.

After V95 was pushed to main 1457786, its verified task worktree, branch and scratch
were removed and both preview origins were moved onto main. V96 starts separately in
feat/v96-words-and-input-clarity. Its initial unapproved queue covers all six games:
three pack proposals, two quick boards and two Alchimie concepts/five recipe ideas.
Author probes record sources, full novelty and conditional playability, including the
actual Lanț corridor preference. Chiftele marinate was excluded as an existing alias;
the vegetable-patty sandwich generalization remains an explicit review question.

A fresh all-game interface critique examines unknown-input feedback, recovery focus
and earned relationship clarity. No serving, generator, fixture or test files change
in this kickoff. The exact landed inventory remains the playable baseline; independent
reviews and installation gates still precede any new served entry. Evidence lives in
docs/reviews/v96-words-and-input-clarity/; current CI status belongs in STATUS.

V95 GitHub CI 35026423470 completed successfully on main 1457786: both Python jobs
and the full frontend/browser job pass. V96 kickoff archives 71 author/critique artifacts,
with all ten served artifact hashes unchanged; docs and whitespace checks pass.

## V96 content and input/focus integration (2026-09-17)

Valid until: bound content/runtime/GUI changes — then repeat affected checks.

The owner requested landing V96 and starting V97. The prior V96 commit contained only
unapproved drafts and critique, so this session completes the actual content and GUI
outcomes before landing. Three pack entries, two quick boards and two Alchimie concepts/
five recipes pass the independent gates. All 710 old pack records, 81 authored quick
payloads/scores, 247 world concepts and 342 recipes remain exact; eight historical books
retain earned progress. Shared KG, rejection ledger and 101 custom captions are unchanged.

Unknown-word feedback now explains that no attempt was spent and offers conservative
advisory spelling variants. The first similarity-only filter removed Nuci/Prafzz advice;
the refined spelling checks restore those useful cases without leaking hidden targets.
All 174 targeted input/feedback cases pass. Alchimie reconciled response loss now restores
usable-word/collection focus while respecting focus moved elsewhere and save ownership.
The initial browser locator matched both visible and hidden feedback; it was scoped to
the visible card. Independent final review passes 60 backend and 12 browser cases.

The sandwich source discrepancy is preserved and resolved against a directly inspected
original recipe; no vegan claim is made. Generic Lanț captions remain a future queue.
All eight historical-book slots are now occupied: V97 must address compatibility before
adding recipes. Final assembled counts, checks and publication proof belong in STATUS
and docs/reviews/v96-words-and-input-clarity/integration/verification.json.


## V96 main landing and V97 authorization (2026-09-17)

Valid until: a later landing changes these inputs — then treat as history.

The owner requested landing V96 and starting V97. Main fast-forwards from 1457786 through
kickoff 15e7561 and completed implementation 57d5bcc. The final integration receipt verifies
183 archived records, 43 changed inputs, 14 removed assets, ten installed-artifact pins and
twelve final-evidence pins. All local gates pass: 2236 backend/53 accounts on each Python,
540 browser, 212 native, validators, lint, build, bundle119.23/120 KiB, docs and whitespace.
The landing record precedes the authorized push. After remote proof, both previews move
off the task worktree before verified V96 cleanup. V97 starts separately, with a required
saved-book compatibility design before further recipe expansion. Production stays V91.


## V97 compatibility, content and caption kickoff (2026-09-17)

Valid until: baseline or proposal bytes change — then repeat affected checks.

V96 was pushed on main 36db143 after all local gates passed; its verified branch/worktree
and scratch were cleaned after both previews moved to main. V97 starts separately in
feat/v97-discovery-continuity-and-new-words. It records three curated round drafts,
two quick-board drafts, two Alchimie concepts/four recipes and twelve earned-caption
proposals. All remain unapproved and no serving files or limits change.

The compatibility design measures the existing eight-book registry and recommends
reviewing a bounded 16-book registry plus generator byte guard, retaining 2 MiB. Its isolated
prototype round-trips nine rule sets, checks 1,009 earned prefixes and rejects 315 newer-recipe
forgeries. A reference encoding is smaller but needs a format migration. Projections are
not a guarantee that arbitrary larger future books fit. Alchimie installation remains
contingent on compatibility work and independent review.

Author review revised a facial-part count claim and a potentially ambiguous quick pair;
original quick evidence is preserved. Cacao→Lapte's Chec bridge means serving together,
not a claimed ingredient. Twelve caption drafts retain exact edge/direction snapshots;
ten unsupported reverse traversals are withheld. The kickoff archive contains 65 bound
files. All ten landed serving-artifact pins remain exact; docs/whitespace checks apply,
with no unnecessary application-suite rerun for this authoring-only change.


## V96 CI interception correction (2026-09-17)

Valid until: bound test or browser interception behavior changes — then repeat checks.

GitHub 35155920107 passed both backend jobs and 539/540 browser cases. Local repetition
reproduced the final mobile case twice. The trace proves POST 200 commit followed by a
pending GET during one-shot route removal. A persistent handler with a manual first-call
abort avoids the teardown race, retaining the original keyboard/result/focus assertions
and adding exactly-one-mutation/read checks. No product/data/assets/dependencies changed;
no timeout increase, retry or sleep was added. Independent review passes 30 consecutive
mobile repeats and all 12 V96 cases. Native 212/lint/build pass, bundle 119.23 KiB. The receipt
binds the sole changed test and all 42 unchanged previous inputs; original integration
proof remains historical. Fresh CI follows this authorized V96 landing correction.

V96 correction main fd3ca7c passed GitHub CI 35158602720, including the complete browser
job and both backend jobs. Additional inherited-code confidence testing passed 120 cases
without changes. V97 retains 65 frozen proposal files and all ten unchanged application/
data pins; proposals remain unapproved and the existing eight-book runtime bound remains.

## V97 Linux resumption (2026-09-22)

Valid until: candidate inputs change — then repeat affected verification.

The owner requested testing and continuing version work from the latest documentation
and Windows handoff. Local and remote main match fd3ca7c. The existing V97 worktree at
442dd7c contains uncommitted, reviewed content and an unfinished release verification.
Its 65 kickoff and 139 lane archive records, 27 initial gate hashes and inherited content
remain exact. No arcade-specific new Windows skill was located; its name/path remains
an explicit clarification, and no unsourced skill instructions are claimed adopted.

The inherited browser run had 485 passes and 67 failures. The browser still accepted
only eight historical recipe hashes while V97 served nine under a reviewed limit of
sixteen. Matching that bound fixes fresh collection updates without changing the
64 KiB save or 256 craft caps. Native checks cover nine/sixteen histories, the actual
bundled catalog and rejection of seventeen. All 84 affected Alchimie journeys pass.

A separate Lanț mobile failure occurs when the temporary outer notice row shrinks by
56 px and moves a partly clipped persistent replay error entirely above the viewport.
A one-time layout scroll reveals the full paragraph without moving focus. All 26
shared start/replay journeys pass, and real-clock geometry confirms both error and retry
remain visible. An initial stronger focus assertion raced the pending disabled render;
the corrected test waits for that actual state before measuring focus. Original errors,
logs and before/after evidence are preserved in the V97 resumption review.

Independent review accepts the two fixes and verifies final source/static bindings.
The complete assembled matrices pass: 2329 backend/53 accounts on each Python, 214 native
frontend and 552 real-browser cases (two workers, zero retries). All validators, lint, build,
docs and whitespace checks pass at 119.23/120 KiB. The exact integration receipt binds 522
inputs and retains the earlier failures. This pickup does not merge, push, deploy or restart
the loop; V97 remains a verified task-branch candidate.

## V97 local landing and V98 authorization (2026-09-23)

Valid until: a later version changes the baseline — then treat as history.

The owner confirmed landing V97 into local main and starting V98. Main fast-forwarded
from fd3ca7c to verified implementation/evidence f783a97. All522 tested inputs and16
archived green gate receipts were rechecked exactly before the merge. The complete
2329 backend/53 account tests per Python,214 native and552 browser checks remain valid;
no source, data or test changed. These landing notes are documentation only.

V98 starts separately from this landing around the documented missing door-neighborhood
vocabulary, clearer Cacao→Lapte associations and onward uses for the terminal Alchimie
dishes. It must preserve old saves, game bounds and independent content review. The
specific Windows skill is still unidentified; current repository workflow applies.
No remote push, deployment or recurring loop is authorized by this local transition.
Cleanup is limited to this verified-merged V97 worktree, branch and matching scratch.
