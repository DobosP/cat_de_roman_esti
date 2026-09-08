# ADR-0138: Owned Intrusul and Perechi action recovery

- Status: accepted
- Date: 2026-09-08

## Evidence

Clean-main V90 browser/BFF reproduction found that both derived games already recover
lost committed guesses, matches, clues and terminal results through one GET. Paid clues
survive resume; hints are capped at one. No backend clue addition or second-charge fix
is needed. Their failed recovery reads, however, release stale board controls with no
persistent verification action. Held successful winning POSTs and recovery GETs can
adopt and record an old terminal round after another tab saves a different round.
A wrong response identity is also adopted, and owned 404 leaves the stale board saved.

Releasing a held win immediately after Exit exposes the same adoption during the exit
animation. Waiting for actual unmount first does not reproduce a score write. Two initial
browser Back probes also passed, but the later desktop/mobile regression reproduced
scoring during Back departure in both games. Both observations are retained. These are
exit-boundary races, not evidence that React records results after unmount. The raw
baseline and final focused evidence live in
[the V91 derived recovery review](../reviews/v91-recovery-and-mobile-clarity/derived-recovery/README.md).

## Decision

Intrusul guess/hint and Perechi match/hint reuse the existing game-action owner
([ADR-0136](0136-reconcile-uncertain-alchimie-actions.md)). One synchronous ticket binds each action to its displayed game and saved
pointer. Successful POST adoption and recovery reads check ticket, pointer and response
identity. Exit, unmount, resume and new-round setup invalidate outstanding ownership.
Animated departure also invalidates ownership in a layout effect when screen presence
ends, before passive focus or score effects. Actions and terminal recording require
screen presence; Perechi clears queued focus when departure begins.

An uncertain action performs one GET, never a mutation replay. A failed GET retains one
bounded pending-action snapshot and a visible “Verifică jocul” control. Tiles, hints and
selection clearing stay disabled until an owned verification succeeds; each manual retry
performs one GET. Retry tickets retain the original saved-pointer observation; a pointer
removed between attempts cannot become the initial null-storage fallback. Server-earned
attempts, solved pairs, clues and terminal state remain
authoritative. The existing result recorder records a recovered terminal result once.

An owned 404 conditionally forgets only its matching saved pointer and returns to setup.
A changed pointer freezes the old board and offers loading the current saved round,
including an empty saved pointer. Perechi defers focus only for accepted replies and
checks the game and pointer again before moving it to another tile or result control.

No backend, public response schema, content, score formula, TTL, capacity or request-size
change is part of this decision. The existing 7200-second sliding TTL, 1000 sessions/game,
locks, 64 KiB request bound and game-specific history and hint caps remain unchanged.

## Verification

Final focused coverage passes 80 desktop/mobile browser variants without retries and
26 native checks; typecheck and focused lint pass. Independent review accepts the
implementation after four exact Back cases and two pointer-retry cases pass on the
final build. Both passing and failing historical observations remain source-bound in
the linked review; final integration and landing receipts belong to STATUS.
