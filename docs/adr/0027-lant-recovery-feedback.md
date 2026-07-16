# ADR-0027: Lanț recovery feedback is persistent and actionable

Date: 2026-07-16
Status: accepted

## Decision

Render ADR-0022's server-authored Lanț recovery fields in the browser instead of
discarding them. Keep dead-end/autocorrection/unknown-concept feedback visible in a
polite live status region. Render bounded fuzzy suggestions and the named alternatives
from a second same-position hint request as keyboard buttons that fill, but never submit,
the existing input.

Clear stale recovery feedback on the next move, undo, hint request, or new game. Do not
auto-request help, reveal an unrequested route, change scoring, or change session TTL or
capacity.

## Context / why

The backend already returned `message`, `dead_end`, `suggestions`, and
`alternatives_labels`, with behavior and tests pinned by ADR-0022. The typed client
omitted those fields and `Lant.tsx` therefore discarded them. A player could legally enter
a dead end or ask twice for alternatives while receiving no durable browser feedback.

This closes a presentation gap. A 2024 Wordle experiment found that visible approach
feedback increased positive affect and motivation, while repeated non-progress increased
frustration (https://www.nature.com/articles/s41598-024-74450-0). Wikispeedia route data
also records orbiting and back-click recovery in comparable navigation play
(https://ai.stanford.edu/~jure/pubs/wayfinding-www12.pdf). These findings support the
principle; the exact Romanian UI remains a product inference to validate in playtests.
WCAG 2.2 status-message guidance requires dynamic action results to be programmatically
available without moving focus
(https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

## Consequences

Lanț feedback now survives transient toasts and works without color or pointer-only
interaction. Stronger help remains voluntary and staged. The change is frontend-only:
server authority, hidden-path boundaries, moves, score, fixture content, two-hour TTL,
and 1,000-entry store cap are unchanged. Frontend source tests pin the typed fields, live
status semantics, and actionable alternatives; Romanian playtesting should measure
repeated invalid moves, hint reuse, undo-after-dead-end, and abandonment.
