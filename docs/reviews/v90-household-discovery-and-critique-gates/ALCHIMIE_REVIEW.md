Valid until: reviewed Alchimie behavior source or tests change — then re-review; final V90 integration is a separate gate.

# Independent Alchimie review — accept

Reviewed 2026-09-08 without implementation authorship. **No blocking findings.** The
bounded recovery and earned-cue contract are accepted at the exact source pins in
[ALCHIMIE_REVIEW.json](ALCHIMIE_REVIEW.json). The worktree was at `be4a441` with the
uncommitted Alchimie lane above clean V89 main `190d7fd`; this review makes no final
V90 graph/content or landing claim. No source, test, fixture or author evidence was edited.

## Behavior reviewed

Combine, hint and reset acquire the unchanged synchronous action owner before POST.
Successful replies and verifying GETs must retain their ticket and saved-round ownership.
Recovery performs one GET and has no mutation replay callback. An owned missing game
conditionally clears only its own pointer; changed, stale and unmounted replies cannot
adopt state or clear another round. Only the current ticket releases its lock.

Failed reads leave persistent verification and disable inventory selection, occupied-slot
removal, clearing, keyboard combine/clear, hint and reset. A retry reads only; fresh-round
navigation invalidates old tickets. GET adoption uses authoritative inventory and neutral
synchronization feedback because GET lacks the lost combine's transient verdict. Normal
successful empty/free-repeat feedback remains intact. Recovered terminal state follows
the existing once-per-game score receipt, explicitly verified by the authored win journey.

The server keeps exactly one four-field `earned_hint`, assembled from its own successful
public hint response. Output cues expose a non-target label; pair cues expose already-owned
concepts. There are no new hidden output/target ids, recipe maps, routes or cue history.
Paid hints replace the cue; GET, rejected actions and free repeated pairs preserve it;
new unique productive/empty/winning combinations and reset clear it. The defensive
no-forward branch clears obsolete state without charging. The eight new backend cases
exercise this lifecycle through Django's client. AST comparison confirms unchanged
session methods, including score, plus unchanged imports, constants and routes.

The 7,200-second sliding TTL, 1,000 sessions per game, session locks, 64 KiB request cap,
32-concept workspace, 496-pair memory and 12-reaction browser journal are preserved.
Fourteen shared/other-game files match baseline bytes, including action transport,
resume/score hooks, session store, request handling and all five other game screens.

## Independent evidence checks

- Verified all 10 lane source pins, 18 pregraph development pins and eight clean-main
  baseline pins. The four raw baseline captures exactly match the assembled proof:
  each mutation committed, with zero browser GETs; a paid cue was absent from GET.
- Verified all 43 gzip archives against their archive hashes, decoded hashes/lengths,
  zero gzip mtime and original scratch bytes. All 29 images match hashes, lengths and
  original bytes. The original native/browser failures remain losslessly preserved.
- Inspected raw passing receipts: 74 focused backend, 193 native, 32 browser cases,
  lint/typecheck/build and 118.88/120 KiB bundle. Initial/final browser specs differ only
  in the corrected exit name and waiting for the transient resume toast to disappear.
- Visually inspected all ten final desktop/mobile screenshots: inventory, paid output
  cue, paid pair cue, win and failed-read retry. The cue appears once, pair selection and
  the 1,000-point result are legible, and retry is visible. Existing mobile HUD scrolling
  and sticky controls remain; no human/device acceptance is implied.

The authored browser case covers one failed verification followed by a successful retry.
I added a separate scratch-only probe for repeated failures: the initial GET plus two
manual retries fail, two synchronous retry clicks still issue one GET, selected ingredients
remain on the locked bench through Escape/Enter, and the fourth GET restores the paid clue.
Both desktop/mobile cases pass on the first attempt: **2 passed in 15.9 s**, zero retries,
**four reads / one mutation / one hint charge**. Node 24.19.0 and Python 3.12.3 served the
current generated app on port 8189; the port was unbound before and after, with no reused
server. Exact commands, source bindings, receipts and lossless archives are in the JSON.
The authored lane used Node 24.20.0; this independent probe did not rebuild the app.

The baseline directly captures missing result UI, not a local-score-store snapshot;
absence of score recording follows from the unchanged won-state effect. The final win
journey explicitly verifies the local play count stays one after reload. This distinction
does not change the demonstrated recovery defect or accepted fix.

Final backend/runtime/accounts, content and frontend integration gates still belong to the
parent version after graph/content freeze. These pregraph development pins are historical
evidence after that integration. GET confirms current state without attributing it to a
particular request or browser. No push, deployment, contact or production test occurred.
