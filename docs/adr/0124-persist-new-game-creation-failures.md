# ADR-0124: Keep new-game failures visible and preserve the previous round

Date: 2026-09-08
Status: accepted

## Decision

Show a persistent, shared Romanian notice when creating a new round fails in any of
the six games. Place it beside the existing start controls in the intro and inside the
shared result card beside its replay controls. Alchimie's in-round “Alt joc” action has
the same notice beside that footer. These locations are mutually exclusive, with one
alert per failure; a long result must not leave its notice above the player's viewport.
Reserve the notice's responsive space beside replay and Alchimie's live replacement
controls so displaying it cannot push the clicked button below the viewport. Unused
reserved text is invisible, has no alert role and is excluded from accessibility; the
intro keeps its compact conditional notice.
The existing free-play, daily and replay controls remain the retry actions; do not add
another start route or expose server messages, HTTP codes or technical instructions.

Each screen keeps only a client-side boolean for this failure. Clear it when the player
starts another attempt or successfully resumes an existing round. Set it if creation
fails. Preserve the selected options, prior server session pointer, completed score and
record feedback. Move replacement-only visual resets into the successful-create branch
so a rejected request cannot erase the old game's feedback or record indicators.
Keep the existing intro or round mounted while creation is pending so its action position
does not jump. Start-flight guards block duplicate creation and old-round action/keyboard/exit
callbacks; pending controls are disabled. Alchimie and Lanț distinguish saved-resume loading
from creation: the former can use their existing spinner, while the latter temporarily
makes the retained intro or round noninteractive.
Do not force-scroll the player to a header or notice.

Keep saved-game resume recovery separate: its current pointer checks, retry action and
durable fallback remain unchanged. A failed attempt to start fresh cannot forget a
saved game. Neither the failure notice nor retrying a creation spends an attempt, writes
a score or changes server session TTL, size limits, identity or gameplay rules.

## Context

All six start handlers previously reported failure only through a toast that disappeared
after 3.6 seconds. The shared intro already explained saved-game resume failures
persistently, but a failed new game could leave a player without an explanation after
that timeout. Several messages exposed HTTP codes or asked the player to inspect the
server. Four handlers also cleared prior visual feedback or record badges before the
replacement request had succeeded.

A shared small notice keeps the explanation available without adding another confirmation
step, retry button or dependency. Its alert semantics announce the failure; it does not
move focus or use a timer. Clearing it on a new attempt lets a second failure be announced
again. The existing bundle cap remains 120 KiB.

## Consequences

All six games consistently retain a failed-create explanation and remain retryable with
the same selected options. The previous finished result remains usable after a failed
replay. Browser coverage checks first-start failure, persistence beyond the old toast
timeout, preserved options and scores, successful retry, and failed replay recovery on
long desktop and mobile result screens. Alchimie's live replacement also blocks an
old-game action and Enter while the new request is pending. Existing saved-resume and
lifecycle checks remain applicable.

The notice reports a request failure, not proof that a disconnected server created no
session. The server's existing bounded session lifetime handles abandoned creations;
this change adds no new API, idempotency protocol, storage record or automatic retry.
