# V86 preparation and cooling graph authoring

Valid until: the proposed graph, source module or bound baseline changes — then treat as history.

Authored on 2026-09-08 against landed V85 plus its local landing record `14e8895`.
This document is the author's rationale, **not independent acceptance**. The exact
candidate is `graph-candidates.json`, SHA-256
`01069c928a5bd4087a2716575b928ad281d461036b2e0213ab4c090a8b32656f`.
The owned source module is `scripts/preparation_graph_v86_data.py`. Apply only through
the existing common-word transaction after independent factual/lexical review.
No fixture or pack has been edited by this authoring lane.

## Exact scope

Nine missing concepts: Frișcă, Albuș, Gălbenuș, Zahăr pudră, Lapte praf, Amidon alimentar,
Cremă de vanilie, Congelator and Mixer de bucătărie. They have 30 explicit grammatical
or qualified forms, 41 new directed links and no removed/reversed existing link.
No added form is counted here as a reviewed synonym. No new pack record is embedded.

All 39 proposed labels/forms were checked against 10,930 existing label/alias rows
and all 70 deliberate deferred terms: zero normalized collisions or deferred-term
intersections. The current runtime adds IDs and fuzzy/suggestion behavior; those
remain a separate before/after owner-preservation gate, not assumed from this scan.
Every new node has at least four meaningful incident neighbors and at least two
neighbors in the same gastronomic category. All 41 links are one-way; no reciprocal
ingredient link is invented to make a hidden target pass a degree gate.

| New concept | Incident neighbors | Incoming neighbors | Role |
|---|---:|---:|---|
| Frișcă | 8 | 5 | Smântână, vanilla, powdered sugar, mixer and refrigerator give distinct ingredient/tool/storage clues; supplies Savarină/Ecler/Înghețată |
| Albuș | 5 | 2 | Egg component, beaten by a mixer and used in named pastry variants |
| Gălbenuș | 4 | 1 | Egg component used in custard, ice cream and cozonac dough |
| Zahăr pudră | 5 | 1 | Finely processed sugar for cream and dusting named pastries |
| Lapte praf | 4 | 1 | Dehydrated milk used in homemade chocolate, ice cream and coffee |
| Amidon alimentar | 5 | 1 | Culinary starch, including corn-derived variants, thickens named preparations |
| Cremă de vanilie | 6 | 5 | Five real ingredients lead to the cream; the cream fills eclairs |
| Congelator | 5 | 1 | Freezer storage for a bounded set of documented foods; may be a refrigerator compartment |
| Mixer de bucătărie | 4 | 0 | Optional preparation tool for whipped cream, egg-white foam and dough/cozonac |

Incoming counts are not a promise of hidden-target eligibility. Frișcă and Cremă de
vanilie merit an independent fresh-target screen; source-only ingredients/equipment
remain useful typed inputs without becoming targets. The new Frișcă→Savarină link
also adds a defining opener to an existing, currently unserved target. Root owns all
new-round selection, critique and promotion decisions.

## Distinctions that must survive implementation

- Keep existing Frigider canonical. Its added equipment link says **some models**
  contain a freezer compartment. Ordinary refrigeration is not claimed to freeze
  ice cream. Congelator→Înghețată is the direct frozen-storage relation.
- Retire only the synthetic `congelator` row once the real node exists. Bare `mixer`
  stays in its current projection; native mixer labels/forms are all qualified.
  The existing audited-native vocabulary policy must count only the exact new owner.
- Bare `rece` is an adjective/state, not a missing concrete appliance or ingredient.
  No generic temperature node is created merely to accept that input. Răcire,
  congelare, gheață, gelatină and praf de copt remain outside this exact batch.
- Smântână→Frișcă explicitly names suitable sweet cream. Fermented sour cream is
  not universally whippable. Vanilla and sugar describe flavored/sweetened variants;
  natural whipped cream need not contain either. The refrigerator edge is storage,
  not a claim that cold alone creates whipped cream.
- Mixer actions are actions on existing ingredients. It beats egg whites and can
  knead dough with suitable attachments; it does not separate an egg or chemically
  produce its white. Hand preparation remains possible.
