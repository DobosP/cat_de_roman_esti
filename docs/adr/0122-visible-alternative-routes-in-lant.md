# ADR-0122: Keep alternative short routes visible in Lanț

- Status: accepted
- Date: 2026-09-08

Refines ADR-0043 choice selection while retaining its corridor and privacy bounds.

## Context

The V85 Stafide→Brânză round has two fair two-hop routes through Pască and Poale-n brâu.
The menu includes only Pască: local edge strength and salience allow longer continuations
to displace the second short route. Typed moves still work, but the suggestions understate
the available paths. This is a generic selection-policy problem, not a missing graph edge.

## Decision

Reserve up to two of the existing three corridor slots for distinct shortest continuations.
Use existing semantic/hub quality to choose among equally short candidates, then fill the
remaining corridor slot using the existing quality policy. Retain the existing safe-detour
selection and alphabetical display. Do not invent a target-specific override.

Keep the six-choice maximum, direct-edge legality, typed moves outside the menu, public
target, private route metadata and existing session/request bounds. This policy changes
which suggestions appear; it does not change legal paths, optimal distance or scoring.

## Consequences

Short alternatives remain visible without making every suggestion an optimal move.
Measure changed menus across the eligible inventory and test several graph shapes,
including a single continuation, multiple equal alternatives and bounded deterministic fill.
Human route comprehension remains a separate acceptance question.
