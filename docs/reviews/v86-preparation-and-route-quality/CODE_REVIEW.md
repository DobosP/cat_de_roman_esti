# V86 independent code review

Valid until: any bound source file changes — then treat as history.

Reviewed 2026-09-08 by v84_graph_research against baseline `14e8895` after the UI author’s source freeze. **Accepted with no remaining concrete blocker.** Exact source and consulted-test hashes are in [code-review.json](code-review.json). This reviewer changed only these two review artifacts and ran no tests.

The initial review found a real placement defect: a failed replay displayed its persistent notice under GameShell, above the viewport when the player had scrolled to a long result. `role="alert"` could announce the error but did not make it visible. The final implementation removes that banner and places the error beside ResultCard’s replay controls. Alchimie’s live “Alt joc” action receives the same adjacent feedback.

The final small fix reserves the notice’s actual responsive text and padding before a failure. Showing it therefore does not shift the clicked retry button below a short viewport. The invisible placeholder has no alert role, is hidden from assistive technology and has no focusable elements. Intro notices remain compact. Root reported the author’s final 16/16 targeted rerun passing for long-result replays, held live Alchimie replacements and the Lanț intro regression; the other ten initial-start cases passed unchanged in the preceding run. The frozen browser tests retain strict viewport assertions for both the notice and retry action. These are attributed results, not tests executed by this reviewer.

All six create handlers now have synchronous flight guards, catch failures without clearing prior game data and release pending state in `finally`. Successful creation is the boundary for changing the active pointer, replacing the round or resetting its feedback and record flags. Retry clears the old error, so another failure can be announced. Saved-session cancellation stops adoption of an obsolete resume response without forgetting its pointer. Existing score completion and conditional pointer cleanup remain unchanged.

Alchimie and Lanț separate new creation from saved-resume loading and retain their intro/round DOM while creating. This preserves scroll position and earlier result/progress instead of remounting a spinner. Pending controls are inert or disabled; exit/options handlers are guarded. Alchimie additionally guards live selection, combine, reset and clue handlers while its replacement request is pending. The notice uses generic Romanian copy and does not expose server diagnostics.

Lanț’s selection change reserves up to two available shortest continuations within the existing corridor before using its remaining quality-ranked slot. It keeps the three-corridor/six-total limits, direct playable edges, reachable targets, unvisited nodes, distinct normalized labels and stable public ordering. Public choices still carry only label and relation; no shortest-path metadata is exposed. The reviewed tests cover multiple alternatives, shuffled graph insertion order, exhausted corridors and real curated routes.

Contexto’s two additions are closed exact pairs: Ecler to Cremă de vanilie, and Savarină to Frișcă. The existing scorer retains submitted identity, prevents a borrowed target score from winning, preserves exact-self wins and checks that required nodes exist. The pair set does not traverse target neighbors or add reverse graph edges. Consulted tests exercise the whole-graph boundary, aliases/repeats, private state, exact wins and custom graphs missing a target.

The final full frontend/browser matrix was still running at archival time. This is independent code acceptance for the frozen sources, not final integration, rollout approval or a claim of human playtesting.
