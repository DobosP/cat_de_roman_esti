# ADR-0036: Complete basic-word coverage with first-class concepts

Date: 2026-07-17
Status: accepted

## Decision
Represent the fifteen remaining eligible beginner terms as first-class easy concepts,
with 44 collision-screened inflections and 53 explicit non-distractor semantic edges.
Give every new concept at least four incident links, two same-category links, and two
forward choices. Keep the eleven ambiguous benchmark terms deferred, preserve the Moon
and ship senses around `lună` and `vapor`, and add no curated boards or promotions.

## Context / why
V25 reached 219/234 eligible benchmark terms but could not honestly resolve the last
fifteen through aliases: mapping `dinte`, `curcubeu`, `meserie`, or the missing feelings
onto nearby nodes would teach false equivalence and make typed answers feel arbitrary.
First-class nodes give each word one clear owner. Broad plurals, generic `related_to`
links, and hub-heavy shortcuts were rejected because they reintroduce ambiguity or
flatten the route choices that Lanț and Contexto depend on.

## Consequences
Eligible beginner resolution is 234/234. The fixture becomes 2,199 nodes, 8,845 edges,
7,077 aliases, and 180 legacy puzzles; deterministic regeneration changes 23 legacy
puzzle records while the 794-item curated pack remains byte-identical and unpromoted.
The exact 33-item critique gate stays clean and the full pending critique report stays
byte-identical. The public mobile contract must move to `fixture-v28-basic-words`, and
v25 regression guards remain additive so later first-class concepts do not erase its
historical alias and edge guarantees.
