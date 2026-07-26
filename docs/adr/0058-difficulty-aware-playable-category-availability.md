# ADR-0058: Report difficulty-aware playable category availability

Date: 2026-07-24
Status: accepted

## Decision

Expose `available_by_difficulty.<game>.<difficulty>` from `/api/categories`. For a
digest-ranked bundled pack, count only boards inside the active `pilot_eligible` selection
boundary. For an unranked custom pack, retain the historical all-approved fallback. Preserve
the existing category node-floor proxy for Contexto, Lanț, and Alchimie mining; never apply
that proxy to Conexiuni.

Keep `curated` as the raw approved inventory count and keep `available.<game>` as the
compatibility summary that is true when any difficulty is available. In the web intro, show
only category chips available for the selected game and difficulty, always keep `Toate
temele`, and silently clear a selected category when a difficulty change invalidates it.

## Context / why

V40 correctly stopped serving 86 known strict-FAIL Conexiuni reserves, but the category
endpoint still counted those approved records across all difficulties. The default easy
picker therefore offered Gastronomie, Geografie, Știință, and Viața în România even though
their safe easy shelves were empty; pressing `Joacă` ended in a themed 503.

Widening selection back into failed reserves was rejected because it would undo the pilot
quality boundary. Showing unavailable native buttons was rejected for the mobile-first
picker because disabled controls add clutter and cannot explain themselves through hover on
a touch screen.

## Consequences

The default easy Conexiuni picker offers ten playable categories instead of fourteen, and
no zero-board ranked shelf is advertised. Changing difficulty cannot leave a hidden stale
category in the request. Direct explicit API requests retain their themed 503, and the
mining proxy remains an availability estimate rather than a proof for every graph shape.

No board is promoted, retiered, or made selectable. Seed/daily hashes, repeat behavior,
hidden answers, scores, the 7,200-second session TTL, and the 1,000-session per-game cap do
not change.
