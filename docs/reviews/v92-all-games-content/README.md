# V92 — more reviewed content across the arcade

Valid until: any bound content, runtime source or review artifact changes — then treat as history.

This wave starts from local V92 commit `75584bf`, after the 221-concept Alchimie kitchen
expansion. The owner requested comparable content growth for the other games while keeping
quality high. The local catalogs now include **70 additional rounds**: 25 curated pack
records and 45 separately reviewed Intrusul/Perechi boards. There are no new shared KG
identities or links. Alchimie's 221 concepts, 285 recipes and 32 optional goals remain exact.

| Game | Added rounds | Local total after this wave |
|---|---:|---:|
| Conexiuni | 4 | 238 |
| Cald sau Rece | 8 | 252 |
| Lanțul Cuvintelor | 13 | 113 |
| Intrusul | 25 | 208 |
| Perechi | 20 | 173 |

All 25 new pack records passed promotion and ranking eligibility. The existing eight
pending records remain pending. The four-game pack is **686 records: 678 approved and
eight pending**, including the unchanged 83 Alchimie challenges. The 45 quick-game additions
all pass the established preferred-score floor; 19 Intrusul and 16 Perechi additions also
qualify for their starter shelves. This archive records automated checks and independent
editorial judgments. Human playtesting, physical-device acceptance and deployment have not
been performed. [Final integration verification](verification.json) records **1934 backend,
53 accounts, 212 frontend-native and 446 browser passes**, plus lint/typecheck, both content
validators, whitespace and documentation gates. Product frontend/static bytes remain exact.

## New content and exact exclusions

The four Conexiuni boards introduce 16 fresh groups spanning useful household objects,
cooking ingredients and concrete wordplay. One board connects the different meanings of
tails, sheets and wheels alongside net sports. The beginner boards use precise functional
predicates. The final full-inventory critique, including rejected-board debt, finds no
reused three-of-four quad, half-board reskin, unfair tile or contested tile in the additions.

The eight Cald sau Rece targets are **Televizor, Florin Piersic, Amza Pellea, Sare, Usturoi,
Minge, Cheie and Ghiozdan**. Every target has at least five native incoming neighbors, but
approval also used actual guess feedback. Ghiozdan gives school/book/pencil-case approaches;
Minge gives football/tennis/volleyball approaches; the actors have distinctive role and
biographical cues. Existing scorer limitations remain explicit: for example, unqualified
`emisiune` needs the recognized `Emisiune TV` form, and key-related `lacăt`/`încuietoare`
vocabulary is absent. This wave does not claim universal improvement to every association.

The 13 new Lanț rounds offer two-step bridges with multiple credible first hops, including
Zahăr→Cremșnit, Avion→București, Sibiu→Muzeu and named literary, historical and sporting
associations. Independent real-API verification replays all **34 representative routes and
68 steps**. Numerical branching was not treated as sufficient evidence: many potential
routes relied on generic category links or incidental associations and were not proposed.

The [complete exclusions report](pack/exclusions.json) records **12 of the 37 raw pack
proposals** that did not advance:

- Six Contexto proposals had misleading defining feedback: Apă, Ou, Făină, Avion,
  Calculator and Arena Națională. Examples include a freezing screen guess for Calculator
  and weak stadium feedback for Arena Națională.
- Muzeul Satului had an overstated description; Dem Rădulescu had an unsupported strong
  film association. Their existing graph records were not silently edited to rescue them.
- Celentano→Mihai Bobonete depended on pub framing, Electricitate→Dunărea had a weak
  incidental bridge, and Ghiozdan→Ion Creangă exposed implementation language in a route.
- One Conexiuni board remained a weak classification exercise anchored by duration units.

Two narrow label corrections preserve an otherwise good Conexiuni board: **Se pot servi
cu lingura** and **Căi folosite și pentru mersul pe jos** avoid statistical or exclusive-use
claims. Only these two strings changed. The [correction receipt](pack/label-correction-receipt.json)
binds both versions; [the original changed-category candidate and factual review](pack/original-viata-de-roman/)
remain exact. Nine other category files are byte-identical to their first review inputs.

## Independent quick-game content

The 25 Intrusul additions use recognizable predicates such as rail transport, facial parts,
geometry instruments, precipitation and household storage. The 20 Perechi boards combine
practical pairs with familiar Romanian culture: broom/dustpan, flour/dough, writer/work,
actor/character and athlete/discipline. All 80 intended pairs are different within this
wave; 73 were absent from the old Perechi catalog. The additions expose 92 concepts previously
unseen in Intrusul and 130 previously unseen in Perechi; those are game-exposure counts,
not newly created graph concepts.

The [editorial source](../../../scripts/quick_game_content_source_v92.py) produces the exact
[candidate](quick/candidates.json). The old **336 derived boards remain fully exact**, with
183 Intrusul and 153 Perechi rows. Their frozen source set is not widened. The new
[installed supplement](../../../cat_de_roman_esti/fixtures/quick_games_v92.json) has SHA-256
`36f5fc575ed5ae36735d792dd71df5860d917dba1b3b58090f792afd4f3b0d39`; its bytes equal the
reviewed proposal, so the archive does not duplicate the entire installed catalog.

