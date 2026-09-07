# V85 independent ingredient graph review

Valid until: the bound graph proposal, authoring module or native projection policy changes — then treat as history.

**Accept the exact eight concepts, 25 forms and 40 links.** This review was performed by
the board-clarity worker, independently of the ingredient proposal's author. No graph or
runtime implementation files were edited during this review. The complete per-concept,
per-form and per-edge verdicts are in [graph-review.json](graph-review.json).

- Authoring module SHA-256: `cee50de77b278879dadf083a69a8381a2d864c61092c19d330c43d2051e2cf53`.
- Candidate JSON SHA-256: `be8e06af36b6b0e389ef1cc879ba8be6fb2a27b6ed0c960a78f0a2dde4fddd2b`.
- Baseline: `39b64cb`; KG SHA-256: `3fb0f97c5b4c813eb72d8fd3589c4ce92f724d0565db840c1bc3909458a60ab0`.
- Every source edge index `0`–`39` and every explicit alias has an acceptance row; none
  is omitted or inferred as accepted from another row. No existing edge removal is proposed.

## Concepts and forms

| Concept | Forms | Review result |
|---|---:|---|
| Scorțișoară | 3 | Recognizable bark spice; genitive and ground/stick forms preserve that meaning. |
| Cacao | 3 | Edible powder; articulated and genitive forms plus qualified powder. Prepared hot drinks keep their existing separate projection. |
| Vanilie | 3 | Culinary ingredient from the pod; synthetic vanillin is not an alias. |
| Ciocolată | 3 | Common chocolate product; plural/genitive and cooking-chocolate form. No claim that every chocolate contains cocoa powder. |
| Stafide | 3 | Dried grapes; regular singular and articulated plural/genitive. Fresh grapes remain a different concept. |
| Migdale | 4 | Edible sweet-almond kernels; regular forms and the explicit sweet variant. |
| Alune de pădure | 3 | Qualified hazelnut identity; every form retains the qualifier and leaves bare alună unresolved by this node. |
| Semințe de floarea-soarelui | 3 | Qualified edible seed identity; bare plant name and generic semințe are not captured. |

