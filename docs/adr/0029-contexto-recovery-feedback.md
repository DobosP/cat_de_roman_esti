# ADR-0029: Cald sau Rece recovery is persistent and fill-only

Date: 2026-07-16
Status: accepted

## Decision

Render ADR-0021 and ADR-0022's existing server-authored Cald sau Rece recovery fields in
the browser. Unknown concepts show their returned message and bounded `suggestions` in a
persistent warning card and polite atomic status. Each suggestion is a keyboard button
that fills and refocuses the input but never submits it. An accepted response's optional
autocorrection `message` remains visible as information, including inside a corrected
win result.

Clear stale recovery before the next guess and on Escape, clue, give-up, new-game,
restored-game, and options transitions. Expected unknown-concept feedback must not also
produce a transient error toast. Network and protocol failures remain toasts. Never
derive a suggestion or correction in the client.

## Context / why

The backend already returns up to three deterministic, de-duplicated suggestions and
removes any label resolving to the hidden target. It also names a confidently accepted
canonical label; a correction equal to the target is already a terminal win. The typed
client omitted both fields, so the screen reduced unknown input to a transient toast and
discarded accepted-correction acknowledgement. Players had to retype safe suggestions
and could not tell which concept a typo had actually played.

A 2024 Wordle experiment found that visible approach feedback improved positive affect
and motivation while repeated non-progress increased frustration
(https://www.nature.com/articles/s41598-024-74450-0). WCAG 2.2 status-message guidance
requires dynamic action results to be available without moving focus
(https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). Fill-only choices
preserve player agency; the exact Romanian presentation remains a product inference to
validate in playtests.

Auto-submitting a suggestion was rejected because it would spend an attempt without a
separate player decision. Client-side fuzzy matching was rejected because the endpoint's
target filter is the secrecy boundary and must remain authoritative.

## Consequences

Recoverable typos now require one selection plus an explicit submit instead of retyping,
and accepted autocorrections remain explainable through a win. The change is frontend-
only: unresolved guesses remain uncounted; accepted corrections, duplicates, scores,
clues, target reveal, two-hour TTL, and the 1,000-session cap are unchanged. Source-
contract tests pin the typed fields, live status, no duplicate toast, fill-only buttons,
winning message, and lifecycle resets. Playtests should measure typo recovery time,
accidental submissions, repeat guesses, and abandonment on mobile keyboards.
