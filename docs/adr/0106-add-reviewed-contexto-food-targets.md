# ADR-0106: Add two reviewed Contexto food targets

- Status: accepted
- Date: 2026-09-06

## Context

V51–V72 added accepted vocabulary without increasing eligible playable stock. A bounded
five-candidate gastronomie/usor batch tested whether familiar existing KG concepts could
support useful Contexto rounds without changing topology.

## Decision

Promote only `ct_gastronomie_318` (Mici) and `ct_gastronomie_319` (Salată de boeuf),
following independent factual screening, quality filtering, strict pending lint and
dossier-bound analyst/adversarial verification. The supported pack-only importer and V2
applier implement the decision. Evidence and rejected candidates are preserved in
[the V75 review](../reviews/v75-contexto-food/README.md).

The other three raw candidates are dropped before staging because ordinary ingredient
or holiday guesses provide misleading feedback. They do not become approved-stock
demotions. The existing editorial holds and rejection ledger remain intact.

## Consequences

Eligible Contexto stock increases from 201 to 203; the original-game total from 448 to
450. KG nodes, edges, aliases, puzzles and all 336 frozen derived boards stay unchanged.
Generated rankings reorder Contexto ordinals and move four existing weight bands, without
changing any existing quality score, approval or eligibility. Seeded and daily selection
can consequently choose a different Contexto target after this content release; within
the same artifacts it remains deterministic. Other games' selection is unchanged.

The KG build remains V72 because this is a pack-only wave. Pack, ranking and derived
wrapper digests identify the new release content. Automated evidence establishes technical
playability and editorial review; Romanian-player enjoyment remains a separate beta gate.
