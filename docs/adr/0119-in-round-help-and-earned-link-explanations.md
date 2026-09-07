# ADR-0119: Keep rules available and explain earned Alchimie connections

- Status: accepted
- Date: 2026-09-07

## Context

All six games hide their introductions once a round starts. A player who forgets a rule
must leave the round to read it again. Alchimie stores the parents of a discovered idea,
but does not expose the actual graph relations explaining the result.

## Decision

Provide a closed-by-default native rules disclosure below each live game's header, with
short Romanian guidance specific to its goal, feedback and recovery actions. Opening help
does not call an API or change attempts, selection or scores. Native summary elements are
interactive keyboard targets and must be excluded from global Enter-to-submit handlers.

For earned Alchimie inventory concepts, return at most two actual oriented graph links
connecting their already owned parents and result. Preserve the authored source, target
and relation label. Omit missing, blank, distractor or mismatched edges; do not manufacture
an explanation. Seed concepts expose no earned links. The response adds optional `links`
data for clients and derives it from existing lineage without additional session storage.

Show those connections in the discovery journal and winning recap, including after resume.
Only already visible concepts appear; private targets and other undiscovered recipe results
are not included. A graph association describes the connection rather than asserting that
every craft is a physical or culinary recipe.

## Consequences

Players can consult rules while retaining progress and inspect why a discovered connection
exists. Six-game keyboard/mobile tests cover the disclosure, state preservation and overflow;
Alchimie checks cover relation direction, privacy and reload persistence. Scoring, game/session
bounds and mechanics remain unchanged by these interface and explanation additions.
