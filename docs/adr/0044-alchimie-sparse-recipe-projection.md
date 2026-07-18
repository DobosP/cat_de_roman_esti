# ADR-0044: Project sparse target-useful Alchimie recipes

Date: 2026-07-18
Status: accepted

## Decision

Treat the shared semantic graph as creation input, not Alchimie's live recipe book.
For each board, deterministically explore at most 50,000 inventory states and retain at
most 128 terminal route candidates in its category-scoped graph. Select the strongest
minimum-action route among those bounded discovered candidates, plus distinct discovered
near-optimal routes up to two actions longer. Sort equal-length candidates by strongest
weakest parent-to-result edge, then mean strength, lower result degree, and stable ids.
Backward-prune every route to results required by a later step, then store a private
session projection of at most four routes, 24 pairs, 32 concepts, and two results per pair.
A second result is allowed only when one selected route needs both together; merging
alternate singleton results must not create it.

Runtime combines consult only that projection. Keep the category public and use it to
build the projection, superseding ADR-0013's direct common-neighbour runtime rule while
retaining its themed-board outcome. Preserve exact deterministic `target_depth`, score
penalties, target-id secrecy, three-fruitless-move hint unlock, two-hour sliding TTL, and
1,000-session cap. Add recent/useful/ready/depleted inventory metadata and mobile-first
`Recente`/`Utile`/`Toate` views; depleted ingredients remain in lineage but leave active
views. The first hint names only a reachable non-target output label, or the already-
public category when the target is next; later hints may reveal one useful owned pair.
Never serialize recipe ids, a full route, or the hidden target id before victory.
For mined boards, prefer at least two seed pairs that are productive in the selected
projection itself; keep the first solvable one-opening board only as a thin-theme fallback.

## Context / why

Category scoping bounded the former graph explosion, but a pair still returned every
fresh shared neighbour. Technically short solutions therefore opened dozens of plausible
branches, made the inventory noisy, and let a weak semantic coincidence outrank a route a
beginner could explain. A hard global strength cutoff was rejected because it can remove
the only solvable minimum route. An authored recipe file for every graph/content wave was
also rejected for this iteration because it would duplicate pack identity and drift from
the validated target/par contract. A deterministic private projection preserves that
contract while separating graph coverage from the player's local decision space.

## Consequences

All 77 approved boards retain their existing exact par and remain solvable at that par.
The frozen projection has 536 pairs: 459 singleton and 77 required two-result exceptions;
72 boards expose two to four routes and five graph-thin boards expose one. Selected route
minimum strength has median 0.66; only five mandatory shortest routes fall below the 0.55
preference floor, with 0.40 the minimum. Cold local measurement builds all approved
projections in about 11 seconds and 12 representative mixed-difficulty mined sessions in
about 18 seconds. The mined test uses a 45-second shared-CI ceiling while pinning every
structural bound. The bounded 12-reaction journal and retained empty-pair correction from
ADR-0034/0035 remain intact. Adding or reweighting graph edges may intentionally change a
mined projection; curated fixtures must continue to pass the pinned projection/par/quality
audit.

The bounded search retains one deterministic parent when same-depth histories converge on
the same inventory state and stops at its explicit state/candidate ceilings. Semantic
ranking is therefore strongest-among-discovered, not a proof of the globally strongest
route in the complete category graph.
