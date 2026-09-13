# ADR-0146: Expand Alchimie and preserve collections

- Status: partially superseded by [ADR-0147](0147-grow-alchimie-with-reviewed-vocabulary.md)
  for inventory, bounds and compatibility history; other decisions remain accepted.
- Date: 2026-09-13
- Partially supersedes: [ADR-0145](0145-persistent-alchimie-discovery-world.md), for the
  initial content inventory and strict rejection of all changed recipe fingerprints.

## Authority and outcome

The owner requested more concepts after the first discovery-world implementation.
This continues V92 from `2257766` on the existing task branch. The scope is additional
playable content and the compatibility work needed to preserve collections. Publication,
deployment, V93 and recurring iteration are not authorized by this request.

The kitchen world expands from 75 to **111 concepts**, 57 to **116 recipes**, and nine
to **19 optional goals**. The 36 added concepts comprise **19 crafted discoveries** and
17 supplied ingredients/tools. Crafted results total 58; later supplies total 45.
Eight starters and the four original supply milestones remain exact. Two new tiers
unlock at 30 and 36 crafted discoveries, so a previously completed 39-discovery save
immediately receives the new supplies and can continue exploring.

The original 75 concept records, 57 recipe records, starters, supply tiers and goals
remain intact. Seven formerly terminal results gain uses: Pâine, Friptură, Fasole bătută,
Salată, Mujdei, Paste and Dulceață. Reusable crafted concepts grow from 12 to 23; results
with multiple recipes grow from 18 to 40. Thirty-five crafted dishes remain terminal.
New foods include sandvișuri, clătite, pizza, șnițele, zacuscă, urdă, mucenici, cornulețe,
halva and plăcinte. Pair rules remain independent of goals and ingredient order.

All new identities already exist in the unchanged KG. World-local descriptions explain
the added concepts and correct inherited wording, including the regional forms of
mucenici. Full original snapshots and provenance remain intact. The review rejected an
oven-to-crumb shortcut; crumbs instead arrive explicitly as a pantry ingredient.
Some recipes are simplified culinary ideas with omitted steps disclosed in their
explanations, rather than complete two-ingredient cooking instructions.

## Compatible collection upgrades

The first world correctly rejected unknown recipe fingerprints but therefore also
rejected legitimate content additions. A reviewed `compatible_versions` catalog now
contains bounded historical mechanics, their fingerprints and the reviewed source SHA.
The generator derives the first archive from the immutable previous candidate at
`docs/reviews/v92-alchimie-discovery-world/candidates.json`, pinned to its exact SHA.
It refuses changed original recipes, starter membership, supply milestones or goals.

The runtime verifies each historical fingerprint and requires its recipes and supply
rules to be preserved in the current world. Restoration first validates every saved
pair against that original book, including ownership and original unlock timing. It
then replays the earned pairs in the expanded world and checks that no previously owned
concept disappeared. New recipes cannot be claimed under an old fingerprint even when
their ingredients were already available. Unknown or incompatible versions still fail.

Existing sessions upgrade atomically before reads and mutations when the new catalog
explicitly supports their old fingerprint. Valid earned hints survive; a former
completion hint clears because the expanded world has more discoveries. Revision
increments preserve the client ordering boundary. An unavailable or incompatible
replacement does not silently replace an existing validated session's world.

Public state adds `compatible_recipe_hashes`, containing only the verified older
fingerprints. Browser saves retain this bounded list. Concurrent saves with different
fingerprints merge only along one explicit compatibility direction, retain the newer
book and keep both successful recipe sequences for server replay. Legacy saves lacking
the metadata remain readable. No client guesses compatibility from similar contents.

The existing bounds remain: 128 concepts, 512 recipes, 48 later supplied concepts,
eight supply tiers, 32 goals, 128 saved craft pairs, 64 KiB requests and a 2 MiB catalog.
There are at most eight compatible historical versions. Session stores keep their
7200-second sliding TTL and 1000-entry cap. No score, account or ranking behavior changes.

## Review and verification

Both semantic reviews cover all 116 recipes. The unchanged 57 rows explicitly inherit
byte-compared prior judgments; 59 additions and 36 new descriptions receive independent
review. Two final judgments bind exact generated catalog bytes and the live replay audit
before the atomic package write. Nine runtime/source files are pinned, including the
historical candidate archive. The current fingerprint does not include editorial copy,
which can be corrected without changing learned recipes.

The serving audit exhausts the world with no goal and each of its 19 goals, then checks
every historical save prefix. Independent reviewers additionally test randomized
complete runs, partial migrations, unknown fingerprints and new-recipe rejection under
old authority. API and browser tests cover completed/live collections, pantry unlocks,
cross-tab unions and ordinary continued crafting after a real historical save restore.

Completed results, exact hashes and limitations are recorded in
[the expansion review](../reviews/v92-alchimie-more-concepts/README.md) and
[STATUS](../STATUS.md). The world remains finite and food-themed; automated checks do
not establish human playtest or physical-device acceptance.
