# ADR-0014: Conexiuni earned-group reveal

Date: 2026-07-10
Status: accepted

## Decision
Reveal a Conexiuni group's key, exact authored label, and four tiles immediately after
the server accepts that group as correct. Continue withholding every unsolved group and
the full `solution` array until terminal win/loss. Treat a guess as an unordered set and
reject an already-submitted set with HTTP 409 without changing lives, mistakes, clue
availability, score, or history.

## Context / why
ADR-0010 hid even a group the player had just proved, so its tiles vanished and the
existing locked-row UI stayed empty until the whole game ended. That removed the format's
main incremental “aha” reward without protecting any fact the player had not earned.
Separately, replaying the same wrong four tiles consumed another life and could unlock the
clue, turning an accidental duplicate into state-changing punishment. A full pre-terminal
solution remains rejected: earned disclosure does not justify exposing unsolved groups.

## Consequences
Web and mobile clients can render solved rows as persistent progress while the server
remains authoritative for all unsolved membership. Correct guess responses are complete
authoritative states, so the web client no longer needs a follow-up GET. Accepted history
stays bounded by the game itself (at most seven distinct correct/wrong guesses before win
or loss); the 6-hour sliding session TTL and 10,000-session LRU cap are unchanged. Contract
tests must assert both sides of the boundary: earned groups are present, unsolved labels
and membership are absent, and duplicate sets do not mutate the session.
