# Anonymous beta candidate

Valid until: the next verified quality wave — then refresh this living checklist.

Target: public anonymous beta for Romanian players. **V84 adds guidance to all six games,
earned Alchimie explanations, 15 concepts, 57 links and four reviewed playable rounds.**
One false graph link is removed. V84 is verified and merged into local main; V85 begins
with another reviewed quality/content batch. Public rollout still requires the external checks below.
Current facts and exact pins: [STATUS](STATUS.md).

## Version objectives

[ADR-0113](adr/0113-outcome-based-version-batches.md) governs the owner's expanded objectives:
continue improving existing games and connections while delivering coherent batches of new
playable content. Each version records its player problem, baseline, intended gains and
acceptance evidence. Its final report separates new concepts, connections, grammatical forms,
reviewed synonyms, rounds by game, promotions and runtime eligibility, alongside visible fixes
and remaining release blockers. File churn is not a content metric.

V82 delivers eight independently reviewed rounds: Cozonac, Pască, Muștar, Mujdei, Ciorbă de
burtă, Urdă, Friptură and Bulz. Contexto eligibility grows **204→212**. The same batch repairs
Burtă feedback for the soup target and adds reusable content-delta reporting and compact
runtime probes. Alchimie cold generation reuses pair results in a bounded local memo
([ADR-0115](adr/0115-reuse-alchimie-pair-results-within-a-build.md)); all 82 curated projections
and twelve sampled mined sessions stay exact, with 88.89% fewer graph queries in that sample.
It adds no KG concepts, connections, aliases or synonyms. Full integration checks passed.

V83 follows the same batch objective: five further food targets become selectable
(212→217), six core ingredient/filling guesses are repaired, and 24 grammatical forms
work across the typed APIs. [ADR-0116](adr/0116-share-current-content-test-expectations.md)
consolidates current test expectations while keeping historical evidence independent;
[ADR-0117](adr/0117-food-forms-and-exact-target-feedback.md) records the content decision.
V83's final verification and retry evidence are recorded below and in its review archive.

V84 adds specific dough, grain, whey, brining and cooking-equipment vocabulary under
[ADR-0118](adr/0118-reviewed-culinary-graph-corrections.md). Contexto gains Plăcintă cu mere,
Salam de biscuiți and generic Pâine (217→220 selectable); Lanț gains Făină→Cornulețe
(94→95). Forty-two forms retain exact sense boundaries; only one is explicitly counted as
a reviewed lexical equivalent. Drojdie's generic-food projection is retired, cooling six
false-hot meat/cheese targets. [ADR-0119](adr/0119-in-round-help-and-earned-link-explanations.md)
keeps rules available in each live game and shows only earned, oriented Alchimie relations.

## Sequence and acceptance

| Wave | Problem addressed | Evidence / outcome |
|---|---|---|
| V73 | Duplicated lifecycle plumbing made shared fixes prone to drift | Narrow backend transaction and frontend resume extractions; 922 backend, 53 accounts, 163 native and 48 real-BFF browser checks passed before intentional behavior changes |
| V74 | Temporary resume errors could discard recoverable games; stale responses and terminal actions could corrupt state | All six retain recoverable IDs, show retry, recover terminal results and keep retry after failed fresh creates; Contexto giveup and Lanț undo preserve terminal state |
| V74 | Scrolling status lacked keyboard access and rendered evidence | Focusable HUD/Lanț history; all six intro/live/result states audited for WCAG A/AA rules, viewport overflow, and complete desktop keyboard play; Perechi focus checked after tile removal |
| V74 | Two tabs could record the same terminal result twice; queued scores could lose their resume pointer | Whole-board Web Lock plus one atomic score/receipt payload; bounded private receipts, storage-failure/concurrency cases, and all-six held-lock options/reload/close recovery |
| V74 | Dependency and runtime risks lacked current evidence | Clean Node24 install/audit reports zero findings; initial transfer 118.73/120 KiB; cold/warm route and bounded RSS measurements archived with limits |
| V75 | Alias growth did not add playable stock | Reusable pack-only import and independent-review serializer; five candidates screened, three dropped, two promoted; Contexto eligibility 201→203 with exact preservation/selection evidence |
| V76 | Accented holiday spellings could play pasta or falsely win | `Paște`/`Paștele` are unresolved without attempts/moves/suggestions; valid food/compound inputs and 13,177 authored surface mappings remain intact; zero content/artifact changes |
| V77 | Ordinary flour guesses were distant from familiar dishes; the graph builder reused retired edge IDs | Two reviewed ingredient links accepted, bread deferred after a misleading Stilou route; allocator advances beyond present IDs; all pack/ranking/frozen-board/puzzle records preserved |
| V78 | Repaired flour alone did not establish dessert-target fairness | 68 fresh API probes and independent reviews defer both candidates: Nucă remains cold for Cozonac; Gem is frozen for Clătite while Dulceață is hot; no served-content changes |
| V79 | Gem inherited misleading honey feedback; a global preserve anchor polluted savory rounds | Reviewed direct associations at strength ≥0.60 repair Papanași and fixed Clătite feedback; other 206 approved target responses and content artifacts remain exact; projection privacy is preserved |
| V80 | Repaired Clătite needed a fresh promotion review | Unanimous dossier-bound approval adds one easy target; all 620 old records and 336 frozen boards exact; known cold/unknown inputs remain documented |
| V81 | Nucă borrowed honey feedback; naive topology spread false warmth | One real word, sole unambiguous alias and four recipe edges; native Contexto feedback is limited to reviewed direct associations; all game records, puzzles and frozen boards preserved |
| V82 | Tiny content increments left repaired associations without enough new playable rounds; cold generation repeated millions of graph queries | Eight food targets independently reviewed, promoted and selectable; defining Burtă feedback repaired within the batch; bounded Alchimie pair reuse preserves exact games; reusable delta reporting and compact probes added. Full integration gate GREEN |
| V83 | Ordinary forms and central ingredient guesses blocked a fresh food batch; repeated current pins slowed extension | Five targets promoted, six exact-target feedback pairs repaired and 24 forms accepted; old surface owners/records/frozen boards exact; current expectations centralized. Backend/accounts/frontend/browser validation complete, with one documented timing retry |
| V84 | Missing everyday concepts, false generic-food feedback and invisible combination explanations limited realistic play | Fifteen concepts, 57 links, one false edge removed, 42 forms, three Contexto rounds and one Lanț route; in-round help across all six games and earned Alchimie explanations. All old playable recipe books/routes/frozen boards preserved; full integration GREEN |

