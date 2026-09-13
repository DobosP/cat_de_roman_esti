# V92 — More Alchimie concepts

Valid until: changes to the reviewed catalog, compatibility mechanics or serving sources — then treat as history.

The owner requested additional concepts after the initial discovery world. Baseline:
`2257766`. Decision: [ADR-0146](../../adr/0146-expand-alchimie-and-preserve-collections.md).
Current integration state: [STATUS](../../STATUS.md).

## Content added

| Measure | Before | After |
|---|---:|---:|
| Collectible concepts | 75 | 111 |
| Crafted discoveries | 39 | 58 |
| Initial starters | 8 | 8 |
| Later pantry supplies | 28 | 45 |
| Canonical recipes | 57 | 116 |
| Results with alternative recipes | 18 | 40 |
| Reusable crafted discoveries | 12 | 23 |
| Terminal crafted dishes | 27 | 35 |
| Optional goals | 9 | 19 |

The additions are **19 crafted discoveries and 17 supplied concepts**. All identities
already existed in the KG. The [editorial delta](editorial-delta.json) lists every added
concept and proves preservation of the original recipe records, starters, supply tiers
and goals. The factual reviewer also byte-compared all 75 original concept records.
Base KG/pack/mobile inventories remain exact: [stock delta](base-stock-delta.json).

New discoveries include Sandviș, Clătite, Pizza, Cartofi prăjiți, Șnițel, Cașcaval pane,
Chiftele, Frigărui, Ciorbă de perișoare, Piftie, Zacuscă, Urdă, Mucenici, Alivenci,
Cornulețe, Turtă dulce, Halva, Colivă and Plăcinte. Bread, roast meat, bean spread,
salad, garlic sauce, pasta and jam gain further uses. New supplies unlock at 30 and
36 crafts; they do not count as crafted discoveries.

All 36 added concept descriptions were inspected. World-local copy corrects inherited
regional Mucenici wording, while complete source snapshots remain intact. An oven-to-crumb
draft shortcut was rejected; the crumb ingredient is supplied explicitly. The urdă/griș
papanași recipe names the sourced baked variant. Some canonical dish associations still
simplify preparation; explanations disclose omitted ingredients and cooking steps.

## Exact review and migration evidence

[Candidate](candidates.json) SHA:
`fc863ff35cebe88d1b2364fc3693f7d765bb33606d9a3191b1d8532540c37209`.
Both independent semantic reviews cover all 116 rows: 57 exact baseline judgments are
explicitly inherited and 59 additions are reviewed:
[factual](reviews/factual-review.json), [quality](reviews/quality-review.json).

Catalog SHA: `2ca7f281c801a4c2e044134c94dfcb29ff5e51a9c2d4982ba3076818f1040a6d`.
The [live audit](live-audit.json) binds nine runtime/source files and the exact catalog.
Two final acceptances precede the atomic package write:
[factual](reviews/final-factual-review.json), [quality](reviews/final-quality-review.json).

Original fingerprint `8b52b6ca9f7d83c804b8ed5cfb3489c6215b64b116583f1fc393569d551b182c`
is accepted only through the immutable reviewed baseline mechanics. The server validates
old saved pairs against that book, then replays them into the expanded world. Every old
recipe, supply and earned concept is preserved. Unknown hashes and new recipes claimed
under old authority are rejected. Existing live sessions upgrade before reads/mutations;
completed old collections can discover again. Browser unions keep the newer book only
when explicit server compatibility allows it.

The runtime audit covers free play, all 19 goals and every historical save prefix.
Independent migration review additionally checked 780 prefixes across 20 randomized
old-world orders. The factual reviewer completed 100 randomized new worlds, 100 current
checkpoint restores and 100 historical-save migrations. These are automated audits,
not human playtests or measurements of player enjoyment.

## Integrated verification

Exact commands, final counts, source fingerprints and intermediate failures are in
[verification](verification.json). Final gates: **1805 backend, 53 accounts, 209 native
frontend and 444 browser checks pass**. Backend checks cover archive tampering, preservation
of original rules, partial/completed migration, live upgrades, hint retention and bounded
state. Native save tests cover cross-version concurrent writes and unknown versions.
The real-browser regression restores the original three-discovery checkpoint, retains
its pantry supplies and chosen goal, crafts again and reloads successfully.

An intermediate focused run passed 102 checks and failed the old test that limited
description overrides to four concepts. That assertion now still requires exactly the
four original fixes within the original inventory, while permitting independently
reviewed descriptions for the added concepts. No historical source or review was restamped.

The expansion stays local on the V92 task branch. No deployment, human playtest,
physical-device acceptance or cross-device account synchronization is established here.
