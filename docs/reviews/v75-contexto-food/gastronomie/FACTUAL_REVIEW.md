# V75 Contexto gastronomie — factual review

Valid until: this frozen V75 candidate batch changes — then treat as history.

Date: 2026-09-06

## Binding and scope

- Frozen candidate: `candidates.json`
- Candidate SHA-256: `sha256:baef6c35007d7da7982058f0bbb220b3fbf95f91377247412368f63898e38431`
- Inspected KG fixture SHA-256: `sha256:fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106`
- Reviewed refs: `contexto[0]` through `contexto[4]`, corresponding exactly to Mici, Cozonac, Salată de boeuf, Pâine de casă, and Clătite.
- Factual outcome: 5 accepted, 0 rejected, 0 unresolved fixes.

This review covers factual correctness of the five existing KG targets, their descriptions, and all 77 direct non-distractor predecessors listed in `kg_screening_dossiers.json` (20, 22, 10, 17, and 8 respectively). It does not issue a quality verdict, approve or promote content, assess the numeric edge strengths, or replace the later bound critique-dossier review required by `docs/CRITIQUE_RUBRIC.md`.

## Provenance finding

The frozen candidate adds no nodes or edges and contains no `source` or provenance declaration. The inspected existing node and edge records in `kg_sample.json` likewise have no source/provenance field. There was therefore no candidate-declared URL or attribution to authenticate. The URLs below are independent review evidence, not candidate-authored provenance.

## Per-item findings

### `contexto[0]` — Mici — accept

The KG description says the dish consists of seasoned minced meat grilled and associates it with mustard, bread, and 1 May outings. The DEX/DLRLC dictionary entry identifies mititei as seasoned minced meat cooked on a grill. A 2025 AGERPRES report on a 1,015-person Romanian survey ties 1 May to grilling and specifically reports strong associations among mici, beer, and outdoor grilling. A Bucharest city guide independently documents the Obor serving pattern with mustard and bread. These sources support the core description and the most specific direct predecessors: Grătar, Muștar, Grătarul de 1 Mai, Bere, Carne, Mititeii de la Obor, Pâine, and Mâncare stradală.

Sources:

- https://dexonline.ro/definitie/mititei
- https://agerpres.ro/economic/2025/04/29/un-sfert-dintre-romani-asociaza-ziua-de-1-mai-cu-gratarele-si-socializarea-studiu--1444181
- https://agerpres.ro/economic/2023/04/30/arc-cererea-de-mici-pentru-minivacanta-de-1-mai-mai-mare-cu-aproximativ-30-fata-de-anul-trecut--1099975
- https://www.bucuresti.ro/articole/5-targuri-de-weekend-din-bucuresti-pe-care-sa-le-explorezi-ca-un-localnic-257

No factual contradiction was found among the remaining direct predecessors. Weaker links such as Chefi la cuțite, Covrigi de Buzău, and Șaorma cu de toate are broad media/category associations; whether they are distinctive or intuitive enough is a later Contexto quality question.

### `contexto[1]` — Cozonac — accept

An AGERPRES first-person recipe report lists flour, yeast, ground walnut, cocoa, rahat, poppy seed or raisins, milk, eggs, sugar, butter, and oil, and describes cozonac as a traditional Easter preparation. The municipal cultural center CREART lists walnut-and-cocoa cozonac at the Bucharest Christmas Market, while the Romanian cultural-heritage resource CIMEC documents cozonac among Christmas and Easter baked goods. These sources support the description and its dominant direct predecessors: the Christmas, Easter, and festive tables; Desert; Dulce; Pască; Ouă roșii; Cornulețe; Prăjitură; Fruct; and Mirodenii.

Sources:

- https://agerpres.ro/social/2021/04/29/traditii-in-bucate-cozonac-moldovenesc-reinventat-dar-cu-acelasi-gust-desavarsit--705669
- https://agerpres.ro/comunicate/2024/11/26/comunicat-de-presa---centrul-de-creatie-arta-si-traditie-al-municipiului-bucuresti--1393226
- https://cimec.ro/Etnografie/Antonescu-dictionar/Dictionar-de-Simboluri-Credinte-Traditionale-Romanesti-a-b.html
- https://basilica.ro/asociatia-femeilor-ortodoxe-din-parohia-schiedam-rotterdam-a-organizat-pomenirea-doamnei-maria-brancoveanu/

