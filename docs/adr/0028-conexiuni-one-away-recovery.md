# ADR-0028: Conexiuni one-away guesses retain their selection

Date: 2026-07-16
Status: accepted

## Decision

After an authoritative, nonterminal Conexiuni response with `one_away: true`, retain
the exact four submitted tiles. Store an order-independent client key for that set and
require the player to change at least one tile before another verification. Enforce the
guard in the submit callback, Enter shortcut, and Verify button; a duplicate `409`
response also restores and blocks the submitted set.

Do not identify or automatically remove a tile. Correct guesses, ordinary wrong guesses,
terminal responses, new games, and restored games clear the recovery state. The Golește
action may empty the visible selection but does not make the blocked set eligible again.

## Context / why

The server already returns a truthful one-away boolean and rejects a repeated four-tile
set without consuming a life. The browser displayed that feedback but unconditionally
cleared all four tiles, forcing players to reconstruct their attempt before testing a
one-tile change. That added avoidable motor and working-memory friction precisely when
the game had supplied useful progress feedback.

A 2024 Wordle experiment found that visible approach feedback improved positive affect
and motivation while repeated non-progress increased frustration
(https://www.nature.com/articles/s41598-024-74450-0). Research on in-game hint design
also supports scaffolding that preserves player agency
(https://doi.org/10.1145/3025171.3025224). Retaining the set is a product inference from
those principles and must still be validated in Romanian playtests.

Automatically deselecting the wrong tile is not an option: `one_away` does not identify
it, and doing so would invent or leak hidden membership. Allowing an unchanged retry is
also needless; the backend must keep its `409` defense, while the browser can prevent
the avoidable request.

## Consequences

One-away recovery now takes a two-click swap instead of rebuilding four selections, and
the guidance remains visible while editing. The change is frontend-only: four mistakes,
duplicate protection, group secrecy, scoring, the two-hour TTL, and the 1,000-session cap
are unchanged. Source-contract tests pin snapshot restoration, terminal clearing, set
equality, and all three submission guards. Playtests should measure retry time, duplicate
attempts, abandonment, and whether the retained selection is understood without focus
movement.
