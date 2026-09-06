# ADR-0109: Defer dessert targets after fresh feedback review

- Status: accepted
- Date: 2026-09-06

## Context

V75 dropped Cozonac and Clătite as new easy Contexto targets because obvious
ingredients produced misleading feedback. V77 added two reviewed flour routes,
without promoting either target. A fresh broader review was required before
adding playable stock.

## Decision

Drop both V78 raw candidates before staging. Retain the current pack, graph,
rankings, frozen boards, vocabulary and editorial holds exactly. The complete
two-candidate screening and 68 actual API probes are archived in
[the V78 review](../reviews/v78-dessert-targets/README.md).

Flour now works, but Cozonac still makes Nucă cold and Clătite makes Gem frozen
while Dulceață is hot. Both targets meet the obvious-warm-opener threshold;
that numerical floor is insufficient to override misleading ordinary filling
guesses in a broad-audience easy round.

Do not invoke the pending-item promotion gate or allocate IDs for these dropped
raw candidates. This is a fresh batch disposition under ADR-0102, not a demotion
of approved content or a reversal of the factual V77 flour associations.

## Consequences

There is no new served content or runtime behavior in V78. Existing V77 technical
release evidence remains applicable, and focused checks and reproducible probes
add diagnostic evidence without claiming a fresh full integration run.

The next bounded repair hypothesis is the Contexto projection for Gem, which
currently borrows Miere. Independently review using the existing Dulceață concept
for feedback. Keep submitted `gem` distinct and nonwinning when its private anchor
is the target, while direct `dulceață` still wins normally. Preserve penalty and
anchor privacy, and measure effects across current targets before accepting any change. Nucă
requires a separate honest route; neither a repair nor a future target promotion
is pre-approved by this decision.

Human playtests and public rollout gates remain outstanding. Candidate count
does not override the reviewed quality standard.
