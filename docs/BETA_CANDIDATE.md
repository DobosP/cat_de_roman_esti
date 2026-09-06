# Anonymous beta candidate

Valid until: the next verified quality wave — then refresh this living checklist.

Target: public anonymous beta for Romanian players. **Technical candidate complete through
V81 and locally verified.** Walnut vocabulary now has reviewed direct recipe feedback; no new target is promoted.
Public beta release still requires the external checks below.
Current facts and exact pins: [STATUS](STATUS.md).

## Completed sequence and acceptance

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

Final V81 gates: **1,024 backend tests on each of Python 3.12.3 and 3.14.6**, 53 accounts
tests on each runtime, **173 native frontend tests and 108 desktop/mobile browser checks**.
Clean install, frontend lint/typecheck, both content validators, Ruff, docs and whitespace
passed. The npm audit reports zero vulnerabilities. Independent factual, impact,
implementation and documentation reviews found no remaining actionable issues. Frontend
assets remain at V75; typecheck and the 118.73/120 KiB budget check passed without rebuilding.
Accounts were enabled only for their isolated test suite. Exact results, unchanged sampled selections and the disclosed percentile-boundary
effects are tracked in STATUS and the V81 review archive.

Decisions and full evidence: [ADR index](adr/README.md), [V75 review](reviews/v75-contexto-food/README.md),
[V77 review](reviews/v77-flour-associations/README.md), [V78 review](reviews/v78-dessert-targets/README.md),
[V79 review](reviews/v79-gem-feedback/README.md), [V80 review](reviews/v80-clatite-target/README.md), [V81 review](reviews/v81-nuca-feedback/README.md),
[runtime measurements](reviews/v74-runtime-measurements/README.md). Refactors preserve
server authority, hidden answers, session bounds, intentional game differences and scoring.
The derived catalog remains frozen at 336 boards. Content critiques are independently
authored Codex-agent judgments with source checks; they are not Romanian-player sessions
or human subject-expert approval.

## Quality coverage and limits

| Area | Evidence and remaining uncertainty |
|---|---|
| Rules, hints and progression | All six seeded rounds reach server-scored results; replay, progressed reload, mistake counters, failed action/start recovery and expiration have real-BFF coverage. Automated solves do not establish intuitiveness or enjoyment. |
| Romanian content and difficulty | Independent factual, recognition, ambiguity and warm-opener reviews promoted only two easy food targets. Ordinary ingredient/holiday probes rejected three in V75. V78 freshly defers Cozonac/Clătite despite repaired flour; accepted nut/jam inputs gave misleading feedback. V79 repairs Gem only in a reviewed direct preserve neighborhood; V80 independently promotes Clătite after reviewing the remaining imperfect inputs; V81 adds bounded native walnut feedback while keeping ambiguous tree forms out. Existing editorial holds and historical rejection evidence remain intact. |
| Onboarding and presentation | Shared intros, categories, HUD, action feedback and results were inspected; mobile layout and rendered states are audited. No broad redesign was justified by this evidence. Real-device rendering and human comprehension are still pending. |
| Keyboard and accessibility | Desktop essential controls support Tab/Space/Enter completion; Perechi focus is checked after pairs disappear and at result. Automated Axe checks run on settled intro/live/result states. Text-entry tests use programmatic fill after keyboard focus; no actual screen-reader usability study ran. |
| Reliability and storage | Retry, stale ID handling, unmount/loading ownership, immutable terminal actions and duplicate completion are covered. Strict concurrent-tab local-score protection requires Web Locks; fallback is best effort. Receipt TTL is 24h with 1,000 IDs per game; a deliberately retained terminal session can record again after expiry. |
| Maintainability and extension | Shared lifecycle code stays narrow, mechanics explicit. Pack-only imports reject topology, V2 artifacts bind two independent complete reviews, and generated fixtures remain tool-owned. Portable review assembly supports Conexiuni/Contexto/Lanț; Alchimie retains its separate projection-bound workflow. |
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

The next useful product iteration is driven by those observations. The clearest existing
content follow-up is a fresh Cozonac target review after V81 repairs the direct nut route.
The new word retains approximate feedback elsewhere and does not make every recipe guess
perfect. V77’s bread route remains deferred. V76 prevents the accented Paște/Paste misinterpretation. Additional vocabulary totals alone do not resolve
these feedback problems. Accounts, derived-catalog expansion and another game require their
separate documented gates.

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
