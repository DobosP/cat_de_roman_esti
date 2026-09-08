Valid until: V88 is superseded — then treat as history.

# V88 Lanț action recovery

A lost committed move, undo or hint now causes one owned GET. Failed verification keeps a
persistent read-only retry beside the input and disables mutations. A changed saved pointer
pauses the old screen before POST; unmount, new-round attempts and saved-game adoption
invalidate old callbacks. Recovered wins use the existing once-per-game score receipt.

Lanț retains only the current position's most recent explicitly requested hint payload.
GET and resume repeat exactly that help; they never calculate or spend another stage.
Accepted moves and real undo clear it; rejected moves and undo at the start preserve it.
The help counter remains capped at three for the session. Session capacity, TTL, locks,
move limits and scoring are unchanged. See [ADR-0128](../../../adr/0128-reconcile-uncertain-lant-actions.md).

The V87 ownership helper is renamed for both games. The helper and Contexto consumer are
exact after identifier changes; the Lanț hint computation is AST-identical after removing
the response-retention wrapper. [Preservation checks](preserved-behavior.json) bind this claim.

## Evidence

[Baseline proof](baseline-proof.json) records real BFF commits whose browser responses were
replaced with 503. GET could not recover the first earned direction and explicit retry
advanced to alternatives. A winning hop left the server won while the client had no result
and zero completed games. The original runner and output are retained as lossless gzip.

[Lane verification](verification.json) binds raw and archived hashes, final source and results:

- Eight new backend cases plus existing Lanț/session tests: **80 passed in 182.73s**.
- Frontend native: **193 passed**; lint and build passed, **118.92/120 KiB** initial budget.
- Actual BFF browser: **20/20 passed on the first run**, ten journeys per desktop/mobile.
- Four screenshot cases passed after adding settled-animation waits and a focused hint view.
  The first screenshots are preserved; no product behavior changed after the 20-case run.

Early command-directory mistakes and two pre-test line-length fixes are disclosed in the
verification record. No assertion, retry count, timing threshold or bundle limit was relaxed.
The parent version's full integration matrix and independent review are separate gates.

## Visual checks

The implementing agent inspected the mobile persistent retry and restored hint, plus the
settled desktop win. This is agent QA, not human playtesting.

- [Mobile read-only retry](initial-read-only-recovery-mobile.png)
- [Mobile earned direction](final-recovered-hint-mobile.png)
- [Desktop recovered win](final-recovered-win-desktop.png)

A read confirms current state without attributing changes to a particular request or tab.
Neutral recovery copy deliberately omits the lost move's transient correction/progress
verdict. The saved-pointer check is a browser ownership guard, not a distributed exactly-once
protocol. Existing horizontal HUD scrolling and voluntary Lanț help policy remain unchanged.
