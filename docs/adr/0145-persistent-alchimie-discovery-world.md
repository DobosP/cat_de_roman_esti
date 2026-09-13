# ADR-0145: Persistent Alchimie discovery world

- Status: accepted
- Date: 2026-09-13
- Partially supersedes: [ADR-0144](0144-reviewed-alchimie-recipe-freedom.md), for its
  deferred discovery-world scope. Its existing challenge recipes and scoring remain accepted.

## Authority and player outcome

The owner explicitly asked to continue building the shared recipe world, additional
discoveries, persistence and optional goals identified in the previous V92 delivery.
This continues V92 on its existing task branch. It authorizes local implementation and
verification, not publication, deployment, V93 or recurring automatic iteration.

Alchimie has an unscored exploration mode alongside the existing scored challenges.
Exploration is the default entry for a new player. Explicit challenge links, daily
circuit links and legacy saved challenges continue into challenge mode. Both modes
are reachable through a small mode navigation control.

## Content and progression

The first world is **Bucătăria românească**: 75 concepts, 57 canonical recipes and nine
optional goals. Eight initial ingredients/tools lead to 39 crafted discoveries. Four
automatic pantry milestones supply another 28 ingredients/tools after 3, 8, 16 and 24
crafted discoveries. Supplied concepts are never described or counted as crafted outputs.
Every supplied item has a recipe use, and the entire collection is reachable.

Each unordered pair has one fixed result independent of the selected goal. Ingredients
are retained. Eighteen results have alternative recipes; twelve crafted results are
reusable intermediates and 27 are final dishes. All pairs express explicit culinary
ideas with original explanatory text and independently checked sources. They are
simplified game recipes, not complete cooking instructions. Some pastry pairs admit
other reasonable interpretations; their acceptance is not a claim of unique causation.

The world uses existing KG concept identities, including 48 concepts absent from every
previous live challenge book. Thirty crafted results were absent from all old challenge
craft outputs, and 54 of the new canonical pair/output triples were absent from those
books. No shared KG node, edge, alias, pack record or historical recipe is rewritten.
Four world-local descriptions correct inherited wording about compot seasonality,
meatless stuffed peppers/sarmale and fresh pasta. Complete original node snapshots,
including source/access fields and descriptions, remain bound to the catalog.

The historical challenge recipe union has 22 pairs with different result sets across
rounds. It is not promoted into this world's dictionary. Consistency is guaranteed
inside exploration, across all its goals; old challenge rules remain a separate mode.

## Interaction and persistence

Two taps or a drag craft immediately. The interface carries a usable discovery into
the next experiment. New dishes remain visible when first earned; final and exhausted
items stay in the complete collection and discovery journal. Search, an optional goal
selector and one progressive hint control are available without setup menus.

Goals guide the next useful hint, never filter recipes or end exploration. Hints are
free and available immediately: first name a craftable discovery, then reveal an owned
ingredient pair. Completing a goal leaves other discoveries playable. Exploration does
not create a score, challenge completion, ranking entry or account record.

The browser stores a bounded checkpoint of successful ingredient pairs and the selected
goal. Its world ID and recipe fingerprint reject incompatible mechanics even if an
editor accidentally reuses the world ID. Copy and goal-label changes remain compatible.
The server replays the checkpoint from the starter set, validating ingredient
ownership, canonical recipes and automatic supplies. It never trusts a submitted list
of owned concepts. Valid duplicate recipes allow merging concurrent local branches.
The checkpoint is intentionally unsigned: exploration is unscored and all earned state
is reconstructed. It survives server expiry/restarts without a secret-key dependency.
It is local to the browser, not cross-device account synchronization.

Session reads and mutations use the existing atomic transaction helper. The exploration
store has its own 1000-session cap and 7200-second sliding TTL. A world is bounded to
128 concepts, 512 recipes, eight supply tiers and 32 goals; checkpoints have at most 128
successful pairs. Failed experiments do not grow persistent histories. A session pins
its validated world so later goal choices or catalog replacement cannot change its rules.

The frontend reconciles uncertain actions with GET rather than resubmitting mutations.
Expired sessions restore from the checkpoint. Browser locks, revision checks and bounded
checkpoint unions preserve concurrent-tab discoveries. Invalid saves remain intact and
recovery is visible. Unavailable browser storage is disclosed. Future incompatible
recipe changes require a new world identity and an explicit checkpoint migration.

## Review and API boundary

The editorial Python source generates candidates; fixture JSON is never hand edited.
Both independent semantic reviews cover every recipe and the entire world, bound to
the exact candidate bytes and source/KG/rubric fingerprints. Only complete dual acceptance
can generate a proposal. Two final reviews bind the exact catalog and actual runtime
replay audit before the generator's atomic package write. Missing, altered, partial,
stale or non-independent evidence fails closed.

The loader validates strict record shapes, source snapshots, unique canonical pairs,
reachability and bounded supply progression. It does not infer recipes from graph
similarity. A missing/invalid world returns a recoverable 503 for exploration.

Five additive endpoints under `/api/alchimie/explore` create/restore, read, combine,
request a hint and select a goal. Their stable operation IDs and public view contract
are recorded in [MOBILE_CONTRACT](../MOBILE_CONTRACT.md). Only earned inventory and recipe
explanations are public. Goal labels are intentional guidance; undiscovered target IDs,
unearned supply IDs and the complete recipe book stay private. The KG/mobile pack
manifest remains unchanged; exploration requires the server's separate reviewed catalog.

## Reference basis and verification

Little Alchemy 2's official documentation supports
[progress-aware hints](https://help.littlealchemy2.com/hints/using-hints), a retained
[encyclopedia](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia), and
[final/depleted item states](https://help.littlealchemy2.com/general/item-types).
Optional goals are our design choice, not an attributed Little Alchemy feature.

Exact catalog/review fingerprints, replay measurements, automated results and limitations
live in [the review evidence](../reviews/v92-alchimie-discovery-world/README.md) and
[STATUS](../STATUS.md). Human playtesting and physical-device acceptance are separate
from automated browser checks. This is a finite kitchen world; further themes are
content expansions, not an unlimited generated sandbox.