V84 focused checks pass: **62 new graph/game checks**, **183 historical/current checks**,
independent implementation review and 3,757 before/after observations per checkout. All
four new public journeys work. Final full gates pass: 1,207 backend tests on each of
Python 3.12.3/3.14.6, 53 accounts tests each, 177 native frontend tests and 122 browser checks.
Five stale historical assertions were repaired before the fresh complete green runs;
original evidence and unchanged limits remain covered in the verification record.
The frontend build passes at **118.87/120 KiB**. See the
[V84 review](reviews/v84-six-game-graph-quality/README.md) for complete quantities and limits.

V83: **1,115 backend tests passed on Python 3.12.3**. Python 3.14.6's full run passed 1,114;
the sole failure was the known load-sensitive Alchimie timing case (50.30s against 45s),
which passed unchanged on retry at 21.96s. **53 accounts tests passed on each runtime**.
**173 native frontend tests and 108 browser checks passed**, along with lint/typecheck,
build, bundle, validators, pending gate, Ruff, docs and whitespace checks. The browser
reload harness now selects the new document's state request after an observed stale-response
race; the full rerun passed and rebuilt application assets are byte-identical. Initial
failures and actual commands remain in the [verification receipt](reviews/v83-food-input-and-feedback/verification.json).

Historical V82 final gates: **1,057 backend tests on each of Python 3.12.3 and 3.14.6**, **53 account
tests on each**, **173 native frontend tests** and **108 desktop/mobile browser checks**
passed. Both validators, strict pending gate, lint/typecheck, retained bundle budget, docs
and whitespace checks passed. Independent content/implementation review and complete
82-projection/12-session Alchimie equivalence checks passed. Exact results and resolved
intermediate failures are in the V82 verification receipt.

Historical V81 full gates passed: 1,024 backend tests and 53 accounts tests on each of
Python 3.12.3 and 3.14.6; 173 native frontend tests; 108 desktop/mobile browser checks.
Clean install/audit, frontend lint/typecheck, both content validators, Ruff, docs and
whitespace passed. The npm audit reported zero vulnerabilities; retained V75 frontend
assets met the 118.73/120 KiB budget. Independent factual, impact, implementation and
documentation reviews found no remaining actionable issues. Accounts were enabled only
for their isolated tests. Exact results and disclosed rank-boundary effects remain in
the V81 review archive.
Decisions and full evidence: [ADR index](adr/README.md), [V75 review](reviews/v75-contexto-food/README.md),
[V77 review](reviews/v77-flour-associations/README.md), [V78 review](reviews/v78-dessert-targets/README.md),
[V79 review](reviews/v79-gem-feedback/README.md), [V80 review](reviews/v80-clatite-target/README.md), [V81 review](reviews/v81-nuca-feedback/README.md),
[V82 review](reviews/v82-playable-content-batch/README.md),
[V83 review](reviews/v83-food-input-and-feedback/README.md),
[runtime measurements](reviews/v74-runtime-measurements/README.md). Refactors preserve
server authority, hidden answers, session bounds, intentional game differences and scoring.
The derived catalog remains frozen at 336 boards. Content critiques are independently
authored Codex-agent judgments with source checks; they are not Romanian-player sessions
or human subject-expert approval.

## Quality coverage and limits