- Culinary starch is qualified; industrial/laundry uses are not captured. Corn is
  one possible source, not a claim that every food starch comes from corn.
- Milk powder is a processed milk ingredient. It is not synonymous with fresh milk
  or an infant formula. The familiar coffee use was chosen after a deeper check
  found the inspected biscuit-salami recipe used powder only for a special coating.
- Freezer storage is limited to documented ice cream, bread, selected milk variants
  and strawberries. The milk source cautions that whole milk can change texture.
  Storage labels contain no temperatures, times, health claims or safety advice.
- Cream ingredients retain variant qualifiers: some vanilla creams omit yolks or
  use flour instead of starch. Five parents are distinct actual ingredients, not
  five spelling variants of the same substance.

## Source evidence

Each exact edge index is bound to source IDs and original URLs in `graph-candidates.json`.
Sources were opened/searched directly; the notes below state only the narrow claim
used. Recipe/media/producer promotional nutrition claims are excluded.

- **egg_parts:** [Dictionary distinguishes yolk inside the egg and surrounding white; not interchangeable ingredients.](https://dexonline.ro/definitie/g%C4%83lbenu%C8%99/902347)

- **cozonac:** [The recipe puts yolks into dough and whipped whites into the walnut/cocoa filling. Author kneads using a mixer; variants are not universal.](https://jamilacuisine.ro/cozonac-cu-aluat-oparit-cozonaci-babani-si-pufosi-reteta-video/)

- **amandina:** [Cocoa sponge uses eggs; cream uses powdered sugar. Separate whipped whites are directly confirmed by the national-TV recipe source.](https://jamilacuisine.ro/prajitura-amandina-amandine-facute-in-casa/)

- **amandina_whites:** [The demonstrated recipe mixes the separately prepared egg-white and yolk masses into the sponge.](https://www.protv.ro/articol/39442-reteta-amandina)

- **pasca_whites:** [Original recipe beats whites to stiff foam then folds them into a crustless sweet-cheese Easter bake.](https://bucate-aromate.ro/2015/03/pasca-fara-aluat-cu-branza-de-vaci-si-multe-stafide/)

- **vanilla_cream:** [Manufacturer recipe lists five yolks, milk, sugar, starch and a vanilla pod for the pastry cream. Each is a direct ingredient in this variant.](https://www.oetker.ro/retete/r/crema-de-vanilie-cu-amidon)

- **yolk_icecream:** [Author recipe uses six yolks with milk, cream and vanilla for a cooked custard subsequently frozen.](https://jamilacuisine.ro/inghetata-de-vanilie-reteta-video/)

- **powdered_sugar:** [Producer states that powdered sugar is finely milled sugar and names doughnuts and crescent cookies among its dusting uses.](https://cio.ro/produse/zahar-pudra-500g)

- **chantilly:** [Test-kitchen recipe combines cream, powdered sugar and actual vanilla-pod seeds into an aerated cream. It is one whipped-cream variant, not a synonym claim.](https://www.dulceromanie.ro/mix-and-match/crema-chantilly)

- **milk_powder_process:** [Institutionally archived dairy research defines milk powder as dehydrated milk. Only the production relation is used.](https://rei.gov.ro/teza-doctorat-document/8291115e5e594d9c34e-Teza-de-doctorat-Ienovan_signed.pdf)

- **milk_powder_uses:** [Producer names use in homemade chocolate and coffee drinks; generic powdered milk is not made an alias for infant formula.](https://www.oetker.ro/produsele/p/lapte-praf-250g)

- **milk_powder_icecream:** [Gelateria original ingredient list contains skimmed milk powder in named ice-cream bases. No nutritional or superiority claim is used.](https://gelaterialaromana.ro/wp-content/uploads/2023/03/lista-ingrediente-la-romana-06032023.pdf)

- **whipped_cream:** [Equipment producer explains whipping chilled suitable sweet cream with a mixer, optional powdered sugar/vanilla, and keeping the finished foam cold. Fermented sour cream is not promised to whip.](https://www.hendi.ro/blog/cum-se-face-frisca-iata-cele-mai-simple-metode)

- **savarina:** [Author recipe decorates soaked savarinas with abundant whipped cream.](https://jamilacuisine.ro/savarine-de-casa-reteta-video/)

- **eclairs:** [Author recipe fills eclairs with vanilla cream and offers whipped cream as an optional addition.](https://jamilacuisine.ro/eclere-pas-cu-pas-reteta-video/)

- **whipped_starch_icecream:** [Retailer recipe for caramel ice cream thickens milk using corn starch and folds beaten whipped cream into the cooled base before freezing.](https://www.auchan.ro/inspiratie-si-savoare/retete-cu-imagini/inghetata)

- **starch_eclairs:** [Manufacturer uses starch in this mini-eclair dough variant and whips a cream filling. The starch link does not claim every eclair needs starch or yeast.](https://www.oetker.ro/retete/r/mini-eclere)

- **starch_product:** [Producer identifies corn starch and use in sauces; the graph keeps the culinary qualifier and does not capture laundry/industrial starch.](https://www.oetker-professional.ro/produsele-noastre/gustin-amidon-alimentar-fin)

- **freezer_manual:** [Manufacturer refrigerator/freezer manual assigns ice cream to freezer shelves and distinguishes the refrigerating compartment; supports a freezer component in some refrigerators, not ordinary fridge shelves freezing ice cream.](https://documents.beko.com/Refrigerator/7202947607/ro-RO/3450429551106844043.html)

- **freezer_storage:** [Producer lists frozen bread and selected pasteurized/semi-skimmed milk, and discusses berries generically. The whole-milk texture caveat remains; explicit strawberry processing is corroborated separately. No times or safety advice enter the graph.](https://www.arctic.ro/blog/idei-practice/congelarea-alimentelor-ce-mancare-se-poate-congela)

- **mixer:** [Manufacturer documents beating egg whites and dough attachments; equipment-to-ingredient labels describe actions, not physical creation of an ingredient.](https://www.philips.ro/c-p/HR3745_00/viva-collection-mixer)


## Required evidence after review

Run the supported graph preflight/apply only after the independent reviewer binds
these exact records. Recheck all prior native owners, qualified/bare exclusions,
projection retention, the two new cream neighborhoods and every new directed move.
Measure fridge/freezer→ice-cream and oven/yeast dessert controls in the actual APIs;
this authoring does not predict an exact new rank or assert every approximation is
fixed. Preserve all prior Alchimie projections, Lanț routes, frozen boards and pending
holds unless a separately reviewed, explicitly authorized decision changes them.

No alcohol-based value, new broad food hub, generic cooling abstraction, session
state or scoring policy is introduced in this module. Human recognition/fairness
and actual public round eligibility remain independent checks.


## Evidence corroboration before review freeze

Arctic's storage list names berries generically; explicit strawberry freezer processing
is separately corroborated by the producer below. The government source is used only
for the dehydrated-milk definition. The alternate original producer menu was checked through indexed recipe text after
direct PDF retrieval became unavailable; complete direct PDF access is not claimed.
These evidence changes leave every node, form, edge and source-module byte exact.

- **freezer_strawberries:** [Original Romanian producer explicitly describes strawberries passing through a continuous freezer, then being packaged and stored frozen. Only processing/storage evidence is used; its health claims are excluded.](https://comprodcoop.ro/capsune-congelate/)

- **milk_powder_definition:** [Original government text, Annex1 point2, defines milk powder as a dehydrated solid produced by removing water from milk. This corroborates the production definition only, without a present-day compliance claim.](https://legislatie.just.ro/Public/DetaliiDocument/175376)

- **milk_powder_icecream_alternate:** [Same producer original March2025 indexed menu lists skimmed milk powder in milk-chocolate and salted-caramel ice-cream bases. This corroboration uses indexed original recipe text; complete direct PDF access is not claimed.](https://gelaterialaromana.ro/wp-content/uploads/2025/03/meniu-romania-mar-2025.pdf)
