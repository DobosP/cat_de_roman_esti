# V91 — recovery, mobile clarity and useful Sport seeds

Valid until: a later change supersedes these bound V91 observations — then treat as history.

Baseline is local main `e2e03638b90fc9248c33f70eedaa8c9c5fbd87ad`, containing landed V90.
V91 is the final authorized version under [ADR-0137](../../adr/0137-finish-v91-and-stop-iteration-loop.md).
V91 is locally merged as `48cd5b81fa42b485c29fd22c39cb9f55be2224ce`.
The automatic loop is paused and stopped; V92 was not started. The candidate ledger and
all sealed evidence are recorded in that commit; later landing notes are documentation only.
No push or deployment is part of this work. All 16 final local gates pass; the
[completed gate receipt](verification.json) records the exact commands and raw log hashes.
The final file ledger is `review-manifest.json`.

## Player outcomes

- **All six games:** full mobile titles and wrapping status badges; notices sit above the
  scrollable game screen. Measured header offsets and short-screen fallback keep controls
  reachable. Long headings wrap at 200% text size. The existing ToastStack API, announcements,
  dismissal and lifetime remain intact. [Mobile evidence](mobile/README.md),
  [independent root check](mobile/root-independent-audit.json),
  [ADR-0139](../../adr/0139-visible-mobile-status-and-notices.md).
- **Intrusul/Perechi:** persistent read-only verification after uncertain actions, mutation
  locks until reconciliation, original saved-pointer ownership across retries, owned 404
  cleanup and response-identity checks. Exit and browser Back invalidate departing screens
  before stale score/focus effects. Paid clues and the one-hint cap already existed.
  [Recovery evidence](derived-recovery/README.md),
  [ADR-0138](../../adr/0138-owned-intrusul-perechi-recovery.md).
- **Alchimie:** replace only the seeds of existing easy Sport 083 with Neagu, Echipă națională,
  Dinamo, Rapid, FCSB and CFR Cluj. All six are useful at the opening; previously three were
  depleted. Four productive pairs express two ideas, with six recipes/four routes/par 2.
  The target and approval stay unchanged. [Author review](content/author-review.md),
  [factual judgment](content/factual-review.md), [quality judgment](content/quality-review.md),
  [ADR-0140](../../adr/0140-reviewed-sport-seed-revision.md).

## Exact content scope

[Content delta](content-delta.json) records zero new concepts, links, forms, synonyms or
rounds, and one revised round. All 2416 nodes/9459 edges/8641 forms/180 puzzles remain exact.
The other 660 pack records,82 Alchimie books,100 Lanț records and 336 derived boards remain.
Pack 661 retains 653 approved / 8 pending; all 491 eligibility decisions are unchanged.
The target's 0.4323 salience warning stays explicit. Four club tiles represent one category
idea; the sparse book does not accept every plausible football-club pair.

[Artifact delta](artifact-delta.json) binds exact current and V90 bytes and reversible
row/header changes. Sport 083's heuristic score 67→70 combines familiarity 49→60 with play
quality 93→85; its rank 38→23 and weight 3→4 shift 15 other ordinal positions and al_limba_042's
weight 4→3. No other score or eligibility changes. Only Alchimie's seeded public start changes.
The served KG and mobile contract are byte-identical to V90; the derived catalog changes
source headers only, with its bundled integrity pin updated.

The dedicated approved-stock migration requires the two exact independent accept judgments,
rebuilds the reviewed dossier/private book and validates both mirrors within a rollback
transaction. Dry-run, real application and artifact generation pass.
[Migration audit](migration-audit.md) independently accepts 85 targeted tests, including
37 writer guards and the seven V91 history/book contracts. [Four fresh public BFF routes](content/final-public-bff-journeys.json)
use the real seed 38 selector and all win in two moves for 1000 points: 16 requests, four
sessions deleted. Only random game IDs are normalized in these complete response bodies.

## Verification and preserved failures

The recovery lane passes 80 final browser variants,26 native checks and six observed
recovery states. Independent review adds four Back variants and two removed-pointer cases.
Six immutable archives preserve 199 raw entries. Mobile passes 14 built browser cases and
10 native checks, with 255 raw/decoded artifact bindings. Full frontend passes 193 native and 342 browser checks, with two isolated browser workers
and zero retries; lint/typecheck/build/bundle pass at 119.08/120KiB. Python 3.12 and 3.14 each
pass 1652 backend and 53 account tests. All 16 final local checks are GREEN.

The records preserve unsuccessful hypotheses and actual failures: initial capture/harness
mistakes, mobile heading overflow, the screenshot-preview false alarm, failed-read and
ownership defects, a passing initial Back probe followed by four reproduced departure
failures, and their subsequent presence fix. A third recovery runner returned 143 after
printing its complete red summary; its cause is unestablished and it is not a green gate.
Initial seed capture 503 occurred before updating the intermediate catalog integrity pin;
the corrected six-game capture passes. Root development logs and source runners are in
[root-checks](root-checks/development-manifest.json). [Two old backend expectations](sparse-recipe-audit/README.md) were corrected while preserving
V87/V90 snapshots. The initial red backend run was deliberately interrupted after 1265
passes/two failures and is excluded. The first completed browser run passed 338 and failed
two old clue setups. [The test-only setup correction](alchimie-test-setup/README.md) keeps
all six original solution fields, preserves output/pair recovery and adds the legitimate
anti-spoiler category case. Focused 34 and final full 342 checks pass. The original failures
remain separate from the final green gate. [The backend test amendment](source-freeze-amendment.json)
and [frontend test amendment](frontend-test-amendment.json) explain their distinct freezes;
all serving/runtime/data and reviewed UI asset inputs remain unchanged.

[Kickoff baseline](kickoff-baseline.json) and [runner](capture-kickoff.py.txt) preserve the
original 15-request inspection, proving clues already survived GET and repeated hints were
rejected without another charge. Earlier runtime guarantees are not recast as new fixes.

## Remaining limits

These checks do not establish human recognition, playtest acceptance or physical mobile
keyboard/safe-area behavior. Three Neagu past-tense edge labels remain a separately reviewed,
unapplied proposal. Four thin approved Contexto neighborhoods, 17 unknown household surfaces
and earlier A5/hidden-target holds stay open. No automatic demotion, approval or next version
is implied. Production remains the last documented anonymous V72 deployment; rollout and
accounts require their separately authorized gates.

[Independent final UI audit](final-ui-audit.md) validates the earlier bound UI evidence.
Its older helper hashes remain historical after the documented test-only amendment; the
final full browser gate validates the complete current test helpers and all six games.
