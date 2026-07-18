# ADR-0050: Bound Lanț path history to 64 moves

Date: 2026-07-19
Status: accepted

## Decision

Accept at most 64 successful Lanț hops in one session, so the retained chain and every
full-state path contain at most 65 earned nodes. Apply the same limit to every difficulty
and seed. The 64th hop remains legal and may win normally; once a nonterminal session is
at the cap, reject further moves without mutation and return the short existing-recovery
shape with `Limită atinsă — folosește Înapoi.`

At the cap, return no local choices and make a hint return the existing `backtrack` stage
with that same message. Free undo removes one hop and immediately permits one retry.
Keep revisits legal below the cap, preserve the complete earned breadcrumb instead of a
rolling window, and leave finished-game idempotence, scoring, sharing, and progress
feedback unchanged.

## Context / why

Lanț intentionally allows exploratory revisits and echoes the complete played path after
each accepted hop. A player or automated client could therefore repeat a legal two-node
cycle forever, growing both one session object and every later move/GET response without
bound. The two-hour TTL and 1,000-session LRU cap bound session count and idle lifetime,
but they do not bound the size of one active session.

A rolling path window was rejected because it would make the visible breadcrumb disagree
with move count, score, and one-step undo. Treating the cap as a loss was rejected because
the existing free undo is a deterministic recovery and preserves a possible win. Forbidding
all revisits was rejected because deliberate backtracking and off-menu exploration are part
of the game below the abuse ceiling.

## Consequences

Normal mutation can retain at most 65 node ids, `_path` can serialize at most 65 earned
steps, and repeated over-cap requests receive a small constant response. Focused tests pin
the exact boundary, a repeated A↔B cycle, no-mutation rejection, capped hint recovery,
undo/retry, a winning 64th hop with normal scoring, and byte-size ceilings for the synthetic
cycle responses.

No route-corridor marker or unearned node is added to the API. The target remains public by
Lanț design, while played/hinted-hop and hidden-route boundaries remain unchanged. Session
TTL remains 7,200 seconds and the per-game store cap remains 1,000.
