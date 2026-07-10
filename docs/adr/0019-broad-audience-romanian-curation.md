# ADR-0019: Curate Romanian game content for a broad audience

Date: 2026-07-10
Status: accepted

## Decision

Favor contemporary civic participation, education, science, public health, and digital
life when adding Romanian word-game content. Use neutral, inclusive labels and factual,
context-bound descriptions instead of presenting habits or stereotypes as universal
Romanian traits. Move boards and targets whose play value depends on adult framing,
profanity, alcohol, insensitive historical humor, or excessive overlap with another board
to `pending`; retain their ids and content so a later human review can revise and restore
them rather than deleting them.

## Context / why

The generated pack offered strong breadth, but its approved pool also contained near-copy
Conexiuni boards and a small set of clues that were less suitable for a general Romanian
audience. At the same time, contemporary civic, school, scientific, and online life was
underrepresented relative to nostalgia and entertainment. Leaving every generated item
approved was rejected because valid graph structure does not guarantee variety, social
care, or fun. Deleting questionable records was also rejected because `pending` preserves
stable ids and makes editorial decisions auditable and reversible.

## Consequences

V14 adds one mixed Conexiuni board and eight Cald sau Rece targets, while moving fifteen
high-overlap or broad-audience-mismatched Conexiuni boards and one profanity-centered
target to review. The shipped pack has 769 records: 537 approved and 232 pending. Future
content passes must check both mechanical playability and this editorial boundary; a
pending record may return only after focused review or revision. No selection algorithm,
daily seed, API shape, session storage, six-hour sliding TTL, or 10,000-entry per-game cap
changes.
