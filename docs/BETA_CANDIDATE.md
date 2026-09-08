# Anonymous beta candidate

Valid until: the next verified quality wave — then refresh this living checklist.

Target: public anonymous beta for Romanian players. **V89 implements recoverable
Conexiuni actions, one reviewed Mop round and four exact feedback corrections.
Full integration is GREEN and V89 is landed locally at `143bfdb`. V90 starts household
discovery and critique improvements; V88 remains in its ancestry at `000b0a2`.**
The recurring local iteration follows [ADR-0127](adr/0127-recurring-local-version-loop.md)
until the owner stops it. No push or deployment occurred.
Public rollout still requires the external checks below.
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

V85 makes cinnamon/cocoa native, adds 25 accepted forms and repairs butter/apple-pie
feedback. Four new Contexto targets (Ecler, Amandină, Halva, Înghețată) bring eligibility
220→224; Stafide→Brânză brings Lanț 95→96. One live Intrusul clue now states the truthful
dairy category; board identities and choices remain stable. The stored Conexiuni source
correction does not widen its eligible pool. See [ADR-0120](adr/0120-native-ingredients-and-audited-vocabulary.md)
and [ADR-0121](adr/0121-exact-label-corrections-with-stable-board-identities.md).

V85 full gates: **1,299 backend tests on each Python version, 53 accounts tests each,
177 native frontend tests and 122 browser checks** passed. The application assets remain
byte-identical at 118.87/120 KiB. Historical observations are retained while current rank
expectations track the reviewed graph. [V85 review](reviews/v85-ingredient-feedback-and-board-clarity/README.md)
records exact quantities, source evidence, warnings and remaining semantic noise.

V86 adds 30 accepted forms, native freezer/cream feedback and two exact reverse
pastry/filling corrections. Five Contexto targets bring eligibility 224→229; one Lanț
route brings 96→97. Existing Alchimie projections, Lanț profiles and 336 derived rows
remain exact. Of 96 old approved Lanț menus, 59 improve; all now show two shortest
alternatives within unchanged bounds. Failed creation/replay preserves options, old
results and scores while keeping the error and retry together onscreen. See
[ADR-0122](adr/0122-visible-alternative-routes-in-lant.md),
[ADR-0123](adr/0123-reviewed-preparation-and-cooling-concepts.md) and
[ADR-0124](adr/0124-persist-new-game-creation-failures.md).

V86 full gates: **1,353 backend tests per Python version, 53 accounts tests each,
177 native frontend tests and 148 desktop/mobile browser checks** pass. Final bundle
is 118.87/120 KiB. The [V86 review](reviews/v86-preparation-and-route-quality/README.md)
records initial UI findings, strict final checks, exact quantities and remaining limits.

V87 adds **nine concepts, 50 directed links and 31 accepted forms**: 30 grammatical or
qualified forms and one sourced Cremșnit/cremeș lexical equivalent. Six easy Contexto
rounds (`ct_gastronomie_346`–`351`) promote Biscuit, Chec, Cremșnit, Tort Diplomat, Pișcot
and Ciocolată, increasing eligibility **229→235**. The pack now contains **655 records:
647 approved and eight pending**. Lanț remains at 97 eligible, Conexiuni at 74 and
Alchimie at 79; Intrusul/Perechi retain their combined 336-row catalog.

Chec and Brioșă become native inputs; their approximate projections are retired. A
separate generic Tort cue brings the projection vocabulary to 467 rows. Three native
and two projected exact-target feedback repairs improve related-food guesses without
making them wins. Projected Tort cannot inherit the native Prăjitură→Cremșnit repair.
The audit-only domain representative changes from Brioșă to Chiflă; the other 25 remain
unchanged. Pandișpan and Brioșă hidden-target rounds remain deferred. See
[ADR-0125](adr/0125-reviewed-snack-concepts-and-biscuit-cues.md).

V87 also recovers lost Contexto guess, clue and give-up responses through one authoritative
read. A failed verification preserves input and offers a persistent read-only retry;
stale callbacks and another tab's saved game cannot overwrite or clear a newer round.
The existing score ledger records recovered wins without replaying paid actions. See
[ADR-0126](adr/0126-reconcile-uncertain-contexto-actions.md).

V87 full gates: **1,409 backend tests per Python version, 53 accounts tests each,
193 native frontend tests and 168 desktop/mobile browser checks** pass. Bundle is
118.90/120 KiB; validators, pending, lint/typecheck, Ruff/docs/whitespace are GREEN.
Both initial backend runs passed 1,408/1,409 before a stale projection test was
corrected; both full matrices then reran GREEN. The
[V87 review](reviews/v87-snack-and-action-quality/README.md) preserves actual logs,
exact impact comparisons and the disclosed Brioșă bread-feedback regression. The
[action receipt](reviews/v87-snack-and-action-quality/action/verification.json)
retains baseline defects and the initial native source-shape failures separately.

