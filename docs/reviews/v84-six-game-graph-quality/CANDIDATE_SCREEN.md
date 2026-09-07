# V84 curated kitchen candidate screen

Valid until: exact raw candidates, authored graph, runtime scoring or rubric changes — then treat as history.

Reviewed 2026-09-07 against root module kitchen_graph_v84_data.py, with 15 new nodes, 57 edges, qualified Cuptor de bucătărie and removal of de520. Raw file: gastronomie/candidates.json. SHA-256: ecbe2c60260a886cbdd3de1ecdc688cd4f163d03ce33226d8a83d4264de16ca2. This research task has written only scratch artifacts. Raw keep means eligibility for pending import; it does not confer promotion.

## Four proposed instances

| Raw reference | Instance | Difficulty | New value |
|---|---|---|---|
| contexto[0] | Plăcintă cu mere | usor | First round for this target; specific apple, dough and equipment routes replace its former one-neighbor isolation. |
| contexto[1] | Salam de biscuiți | usor | First round for this target; defining biscuit and common butter-variant inputs now work directly. |
| contexto[2] | Pâine | usor | First round for the generic bread target; dough, yeast and qualified oven are direct clues, and flour improves from cold to warm. |
| lant[0] | Făină → Cornulețe | usor | Two-hop route gains a precise dough alternative alongside an older seasonal baking route. |

Inventory review found no existing record for any of the three Contexto target IDs, including pending records, nor either bread subtype as an approved round. Făină→Cornulețe is absent from current Lanț inventory and the rejection tombstones. Current high-water marks predict Contexto IDs ct_gastronomie_334–336 and Lanț lt_gastronomie_220; the importer remains authoritative.

## Factual and recognition checks

