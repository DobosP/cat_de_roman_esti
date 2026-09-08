# Independent V87 raw quality screen

Valid until: the raw candidate, reviewed graph or bound scoring inputs change — then treat as history.

Reviewed 2026-09-08. The six-target raw file is bound by
`b64deecee12dd3177d69367b738f56e76b6fd244684ad9c5f7f6ca2cc6a2f12e`.
This lane did not author that file or the graph. The preliminary `keep` decisions
allowed pending staging; final promotion required the separate dossier-bound reviews.

## Recognition and playable cores

| Target | Incoming links | Salience | Responsive concepts | Final raw assessment |
|---|---:|---:|---:|---|
| Biscuit | 11 | .87 | 1,727 | Familiar flour/butter/sugar/oven core now hot |
| Chec | 6 | .85 | 941 | Flour/egg/sugar/oil core; related Pandișpan stays nonwinning |
| Cremșnit | 5 | .75 | 1,072 | Vanilla cream, milk/starch/powdered-sugar core; pastry-type cue repaired |
| Tort Diplomat | 5 | .75 | 774 | Pișcot, whipped cream, gelatin and fruit core; broad tort cue repaired |
| Pișcot | 5 | .80 | 675 | Flour/egg/sugar preparation; Biscuit type cue repaired |
| Ciocolată | 5 | .90 | 1,249 | Cocoa and solid-chocolate recipe inputs; related hot drink remains nonwinning |

Incoming counts are actual directed predecessors, not total degree. Recognition was
checked separately from numeric salience. [Cremșnit's published recipe](https://jamilacuisine.ro/prajitura-cremsnit-pas-cu-pas-reteta-video/)
and [ProTV's independent recipe](https://www.protv.ro/articol/39741-reteta-cremsnit)
support a familiar named pastry. The same is true for [Tort Diplomat](https://jamilacuisine.ro/tort-diplomat-facut-in-casa-reteta-video/)
and [ProTV's version](https://www.protv.ro/articol/38901-diplomat).
[Pișcot's dictionary definition](https://dexonline.ro/definitie/pi%C8%99cot)
supports the biscuit family cue. [Robert Eisler's homemade chocolate](https://www.roberteisler.ro/retete/ciocolata-de-casa-1)
uses liquid milk in a mixture set in a frame and cut into pieces; that edge supports
the solid target, separately from the retained hot-drink projection.

Pandișpan and Brioșă remain usable graph inputs but were deferred as hidden targets.
[A recipe titled Chec](https://bucate-aromate.ro/2019/07/chec-cu-visine-si-cacao/)
also uses Pandișpan naming, creating avoidable double-target ambiguity.
[Brioșă's dictionary sense](https://dexonline.ro/definitie/brio%C8%99%C4%83)
and [modern muffin usage](https://www.reteta-video.ro/retete/briose-muffins-cu-mere-iaurt-si-topping-crocant.html)
span different recipe families. Deferral preserves the useful ingredient inputs while
avoiding an unsupported claim that all nine new concepts make equally fair targets.

## Actual private journeys and focused corrections

`quality-before.json` records 257 first guesses and six complete private sessions:
cold guesses, a private clue, repeated input, resumed state and an exact winning answer.
These sessions use the real API over private registered targets; no public-selector
claim was made before promotion. Five affected scopes were then rechecked with 215
first guesses and five complete sessions in `quality-after-five-scopes.json`.
Biscuit's unchanged target scope reused its original journey plus the new Tort column.

The defining misses were Pandișpan→Chec 463/cold, Biscuit→Pișcot 714/cold,
Prăjitură→Cremșnit 254/cold, unrecognized generic Tort, and hot chocolate→solid
Ciocolată 501/cold. The first three use reviewed native target-specific feedback pairs.
The latter two use separate projected exact-target neighborhoods with direct-neighbor
expansion disabled. All five become rank 2/hot and retain their native/projected guess
identity without winning. Generic Tort has a food sense supported by
[the dictionary](https://dexonline.ro/definitie/tort); its secondary textile sense is
disclosed, and the input is not claimed as a synonym for Diplomat.

Final source verification found and closed one interaction: Tort's Prăjitură fallback
must not inherit the native Prăjitură→Cremșnit exception. Six focused final API cases
confirm the five intended hot cues and Tort→Cremșnit cold at 255. Source inspection
shows Tort is the only projected base anchor overlapping an exact-native source;
old projections are unaffected by the new isolation guard. Native scoring/clues retain
their original path, and projected typo filtering uses the same isolation boundary.
The audit-only Brioșă→Chiflă representative change leaves scoring rows and other audit
examples exact. [Both binding checks](../feedback-isolation-review.json) accompany
[the audit proof](../audit-representative-change.json), so intermediate probe hashes
are not presented as if they already contained the final guard.

## Limits retained

This is an agent quality review with Romanian source checks, not a Romanian-player
playtest. Broad Prăjitură cues for Chec/Diplomat remain lukewarm; optional butter/dairy
recipes and reciprocal Pișcot→Biscuit can be too cold. Savory Sarmale associations
remain too warm. Later old-target impact capture also records the Brioșă→Pâine
regression caused by retiring its broad bread projection. These limitations remain
visible in [the impact review](../impact/IMPACT_REVIEW.md); changed ranks are not all
counted as improvements. No Lanț round was added merely to increase the batch count.