V88 adds **seven concepts, 28 accepted forms and 33 directed links**, removing the one
false fermented-Smântână→Frișcă link for **32 net new links**. Forms comprise 25 grammatical
and three qualified expressions, with **zero new synonyms**. Compas, Echer, Raportor,
Mătură, Taburet, Cratiță and Smântână dulce pentru frișcă support specific reviewed uses.
The served build is `fixture-v88-cross-game-quality`: **2,413 concepts / 9,442 links /
8,631 forms / 180 puzzles**. [ADR-0131](adr/0131-everyday-tools-and-cream-sense-correction.md)
records the cream correction, projection retirements and bounded cleaning-graph opening.

Three new rounds are approved and selectable: Alchimie Cremșnit (`al_gastronomie_107`)
and Conexiuni `cx_viata_de_roman_362` / `cx_viata_de_roman_363`. The pack contains **658 records:
650 approved and eight pending**, with **488 eligible** across its four games.
No Contexto, Lanț, Intrusul or Perechi round is added in V88. Tort Diplomat remains held
after recipe-sense and useful-depth review; the batch does not force its proposed count.

V89 adds only Mop353: **659 records /651 approved /8 pending**, with **489 eligible**.
Two initial household candidates are rejected after final directed-neighbor review:
Făraș/Aspirator have3 incoming cues each; Mop has5. The original union-degree mistake
and both corrections remain in [the V89 review](reviews/v89-feedback-and-conexiuni-recovery/README.md).
[ADR-0133](adr/0133-closed-dust-and-whipped-cream-feedback.md) records specific Diplomat/Frișcă
and Praf feedback; [ADR-0132](adr/0132-reconcile-uncertain-conexiuni-actions.md) records lost-action
recovery, earned clues and persistent read-only verification. No KG word, link or form is added.
The following inventory is current; V88 evidence below remains its historical verification.

| Game | Total | Approved | Pending | Eligible / preferred |
|---|---:|---:|---:|---:|
| Alchimie | 83 | 80 | 3 | 80 eligible |
| Conexiuni | 234 | 234 | 0 | 76 eligible |
| Cald sau Rece | 242 | 240 | 2 | 236 eligible |
| Lanțul Cuvintelor | 100 | 97 | 3 | 97 eligible |
| Intrusul | 183 | 183 | 0 | 144 preferred |
| Perechi | 153 | 153 | 0 | 113 preferred |

All 655 old pack records, 82 Alchimie profiles, 100 Lanț profiles and 336 derived rows
remain exact. One nonshortest Lanț menu entry changes from Saramură to Găleată;
all 206 previously shown shortest first hops remain available, with no lost eligibility.
Native Mătură and Taburet replace two approximations, leaving 465 projected inputs.
A closed native Brioșă→Pâine repair gives rank 2/hot without a false synonym or global
bread projection; [ADR-0130](adr/0130-closed-native-bread-family-feedback.md) records its
qualified family interpretation and retained hidden-target holds.

Lanț move, undo and hint failures now reconcile through one owned GET. A failed read
keeps a persistent read-only retry and disables mutations; earned help survives recovery
and resume without spending another stage. [ADR-0128](adr/0128-reconcile-uncertain-lant-actions.md)
records the shared action owner and one bounded current-position hint payload.
[ADR-0129](adr/0129-portable-alchimie-projection-reviews.md) extends portable independent
review to Alchimie while retaining exact audit/source/projection/batch bindings and two
independent judgments. It makes later recipe batches easier to review without weakening
promotion gates.

V88 frontend integration is GREEN: **193 native tests and 188 desktop/mobile browser
checks**, with lint, typecheck, build and the **118.92/120 KiB** budget passing. Initial
backend integration passed 1,501 tests and failed seven historical/aggregate assertions.
Their source-aware corrections passed all seven focused cases. Final full backends passed
**1,508 tests each on Python 3.12.3 / 3.14.6**, plus **53 accounts tests each**. One
intermediate Python 3.12 attempt was terminated before completion; its preserved partial
log is excluded from success counts and the unchanged complete rerun passed.
Final gate state and actual receipts belong in [STATUS](STATUS.md) and the
[V88 review](reviews/v88-cross-game-quality/README.md).

