# ADR-0006: Conexiuni Redacted Clue

Date: 2026-07-04
Status: accepted

## Decision
Conexiuni may offer one server-authored clue after two mistakes: a redacted label pattern
for one remaining category, with a score penalty and no category key, exact category
label, tile ids, or membership before win/loss.

## Context / why
Players can get stuck after repeated wrong groups, but returning an exact category label
would expose part of the hidden answer. A pattern such as `L_________` gives useful
shape without revealing the solution or moving category logic into the client.

## Consequences
The mobile/openapi contract includes the additive `conexiuni_clue` operation. Tests must
keep asserting that pre-finish clue responses contain only redacted clue text and never
solution membership.
