# ADR-0147: Grow Alchimie with reviewed vocabulary

- Status: accepted
- Date: 2026-09-13
- Partially supersedes: [ADR-0146](0146-expand-alchimie-and-preserve-collections.md), for
  the content inventory, collection limits and single-predecessor generation workflow.

## Authority and outcome

The owner again explicitly requested more concepts. This continues V92 from `8f97bd9`
in the existing worktree. The scope includes a substantial content expansion and the
bounded vocabulary/save changes needed to support it. Publication, deployment, V93 and
recurring automatic iteration remain outside this request.

The kitchen world grows from 111 to **221 concepts**, 116 to **285 recipes** and 19 to
**32 optional goals**. Craftable discoveries grow from 58 to **117**. There are still
eight starters; later supplies grow from 45 to 96 across twelve automatic tiers.
The additions therefore comprise **59 crafted results and 51 supplies**. All original
111 concept records, 116 recipes, six supply tiers, starters and goals remain intact.

There are 47 reusable crafted intermediates and 70 terminal dishes. Seventy-seven
results have alternative recipes. Productive starting pairs increase from seven to
nine out of 28. New foundations include mayonnaise, choux pastry, laminated pastry,
tomato sauce, mashed vegetables, caramel, ganache, chickpeas and aubergines. These
support recognizable chains through fillings and sauces to completed dishes.

Review removed generic grill-to-Kürtőskalács and tray-to-regional-dish shortcuts.
Cooked cabbage now precedes the Cluj cabbage dish. Oven and pan both turn bread into
toast, which can be cut into croutons. Dubai chocolate requires an explicit pistachio
and kataif filling. Preparation remains simplified game content with omitted steps
disclosed, rather than a claim that two ingredients uniquely define a real recipe.

## World-local vocabulary

Remaining KG vocabulary alone lacked important foundations, encouraging arbitrary
shortcuts to named foods. Alchimie now supports reviewed, world-local concepts without
mutating the shared graph or other games. The new book contains **174 KG concepts** and
**47 authored definitions**. The global KG retains its previous counts and fingerprints.

The editorial source declares `WORLD_CONCEPTS` with a stable `alw_food_` identifier,
original Romanian definition and primary reference URLs. The generator preserves an
exact definition/provenance snapshot, marks `origin: authored`, records
`source: authored:alchimie`, and leaves `redistributable: false`; it does not infer a
third-party license from a linked webpage. Existing KG records keep their full original
snapshots and access/source metadata. Both forms remain server-owned catalog content.

The generator rejects authored labels that shadow a KG label or alias. The runtime
checks the namespace, nonempty unique normalized labels, valid reference URLs and exact
authored snapshots, and independently rejects identity shadowing against the current
KG. It never imports new authored concepts into the graph. The complete recipe book
and undiscovered IDs remain private; earned labels and explanations use the same API.

Both independent semantic reviews now cover **every concept record** as well as every
recipe. A concept judgment binds the digest of its exact record and must explicitly
accept it. New factual judgments require checked URLs. An inherited concept judgment
is allowed only when the whole record is byte-equivalent to the reviewed predecessor.
Incomplete, duplicate, stale, rejected or invented inheritance fails before a proposal.
Two final reviews still bind the exact generated catalog and runtime audit before the
atomic package write.

## Bounds and compatibility

The world and saved-craft bounds rise from 128 to **256**. Later supplies are capped at
**96**, supply tiers at **12**, and items per tier remain capped at 12. Existing caps of
512 recipes, 32 goals, eight historical versions, 2 MiB catalog and 64 KiB request bodies
remain. Session stores retain 1000 entries and a 7200-second sliding TTL. Browser saves
enforce their 64 KiB limit using UTF-8 bytes, and bounded unions support up to 256 pairs.

The generator now starts from the immutable reviewed 111-concept candidate and carries
forward its older compatibility records before adding that book's mechanics. Thus both
the original 75-concept and subsequent 111-concept saves restore into this expansion.
Their exact fingerprints and source bindings remain preserved. Existing server-side
historical validation, additive preservation and atomic live-session upgrades continue.

The current book has 117 earned crafts; a synthetic 256-concept world separately proves
that restoration beyond 128 earned crafts works and the new ceiling is enforced.
Unrecognized fingerprints still fail, and an older fingerprint cannot claim a new recipe.
The public API adds no new operation or required field in this pass. The KG/mobile
manifest remains unchanged: this vocabulary belongs to the server's exploration catalog.

## Verification

The serving audit exhausts free exploration and all 32 goals, distinguishes KG snapshots
from authored provenance, and restores every historical prefix for both predecessors.
Factual and quality reviews preserve exact judgments for the previous 116 recipes and
111 concepts while independently judging all additions. Browser checks restore a full
111-concept/58-craft collection, retain its goal and journal, then continue discovering.

Exact artifact fingerprints, integrated results and limitations live in
[the large expansion review](../reviews/v92-alchimie-large-concepts/README.md) and
[STATUS](../STATUS.md). This remains a finite food-themed world. Automated verification
does not establish human playtesting or physical-device acceptance.