The [independent supplemental review](reviews/v88-cross-game-quality/SUPPLEMENTAL_REVIEW.md)
accepts the measured tradeoffs conditionally on full green integration. Correcting cream
sense cools plausible pastry guesses toward Frișcă, and retiring broad proxies cools some
Taburet/Mătură home context. These are disclosed quality costs, not universal feedback
improvements; the exact affected examples remain in the impact report.

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
| V85 | Approximate ingredient guesses and misleading labels weakened otherwise familiar rounds | Eight concepts, 25 forms, 40 new links plus one relabelled relation; one served dairy clue corrected; four Contexto targets and one Lanț route. Full integration GREEN |
| V86 | Weak preparation/cooling clues, hidden short routes and disappearing creation errors | Nine concepts, 30 forms, 41 links and six reviewed rounds; two exact feedback corrections; 59 old approved Lanț menus improve; all-six-game failure/replay recovery preserves state and action visibility. Full integration GREEN |
| V87 | Weak snack-defining cues and lost paid/terminal action responses | Nine concepts, 31 forms, 50 directed links, six promoted Contexto targets and five bounded feedback repairs; owned authoritative recovery without mutation replay. Full 1,409 backend tests per runtime, 53 accounts each, 193 native/168 browser checks pass |
| V89 | Lost Conexiuni actions, household feedback and directed-neighbor quality gaps | One Mop round, four exact feedback scopes, owned Conexiuni recovery; two candidates rejected under C3. Full integration GREEN: 1,531 backend tests per runtime, 53 accounts each, 193 native and 214 browser checks. |
| V88 | Missing everyday tools, a false cream sense, inaccessible recipe-review tooling and lost Lanț actions | Seven concepts, 28 forms, 33 links added/one removed; one Alchimie and two Conexiuni rounds; portable projection-bound Alchimie review; owned Lanț action and earned-hint recovery. Frontend 193 native/188 browser checks GREEN; full backend 1,508 per runtime and accounts 53 each GREEN |

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
| Rules, hints and progression | All six seeded games have server-scored completion coverage. V88 recovers Lanț moves, undo, hints and wins without mutation replay; earned hints survive resume without escalating. V86 route-choice and V87 Contexto recovery remain covered. Automated solves do not establish enjoyment. |
| Romanian content and difficulty | V88 adds seven everyday/preparation concepts, 28 forms and three rounds across Alchimie/Conexiuni, and repairs native Brioșă→Pâine feedback. Correct whipping-cream ownership exposes reverse pastry→Frișcă cooling; native Taburet/Mătură lose some broad home affinities. No old eligibility is lost. Pandișpan/Brioșă targets and the new Diplomat recipe remain held. Human fairness/enjoyment is unmeasured. |
| Onboarding and presentation | Shared intros, categories, HUD, action feedback and results were inspected; mobile layout and rendered states are audited. No broad redesign was justified by this evidence. Real-device rendering and human comprehension are still pending. |
| Keyboard and accessibility | Desktop essential controls support Tab/Space/Enter completion; Perechi focus is checked after pairs disappear and at result. Automated Axe checks run on settled intro/live/result states. Text-entry tests use programmatic fill after keyboard focus; no actual screen-reader usability study ran. |
| Reliability and storage | Retry, stale IDs, unmount/loading ownership, immutable terminal actions and duplicate completion are covered. Contexto and Lanț have actual committed-response-loss and delayed/cross-tab recovery checks; an already different pointer blocks the old POST. Lanț stores one earned hint payload, not a history. Strict concurrent-tab score protection requires Web Locks; fallback is best effort. Receipt TTL is 24h with 1,000 IDs/game; retained terminal sessions can record again after expiry. |
| Maintainability and extension | Shared lifecycle code stays narrow and mechanics explicit. V88 shares the owned action helper across Contexto/Lanț and extends portable independent review to Alchimie with exact source, sparse-projection, audit and batch bindings. All four pack games retain two complete independent judgments and generated transactions. Content-delta reporting and compact probes measure playable gains separately from metadata churn. |
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

Player observations should guide the next product iteration. V84–V88 address ingredient
approximations, specific preparation/cooling cues, board wording, visible route alternatives
and failed-game creation/replay. V88 adds everyday concepts, cross-game rounds and Lanț
action recovery; semantic follow-ups include the newly measured cream and home-context costs.
Biscuit is now promoted; Pandișpan and Brioșă remain inputs while their target rounds are
deferred. Follow-ups include indirect oven/yeast/Sarmale associations, butter/dairy feedback,
unrecognized temperature words and variant-specific routes. The
[V82 dispositions](reviews/v82-playable-content-batch/shortlist/dispositions.json) retain
other investigated candidates. Repairs and fresh playable reviews belong together where
feasible; these are investigation candidates, not approved promotions. Generic Pâine now
passes review; the earlier direct Făină→Pâine de casă edge remains deferred. Accounts,
derived-catalog expansion and another game retain their separate gates.

V87 impact also records a remaining input regression: native Brioșă→Pâine is rank
424/cold after its former broad bread projection retires (previously rank 2/hot).
False Zacuscă affinities cool; eight old-native warm→lukewarm shifts keep their
distances. Correct concept ownership does not make every feedback change an improvement.

V88 closes that recorded Brioșă→Pâine regression with the exact native rank 2/hot pair.
It does not restore the broad projection or resolve every pastry/household association.
In the V88 impact sample, Tort Diplomat→Frișcă is 345/cold, Cremșnit→Frișcă 504/cold,
Pișcot→Frișcă 944/very cold and Prăjitură→Frișcă 181/lukewarm. Qualified whipping cream
is 2/hot and Zahăr is 11/hot, while unrelated Zacuscă remains 24/warm. Taburet→Viața la
bloc becomes 678/cold. These concrete follow-ups require focused review without restoring
false edges or universal approximations.

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

V89 closes the recorded Tort Diplomat→Frișcă cost with one exact native hot pair.
Cremșnit/Pișcot and the truthful Zacuscă route retain their prior feedback. The household
stress sample exposes19 unknown words and several weak alternate approaches; these and
the two rejected hidden targets remain next-version work, not a claim of broad completion.
