# ADR-0111: Promote the reviewed Clătite Contexto target

- Status: accepted
- Date: 2026-09-06

## Context

V75 and V78 deferred Clătite because ordinary flour and jam guesses produced
misleading feedback. V77 repaired the flour edge; V79 repaired Gem with a
bounded, independently reviewed Contexto policy. The target required a fresh
review rather than an automatic promotion following those repairs.

## Decision

Promote only `ct_gastronomie_320`, targeting existing `n_v3gas_clatite`, in
`gastronomie/usor`. The one-row candidate passes complete factual/quality
screening, strict pending critique and unanimous independent dossier-bound
analyst/verifier review. The supported pack-only importer, portable review
serializer and V2 applier implement the decision. Evidence is in
[the V80 review](../reviews/v80-clatite-target/README.md).

The accepted target has several specific warm batter, filling, dairy and
dessert paths. Reviewers explicitly considered frozen butter/oil/honey/nut
guesses and unresolved chocolate/dough. Those remain real vocabulary/feedback
limitations, but after repairing flour and both jam words they do not outweigh
the coherent core paths. Acceptance does not claim perfect feedback or human
enjoyment, and it does not relax the rubric for subsequent candidates.

## Consequences

Pack stock becomes 621 records: 613 approved and eight existing pending holds.
Contexto eligibility grows from 203 to 204. All 620 previous records, their
scores/status/eligibility and all 336 frozen derived boards remain exact.
KG nodes, edges, aliases, puzzles, mobile payload and runtime game logic do not
change. The generated ranking/derived metadata and trusted catalog digest advance.

Adding the target shifts 158 existing Contexto ordinal ranks by one and one
global selection-weight band. Filtered shelf weights are recalculated too.
Selection remains deterministic within the new artifacts; a seed or date may
select a different Contexto target across releases. Other games' sampled
selections are unchanged. The receipt records the exact differences.

Cozonac and bread remain deferred. An honest nut-feedback route is a separate
next investigation. Anonymous-beta external evidence and rollout authorization
remain governed by the existing release checklist.