The uncommon spelling check was explicit: [DEX/DOOM's cacao entry](https://dexonline.ro/definitie/cacao)
supports `cacaua`; [DMLR's cacauă entry](https://dexonline.ro/intrare/cacau%C4%83/7526)
explicitly gives `cacauei`. This genitive is also attested in
[Romanian institutional prose](https://eur-lex.europa.eu/legal-content/RO/TXT/?uri=CELEX%3A52010PC0705).
The bare cacao page did not expose that paradigm during this review, so the separate exact
entry is the checked source. The new aliases do not include `cacaoa` or artificial flavorings.
These are 25 grammatical/qualified forms, not 25 newly introduced synonyms.

## Specificity and actual variants

Cinnamon in [apple-pie filling](https://jamilacuisine.ro/placinta-cu-mere-reteta-video/),
[gingerbread](https://www.oetker.ro/produsele/p/mix-pentru-turta-dulce) and
[boiled Muntenian mucenici](https://jamilacuisine.ro/mucenici-muntenesti-fierti-reteta-video/)
is directly supported. The mucenici edge names the boiled variant. The apple-pie recipe
also supports butter in a pastry variant and explicitly acknowledges other doughs.

Cocoa and raisins are directly present in the original
[biscuit-salami recipe](https://jamilacuisine.ro/salam-de-biscuiti-facut-in-casa-reteta-video/).
The [amandina recipe](https://jamilacuisine.ro/prajitura-amandina-amandine-facute-in-casa/)
uses cocoa in sponge and cream and chocolate in its chosen glaze. A separate
[chocolate biscuit-salami recipe](https://desertdecasa.ro/salam-de-biscuiti/) confirms that
variant without pretending cocoa powder and chocolate are interchangeable identities.

The original [eclair recipe](https://jamilacuisine.ro/eclere-pas-cu-pas-reteta-video/)
uses a vanilla pod and offers grated chocolate in the cream. Original
[ice-cream](https://jamilacuisine.ro/inghetata-de-vanilie-reteta-video/),
[crêpe](https://jamilacuisine.ro/clatite-clasice-frantuzesti-pufoase-si-delicioase-reteta-video/),
[pască](https://jamilacuisine.ro/pasca-cu-aluat-de-cozonac-reteta-video/),
[poale-n brâu](https://jamilacuisine.ro/poale-n-brau-pas-cu-pas-reteta-video/) and
[cozonac](https://jamilacuisine.ro/cozonac-cu-aluat-oparit-cozonaci-babani-si-pufosi-reteta-video/)
recipes support the corresponding vanilla, cocoa and raisin variants. For chocolate as a
cozonac filling, the newer chocolate-cream recipe is corroborated by the original author's
[2016 chocolate-piece alternative](https://www.reteta-video.ro/retete/cozonac-pufos-cu-umplutura-de-nuca-stafide-si-cacao-cu-aluat-neoparit.html).

The five nut-category links use the Romanian culinary category expressly listing almonds,
hazelnuts, walnuts and pistachios in
[Annex II item 8](https://eur-lex.europa.eu/eli/reg/2011/1169/2013-12-06/ron/pdf).
They do not assert identical botanical fruit structure, plant family or interchangeability.
[Actual almond flakes](https://www.bucataras.ro/retete/biscuiti-cu-migdale-63417.html),
[almonds in crescent-cookie dough](https://teoskitchen.ro/2017/09/cornulete-cu-migdale.html),
[hazelnuts in biscuits](https://www.pakmaya.ro/reteta/biscuiti-cu-alune-de-padure) and
[hazelnuts with homemade chocolate](https://www.roberteisler.ro/retete/ciocolata-de-casa-1)
give these nodes concrete uses beyond category links. The homemade chocolate source also
supports the deliberately limited cocoa-powder-to-chocolate relation; industrial cocoa mass,
cocoa butter and white chocolate are not conflated with this recipe.

[Feleacul's product ingredients](https://feleacul.ro/produse/halva) support sunflower-seed
halva and its cocoa variant. The seed links to
[oil](https://sanovita.ro/blog/de-ce-folosesti-ulei-presat-la-rece-in-bucataria-ta/),
[bread](https://savoriurbane.com/paine-neagra-cu-seminte-diana/) and
[salad](https://sanovita.ro/blog/salata-vitality-cu-telina-si-seminte/) describe specific
production or recipe uses. Unrelated nutritional and promotional claims on these pages
were excluded from the graph review. Source access occasionally required a later successful
fetch or the same primary author's indexed text; inaccessible interstitials were not evidence.

## Independent structural and projection checks

A read-only probe loaded the actual Git baseline and the frozen proposal into separate
resolver instances. All **10,897 old authored label/alias rows** retain the same exact owner.
All **33 new label/form rows** resolve exactly to the intended new owner, with zero old-owner
collisions, zero internal collisions and zero intersections with the 70 deferred terms.
The module's node/edge payload equals the JSON proposal. All endpoints exist, all 40 edge
keys are unique and the five category pairs produce exactly **45 allowed directions**.
Incident-neighbor counts are 4/6/6/7/5/5/5/4; these are not all outgoing moves or hidden-target
eligibility. This ownership probe does not claim a full synthetic/fuzzy-suggestion audit.

The projection review independently reconstructs V84's Python inventory from Git:
exactly `scorțișoară` and `cacao` are retired, and all **469 retained projection records**
remain exact. Alună, floarea-soarelui, cappuccino, espresso, cafea cu lapte and ciocolată caldă
keep their original projections. No new approximation or rank-penalty change is introduced.

`NATIVE_PROJECTION_REPLACEMENTS` is accepted as audit-only metadata. Its four exact rows
name Nucă, Drojdie, Scorțișoară and Cacao with their native IDs and original audited domains.
All four resolve to the native owner and have no projection. The tuple has no production
resolution/scoring consumers. Its canonical metadata SHA-256 is
`eadfdfb8313281a99bf7752815913dc77a4fe69113f93fd1cc6111b8274cc64b`.

The distinction must remain explicit: V84's synthetic-only minimum is 14; V85's is 13;
the accepted native-plus-synthetic vocabulary still has a minimum of **14 per domain**.
The unchanged historical inventory test retains the old 471-row/14-floor contract. The
new ADR must explain this native migration of the coverage measure. Historical domain
provenance, especially Cacao's beverage domain, is not a new taxonomy or scoring claim.

## Remaining release work

No factual or lexical revision is required for the bound proposal. The root session still
must run the protected graph transaction, graph/pack validators and the actual six-game
impact and integration checks. The true Condiment type edge can still produce indirect
ranking noise. Good source facts alone do not guarantee calibrated temperatures, satisfying
recipes or fair new curated boards. New target/round promotions need their separate rubric
review; this acceptance neither promotes stock nor substitutes for Romanian-player testing.
