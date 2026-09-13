# ADR-0144: Reviewed Alchimie recipe freedom

- Status: accepted
- Date: 2026-09-13
- Partially supersedes: [ADR-0044](0044-alchimie-sparse-recipe-projection.md), for the
  target-route-only runtime book and retained penalties on unsuccessful attempts.
  The historical core, its search limits and the session boundaries remain accepted.

## Context and authority

After the V92 interface work, the owner explicitly requested improvements to Alchimie's
content: many reasonable pairs failed, the number of paths was unclear, and the balance
between exploration, vocabulary and predetermined solutions needed comparison with
similar games. This extends V92 into Alchimie content and scoring. It does not start V93,
resume automatic iteration, publish a branch or deploy production.

The baseline audit covered all 80 approved, eligible rounds. The target projection kept
554 recipes across those rounds, with a median of only 4.5 discoverable concepts. Of
476 pairs formed from initially active words, 190 worked. Sixteen rounds had one
opening; five had exactly one productive winning sequence. Multiple stored routes did
not necessarily provide different final approaches: 19 rounds had one target-producing
pair. The source graph offered more relationships than the target projection accepted.

## Reference observations and design direction

Official Little Alchemy 2 material, inspected on 2026-09-13, shows that predefined recipes
can support substantial freedom. Its [Plant page](https://hints.littlealchemy2.com/item/plant)
lists ten producing pairs and its [Life page](https://hints.littlealchemy2.com/item/life)
lists twelve. Its [hints](https://hints.littlealchemy2.com/) encourage unpenalized
experimentation, while [item types](https://help.littlealchemy2.com/general/item-types)
distinguish terminal discoveries from items whose possible combinations are exhausted.
Both remain available in the encyclopedia. These are examples of alternative recipes
and managed progression, not a claim that every pair works.

In a [5 February 2024 creator interview](https://www.pcgamer.com/this-browser-based-endless-crafting-game-starts-you-off-with-fire-and-water-but-it-quickly-escalates-to-god-the-big-bang-and-yin-yoda/),
Neal Agarwal described Infinite Craft as an open-ended sandbox and explained that a
language model proposed results for novel combinations. This is historical evidence of
that generation model, not a claim about its current provider, model or caching contract.

For later exploration work, the preferred direction is a curated Romanian discovery
world with persistent discoveries and optional goals. Multiple coherent recipes can
give players freedom while keeping results explainable. Concept count alone is a poor
target: with our distinct-ingredient rule, `n(n-1)/2` possible pairs means six concepts
offer 15 pairs, while twenty offer 190. Adding vocabulary without enough meaningful
relationships can make experimentation less responsive. A future shared world needs
new reviewed content and results that remain consistent across targets; automatically
accepting semantic similarity does not establish a recipe.

This pass improves the existing short target challenges. It introduces no free-play
world, side discoveries, generated answers or larger concept inventory.

## Decision

Retain `_build_recipe_projection` as the deterministic historical core. Serving and
current-content audits call `_build_playable_recipe_projection`, which adds only
independently reviewed missing recipes and verifies the unchanged exact action par.
Every existing pair and its outputs remain identical. The graph, curated pack, seeds,
targets, approvals, category, difficulty and declared par remain unchanged.

The generated `alchimie_recipe_extensions_v92.json` contains exact per-round additions.
Each accepted recipe uses only existing core concepts and an absent ingredient pair;
it produces one non-seed result and never uses the target as an ingredient. Candidates
cover missing starting pairs or alternative target-producing pairs, with both actual
graph edges at least 0.70. Edge strength establishes eligibility, not semantic approval.
The live book retains bounds of 24 pairs, 32 concepts and two results per recipe.

`build_alchimie_recipe_extensions.py` is the only catalog writer. Its default is a dry
run. Two distinct reviewers supply complete factual and quality judgments bound to the
exact candidate artifact. Only their accepted intersection can survive; competing
accepted outputs for the same absent pair are all dropped. Factual acceptances require
valid source URLs. The generator checks current pack/KG/rubric bindings, replays exact
core books and verifies the actual node and edge metadata, including provenance.

Before the package write, both reviewers accept the exact proposed catalog bytes and
the exact live audit. That audit binds the final runtime and generator sources. The
writer checks those bindings and replaces the catalog atomically. The runtime loader
matches the exact core scope, routes, par and graph metadata, preserves the original
book on unrelated contexts, and fails closed on malformed catalog structure. Loading
is bounded and cached. No similarity-based recipe discovery occurs during a combine.

Current pending-board projection audits bind the extension loader and published catalog
alongside the required runtime sources. Their applier checks the same manifest. Older
archives without the catalog binding replay against the historical core; they do not
silently inherit current additions. Existing [projection review requirements](0129-portable-alchimie-projection-reviews.md)
remain in force. The V91 seed migration retains its old source hashes and replays its
test setup from exact archived runtime bytes.

Empty experiments and repeated pairs cost zero points. Each successful craft beyond
par costs 120 points; each requested hint costs 150 points; the score floor remains
100. Successful crafts count actions, including recipes that produce two discoveries.
The frontend local result key includes `productive-crafts-v92`, separating these scores
from earlier local records. The score and perfect-result marker use the same policy.
Feedback distinguishes an unsupported pair from a known result already owned.

## Consequences and limits

The approved catalog adds 50 distinct pair-to-output recipes across 28 rounds. None of
those triples was accepted elsewhere in the old core collection. They introduce 49
globally new ingredient pairs; one pair already had a different result in another
round. Consequently this remains a collection of scoped challenges, not a globally
consistent recipe dictionary.

Across the 80 rounds, live recipes increase from 554 to 604 and active starting-pair
coverage improves from 190/476 (39.9%) to 223/502 (44.4%). One-opening rounds fall from
16 to 12, and rounds with one productive winning sequence fall from five to three.
All 19 single-ending-pair rounds remain; median discoverable concepts stays at 4.5.
The correction reduces arbitrary failures but does not solve the request for a larger
discovery world. Ordered winning sequences also include alternate craft order and
must not be presented as a count of independent conceptual approaches.

Target IDs, recipes and routes retain their existing disclosure rules. Session TTL,
capacity, locking, ownership, request size, recovery,
hint consent and terminal recording remain unchanged. Exact evidence and completed
checks belong in the [review record](../reviews/v92-alchimie-recipe-freedom/README.md)
and [STATUS](../STATUS.md). Human playtesting and production deployment are separate
from these local content and implementation checks.
