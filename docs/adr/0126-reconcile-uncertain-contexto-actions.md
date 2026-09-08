# ADR-0126: Reconcile uncertain Contexto actions without replaying them

Date: 2026-09-08
Status: accepted

## Decision

After a failed Cald sau Rece guess, clue or give-up request, read the same session once
through the existing authoritative GET. Adopt only the complete server state for that
session while the operation still belongs to the displayed screen and expected saved
pointer. Never automatically replay the mutation, infer a score, reconstruct an answer
or substitute the previous client state for a failed read.

Use one synchronous action ticket across all three mutation types and manual verification.
Tickets are invalidated on unmount, a new-round attempt or adoption of a saved game. Old
callbacks cannot update state or release a newer operation's busy flag. A late response
for another game ID is rejected. An already different saved pointer is detected before
sending a POST, so an old visible round cannot spend an action and then lose its response
solely because another tab had already saved a newer game.

If verification also fails, retain the typed input and show a persistent, read-only
“Verifică jocul” action. Disable guesses, clues, give-up and options until verification
succeeds; this prevents a blind second paid clue or a guess against a stale terminal
state. If the saved pointer changed, explicitly offer the existing saved-game loader
through “Încarcă jocul curent”. That action selects the current pointer afresh and keeps
the existing saved-resume ownership checks.

An exit while an action is pending or unconfirmed preserves its saved pointer so ordinary
resume can recover the outcome. Confirmed live exits/options and missing-session cleanup
use `forgetIfCurrent`, never an unconditional pointer deletion. A verified 404 returns to
the intro without deleting another tab's saved game. A locally owned round can still
recover when browser storage is unavailable and both saved-pointer observations are null.

Recovered wins/give-ups use the existing terminal effects and score-receipt ledger. Only
the server reveals terminal answers or supplies scores. An adopted win is recorded once;
unmount or a changed pointer cannot make an old recovery overwrite a new round.
The nonterminal recovery message is neutral because a GET confirms current state, not
which tab produced every change. No specific comparison feedback is invented.

## Context

An actual-BFF probe forwarded a winning guess and then replaced its response with a 503.
The server had won and awarded 1000, while the client showed no result and recorded no
completed game. Retrying the answer returned “game finished” and left the client stuck.
A second probe lost the response of a committed clue: natural retry consumed clue two
while the player had not received clue one. Existing tests only simulated a failure
before the BFF mutated and then reloaded the page.

Intrusul and Perechi already used authoritative recovery. Lanț and Alchimie have terminal
mutation responses that can recover on retry; Conexiuni refreshes known stale rejections.
This change targets Contexto's reproduced gap rather than cosmetically editing all games.
The shared `recoverAuthoritative` and single-flight primitives are reused. The new owner
holds only one frozen ticket; there is no accumulating history or new storage document.

## Consequences

The frontend handles committed and uncommitted failures, failed verification, terminal
adoption, missing sessions and stale ownership without extra mutation calls. The route
continues to use existing API fields and the server's bounded session behavior: 7,200-second
sliding TTL, 1,000 sessions per game, 64 KiB requests, score formula and private-answer
boundaries are unchanged. Other games and their recovery flows remain untouched.

Tests use controlled promises for ticket ownership and actual browser/BFF mutation loss
for the player journeys. A successful GET is a snapshot, not a distributed exactly-once
protocol; this decision adds no automatic retry or new backend idempotency mechanism.
