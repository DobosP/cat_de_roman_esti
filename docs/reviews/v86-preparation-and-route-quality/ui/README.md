# V86 persistent new-game failure feedback

Valid until: the bound UI, test sources or built application changes — then treat as history.

The implementing worker completed source checks, real-browser tests and rendered visual
inspection. This is self-validation; the root session owns independent review and the full
release matrix. Exact sources, commands, log hashes and images are in
[verification.json](verification.json). Decision: [ADR-0124](../../../adr/0124-persist-new-game-creation-failures.md).

## Final behavior

All six games show the same clear Romanian failure notice and preserve selected options
and the previous round/result. Intro failures stay beside start controls. Completed-round
failures appear in the shared result card beside replay controls; Alchimie's live “Alt joc”
failure appears beside that footer. The header itself is unchanged from the baseline.

Saved-resume errors retain their own recovery controls. Starting again or successfully
resuming clears the new-game failure. No HTTP status, server diagnosis or technical
instruction enters the notice. Existing start/daily/replay actions remain the retry paths.

Alchimie and Lanț keep their intro or previous round mounted during creation, distinguishing
it from saved-resume loading. Pending controls are noninteractive; synchronous guards cover
creation, old-game actions, keyboard and exit. Prior feedback/record resets run only after
successful creation. The responsive notice space in result cards and Alchimie's live footer
keeps the clicked action in place; unused text is invisible and excluded from accessibility.
The intro keeps its compact conditional notice. There is no forced scrolling or overlay.

## Browser findings and verified fixes

| Run | Actual result | Product findings | Test setup findings |
|---|---|---|---|
| [Initial](runs/initial-browser.log.gz) | 19 passed, 7 failed; 3.2 minutes | Lanț's failed first start remounted its long intro and lost scroll position. | Six mobile replay setups incorrectly expected the intentionally sticky header to leave the viewport. |
| [Retained intro](runs/retained-intro-browser.log.gz) | 22 passed, 4 failed; 2.6 minutes | Live Alchimie and mobile Lanț replay notices pushed their retry buttons below the viewport. | Two desktop setups incorrectly required the entire rules block to disappear despite genuine scrolling. |
| [Final focused](runs/final-focused-browser.log.gz) | **16 passed, zero failed; 1.4 minutes** | Both layout problems are fixed; notice and retry action remain in the viewport. | The test now verifies an actually scrolled overflow container, without confusing sticky/partially visible content with a short result. |

The final selection covers all twelve desktop/mobile completed-result failures and retries,
both live Alchimie replacement cases, and both Lanț intro regressions. The other ten first-start
cases passed in the previous run and were not repeated in this focused rerun. The root's
full matrix separately exercises all 26 new browser cases. Notice/action viewport requirements
remain strict; no retry setting, test timeout or retained-state assertion was relaxed.

Every first-start scenario holds the request long enough to verify that the intro and exit
controls are unavailable, then checks a sanitized error after the former toast's 3.6-second
lifetime, unchanged selected options and scores, and successful retry. Completed-result
scenarios open real rules, use a short viewport, scroll to the actual replay action and keep
the finished score/copy controls after failure. Live Alchimie additionally attempts an old
action, Enter, Escape and exit during the held replacement and confirms no old-session
mutation or pointer replacement occurs. After failure the selected pair still works.

The final [build](runs/final-build.log.gz) passes at **118.87 / 120 KiB** initial JS/CSS gzip;
[ESLint](runs/final-lint.log.gz) passes. The build includes TypeScript validation. Application
and browser-test sources remain frozen after the green focused result.

The root's later native run found four obsolete source-shape expectations. Those four
tests now require the stronger creation/flight guards while retaining the old empty-pair,
depleted-node and recovery behavior. The CaldRece check uses a bounded function slice
instead of widening its fragile character window. The [updated native run](runs/native-after-guard-expectations.log.gz)
passes **177/177**, with zero skips, in 1117.160469 ms. No application or asset byte changed
for that expectation update; its exact test bindings are in the verification JSON.

## Rendered evidence

All four saved images were visually inspected. The failure text is readable, the relevant
retry action is visible with it, and the prior selected pair or completed score remains.
The existing mobile sticky HUD is unchanged and is not mistaken for the failure notice.

- [Desktop Lanț intro](screenshots/desktop-lant-intro-failure.png): Normal/Muzică selection survives and the notice stays beside Joacă.
- [Desktop live Alchimie](screenshots/desktop-alchimie-live-failure.png): the selected pair survives and Alt joc remains visible beneath the notice.
- [Mobile live Alchimie](screenshots/mobile-alchimie-live-failure.png): both the error and Alt joc remain in the short viewport.
- [Mobile completed replay](screenshots/mobile-alchimie-replay-failure.png): score 1000, record badge, error and replay/copy controls stay available together.

Initial failure screenshots and full traces remain in task scratch under `ui/initial-browser-results`
and `ui/retained-intro-browser-results`; their failures and actual logs are archived above.
Browser checks are not a human screen-reader or real-device usability study.

Raw logs are stored as lossless gzip archives. In verification.json, `log_sha256` binds
the decompressed original bytes and `archive_sha256` binds the archive. Tool-emitted
trailing spaces are preserved; no test output or judgment was rewritten.
