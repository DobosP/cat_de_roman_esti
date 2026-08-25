# ADR-0093: Reserve a trivial Contexto target and weight within the filtered shelf

Date: 2026-08-25
Status: accepted

## Decision

Keep `ct_muzica_163` approved for provenance but make it unselectable through a new,
mirrored V69 impact-reserve sidecar. Do not change either exact vocabulary owner: _Refren_
and _Refren viral_ remain distinct concepts. Add the V69 sidecar to ranking demotions after
the unchanged V43 and V44 sidecars, then regenerate the ranking artifact and only the
ranking-bound metadata of the frozen derived catalog.

For digest-ranked Contexto only, derive effective 1–5 integer tickets after applying the
exact game/category/difficulty and pilot-eligibility filters. Order that shelf by descending
`pilot_score`, break ties by stable board ID, and assign quintile tickets while retaining a
positive ticket for every board. Fix these weights before applying a signed-in player's
finished-board exclusions. Use the same effective weights for seeded and daily selection.
Keep this mode opt-in so neutral/custom packs and other games preserve their selectors.

This decision layers on ADR-0092's bounded Romanian-language morphology wave; it does not
supersede that vocabulary decision or ADR-0092's derived-game contracts.

## Context / why

The shipped _Refren viral_ target is mechanically valid and highly ranked, yet the ordinary,
separately owned guess _Refren_ lands at rank 2. That nearly reveals the answer from its
lexical head and makes the round feel like a synonym trap. Reassigning an alias would create
a real resolver collision; deleting the reviewed record would discard provenance; changing
shared graph topology would affect unrelated games.

V37's global within-game quintiles also compare a small requested shelf with all Contexto
targets. This can flatten meaningful score differences inside the category and difficulty a
player actually chose. Recomputing after private history was rejected because two players
would assign different quality weights to the same retained board.

## Consequences

Cald sau Rece serves 201 unique reviewed targets across all 14 categories. Music/easy keeps
six targets, above its four-board daily floor. Every retained target remains reachable with
a positive ticket, seeded and daily choices remain deterministic and insertion-order
independent, and history never changes relative quality weights.

The pack, graph, vocabulary, projections, sessions, accounts, API shapes, and frontend do
not change. Ranked original-game inventory becomes 448 eligible boards: Conexiuni 74,
Contexto 201, Lanț 94, and Alchimie 79. The derived catalog still contains the exact frozen
336-board payload; only its ranking digest metadata and artifact checksum change.
