# ADR-0009: Contexto hidden-answer rank view-model

Date: 2026-07-04
Status: accepted

## Decision
Expose Contexto guess feedback through a server-built rank view-model: every accepted guess carries distance, one-based rank, temperature, and closeness, while the target id, target label, target description, and any solution payload remain absent from create/get/guess/clue responses until the player wins or gives up.

## Context / why
Cald sau Rece needs richer feedback than a percentage alone, but the API must not make mobile or web clients responsible for deriving ranks from a hidden answer. Returning a full candidate ranking or solution list would disclose too much structure and create a larger response surface. A bounded per-guess rank gives clients a stable display value while keeping gameplay server-authoritative.

## Consequences
Clients can render Contexto ranks directly from the API. Hidden-answer contract tests must cover create/get/guess/clue pre-reveal responses and the win/give-up reveal boundary. Future Contexto feedback fields should be added to the same public view-model instead of exposing target internals or full ranking tables.
