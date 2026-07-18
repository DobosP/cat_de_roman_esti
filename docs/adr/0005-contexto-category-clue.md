# ADR-0005: Add a bounded Contexto category clue

Date: 2026-07-04
Status: superseded-by ADR-0042

## Decision
Add a one-use category clue to Cald sau Rece after three counted guesses; it reveals only the hidden concept's KG category, applies a score penalty, and keeps the target id, label, and description hidden until win or give-up.

## Context / why
Contexto already gives temperature feedback, but cold starts can stall when every early guess lands far from the secret. A coarse category clue gives a stuck player a meaningful text-only direction without exposing graph structure or requiring a graph UI. The clue is delayed and penalized so it does not become the default first move, and it reveals category metadata only because revealing the label, id, path, or nearest neighbours would collapse the hidden-answer design.

## Consequences
The Contexto API has an additive `POST /api/wordgames/contexto/games/{game_id}/clue` route and a new stable OpenAPI operationId, `contexto_clue`. Clients should render `clue_available`, `clues_used`, and `clue` from server state. Hidden-answer contract tests must cover this clue boundary alongside create/get/give-up.
