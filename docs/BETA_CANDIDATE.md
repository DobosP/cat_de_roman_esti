# Anonymous beta candidate

Valid until: the next verified quality wave — then refresh this living checklist.

Target: public anonymous beta for Romanian players. Current implementation, artifact pins
and executed checks are in [STATUS](STATUS.md); this checklist separates technical evidence
from acceptance that requires players or a production release. Accounts remain a separate
scope under [DEPLOY](DEPLOY.md).

## Bounded sequence

| Wave | Problem / hypothesis | Acceptance | State |
|---|---|---|---|
| V73 | Duplicated lifecycle plumbing makes fixes drift between games | Preserve representative seeded boards, real complete rounds/replay, progressed reload, expiration and start retry; shared backend transactions and frontend resume; independent review | Implemented; integrated local gates passed (922 backend, 53 accounts, 163 frontend, 48 browser) |
| V74 | Temporary resume errors can discard recoverable rounds; stale responses and terminal actions can change the wrong state | Retain recoverable IDs, provide a clear retry, reject stale results and preserve terminal results; browser regressions plus targeted concurrency/side-effect tests | Confirmed issues; implementation follows V73 |
| V74 | Keyboard, focus, contrast and mobile behavior lack rendered evidence | Audit all six intro/live/result states; correct reproducible issues; automate repeatable checks | Pending |
| V75 | Recent alias waves did not increase eligible playable boards | Reusable bounded pack-only import/review path; execute one independently reviewed candidate batch; report eligible delta, rejected/pending candidates, unchanged protected payloads | Five familiar-food Contexto candidates proposed; unreviewed |
| Candidate gate | Dependency and operational risk remains unmeasured or unresolved | Remediate reachable installed advisories, run local release/performance checks, record production/human gates distinctly | Pending |

Each new wave records the problem, baseline, expected player benefit, acceptance criteria,
scope, independent review and measured result. Further waves follow demonstrated deficits;
alias totals and code churn are not success criteria. Refactor decisions:
[browser baseline](adr/0098-protect-real-browser-game-journeys.md),
[server transactions](adr/0099-consolidate-session-endpoint-transactions.md),
[saved-game lifecycle](adr/0100-extract-saved-game-resume-lifecycle.md).

## Coverage and remaining questions

| Area | Evidence so far | Required before technical candidate |
|---|---|---|
| Game rules and privacy | Existing Python contracts; private test-process solution oracle; server-scored browser rounds for all six | Integrated required backend/accounts/content gates; terminal-action regressions |
| Resume and recovery | All six progressed reload, expired ID, failed start and replay journeys pass on desktop/mobile emulation | Transient recovery, stale-ID guard, terminal score recovery, failed-action/stuck journeys |
| Presentation and access | Direct mobile play through an Intrusul win and Alchimie opening; repeatable Chromium mobile journeys | All six rendered layout, keyboard/focus and accessibility checks; record browser/device limits |
| Romanian gameplay | Current approved stock and holds retained; no new content accepted yet | Rubric-bound independent reviews, recognizable warm guesses/routes, rejection evidence and a real playable-content wave |
| Maintainability | Shared narrow lifecycle extractions; mechanisms and tests remain game-specific | Reusable pack-only workflow with no silent KG omission or derived-catalog expansion |
| Performance | Existing generation and transfer budgets; initial gzip transfer 118.17 KiB against 120 KiB gate | Record cold/warm create/action latency and bounded-session memory under a stated local load |
| Dependencies | Lock audit found six high advisories; SPA and build-only exposures distinguished | Apply supported fixes, rerun audit and affected gates; document any unresolved exposure |
| Production | Last documented rollout is anonymous V72 on 2026-08-27 | Authorized deployment, current public-page/config checks, release smoke and rollback rehearsal |
| Player feedback | No feedback intake established for anonymous beta | Owner selects a usable contact route; do not enable account/submission storage implicitly |

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
