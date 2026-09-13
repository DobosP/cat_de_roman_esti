# Independent discovery-world reference review

Valid until: a change to the inspected reference mechanics or implementation proposal — then treat as history.

Inspected 2026-09-13 by discovery_review. Read AGENTS.md, CRITIQUE_RUBRIC.md A/E/F/G, ADR-0144, V92 recipe-freedom record and current STATUS. This is research/design evidence, not an approval of unreviewed new content.

## Primary observations

- Official [Little Alchemy 2 hints](https://hints.littlealchemy2.com/) encourage experiments without penalty; identify high-utility concepts; permit two-item/self combinations; describe non-craftable milestone unlocks and hiding final items. The page calls the game an educational crafting game enjoyed by millions, but no comparative popularity measurement was attempted.
- [Item types](https://help.littlealchemy2.com/general/item-types) distinguishes basic, unlockable, final and depleted concepts. Unlockable concepts appear after progress milestones or enough related discoveries. Final concepts have no further combinations; depleted concepts have had all combinations discovered. Both stay in the encyclopedia after leaving the work area. Page carries a 2017 update date and was re-read live today.
- [Encyclopedia](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia) retains all discoveries, permits category filters, explains concepts and relationships, records first discovery, and offers collection statistics. Page carries a 2017 update date and was re-read live today.
- [Hints](https://help.littlealchemy2.com/hints/using-hints) reveal a concept makeable from owned concepts without immediately naming the producing recipe. Monetization details are irrelevant to this implementation. Page carries a 2017 update date and was re-read live today.
- [Cloud saves](https://help.littlealchemy2.com/general/login-and-cloud-saves) describes continued progress across devices through login. Our anonymous browser-local progress does not claim this cross-device behavior. Page carries a 2017 update date and was re-read live today.

## Design inference for Alchimie

A stable shared recipe dictionary with a persistent collection, useful-next-discovery hints, and optional goals is a reasonable adaptation. Optional selected target challenges are our design, not a mechanic claimed by these reference pages. Goals must never change a pair's result or restrict the recipe dictionary. An exhausted concept is determined against the complete world, not current goal or currently owned partner concepts; otherwise useful ingredients may disappear too early.

Milestone ingredient unlocks can keep starting choice manageable while expanding the world, but the UI must explain why a supplied ingredient appears rather than imply it was crafted. Unlock policy and discovery counter must be deterministic, monotone and server-validated on restoration. Every promised final goal must remain reachable after rejected recipes are removed.

Do not reuse a raw union of target-projected books: existing context-dependent outputs and pruning are part of the original frustration. A separate reviewed canonical world should explicitly cover every accepted input pair. Category filtering is presentation only, never a recipe scope. Pair-density statistics alone do not establish quality: predictable physical transformations and recognizable, specifically meaningful associations matter more than graph-neighbor counts.

## Review guardrails

Every candidate needs exact pair/result IDs, labels, explanation, source URLs and binding to its generated source/catalog. Verify omitted physical steps or ingredients are honestly presented as a conceptual simplification. Prefer a direct transformation such as flour plus water leading to dough over arbitrary dish selection from two generic ingredients. Avoid cooking-time/food-safety instructions in game copy; conceptual discovery is sufficient. Review must reject misleading taxonomy, non-distinctive regional claims, and brand/person outputs chosen from generic inputs.
