Valid until: V89 is superseded — then treat as history.

# V89 Conexiuni action recovery

A lost committed guess or clue now causes one owned GET. A failed read leaves persistent
verification and locks all board actions until the player can read current state. Recovered
groups and clues are exactly those already earned; recovered wins/losses use the existing
server score and once-per-game receipt. No mutation is automatically replayed.

[ADR-0132](../../../adr/0132-reconcile-uncertain-conexiuni-actions.md) records the policy.
[Preservation checks](preserved-behavior.json) bind twelve exact baseline files: shared
owner, previous consumers, active/resume/score hooks, request handling and Conexiuni API/server.
No backend field, private reveal, session bound, scoring rule or clue economy changed.

## Actual before/after evidence

[Baseline proof](baseline-proof.json) records four actual BFF commits whose browser replies
were replaced with 503. The client issued no recovery GET: the earned clue remained absent,
a solved group left sixteen tiles, and final win/loss left no result and zero recorded games.
Explicitly retrying the first lost clue after three mistakes consumed clue two; solving the
board then scored **50 rather than 150**. The exact runner and log are retained as lossless gzip.

The final browser suite covers thirteen journeys on each desktop/mobile viewport:

- Earned clue recovery, exact saved resume and a **150-point** finish with one clue.
- Solved-group recovery with only its four tiles removed and unsolved answers still private.
- Won and lost terminal states, exact scores, single receipt and conditional pointer cleanup.
- Persistent failed verification; all board controls locked; manual retry issues only GET.
- Failure before commit preserves the valid selection and prior earned clue.
- Late win/404 against another saved round, exit during recovery and preexisting foreign pointer.
- Missing owned session recovery; neutral lost one-away feedback and duplicate restrictions,
  including a duplicate rejection whose first verification read also failed.

The full group/clue selection and ordinary one-away mechanics remain intact. GET cannot
reconstruct `one_away`; synchronization copy makes no such claim. A server-confirmed 409
retains a still-visible duplicate set with neutral change-one-piece guidance, even through
a failed verification. This context holds only four selected ids and one server message.

## Verification and initial failures

[Verification](verification.json) binds exact source hashes, commands, raw/archive hashes,
screenshots and the following completed lane checks:

- **193 native tests**, ESLint and TypeScript/build passed; **118.92/120 KiB** initial budget.
- **26/26 actual BFF browser journeys** passed in the corrected behavior run (2.2 minutes).
- **2/2 stricter screenshot checks** passed after asserting the outer screen animation settled.

The initial native run passed 186/193: seven source-shape assertions still described the
old error refresh/exit behavior and were updated to assert owned recovery and conditional
cleanup. The initial browser run passed 18/26: eight locators omitted the existing decorative
arrow from exact feedback text. Status-scoped locators corrected this; product code did not
change. The failed run's original spec, full output and eight error contexts/screenshots are
preserved. Three npm commands ran from the repository root and failed before running a check;
their exact logs are also retained. No retries, timeouts, budgets or assertions were weakened.

Independent visual review caught blank desktop read-only screenshots: mocked time had
advanced without enough animation frames to finish the outer screen transition. The final
screenshot case advances 500 ms of mocked frames and asserts exact screen opacity. The
26-case passing spec is separately archived; this stronger two-case check uses the final
spec. The initial desktop win clipped its result inside the scroll container, so the passing
behavior run scrolls its actions into view and waits for the resume toast to leave.

## Visual review and limits

The implementing agent inspected the final desktop verification card and recovered win,
and the mobile earned clue. These are agent checks, not human playtesting.

- [Desktop persistent verification](final-read-only-recovery-desktop.png)
- [Mobile persistent verification](final-read-only-recovery-mobile.png)
- [Desktop recovered 1000-point win](behavior-recovered-win-desktop.png)
- [Mobile earned clue](behavior-recovered-clue-mobile.png)

The existing mobile HUD scroll and transient resume-toast overlap remain. GET confirms the
current session without identifying which request or browser changed it. Saved-pointer
ownership is a browser guard, not a distributed exactly-once protocol. The parent version's
full integration matrix and independent review remain separate from this focused lane.
