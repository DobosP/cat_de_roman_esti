# ADR-0075: Bound alias morphology and common typed guesses

Date: 2026-08-12
Status: accepted

## Decision

Extend only previously unanimous exact aliases with independently reviewed,
normalized-unique Romanian grammatical forms. Add related common words only to
Contexto's non-winning projection with rank penalty one and one exact reviewed anchor.
Disagreement defers; hard homonyms reject. Author only one spelling for a projected
concept when alternate spellings would otherwise create separate attempt identities.

V51 admits 32 alias inflections and eight Contexto projections from a fixed 50-surface
funnel. It defers seven surfaces, including disputed `amicii`, and rejects three hard or
ownership-ambiguous forms. It adds no node, edge, puzzle, game record, hold disposition,
tap-game content, projection-alias behavior, or derived board.

Supersede ADR-0074 only where it fixed the resolver at 7,460 aliases and the Contexto
projection at 465 terms. Preserve its exact-alias/related-projection separation, archive
versus live-gate boundary, non-winning behavior, collision rules, and every topology,
pack, ranking-payload, session, privacy, and owner-hold boundary.

## Context / why

V50 established safe lexical classes but intentionally stopped at one surface for each
accepted synonym. Common inflections such as `odăi`, `automobile`, and `mămicilor` still
failed typed input even though their lemmas had already passed exact-referent review.
Separately, eight common digital, home, and transport guesses had honest mature Contexto
anchors but were not exact KG aliases.

Two independent reviews agreed on every admitted alias and exact projection tuple. They
disagreed on `amicii`, so it remains absent. `Wi Fi` is the sole authored spelling for
that projection; hyphenated and unspaced variants remain absent because projection IDs
currently derive from each normalized surface and would count as separate attempts.

## Consequences

The KG remains at 2,364 nodes, 9,217 edges, and 180 puzzles while aliases increase from
7,460 to 7,492. Contexto's projection increases from 465 to 473 terms across the same 26
domains. Pack bytes and all 618 records remain unchanged. Ranking and derived wrappers
are rebound to the new KG, while their board arrays and the frozen 336-board derived
payload remain byte-stable. Any new synonym lemma, projection spelling alias, disputed
surface, topology, or board needs a separate bounded decision and test contract.