All new Intrusul trios meet the same-type, two-strong-link and disconnected-intruder gates.
All Perechi intended pairs meet the strong-link floor, while all unintended on-board pairs
remain below it. [Independent mechanical checks](quick/independent-quality-mechanical.json)
also confirm no repeated old Intrusul trio, at most two shared concepts with any old board,
and at most one shared concept between two new boards of the same game. Independent semantic
reviews separately test plausible alternative partitions; a missing graph edge alone is
not proof that a pair is unreasonable.

Both [factual](quick/factual-review.json) and [quality](quick/quality-review.json) reviews cover
all 45 raw rows and bind candidate SHA-256
`5a8cd3aefce8807f6314e5ce372d99ea289db6420e736b2515ccaf908a5e3257`.
Every accepted factual judgment carries references. Culinary shell/kernel wording avoids
misclassifying almonds as botanical nuts. The cacao intruder uses the exact powder identity.
Bobiță's accepted pairing is actor/character recognition; it does not authorize pub-themed
or alcohol-dependent content. The excluded Celentano ladder required that different framing.

The [live audit](quick/live-audit.json) naturally selects and solves all 45 additions through
real API endpoints, checking hidden labels, private source/catalog IDs and persistent wins.
Its exact SHA-256 is `6709af51085192b8359d94567674de871515bd80aecf66f1863f9c4e5ccac080`.
Both reviewers independently reproduce it. A second factual pass uses the actual runtime
loader with only the unpublished proposal path substituted. A second quality pass checks
all 45 boards through wrong attempts, free repeats, earned hints, pre-win GET privacy and
650-point hinted wins. The exact [final factual](quick/final-factual.json) and
[final quality](quick/final-quality.json) acceptances bind the proposal, audit and original
reviewer identities before package writing. All eight runtime source pins are recorded.

## Clearer Lanț relationship captions

The new routes exposed an existing display problem: one grammatical edge caption was shown
unchanged in both directions, producing assertions such as the sea flowing into the delta.
The [original finding](captions/original-direction-finding.json) is preserved. No graph edge,
direction, weight or shortest path changed.

The finite [caption module](../../../cat_de_roman_esti/wordgames/lant_relations.py) supplies
**68 reviewed noun-phrase captions**, such as an author and work or a river and its mouth.
They identify the relationship without assigning its grammatical verb to the wrong end.
The override is bound to each full edge snapshot and applies whenever that exact pair is
displayed, including existing rounds that traverse it. Unmapped or changed edges use neutral relation-type wording;
missing edges produce no caption. This is a bounded caption repair, not a general rewrite of KG facts.

The exact [candidate](captions/candidates.json) and
[independent factual review](captions/factual-review.json) preserve all 68 judgments, full
edge digests, reverse-traversal observations and 340 changed-edge fallback checks. The
candidate also records the reviewed module digest. Final Lanț dossiers were regenerated
after the caption repair, and their real API routes were checked again.

## Evidence and provenance

The [evidence manifest](evidence-manifest.json) records exact copied bytes, hashes and scratch
origins. Original judgments, including spelling and whitespace, have not been rewritten.
It covers the preserved evidence files, not future integration reports or this narrative.

- [Raw final pack candidates and both reviews](pack/candidates/) retain all 37 references,
  including exclusions. [Authoring snapshots](pack/authoring/) and the correction receipt
  show how the two versions were generated. Unused scout ideas are historical authoring
  material, never approved content.
- [Allocated IDs](pack/staged-ids.json), [analyst judgments](pack/analyst.json),
  [adversarial verifier judgments](pack/verifier.json), and the complete [portable gate](pack/gate/)
  preserve one set of 25 bound dossiers and the three final verdict artifacts. Dossiers are
  stored once inside the gate directory. [Promotion output](pack/promotion.log) records the
  strict prospective check and 25 actual approvals.
- [Contexto candidate probes](pack/contexto-candidate-probes.json) retain weak as well as
  strong observed feedback. [Independent final Contexto journeys](independent/contexto-journeys.json)
  and [Lanț journeys](independent/lant-journeys.json) distinguish fixed-session API checks
  from public-selector testing. The [Contexto development correction](independent/contexto-development-correction.json)
  records the unsuccessful unqualified input instead of hiding it.
- [Independent factual quick-game receipt](quick/independent-factual-receipt.json) and
  [independent quality replay](quick/independent-quality-replay.json) preserve separate
  checks against baseline `75584bf` and the exact current catalog. Duplicate audit output,
  test scratch directories and whole scout inventories are deliberately not copied.

The governing pack workflow remains [PACK_ONLY_CONTENT_WAVES](../../PACK_ONLY_CONTENT_WAVES.md).
Current product state belongs in [STATUS](../../STATUS.md). The continuation branch remains
local V92; this evidence does not claim a production release.

## Final integration

The [content delta](content-delta.txt) and [identity-level report](content-delta.json)
compare the final catalogs with `75584bf`: 70 additions, no removed or changed previous
records, and no graph changes. The report includes the new authored supplement.
[Backend](backend-tests.log), [accounts](accounts-tests.log) and [browser](browser-tests.log)
logs preserve the completed final runs. Original historical review pins remain intact;
tests reconstruct exact predecessor artifacts before checking earlier waves.
