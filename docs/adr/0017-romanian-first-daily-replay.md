# ADR-0017: Romanian-first daily and replay contract

Date: 2026-07-10
Status: accepted

## Decision

Present the arcade in natural Romanian with diacritics while keeping ASCII wire tokens
and game keys stable. Every daily request carries the selected difficulty, so the puzzle
is shared among players on that difficulty; category selection applies only to free play
and is labelled accordingly. At every result screen, “Încă unul” starts a fresh
same-difficulty/same-category free game immediately, while “Schimbă opțiunile” returns to
setup and “Meniu” returns home.

## Context / why

The four screens had drifted into three replay behaviors, and Alchimie plus Cald sau Rece
silently discarded the selected difficulty for daily play while Lanț and Conexiuni kept
it. The tooltip nevertheless promised one universal puzzle and category controls gave no
warning that dailies ignore them. Romanian copy also mixed unaccented text, borrowed
English hooks, a stale 330-concept count, and an Alchimie instruction that called its
visible target hidden. A single difficulty-independent daily was rejected because it
would discard an existing, meaningful player choice and change the established Lanț and
Conexiuni contract.

## Consequences

Daily identity is `(date, game, difficulty)`, not category; copy states that boundary.
Replay is one action without losing the chosen free-play filters, but options and menu
remain explicit. Existing API enums such as `usor`, `Gasit`, and `Inghetat` do not change;
the client maps them to `Ușor`, `Găsit`, and `Înghețat`. Local score identifiers and
server storage are unchanged; copied results use the Romanian brand and omit the internal
puzzle key. Session bounds remain six hours and 10,000 entries per game.
