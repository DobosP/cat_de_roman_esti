# ADR-0026: Give Lanț and Alchimie game-specific critique criteria

Date: 2026-07-16
Status: accepted

## Decision

Judge Lanț against explicit endpoint-recognition, semantic-step, route-choice,
difficulty, and arc criteria; judge Alchimie against seed quality, intuitive openings,
inferable target, free-answer, and bounded-choice criteria. Add runtime-derived Lanț
branch profiles plus bounded labeled shortest paths, and Alchimie craft profiles plus
productive openings and one minimum-action recipe, to their dossiers. Route both
workflow layers to the corresponding rubric sections.

## Context / why

ADR-0023 named all four games but only Conexiuni and Contexto had game-specific rubric
sections. Lanț and Alchimie fell back to universal/A-C-lite prompts, so a technically
valid path or closure could be promoted without judging whether its choices felt
legible or satisfying. Universal criteria alone were rejected because the two mechanics
fail in different ways even when recognition and factuality pass.

## Consequences

Every game now has a mechanic-specific subjective review. Dossiers become slightly more
expensive to build because they reuse the bounded branch/closure helpers already used by
pack validation. Runtime selection, sessions, APIs, and served content are unchanged.
