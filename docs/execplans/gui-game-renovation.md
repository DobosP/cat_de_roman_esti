# Finish the Cat game migration

Branch: `feat/gui-cat-m3`
Session: GUI completion loop, M3 and M4
Worktree: `/home/dobo/work/_worktrees/cat_de_roman_esti/feat__gui-cat-m3`

## 1. Purpose / Big Picture

Finish the existing Preact game migration without changing game content, saved
progress or the accepted design. The owner requested completion on 2026-10-18.

## 2. Progress

- [x] 2026-10-18T17:09Z — inspected all98 unmerged paths and preserved their exact
  entry bytes in the compact scratch source packet; no other lane was changed.
- [x] Read-only review confirms all eight app paths and both Alchimie modes exist.
- [x] Static shared-control extraction removes18 CSS bags; exact site inventory retained.
- [x] Class-only Challenge markup uses native tags;47 wrapper tags, handlers unchanged.
- [x] 2026-10-18 — owner explicitly approves the reviewed mechanical score-module
  split and scoreSync import narrowing; all other source freezes remain.
- [x] Applied approved score split: original34 score tests/147 assertions,38focused,
  types/tools/lint/build/docs62 and26desktop/recovery cases pass.
- [ ] Qualify native Preact state for the20 Challenge render snapshots (ADR-0204),
  retaining all asynchronous ownership/motion/focus/scoring and existing assertions.
- [x] 2026-10-18T19:01Z — all10JS caps pass: Challenge40,864/40,960, Home29,011/30,720 target.
- [x] Broad native-state diagnostic:111passed/2failed,0skip/flaky; exact source, logs and failure traces retained.
- [x] Two minimal fixes pass113/113desktop: committed key listener timing and new-round access after failed verification.
- [x] 2026-10-18T19:11Z — all6 real history regressions fail on old late-create pointer adoption (3games×2projects), not fixture/setup/timeouts.
- [x] 2026-10-18T19:16Z — reviewed three-screen repair passes139desktop/38focused/34score, all10JS caps/types/tools/lint/build/docs; strengthened history response/count witnesses pass.
- [x] Final bounded source review15256eff is clear for all8 route bindings, frozen boundaries,12 score-module bindings and22 critical runtime inputs.
- [x] Actual browser discovery retains933 existing case identities.
- [x] Focused38/38 checks pass after source census119/8 correction.
- [x] Real mode-switch blank-screen regression reproduced in both desktop projects;
  instance-local lazy retry fixes it and all four chunk/storage recovery cases pass.
- [x] Final app/tools types,38focused,lint/build and26desktop/recovery cases pass;
  both navigation regressions and immutable loader initialization are verified.
- [x] Unused Router export compiler candidate measured and rejected: positive
  DCE test fails and JS grows; entire candidate reversed, source/evidence retained.
- [ ] Qualify clean M3 on the exact merged SHA, obtain independent review and land locally.
- [ ] Complete M4 CSS/budget ratchets, full qualification, release image and documentation.

## 3. Surprises & Discoveries

At entry the latest actual measurement was Challenge44,592/40,960 gzip bytes:
a3,632-byte gap. Final current results are recorded in section5.
All other nine measurements pass; Explore40,087 leaves873 bytes. Older status
figures45,441/45,806 precede the current common-controls build layout.

## 4. Decision Log

2026-10-18 — resume the existing lane and preserve its98 unmerged source paths.
Existing S1 protected helper/API/content rules remain in force except the directly
approved mechanical scores.ts/scoreSync split. Owner answer: “Allow the
behavior-preserving module split”. Preserve original bodies, public API, keys,
formats, receipt locking/timing and all test assertions; no broader waiver.
The live explicit-unit audit inventory is rebound161→119 after24 historical Challenge bags and18
shared-control bags were transferred literally to authored CSS; all declaration checks and nested-bag assertions remain.
A build-only pinned preact-iso export rewrite may eliminate an unused Router
closure while retaining the original hoisted function and Provider assignment.
Use exact package source hash, original/transformed API and used/unused installed
Rolldown controls; reject if the positive DCE control fails. Never change vendor
bytes or broad tree-shaking defaults. Both source reviewers approved source evaluation. Actual installed Rolldown then
failed the positive removal assertion; the exact candidate was fully reversed.
Do not retry an export-alias variant or weaken that assertion.
Do not repeat nonclosing CSS/minifier/JSX experiments already measured.

