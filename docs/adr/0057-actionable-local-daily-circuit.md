# ADR-0057: Make unfinished local daily-circuit rows actionable

Date: 2026-07-24
Status: accepted

## Decision

Render every unfinished Home daily-circuit entry as a 44-pixel-or-larger native button that
opens the existing intro for that game and carries a short visible `Joacă →` cue. Give the
button an explicit Romanian accessible name and a visible keyboard focus state. Keep a
completed entry as a non-action status row showing its retained daily score.

Do not auto-start the shared daily from Home. Preserve the intro's free-versus-daily choice,
the six-game order, and the circuit's local-only score source.

## Context / why

At 390×844, all six compact circuit rows fit in the first viewport and visually resembled
controls, but none was focusable or clickable. The equivalent full game cards extended to
roughly 1,400 pixels down the page, so a player had to find and scroll to a duplicate card
before choosing the daily challenge.

Deep-linking directly into a new daily session was rejected because it would bypass the
short beginner intro and require six new URL/session-start contracts. Making completed rows
clickable was rejected because their primary meaning is status, not the next unfinished task.

## Consequences

Mobile and keyboard players can move from the circuit to the correct game intro in one
action, while completed rows remain honest status. No aggregate, board identity, action,
telemetry, API call, score rule, or session behavior is added. The initial bundle remains
within its 120 KiB gzip budget.