The Basilica account also directly supports the otherwise niche Colivă/Cozonac co-occurrence at a memorial. No factual contradiction was found. Links such as Clip culinar, Cafea, and Chefi la cuțite remain generic association-strength questions for the later quality review.

### `contexto[2]` — Salată de boeuf — accept

The target describes a festive salad with vegetables, meat, and mayonnaise. A PRO TV recipe from chef Cătălin Scărlătescu lists beef, potatoes, pickles, boiled egg, mayonnaise, pickled peppers, peas, and parsley. Another PRO TV first-person Easter recipe uses chicken, potatoes, root vegetables, pickles, peas, mayonnaise, and mustard and explicitly places the dish at both Easter and Christmas. AGERPRES documents a meatless fasting variant, showing that recipes vary; that variation does not contradict the target's non-exclusive description of a common meat version. These sources support Cartof, Murături, Sosuri/maioneză, Ou, Salată, and the Christmas/Easter/festive-table links.

Sources:

- https://www.protv.ro/articol/130281-se-pune-sau-nu-mazare-in-salata-de-boeuf
- https://www.protv.ro/articol/124617-retete-de-paste-iulia-parlea-ne-a-dezvaluit-reteta-de-salata-de-boeuf-care-nu-lipseste-niciodata-de-pe-masa-de-paste
- https://agerpres.ro/social/2021/04/09/tradi-ii-in-bucate-gospodinele-din-rapa-de-jos-mures-promoveaza-retete-stravechi-se-mananca-bine-si---694233

No factual contradiction was found. Revelionul la televizor is a plausible seasonal co-occurrence rather than an ingredient or identity claim; its gameplay distinctiveness remains outside this factual pass.

### `contexto[3]` — Pâine de casă — accept

AGERPRES records a first-person monastery practice of making leavened house bread and serving it with soup, and a Romanian milling/baking-industry release specifies flour, water, salt, yeast, fermentation, and baking. CIMEC documents the central place of bread in household and ritual life. This supports the target description and the direct links to Pâine, Pâine cu maia, Apă, Gospodăria bunicilor, and foods spread on or served with bread such as Zacuscă, Salată de vinete, Slănină cu ceapă, and Magiun de Topoloveni.

Sources:

- https://agerpres.ro/2024/04/26/tradi-ii-in-bucate-ciorba-falsa-de-burta-cu-pleurotus-si-painea-de-casa-cu-masline---printre-delicii--1287928
- https://agerpres.ro/comunicate/2025/10/15/comunicat-de-presa---patronatul-roman-din-industria-de-morarit-panificatie-si-produse-fainoase---rom--1493906
- https://cimec.ro/Etnografie/Antonescu-dictionar/Dictionar-de-Simboluri-Credinte-Traditionale-Romanesti-p.html

No factual contradiction was found. Some meal-pairing predecessors, including Supă cu găluște, Cașcaval pane, and Friptură, are ordinary serving associations whose strength and distinctiveness must be judged later.

### `contexto[4]` — Clătite — accept

AGERPRES describes the usual batter ingredients as flour, eggs, sugar, milk, and melted butter, and documents both sweet fillings (including jam and chocolate) and savory fillings (including mushrooms and cheese). This directly supports the thin pan-cooked preparation, sweet-or-savory description, and the Ou, Dulceață, Brânză, and Desert predecessors. Papanași, Plăcinte, Gogoși, and Înghețată are factually valid dessert/category or serving associations.

Source:

- https://agerpres.ro/zigzag/2022/02/01/it-s-today-my-favorite-day-2-februarie---ziua-cartitei-a-cititului-cu-voce-tare-si-a-clatitelor--857650

No factual contradiction was found. The numeric strengths and the sufficiency/intuitiveness of eight direct predecessors remain for the later bound quality review.

## Limitations and blockers

There are no factual blockers for initial import and no rejected refs. Source attribution cannot be traced through the candidate or fixture because neither carries provenance fields; this review records external evidence separately. Recognition bands, dominant sense, opener quality, neighbor distinctiveness, and player experience were deliberately not adjudicated here. Those are still required in the later SHA/rubric-bound dossier approval before promotion.
