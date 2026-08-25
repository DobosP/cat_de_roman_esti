# ADR-0094: Keep game exit reachable and make beginner entry explicit

Date: 2026-08-25
Status: accepted

## Decision

On narrow screens, keep the shared game header sticky below the device safe area and offset
each game's secondary sticky controls below that header. Label the shared action `Ieși` and
replace the current route when it returns to the lobby. For Conexiuni, an explicit exit from
the intro, board, or result forgets only the Conexiuni resume pointer before leaving; reload
continues to resume a live board. Keep Conexiuni feedback and earned clues in normal flow
immediately before the grid, so only the compact next-move coach remains sticky.

Recommend Intrusul as the lobby's sole `Începe aici` game. Explain all three Conexiuni
difficulties as `grupuri clare`, `mix echilibrat`, and `legături subtile`. This supersedes
only ADR-0052's lobby-recommendation clause; its derived catalogs, ranking, gameplay,
session, and scoring contracts remain accepted.

## Context / why

A 360 × 430 browser reproduction showed the non-sticky game exit above the viewport after
scrolling, while Conexiuni's sticky recovery stack grew when feedback and clues appeared.
The old Conexiuni exit also pushed a new history entry and retained
`cat_active_game_v1_conexiuni`, so browser Back reopened the board the player had explicitly
left. Clearing every game pointer or deleting the server session was rejected: the bug is a
single-game navigation intent, and refresh recovery remains useful.

Alchimie's earlier recommendation was an explicit pre-playtest hypothesis. Intrusul has a
strict starter shelf and a one-tap, one-choice first turn, making it the narrower truthful
entry point. A broad lobby redesign and claims of measured enjoyment remain out of scope.

## Consequences

Exit remains reachable while a mobile board scrolls, secondary sticky controls cannot cover
it, and safe-area inset keeps both surfaces below a notched viewport. Browser Back cannot
resurrect a deliberately exited route, while reload and non-exit revisits retain the existing
best-effort resume behavior. The change is frontend-only: server sessions, TTL/cap, game
payloads, catalogs, scoring, content, accounts, and deployment contracts do not change.