Plăcintă cu mere is an ordinary apple-filled pastry, not a specialist regional claim. [Dr. Oetker’s recipe](https://www.oetker.ro/retete/r/placinta-clasica-cu-mere) documents apples, dough and baking equipment. [Paste Băneasa](https://www.pastebaneasa.ro/retete/placinta-cu-mere/) explicitly describes homemade sheets rolled with a sucitor in its indexed excerpt. Direct access returned a verification screen; this is not claimed as a full-page read. The [Arad library recipe excerpt](https://digital.bibliotecaarad.ro/files/original/d64f6b3103080d1994b6f1de452a49ce9e54c086.pdf) and [2014 national-news Christmas menu](https://www.digi24.ro/stiri/actualitate/social/cat-costa-masa-de-craciun-produsele-traditionale-maresc-de-trei-patru-ori-cheltuielile-338418) independently support ordinary Romanian familiarity. No recipe quantities are copied.

Salam de biscuiți is the concrete biscuit dessert; the qualified title distinguishes it from meat salami. [RRI](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/salam-de-biscuiti-id594218.html) describes its established domestic history and a recipe with biscuits and butter. A [2023 PRO TV segment](https://www.protv.ro/emisiuni/vorbeste-lumea/clip/52864-salam-de-biscuiti-cu-fistic-si-merisoare) and [current recipe coverage](https://www.protv.ro/emisiuni/vorbeste-lumea/articol/127232-florenta-a-cucerit-bucataria-vorbeste-lumea-cu-doua-variante-delicioase-de-salam-de-biscuiti-nu-stiam-ca-se-face-atat-de-usor-un-salam-de-biscuiti) provide mainstream recognition signals. Butter is explicitly a variant ingredient; the graph does not claim it is obligatory or imply baking is required.

Pâine is the familiar staple sense. [Historical and current dictionary entries](https://dexonline.ro/intrare/p%C3%A2ine/40183) establish longstanding Romanian recognition and its flour/dough/oven associations. The [manufacturer’s bread preparation](https://www.oetker.ro/retete/r/paine-cu-maia) independently confirms wheat and rye flour, dough, water, yeast and oven in one documented variant. Bread without baker’s yeast also exists, so no universal yeast requirement is asserted. All 18 incoming graph neighbors were inspected: bread subtypes, spreads, knife, dairy snack, packed/family meal contexts, food and the four new production inputs. This is generic Pâine, not a relabeling of the previously deferred Pâine de casă proposal.

For Lanț, [the aluat dictionary](https://dexonline.ro/definitie/aluat/322624) supports flour-to-dough, and [Ferrero’s cornulețe method](https://www.nutella.com/ro/ro/lasa-te-inspirat/retete/cornulete-cu-fructe-uscate) supports shaped dough-to-cornulețe. [Dr. Oetker’s cozonac ingredients](https://www.oetker.ro/produsele/p/mix-pentru-cozonac) support the alternative opening. The older Cozonac→Cornulețe association is grounded in shared holiday baking, attested by [Digi24’s Christmas menu](https://www.digi24.ro/stiri/actualitate/social/cat-costa-masa-de-craciun-produsele-traditionale-maresc-de-trei-patru-ori-cheltuielile-338418) and [Profi’s named cornulețe recipe](https://www.profi.ro/practic/retete/desert/reteta-de-cornulete-fragede-cu-nuca/). It is a semantic association, not physical conversion. The second path is weaker and must receive explicit D2 scrutiny from the bound judges.

No adult framing, alcohol-dependent puzzle value or unsupported exclusive-region claim is used. These source checks establish factual and cultural plausibility, not human enjoyment.

## Prospective scoring evidence

The scratch harness constructs an in-memory graph from baseline Git bytes plus the exact root module, removes the exact rejected edge, and calls the actual WordGameService and Contexto scoring functions. It does not mutate fixtures or imitate the scoring formula. It finds 2,304 nodes reaching each candidate; within three hops the counts are 101, 260 and 400 respectively. All three pass the actual Contexto payload validator. Raw incoming degrees are 5, 6 and 18.

- Apple pie: Plăcinte rank 2 hot; Măr, Aluat, Sucitor and Tavă de copt rank 3 hot; Făină 11 hot; Mâncare 21 and Desert 26 warm. Train 1,216 very cold and football 458 cold. Limitations: Unt 506 cold despite ordinary butter variants; Drojdie 11 hot through dough despite being optional; the qualified oven 78 lukewarm. Thus the central fruit/dough routes work, but complete recipe realism is not claimed.
- Biscuit dessert: Desert rank 2, Biscuit/Unt 3 and Prăjitură 7 hot; Mâncare 18 and Lapte 61 warm. Train 1,968 frozen and football 976 very cold. Oven and tray remain warm at 36 through Cornulețe, even though this is commonly a no-bake preparation; yeast 77 and Sarmale 86 are lukewarm. Defining ingredients outrank this secondary preparation noise, which remains a reason for adversarial review.
- Bread: Mâncare rank 3 hot; Aluat/Drojdie/qualified oven 7 hot; Făină/Grâu/Apă 45 warm. The old flour opener was 391/cold and now improves to 45/warm. Train 1,818 frozen, football 1,458 very cold. Stilou remains inherited lukewarm noise (204→219), Christmas 98→108 lukewarm, and Sarmale 23→27 warm; none beats the direct production core, but Sarmale still ranks ahead of flour within the warm band.

The V77 deferral concerned a proposed direct Făină→Pâine de casă edge that made flour warm for Stiloul cu rezervor. That edge is absent here. The same old pen-target control is 1,280/very cold on baseline and 618/cold on V84; it remains outside every warm band. This is a bounded preservation check, not a claim that all historical ranks remain identical.

Lanț Făină→Cornulețe has exact shortest distance 2, two first-hop choices, narrowest intermediate layer 2 and no shared intermediate choke point. Its two shortest paths are Făină→Aluat→Cornulețe and Făină→Cozonac→Cornulețe. The new precise route makes the board more than a chain of holiday co-occurrence; independent judges still decide whether its weaker alternate route satisfies the quality standard.

## Deliberate deferrals

- Făină Contexto: eligible by counts but Sarmale rank 15 outranks bread 44 and dough 183; do not add an easy round whose natural production guesses trail generic-food shortcuts this strongly.
- Aluat, Griș and Mălai Contexto: fewer than five incoming neighbors, failing rubric C3 even where runtime reachability floors pass. Incoming counts are 4, 4 and 3; outgoing authoring degree does not substitute for target quality.
- Drojdie Contexto: zero incoming neighbors; reachable only from itself. It is useful as a new input, not a viable target.
- Urdă Contexto: already approved; no duplicate proposed.
- Grâu→Pâine, Grâu→apple pie, Saramură→Urdă and other material routes: single first-hop/intermediate choke point.
- Cheag alimentar→Urdă: three shortest paths pass through broad cheese/milk relations, bypassing the real whey process and inviting a misleading rennet implication.
- Drojdie→Cornulețe: same two intermediates/end target as the flour board; do not create a near-duplicate.

Final evidence files: prospective-profile.json, prospective-feedback.json and prior-flour-guard.json. Final applied graph and imported-record dossiers require fresh binding before promotion. No test threshold, rubric floor or inventory-preservation requirement was relaxed.
