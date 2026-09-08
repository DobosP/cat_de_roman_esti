# ADR-0128: Recover uncertain Lanț actions and already-earned help

Date: 2026-09-08
Status: accepted

## Decision

Lanț move, undo and hint requests share one synchronous action owner with read-only
verification. A failed mutation triggers one GET of that same session; it never replays
the mutation. Only a still-current ticket owning the expected saved pointer can adopt the
complete state. Failed verification retains a persistent “Verifică jocul” button and locks
all moves, hints and undo until a successful read. Another saved pointer pauses the old
screen before POST and offers “Încarcă jocul curent”. Missing-session cleanup remains
conditional on ownership. Leaving preserves the saved pointer for ordinary resume.

Generalize the exact V87 owner/reconciliation helper as `gameActionRecovery`. Contexto
uses its renamed exports with its existing behavior, so the two screens share ticket,
storage-unavailable, stale/unmount and foreign-pointer handling. A new round attempt or
saved-game adoption invalidates old tickets; stale cleanup cannot unlock a newer action.
Recovered Lanț wins use the existing server score and once-per-game receipt mechanism.
A recovered nonterminal state receives neutral synchronization copy; it does not fabricate
the move's direction, typo correction or other transient verdict.

Lanț sessions retain one optional `earned_hint` payload: the exact most recent explicitly
requested help for the current chain position. GET and ordinary saved resume can repeat
that payload without calculating or consuming another stage. Before the first voluntary
hint and after an accepted move or real undo the field is absent. Invalid moves and undo
at the start preserve it. Moves and undo continue to preserve the capped, session-wide
`hint_requests` scalar. A fresh request replaces the single payload; there is no per-node
cache or hint history. Won sessions retain no position hint. Requested dead-end and
64-move-limit backtrack messages are recoverable through the same optional field.

## Context

An actual browser/BFF baseline sent a hint, allowed the server to commit it, then replaced
only its response with 503. GET had no earned hint, and the natural retry advanced direction
to alternatives without the player receiving the first stage. The corresponding winning
hop probe left the server won while the client showed no result and recorded zero games.

The prior Contexto implementation supplies the same ownership semantics. Lanț additionally
needs authoritative earned-help state: reconstructing help from a stage counter at a new
position would reveal unrequested content, while resending the hint would consume a stage.
Retaining one current payload recovers exactly what the player already requested.

## Consequences

Help can survive a lost response or page reload without additional requests. The optional
field contains only already-earned material; choice-route metadata and unrequested hint
stages remain private. It is bounded by existing hint shapes: at most two named alternatives
or one hop, plus fixed scalar fields and server-authored messages. Session TTL 7,200 seconds,
maximum 1,000 entries/game, per-session locks, request limits, move cap 64, help cap 3 and
scoring are unchanged. This adds no backend mutation-replay or distributed exactly-once
protocol; GET confirms current state under the existing session lock.

Focused backend tests cover exact stage recovery, read privacy, clearing on movement,
retention after rejected/no-op actions, capped help and terminal cleanup. Actual desktop
and mobile browser tests cover committed response loss, read failure, win scoring, undo,
resume and stale/foreign-pointer outcomes; shared helper tests retain Contexto coverage.
