# V92 — Alchimie recipes and freedom to experiment

Valid until: a later change to the catalog, reviewed graph, source bindings or scoring — then treat as history.

The owner extended the V92 interface work into Alchimie content after reporting that
reasonable pairs failed and asking how similar games balance freedom with predefined
recipes. Baseline: `e46bf3da621a43e19bc79f71ff7a4f223afa3a0f`.
Decision: [ADR-0144](../../adr/0144-reviewed-alchimie-recipe-freedom.md).
Current integration and completed gates: [STATUS](../../STATUS.md).

## Research and what it means for this game

The official [Little Alchemy 2 hints](https://hints.littlealchemy2.com/) encourage
experimentation without penalties. Its fixed recipe pages list ten ways to make
[Plant](https://hints.littlealchemy2.com/item/plant) and twelve ways to make
[Life](https://hints.littlealchemy2.com/item/life), inspected on 2026-09-13. Predetermined
results therefore need not imply one solution path. Its
[item-type documentation](https://help.littlealchemy2.com/general/item-types) separates
items with no further recipes from items whose recipes the player has exhausted,
retaining both in the encyclopedia.

Neal Agarwal's [February 2024 creator interview](https://www.pcgamer.com/this-browser-based-endless-crafting-game-starts-you-off-with-fire-and-water-but-it-quickly-escalates-to-god-the-big-bang-and-yin-yoda/)
described Infinite Craft as an open-ended sandbox whose novel combinations prompted
language-model results. That historical mechanism explains a different exploration
model; it supplies no claim about the service's current model or result consistency.
These references document mechanics, not comparative popularity or a measured player
preference for this implementation.

The distinction matters because Alchimie currently serves a short target challenge.
The historical projector discarded graph relationships outside a few selected target
routes. A larger vocabulary alone would not fix that: our distinct-item combinations
grow from 15 possible pairs with six concepts to 190 with twenty. The future curated
world and optional-goal direction is recorded in ADR-0144; this delivery addresses
missing recipes and penalties within the current challenges.

## Before and after across all 80 eligible rounds

These are exhaustive combinatorial measurements of the actual served books, not
telemetry or estimates of a player's probability of guessing correctly.

| Measure | Before | After |
|---|---:|---:|
| Recipes, counted within each round | 554 | 604 |
| Productive pairs among initially active/selectable words | 190 / 476 (39.9%) | 223 / 502 (44.4%) |
| Productive pairs among all starting words, including sidelined words | 190 / 1,226 (15.5%) | 223 / 1,226 (18.2%) |
| Median productive openings | 2 | 3 |
| Median recipes per round | 6 | 7 |
| Rounds with one opening | 16 | 12 |
| Rounds with one productive winning sequence | 5 | 3 |
| Rounds with one target-producing pair | 19 | 19 |
| Median discoverable concepts per round | 4.5 | 4.5 |

The raw all-seed denominator includes words unavailable for selection in the default
active workspace. The active denominator also grows because eight additional seed
appearances acquire a usable recipe. Neither percentage should be reported as observed
player success. Stored historical route counts remain unchanged; the additional
accepted recipes create more executable sequences through the same concepts.

The 50 additions cover 28 rounds and are also 50 distinct new pair-to-output triples
globally. None duplicates a recipe already accepted in another old core. They add 49
globally new ingredient pairs: Dacia + Războaiele daco-romane gains Sarmizegetusa Regia
in one round, while another old round returns Decebal for that pair. Scoped result
differences therefore remain. The collection is not a universal recipe dictionary.

In the easy seed-38 Sport round, all six football-club pairings now produce Club sportiv.
The formerly missing Dinamo + Rapid, Dinamo + CFR Cluj and FCSB + CFR Cluj pairs are
accepted. Starting coverage improves from 4/15 to 7/15. This round still contains only
three discoverable concepts and two final approaches to Liga Campionilor la handbal.
Its 16-to-31 increase in ordered productive winning sequences includes different
ordering and preparatory choices; it does not mean 31 distinct target ideas.

Evidence: [baseline](baseline.json), [after](after.json), and [exact live audit](live-audit.json).

## Review boundary and resulting behavior

The [candidate artifact](candidates.json) records exact core books, labels, source
edges, stable identities and bindings. The initial [factual review](reviews/factual-review.json)
and [quality review](reviews/quality-review.json) independently judge those candidates.
Their accepted intersection is passed through the generator; competing accepted
outputs for one missing pair are excluded. The original final reviews
([factual](reviews/final-factual-review.json), [quality](reviews/final-quality-review.json))
bind the exact generated catalog and [initial audit](initial-apply-audit.json) used for
the atomic package write. After required-source checks were hardened, both reviewers
revalidated the unchanged catalog against the current live audit:
[factual](reviews/final-factual-review-current.json) and
[quality](reviews/final-quality-review-current.json). The current write gate was then
verified without rewriting the catalog.

The published catalog SHA-256 is
`ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301`.
Runtime checks match the original book and actual concept/edge metadata before adding
recipes. Existing pairs, outputs and routes remain intact, as do exact target pars.
The graph, pack, seeds, targets and number of discoverable concepts do not change.
The existing limits remain 24 pairs, 32 concepts and two results per recipe.

Failed experiments and repeats now cost zero points. Successful craft actions beyond
par still cost 120 points, hints cost 150 and the floor remains 100. Feedback separates
an unsupported pair from a recipe whose result is already owned. The frontend result
key separates this scoring policy from earlier local scores.

Current projection audits and serving use the same extended books. Pending-content
review binds the catalog and required runtime files. Historical archives retain core
replay. A compressed, hash-checked copy of the V91 runtime lets its migration tests
reconstruct the historical input; the migration still rejects current source as stale.

## Verification scope and remaining content limits

The [verification record](verification.json) carries exact commands, source fingerprints,
completed results and any intermediate failures. Relevant checks exercise immutable
core preservation, altered sources and graph metadata, incomplete or non-independent
reviews, invalid source URLs, conflicting recipes, catalog bounds, final write approvals,
score/replay behavior, historical migration rejection and actual browser experiments.
This document records no final pass total independently of that evidence.

This is a local V92 improvement to short target challenges. It adds no free-play world,
side discoveries or AI-generated answers. Twelve rounds still have one opening; the
Diplomat, România interbelică and Universitate rounds retain a single productive winning
sequence. The unchanged concept breadth and remaining scoped inconsistencies are
follow-up content work. No production deployment, human playtest or physical-device
acceptance is established by this record.