| Area | Evidence and remaining uncertainty |
|---|---|
| Rules, hints and progression | All six seeded rounds reach server-scored results; replay, progressed reload, mistake counters, failed action/start recovery and expiration have real-BFF coverage. Automated solves do not establish intuitiveness or enjoyment. |
| Romanian content and difficulty | V84 adds 15 real concepts, 57 specific links and four reviewed rounds; 42 forms preserve deliberate sense exclusions. Drojdie's old meat/cheese false-hot cases cool, and defining apple/biscuit/whey/brine associations work. Cinnamon/bread and oven/biscuit-dessert rankings remain noisy; human fairness/enjoyment is unmeasured. |
| Onboarding and presentation | Shared intros, categories, HUD, action feedback and results were inspected; mobile layout and rendered states are audited. No broad redesign was justified by this evidence. Real-device rendering and human comprehension are still pending. |
| Keyboard and accessibility | Desktop essential controls support Tab/Space/Enter completion; Perechi focus is checked after pairs disappear and at result. Automated Axe checks run on settled intro/live/result states. Text-entry tests use programmatic fill after keyboard focus; no actual screen-reader usability study ran. |
| Reliability and storage | Retry, stale ID handling, unmount/loading ownership, immutable terminal actions and duplicate completion are covered. Strict concurrent-tab local-score protection requires Web Locks; fallback is best effort. Receipt TTL is 24h with 1,000 IDs per game; a deliberately retained terminal session can record again after expiry. |
| Maintainability and extension | Shared lifecycle code stays narrow, mechanics explicit. Pack-only imports reject topology, V2 artifacts bind two independent complete reviews, and generated fixtures remain tool-owned. Portable review assembly supports Conexiuni/Contexto/Lanț; Alchimie retains its separate projection-bound workflow. V82 adds reusable delta reporting and compact probes so later batches can measure actual playable gains without large duplicated response archives. |
| Performance and dependencies | Measured offline routing/serialization/game cost and bounded process RSS; no production load/SLO claim. Alchimie generation variance and worst-case Contexto history capacity remain measurement follow-ups. |
| Release operations | Local tests force offline anonymous mode. Last documented production is V72; no push, deployment, accounts enablement, contact with players or production re-verification occurred. |

## Release gates still requiring external evidence or an owner decision

- Run the Romanian-player protocol below; observe comprehension, fairness and replay interest.
- Test real Android/iOS devices and the intended browser set; Chromium emulation is partial evidence.
- Select and verify a usable public feedback email or URL; the owner question remains unanswered.
- Reverify the configured `CAT_LEGAL_OPERATOR` and `CAT_LEGAL_CONTACT_EMAIL` and public legal pages
  against DEPLOY; a feedback URL alone does not satisfy those rollout requirements.
- Authorize a release, preserve the deployed image, execute the [deployment and rollback procedure](DEPLOY.md),
  and re-run public health/config/content/asset smokes. Keep production anonymous.

Player observations should guide the next product iteration. V84 addresses the broad
Drojdie approximation and the grain, biscuit/apple, whey and qualified oven vocabulary.
Follow-ups include remaining generic spice/cocoa projections, false-hot holiday routes,
butter/preparation feedback and old derived-board wording that treats Urdă as inherently salty. The
[V82 dispositions](reviews/v82-playable-content-batch/shortlist/dispositions.json) retain
other investigated candidates. Repairs and fresh playable reviews belong together where
feasible; these are investigation candidates, not approved promotions. Generic Pâine now
passes review; the earlier direct Făină→Pâine de casă edge remains deferred. Accounts,
derived-catalog expansion and another game retain their separate gates.

## Romanian-player playtest protocol — not yet run

Recruitment/contact requires owner authorization. Suggested first round: eight Romanian
speakers with varied word-game experience and device familiarity, using anonymous test
codes. Start with adults; the accounts/minor-data scope stays outside this playtest.
Use a local observation sheet without names, recordings or contact details.

Allocate about 45 minutes per participant. Rotate game order so the same games are not
always tested last. Use the default starter/easy path, then one ordinary replay. Ask the
player to read the intro and explain the goal before the observer helps. Observe first
action, first mistake, hint/recovery, ending, replay and one reload. Record elapsed time,
where help was needed, the exact confusing word/association, and whether feedback resolved it.

| Game | Specific observation |
|---|---|
| Alchimie | Can the player find a productive opening, understand useful/all inventory and explain a recipe? Can hints/history get them moving again? |
| Conexiuni | Does the player see one defensible partition? Do predicates and end explanations resolve plausible alternatives? |
| Cald sau Rece | Are ordinary guesses recognized? Does a recognizable warm opener lead to a useful direction instead of arbitrary heat changes? |
| Lanțul Cuvintelor | Can the player explain the direction of a link and use rejection feedback/hints to find a credible route? |
| Intrusul | Is the exclusion convincing once explained, including any plausible alternate intruder? |
| Perechi | Are pair relations defensible and can keyboard users predict where focus moves after a solved pair disappears? |

Proposed acceptance for the first round: at least six of eight players explain each game's
objective and make its first legal move within 60 seconds without coaching; no reproducible
lost progress or inaccessible essential control; investigate any confusion shared by three
players. Ask for 1–5 fairness and replay-interest ratings with one concrete reason. Ratings
guide the next wave; automated agents cannot supply them or establish enjoyment.

Human acceptance and real-device/browser coverage remain **pending** until observed. A green
technical candidate is not permission to publish and is not evidence that public beta
acceptance has passed.
