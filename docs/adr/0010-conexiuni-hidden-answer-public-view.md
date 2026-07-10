# ADR-0010: Conexiuni Hidden-Answer Public View

Date: 2026-07-04
Status: superseded-by ADR-0014

## Decision
Conexiuni create/get/guess/clue responses must use one hidden-answer-safe public view
model before terminal win/loss: public remaining tiles, solved/remaining counts,
status/clue fields, and safe guess feedback only. Category keys, exact category labels,
solved group tile membership, and full solution arrays are serialized only after the game
is won or lost.

## Context / why
The mobile Conexiuni shell is online-only and depends on the BFF staying
server-authoritative. Returning solved group rows or category labels before terminal
state lets a client reconstruct category membership even though the formal `solution`
field is absent. Contexto already centralizes its public rank view behind a reveal gate;
Conexiuni needs the same fail-closed serializer pattern.

## Consequences
Solved tiles disappear from the pre-terminal public board after a correct guess, while
progress is reported through `solved_count` and `remaining_groups`. Existing terminal
win/loss responses still reveal `solution`, score, and share data. Backend and mobile
contract tests must assert both the pre-terminal absence of category membership and the
terminal reveal boundary.
