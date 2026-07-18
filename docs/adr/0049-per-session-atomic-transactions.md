# ADR-0049: Linearize each word-game session transaction

Date: 2026-07-19
Status: accepted

## Decision

Store each live session in one capped entry that owns a re-entrant transaction lock and a
borrower count. Every HTTP read or mutation for Alchimie, Cald sau Rece, Conexiuni, and Lanț
must pin the entry and hold that lock from validation through response-payload construction.
Keep the metadata lock short, so different sessions remain concurrent. TTL and LRU cleanup
must skip borrowed entries; missing IDs allocate no lock. If all 1,000 capped entries are
borrowed, creation fails immediately with `SessionCapacityError`, which game endpoints map to
a short HTTP 503. Deleting a borrowed entry fails without waiting and may be retried.

## Context / why

`SessionStore.get()` protected lookup but returned a shared mutable object after releasing its
lock. Simultaneous requests could therefore charge one Alchimie pair twice, count a Contexto
guess or Conexiuni mistake twice, or validate two Lanț hops from the same old node and retain an
illegal chain. Holding the store-wide metadata lock throughout a request would serialize every
game and expensive graph calculation. A separate lock map could outlive evicted sessions and
break the memory cap. Waiting for capacity or deletion while a caller already owns the only
borrowed slot can deadlock, so the hard-cap edge is explicit and fail-fast instead.

## Consequences

Same-session requests are linearizable, while different sessions can still progress in
parallel. Locks and pins have the same 1,000-entry bound as sessions; the 7,200-second sliding
TTL, LRU order, response contracts, scores, and hidden-answer rules do not change. The legacy
`get()` accessor remains available for simple compatibility/test inspection, but compound
request work must use `transaction()`. At the exceptional all-slots-borrowed instant, starting
a new game returns 503 rather than overshooting the cap, detaching live state, or blocking.
