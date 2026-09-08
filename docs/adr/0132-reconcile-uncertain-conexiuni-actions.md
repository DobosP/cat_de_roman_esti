# ADR-0132: Recover uncertain Conexiuni guesses and earned clues

Date: 2026-09-08
Status: accepted

## Decision

Conexiuni guesses, clues and read-only verification share the existing synchronous
`gameActionRecovery` owner. A failed mutation triggers one GET of the same session and
never automatically replays its POST. Only a current ticket owning the saved round may
adopt the returned state. Failed verification leaves a persistent “Verifică jocul” button
and locks selection, submission, clues, clearing and shuffling until an authoritative read
succeeds. A different saved pointer pauses the old screen before mutation and offers
“Încarcă jocul curent”. Unmount, new-round attempts and saved-game adoption invalidate old
tickets; a stale completion cannot release another action's lock.

The existing GET already supplies all earned category groups, redacted clues, mistake
counts and terminal scores. Apply these fields as a complete state and remove selected
ids that are now solved. Recover wins and losses through the unchanged once-per-game
score receipt. The transient `one_away` verdict is not in GET: display neutral synchronization
copy instead of inferring it from a changed mistake count or reconstructed membership.
An explicit 409 duplicate rejection can still retain and block the submitted combination,
provided all four ids remain unsolved after GET; its message never claims three-of-four.
Keep this bounded duplicate context through failed verification so a later read preserves
the same restriction. An ordinary successful one-away response retains its existing
selection, change-one-piece guidance and order-independent duplicate-set behavior.

An ordinary live-board exit conditionally forgets only its own saved id. An exit during
an action or unresolved verification preserves that pointer for normal resume. A confirmed
owned 404 returns to setup and conditionally removes the missing id. Terminal score
completion retains its existing conditional cleanup. Storage-unavailable local play uses
the existing owner's stable-null rule; another remembered game always takes precedence.

## Context

Four actual browser/BFF baseline cases allowed a clue, correct group, final win or final
loss to commit, then replaced only the response with 503. None caused a verification GET.
The earned clue remained absent, a solved group left all sixteen tiles selectable, and
terminal results remained invisible with zero recorded games. After three mistakes, the
natural retry of the first lost clue consumed clue two and reduced the eventual score from
150 to 50. A GET could already recover this exact earned state without charging again.

The V87/V88 shared helper supports this ownership and read-only recovery contract unchanged.
Conexiuni needs no server response or retained-session field expansion. Its old recovery
only attempted GET for HTTP 400/409, leaving network and 5xx uncertainty unresolved.

## Consequences

Lost actions recover their earned results without another clue payment or automatic guess.
A failed read visibly pauses play instead of inviting mutation retries against stale state.
Private unsolved group membership remains unavailable until the existing terminal reveal.
Session TTL 7,200 seconds, maximum 1,000 sessions/game, per-session locks, 64 KiB request
limit, four mistakes, two clues, duplicate-history bounds, category selection and scoring
are unchanged. The shared helper and other game consumers are unchanged.

GET confirms current state and does not identify which request or browser changed it.
The saved-pointer guard is browser ownership protection, not a distributed exactly-once
protocol. Native ownership tests remain shared; focused real-BFF desktop/mobile journeys
cover response loss, failed verification, clue economics, terminal scoring, duplicate
feedback, selection retention, missing sessions and cross-tab/unmount outcomes.
