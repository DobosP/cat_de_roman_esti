# ADR-0018: Contexto ranks use guess-to-target distance

Date: 2026-07-10
Status: accepted

## Decision

Build every Cald sau Rece reachability histogram, responsive-zone check, rank, and
closeness score from directed **guess-to-target** distance. Use
`WordGameService.distances_to(target)` in runtime session construction, mined-target
selection, curated validation, and fallbacks. Keep the direct guess check
`distance(guess, target)` and all target-reveal boundaries unchanged.

## Context / why

Runtime temperature already measured whether the typed concept can reach the secret, but
the comparison histogram used `distances_from(target)`. Those are equal only on an
undirected graph; the fixture has 103 traversable directed edges. Across approved
target/guess pairs, the mismatch changed rank or closeness for about 91% of pairs, by as
much as 495 ranks or 35 closeness points. It also admitted two one-way restaurant nodes
as mined targets even though almost no guess could reach them. Treating every graph edge
as undirected was rejected because direction is intentional and shared with Lanț.

## Consequences

All 189 existing curated/review Contexto targets still clear the reachability and warm-
zone floors, so current curated target ids and pack counts do not change. Public
`reachable_count`, ranks, closeness, and some share-trail squares become truthful; rare
future mined seeds skip Caru' cu Bere and Casa Capșa as one-way dead targets. The API
shape and ADR-0009 hidden-answer view remain stable. Session bounds remain six hours and
10,000 entries per game.
