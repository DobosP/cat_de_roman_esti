# ADR-0048: Keep Conexiuni recovery beside the active board

Date: 2026-07-19
Status: accepted

## Decision

Render wrong-group, one-away, and earned redacted-clue messages in one compact live
status immediately after the sticky `ACUM` coach and before the unsolved tile grid.
Derive that status only from the existing server-authored `one_away`, duplicate error,
and `clues[].message` fields. When a clue succeeds, clear generic local wrong-guess copy
and do not repeat the clue in a success toast. Keep the retained one-away selection,
free shuffle, exact-retry block, and server-authoritative clue unchanged.

Show the four-mistake budget as four tiny, colour-independent dots with an accessible
Romanian count beside `Verifică` in the sticky coach. A spent dot becomes outlined and
dimmed; it never replaces the text alternative. Keep the existing HUD badge as a wider-
screen summary. Do not derive or render an unsolved category, tile membership, or solution
identifier in either progress element.

## Context / why

At 320 px the two-column board is roughly a full phone viewport tall. The former recovery
and clue rows came after that board, so the most useful correction could be below the fold
while the player was choosing a replacement. One clue action also wrote the same message
to local feedback, the authoritative clue row, and a toast. Repetition added vertical text
without adding information.

The English Connections loop keeps mistakes, selection, submission, near-miss feedback,
and shuffle close to the active 16-word decision surface
(https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections).
Moving already-earned feedback is safer than identifying the incorrect tile or restoring a
client-inferred group, both of which would leak membership.

## Consequences

Phone players see one short recovery channel before scanning the board and can read their
remaining budget without returning to a horizontally scrolled HUD. `aria-live` announces
the combined status once, and the dots carry an explicit accessible count. Backend state,
API operations, hidden-answer boundaries, scoring, daily determinism, two-hour session TTL,
1,000-session cap, and response sizes are unchanged. The final integration build must ship
the updated tracked static bundle and keep the 120 KiB initial gzip budget green.
