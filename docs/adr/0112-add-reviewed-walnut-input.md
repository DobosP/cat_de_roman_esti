# ADR-0112: Add a real walnut input with bounded Contexto feedback

- Status: accepted
- Date: 2026-09-06
- Partially supersedes ADR-0033's three-edge fan-out cap only for the new Nucă node below.

## Context

V80 left Cozonac deferred because Nucă borrowed Miere and gave cold feedback.
The graph described walnuts in several recipes but had no walnut concept.
Both a one-edge and a four-edge unrestricted graph simulation made unrelated
savory targets warm; the latter also spread warmth to places and historical
figures. Correct recipe facts alone did not make unconstrained feedback safe.

## Decision

Add exactly one canonical culinary node, `n_v81_food_pantry_nuca` (Nucă), at
editorial salience 0.90, with the sole reviewed alias `nucile`. Canonical accent
normalization already accepts `nuca`. Keep ambiguous fruit/tree forms `nuci`,
`nucii`, `nucilor`, tree names, kernel part/whole phrases and coconut separate.

Add four outgoing, non-distractor, one-way `part_of` edges labeled `ingredient
pentru`: Cozonac and Colivă at 0.97, Baclava dobrogeană at 0.95, and Cornulețe at
0.90. These are source-supported common preparations, not claims about every
recipe. The weights are editorial association estimates, not quantities or
probabilities. Four meaningful links satisfy the existing new-word density and
forward-choice rules; no sparse-node exception or filler relation is introduced.
Only this new node may exceed ADR-0033's three-edge fan-out cap. No old node gains
an outgoing edge or a new route to another old node.

Remove Nucă's former synthetic projection by explicitly assigning its surface
to the KG. Preserve the other 472 projection rows, the Gem policy and all 71
legacy common-word proxies. A separate native-ingredient policy keeps Nucă's
real feedback only for exact self or a direct, directed, non-distractor
`part_of`/`ingredient pentru` edge of strength at least 0.90. Elsewhere it retains
the prior penalized Miere approximation. This is not a synonym or exact answer.
The existing shared scorer applies the same policy to guesses, fuzzy handling,
suggestions and warmer clues, preserving target privacy and exact-self wins.

Use the existing V24 rollback transaction, recipe data module and thin wrapper.
Regenerate puzzles, mobile, rankings and frozen-catalog metadata through their
builders; preserve the complete pack and the 336 frozen board payloads.
Evidence: [the V81 review](../reviews/v81-nuca-feedback/README.md).

## Consequences

The graph gains one word, one alias and four real recipe edges. There is no
target promotion, curated-game change or change to session limits. Nucă now
offers a direct correct ingredient guess for Cozonac and Baclava; other targets
retain the prior approximate route outside the reviewed direct associations.
Adding a reachable word shifts some guess ordinals and marginal temperature
boundaries; those effects and generated board-ranking changes require explicit
impact evidence rather than an unchanged-scoring claim.

The legacy Miere fallback remains approximate. Cozonac still needs a fresh
content review, and the bread issue remains deferred. The new density-compliant
node does not authorize broader aliases, reverse edges or unreviewed recipe
links. Human playtests and public rollout remain separate beta gates.
