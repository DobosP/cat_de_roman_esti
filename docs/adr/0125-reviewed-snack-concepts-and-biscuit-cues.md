# ADR-0125: Connect familiar snacks to their defining ingredients

- Status: accepted
- Date: 2026-09-08

## Context

V86 deferred Biscuit: tea, nuts and oats were hot, but flour, butter, sugar and dessert
guesses were weak despite ordinary biscuit recipes. Several familiar baked goods and
their distinct leavening/setting inputs are missing. These gaps fit one coherent batch.

## Decision

Add nine independently reviewed snack/preparation concepts, 31 accepted forms and 50
specific directed links, including defining ingredient/preparation cues for Biscuit and
solid-chocolate variants. One form is the documented Cremșnit/cremeș lexical equivalent;
the other 30 are grammatical or qualified forms. Keep baking powder, bicarbonate
and yeast distinct. Qualify recipe variants and chemical/culinary senses. Do not manufacture
reverse arrows or filler relationships to make a target pass its recognition/neighborhood gate.

Promote six independently reviewed easy Contexto rounds (`ct_gastronomie_346`–`351`):
Biscuit, Chec, Cremșnit, Tort Diplomat, Pișcot and Ciocolată. Eligibility rises from 229
to 235. Their actual feedback supplies recognizable incoming cues and distinguishes
related baked goods; approval is bound to each complete candidate dossier. Keep the
Brioșă/brioche/muffin sense issue explicit rather than treating these as full synonyms.

Keep Pandișpan and Brioșă as inputs while deferring their hidden-target rounds. Retire only
Chec and Brioșă's approximate Pâine projections; their native nodes have real outgoing
associations as well as ingredient parents. The affected domain retains 19 synthetic rows,
so no vocabulary-floor change or additional audit tuple is needed. The other 466 projection
rows and all four prior native-audit tuples stay exact. No old graph edge is removed.

Replace the audit-only `mâncare gătită` representative Brioșă→Pâine with the retained
Chiflă→Pâine projection after Brioșă becomes native. The other 25 domain representatives
remain exact. This metadata correction changes no scoring behavior, vocabulary floor or
native-audit tuple; its exact source comparison is retained in the V87 review.

Use the existing closed feedback mechanism for Pandișpan→Chec, Biscuit→Pișcot and
Prăjitură→Cremșnit. Their initial family/type guesses ranked 463, 714 and 254, all cold.
Keep their native identities and nonwinning feedback; do not add reverse graph edges.

Add the separate projected guess “tort” using the existing Prăjitură anchor, with an
exact-target-only Tort Diplomat override. The food meaning is explicit; the secondary
textile sense is not a global native owner or synonym. This cue cannot win for Diplomat,
and no neighboring targets inherit the override. There are 467 projection rows after
the two retirements and this one addition; the six previous native pairs remain exact.
Keep the projected hot-chocolate identity and its Tea fallback, while adding a closed
solid-Ciocolată override for that exact drink guess. Its initial rank 501/cold is a poor
ingredient-family response. Related words remain nonwinning; the drink is not an alias
for solid chocolate and no surrounding target inherits this override.

Keep projected and native exact-target policies separate when scoring and filtering typo
suggestions. Projected words retain legacy proxying but do not inherit an exact native
pair through their fallback anchor. Without this guard, Tort would silently inherit the
Prăjitură→Cremșnit exception. The intended five source/target repairs stay explicitly bounded;
the ranking formula, ordinary native behavior and session limits remain unchanged.

## Acceptance

Require independent exact graph review, supported graph transactions, both validators,
separate bound content judgments, public typed journeys and the six-game integration matrix.
Retain old owners and historical snapshots, measured game profiles, session/request bounds
and private answers. Report changes and residual noise independently from raw record counts.
