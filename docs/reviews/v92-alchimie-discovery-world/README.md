# V92 — Shared Alchimie discovery world

Valid until: changes to the world, reviewed sources, serving code or persistence contract — then treat as history.

The owner asked to continue the remaining shared recipe world, additional discoveries,
persistence and optional goals after the recipe-freedom delivery. Baseline: `c0f3945`.
Decision: [ADR-0145](../../adr/0145-persistent-alchimie-discovery-world.md).
Current completed gates and integration state: [STATUS](../../STATUS.md).

## What became playable

| Measure | Shared kitchen world |
|---|---:|
| Total collectible concepts | 75 |
| Initial ingredients/tools | 8 |
| Automatically supplied later | 28 |
| Crafted discoveries | 39 |
| Canonical unordered recipes | 57 |
| Results with alternative recipes | 18 |
| Crafted intermediates / final dishes | 12 / 27 |
| Productive initial pairs | 7 / 28 |
| Optional goals | 9 |

Automatic supplies unlock after 3, 8, 16 and 24 crafted discoveries. Supplies do not
advance those thresholds. Every concept is reachable, every supplied item has a use,
and completing a goal leaves the other recipes playable. The count of 75 includes
ingredients/tools supplied to the player; it does not mean 75 crafted discoveries.

The [comparison](challenge-comparison.json) identifies 48 world concepts absent from
all 80 old live challenge books, 30 crafted results absent from their crafted outputs,
and 54 pair/output triples absent from their recipes. All concept IDs already existed
in the unchanged KG. This is broader playable content, not new KG vocabulary.

The [legacy audit](legacy-consistency-audit.json) found 22 ingredient pairs with differing
result sets across old challenge rounds. Those scoped rules remain in challenge mode.
The new world has one canonical result per pair across all optional goals; it does not
claim to make the old challenge union globally consistent.

## Content and review evidence

The editorial Python source generated [the exact candidate](candidates.json). Both
independent semantic reviews cover all 57 recipes and the complete world:
[factual](reviews/factual-review.json) and [quality](reviews/quality-review.json).
The candidate SHA is `559abb0b475665f73b010b1a0acdc7650576d829819a50a2e99bdd50700f8fae`.

The generator inserts the factual review's checked source URLs and emits the catalog.
Catalog SHA: `fd3f5547e2a771b8d6d6caae7cf2d18335ce97d512a37446daa3062acb638a8c`.
Two final reviews bind these exact bytes and [the live runtime audit](live-audit.json):
[factual](reviews/final-factual-review.json), [quality](reviews/final-quality-review.json).
The runtime audit pins eight source files and reproduces the complete collection for
free play and every optional goal. The factual reviewer also ran 100 randomized complete
playthroughs while changing goals between crafts.

Four inherited concept descriptions were corrected only in this world: meatless stuffed
peppers/sarmale, the flour used in fresh pasta, and compot preparation/seasonality.
Every original source snapshot remains intact. Recipe explanations disclose omitted
cooking steps and ingredients. Some pastry pairs could also suggest another legitimate
dessert; review acceptance establishes a plausible canonical game association, not a
unique two-ingredient cooking definition or measured player preference.

The initial runtime review found that a checkpoint bound only to `world_id` could silently
change earned outputs if an editor changed recipes without changing that ID. The final
checkpoint also binds a canonical `recipe_hash` over recipes, starters and supplies.
The prior audit/review are retained as [initial audit](initial-live-audit.json) and
[initial final factual review](reviews/initial-final-factual-review.json); they did not
authorize a package write. Final reviews bind the corrected runtime before application.

## Interface, persistence and verification scope

The new default entry offers exploration, with existing daily/scored challenges under
Provocări. Crafting is immediate by two taps or drag. The collection, first-discovery
recipes and optional goal persist in the browser; expired sessions restore through
server-validated replay. Goals do not stop crafting or affect pair results. Free hints
first name a reachable discovery and then reveal the owned pair.

Checks cover complete reachability, alternative pairs, source/review tampering, bounded
content and checkpoints, goal-independent outcomes, automatic supplies, hidden unearned
IDs, simultaneous crafts, expired sessions, changed recipe fingerprints and compatible
copy edits. Browser checks exercise real crafting, pantry rewards, nonterminal goals,
lost responses, cross-tab saves, incompatible checkpoints and enlarged text.
The exact commands and completed results are in [verification](verification.json).
The final run passed 1787 backend, 53 accounts, 204 native frontend and 442 browser
checks. Inspected previews: [desktop starters](desktop.png),
[mobile goal completion](mobile-goal.png).

One intermediate browser run passed 66 checks and failed the two 320-pixel/enlarged-text
checks for the new mode navigation. Later checks caught intro-button contrast and a
stylesheet-order issue affecting desktop starter visibility. The final run includes
those fixes. Invalid local saves are preserved rather than silently overwritten.

The [reference review](reference-review.md) links official Little Alchemy 2 documentation
for progress-aware hints, the encyclopedia and final/depleted items. Optional goals
are our design choice. No deployment, human playtest, physical-device acceptance or
cross-device account synchronization is established here. The world is finite and
food-themed; 27 crafted dishes are terminal collection entries.
