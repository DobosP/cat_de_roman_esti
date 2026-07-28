# ADR-0063: Require four-board variety for category-scoped curated dailies

Date: 2026-07-28
Status: accepted

## Decision

Require at least four selectable records in the exact `(game, category, difficulty)` shelf
before a category-scoped daily may use curated content. The unscoped daily floor remains
eight. A ranked bundled pack counts only `pilot_eligible` records; a neutral custom pack
counts its approved selectable records. An explicit internal `min_pool` keeps the exact floor
its caller requests.

When the category shelf is thinner than four, return no curated pick. Alchimie, Cald sau
Rece, and Lanț then use their existing deterministic miner inside the requested category;
Conexiuni returns its existing themed 503 because it cannot mine a safe partition. Never use
an unscoped daily as the fallback for an explicit theme, because doing so would serve one
category while echoing another.

## Context / why

ADR-0055's eligibility boundary protected against known-bad boards, but its category floor
of one pinned a one-board shelf to the same category daily indefinitely. Falling back to the
shared daily was tested and rejected: callers correctly retain the player's requested
`board_category`, so an off-theme curated record would be mislabeled and could suppress
useful category guidance.

Four is the smallest reviewed variety floor already used when judging whether a beginner
shelf is worth exposing. Raising the shared floor or relaxing critique eligibility would
either reduce the main daily unnecessarily or reintroduce known failures.

## Consequences

Thin explicit category dailies may be mined or unavailable even though normal seeded play can
still select that shelf. Same inputs stay deterministic. Category, difficulty, eligible-only
selection, hidden answers, repeat history, scores, session TTL, and session caps do not
change. Integration tests require every successful explicit category daily to remain in that
theme; a 503 is preferable to silently crossing themes.
