# V87 independent Contexto recovery and scoring review

Valid until: any bound source file changes — then treat as history.

Reviewed 2026-09-08 by v84_graph_research against baseline `daae025`. **Accepted with no concrete blocker.** The exact six changed source hashes, unchanged dependencies, consulted tests and observed native-log hash are archived in [code-review.json](code-review.json). No application or test file was edited; this reviewer ran no tests.

## Action recovery

The helper creates one immutable action ticket under a synchronous lock. Adoption and cleanup both require the identical current ticket, so an old callback cannot release a newer same-ID action or replace another screen’s state. Before a mutation, the screen checks that the saved pointer still owns the displayed round. A different pointer pauses the action before any POST. The same ownership checks surround recovery and direct successful mutation responses.

After a failed guess, clue or giveup request, the helper performs one authoritative GET. It has no mutation callback, timer or automatic retry. A failed read leaves the prior state and typed text available for inspection but disables mutations and options; the explicit verification button performs only another GET. A response with another or missing game ID is not adopted. Pointer changes before or during the read supersede both success and 404 results.

A committed winning response recovered by GET reaches the unchanged once-per-session score recorder. A committed clue adopts the actual paid clue and counters without requesting another clue. A recovered giveup shows the authoritative terminal answer without adding a score. Verified missing sessions return to setup and clear only their own pointer. When storage is unavailable, a locally held round still works while both pointer observations are null; a newly stored different ID takes precedence.

Exit preserves an uncertain action’s pointer because a server-side win may not yet have reached the UI. It then invalidates local ownership. Resume and new creation similarly invalidate old tickets. The existing score completion uses conditional pointer cleanup, so it cannot remove a newer saved round. The old saved-resume and storage/score helpers are unchanged.

## Native and projected feedback

Three native exact pairs are explicit: Pandișpan→Chec, Biscuit→Pișcot and Prăjitură→Cremșnit. Two projected exact targets are separate: Tort→Tort Diplomat and Ciocolată caldă→Ciocolată. Projected words keep their own public identities and cannot win through an exact-target cue.

The new allow_exact_pairs argument defaults to true. Native feedback, ordinary proxy behavior and the existing ingredient-specific policy retain that default. Projected scoring and projected typo-suggestion filtering explicitly disable inheritance of native exact pairs, while retaining their own projection neighborhood rules and subsequent legacy fallback behavior.

I inspected the configured projection anchors: only the newly added Tort row shares an anchor with a native exact-pair source. The guard therefore prevents Tort from accidentally borrowing Prăjitură’s Cremșnit override without broadly changing older projected cues. Native Prăjitură still receives its reviewed override. Actual-target typos, source identity, nonwinning proxy feedback, missing-anchor behavior and private-answer filtering retain their existing boundaries.

No server session field, scoring formula, TTL, capacity or request-size setting changed. Defaults remain a 7,200-second sliding TTL, 1,000 sessions per game and 64 KiB requests. No automatic mutation retry or persistence layer was added.

## Evidence and limits

The existing completed native log reports **193 tests passed, zero failures and zero skips** in 1080.705652 ms. I read that log and the relevant helper tests; I did not rerun them. The older native assertions were adapted to the owned-GET flow while retaining their input, clue and lifecycle requirements.

The consulted browser cases explicitly check lost committed win/clue/giveup responses, exactly one mutation and recovery read, failed-read locking, GET-only retry, pre-POST pointer rejection, late 200/404 suppression, exit during recovery and owned missing-session cleanup. Backend tests cover the native/projected boundary, Tort’s isolated fallback, private typo suggestions and preservation of legacy proxies. These tests were inspected as evidence of intended coverage; final browser and full-CI success are not claimed by this source review.

Content promotion remains a separate bound review. Acceptance here applies only to the frozen source bytes recorded in the JSON artifact.