2026-10-18 — ADR-0204 revises only the unqualified Signals direction. Independent
architecture review confirms that the adapter supplies render snapshots rather
than fine-grained observers; native Preact queues these synchronous setter groups.
Preserve all functional requirements and verify the actual runtime/complete budgets.

2026-10-18 — broader original journeys prove the keyboard listener must attach
with the committed selection via useLayoutEffect. Failed verification locks old
round mutations but must permit explicit new creation, as the original React
source did. Keep presence/loading/busy/create guards and existing owner
invalidation; change only that button and listener timing. Preserve assertions.
Measured record-writer startup grouping may share its already-startup core; all
routes must count the full writer bytes and Home target remains30,720.

## 5. Outcomes & Retrospective

Latest dirty focused preflight at e75518c1/tree40981bbe passes app/tools types,
38focused and34original score tests, lint/build/docs,139desktop cases with0
skips/flaky. Discovery retains933 identities. All10JS caps pass: Challenge
40,847/40,960 and Home29,000/30,720 target. The score split retains42 function
bodies and147 original assertions. [Focused proof](../reviews/gui-m3/renovation-focused.json).
All6 three-game history scenarios first fail on stale saved-pointer adoption,
then pass with reviewed live/epoch/reentry guards and stronger response/request
witnesses. Read-only local recovery remains when storage is unavailable. No
protected helper/API/scoring semantics change beyond the approved module split.
[Bounded independent review](../reviews/gui-m3/bounded-source-review.json) is clear
in its stated scope; exact clean unit/full and final acceptance remain required.
Original source/failure packets retained. Superseded reproducible planner binary
was pruned; historical full archive bytes are unavailable, compact logs/traces remain.

M4 also requires the unchanged original16,093-byte total-CSS ratchet, in addition
to per-route checks. Current emitted unique CSS totals20,617 gzip bytes; this
requires real consolidation and visual proof, not a larger cap.

## 6. Context and Orientation

Local main at entry: `d30b0aa47248b9a5944e015f2daf54cc5a795617`.
Feature HEAD: `e75518c1473be3a32ec2a0f2e1565764bbcf5d5b`.
Read `.agent/S1.md`, `docs/STATUS.md`, the programme completion ledger and
`docs/execplans/s1-cat.md`. Original/frozen sources and content stay authoritative.

## 7. Plan of Work

Review the actual emitted dependency graph, implement a substantive allowed
reduction and measure every route's complete closure. Preserve mandatory account
and mode dependencies. Then run the existing functional and visual contracts,
integrate literal content-main only at the milestone boundary, and qualify.
Separate M4 source changes from M3 acceptance; retain one rolling test setup.

## 8. Concrete Steps

Work in this worktree. Use the pinned `scripts/gate.sh shell --sha <HEAD> --dirty`
for focused iterations. After clean commits run `scripts/gate.sh unit --sha <SHA>
--parallel 2`, then `python3 -I scripts/gui-full-runner.py --sha <SHA>`.
Run image qualification at M4 and record actual command/result hashes.

## 9. Validation and Acceptance

Existing assertions, gzip caps, saved-game lifetimes, native drag/drop, focus,
motion/reduced-motion, CSP, nine exact PNGs, full browser inventory, zero-skip PG,
parity1207 and independent review remain required. No physical device testing.
Only a green exact-SHA unit/full plus review permits local main landing.

## 10. Idempotence and Recovery

Never overwrite or delete prior unmerged source packets. Preserve failed-run
evidence compactly, then prune only owned stopped raw outputs after verification.
No writer may change a worktree while its gate runs. Never force-push app history.

## 11. Artifacts and Notes

Entry packet: `_temp/feat__gui-cat-m3/renovation/entry-unmerged.tar.gz`, SHA256
`b0f9babf3bfe920a36a0e6274d2959481f68a7c807138b8c8393992e90cd06b5`.
Disk check before runs:52GiB available,93% used. Keep evidence compact.

## 12. Interfaces and Dependencies

Current core-v1.11 consumer dependencies remain pinned. Do not hand-edit locks,
kit/vendor files or baselines. Cat main may be landed locally under PROGRAM E10;
pushing main, production and real-account activation remain owner-only.
