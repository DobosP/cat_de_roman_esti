# ADR-0015: Alchimie scores against exact action par

Date: 2026-07-10
Status: accepted

## Decision

Keep the stable `target_depth` API field, but define its value as the exact minimum
number of sequential pair selections needed to craft the target. Compute it with a
deterministic category-scoped inventory BFS that mirrors runtime combine semantics and
fails closed after six actions or 50,000 distinct states. Continue using parallel
closure generation only to choose the difficulty band and to guide the existing hint.
Apply the same exact-par helper in mined-game creation, curated-pack validation, and
content import/re-derivation.

## Context / why

Closure generation applies every productive pair in parallel, while a player can select
only one pair per move. Thirteen pack records therefore understated the achievable
optimum; seven were approved and could not earn the advertised 1,000-point/✨ result.
Renaming the public field would break the stable mobile contract without helping the
player, so its legacy name stays while its scoring meaning becomes truthful. An
unbounded exact search was rejected because adversarial mined inventories can produce
hundreds of thousands of states; the reviewed pack needs at most six actions and fewer
than 50,000 states.

## Consequences

All seven served and six pending undercounts are corrected, and every approved
Alchimie board now has an achievable perfect score. Mined targets that cannot be
certified inside both bounds are deterministically skipped. Difficulty still describes
closure depth plus seed width, so an `ușor` board may have action par 3 and a `normal`
board par 4. The category-scoping decision in ADR-0013 remains unchanged. Session TTL
and capacity remain six hours and 10,000 entries per game.
