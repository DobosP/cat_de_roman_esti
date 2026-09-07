# ADR-0118: Add culinary concepts and correct exact reviewed graph links

- Status: accepted
- Date: 2026-09-07

## Context

The owner requested a version improving all six games, including genuinely new concepts
and realistic graph links. The V83 graph cannot represent ordinary dough, grain, whey and
brining ideas. Drojdie borrows generic food feedback, and a category edge falsely calls
Poale-n brâu a cheese. More aliases cannot repair these gaps.

## Decision

Author a reviewed culinary batch through the shared rollback-protected V24 transaction.
New concepts have explicit senses, modest input forms and sourced, directional relations;
qualified labels retain intentionally ambiguous bare-input exclusions. Ingredient variants,
production steps, utensils and same-category links keep distinct labels and relations.
Graph proximity does not imply that ingredients are interchangeable.

Permit removal only of complete, exact previously reviewed edge records. Reject stale,
partial, missing, duplicate or differently typed evidence, and duplicate baseline edge IDs.
Reserve original IDs during new-link allocation, rebuild degrees and legacy puzzles, and
validate the graph, existing approved game payloads and mobile mirrors in one transaction.
Any failure restores every affected artifact. Never remove by a fuzzy label or endpoint match.

Drojdie becomes a native concept with actual directed dough associations; its previous
generic-food projection is retired. No generic Mâncare fallback is retained for the new node.
Measure the changed feedback, recipes, selectable inventory and directed routes before
claiming an improvement. Independently review additional playable candidates under the
existing rubric and promotion contract; new graph nodes are not automatically new rounds.

Promote `ct_gastronomie_334`–`336` (Plăcintă cu mere, Salam de biscuiți and generic Pâine)
and `lt_gastronomie_220` (Făină→Cornulețe) after separate dossier-bound analyst/verifier
judgments. These rounds use the new apple/biscuit/dough/production routes. Accept the Lanț
salience warning because the familiar endpoint is displayed and the precise dough route
is elementary; do not inflate its source salience. Its second Cozonac route is a weaker,
explicit holiday-baking association. Generic Pâine is distinct from the V77 deferred
Pâine de casă link, which remains absent. Cinnamon/bread, oven/biscuit-dessert and other
remaining rank noise stay disclosed; clear direct cores justify these playable targets
without asserting that every ingredient's feedback is correct.

## Consequences

The batch increases the vocabulary available to graph games and makes a false relationship
explicitly correctable. New incoming paths can change ranks and generated recipes, requiring
an impact report and gameplay checks. Existing curated records and the frozen derived-board
inventory remain separate from graph extension. Agent checks do not establish human enjoyment.
