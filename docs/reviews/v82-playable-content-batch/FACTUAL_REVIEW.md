# V82 playable-content batch — independent factual review

Valid until: the frozen V82 candidate bytes or reviewed V81 graph changes — then treat as history.

Date: 2026-09-06

Reviewer: `session_refactor`

Role: independent factual verifier

## Binding and scope

- Candidate: `gastronomie/candidates.json`
- Candidate SHA-256: `sha256:c1b2bf353fac92124cf2c3866d8ef352eefa7308cfb254d3b01a28922d0171d0`
- KG SHA-256: `sha256:fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331`
- Exact coverage: `contexto[0]` through `contexto[7]`; all other candidate arrays are empty
- Outcome: 8 accepted factually, 0 blocked, 0 unresolved fixes

The batch selects existing KG nodes and authors no nodes, edges, aliases, or provenance fields. I inspected each target record and all 77 incident direct non-distractor relations: 24 Cozonac, 5 Pască, 8 Muștar, 11 Mujdei, 7 Ciorbă de burtă, 7 Urdă, 7 Friptură, and 8 Bulz. The sources below are independent review evidence rather than candidate-declared provenance.

Factual acceptance establishes that the concepts and graph claims are supportable. It does not approve the proposed difficulty, whole-player Contexto route, or promotion. Those remain for the probe- and dossier-bound quality gate.

## Per-item findings

### `contexto[0]` — Cozonac — factual accept

DEX editions describe a sweet leavened preparation using eggs, milk, butter, sugar, and other ingredients. AGERPRES documents a Moldavian recipe with flour, walnut, cocoa, and fillings such as rahat, poppy seed, or raisins. Current national reporting treats cozonac as a leading Easter product; RRI independently places it at both Easter and Christmas meals. These signals span older lexicography and current broad-audience use.

The node description and its holiday, dessert, dough, walnut, flour, cocoa/fruit, and pastry associations are materially correct. Coffee and media links are broad rather than defining, while the Colivă co-occurrence is ritual/region qualified; none creates a factual contradiction. Their distinctiveness is a later C3/C4 issue.

Sources:

- https://dexonline.ro/definitie/cozonac
- https://agerpres.ro/social/2021/04/29/traditii-in-bucate-cozonac-moldovenesc-reinventat-dar-cu-acelasi-gust-desavarsit--705669
- https://agerpres.ro/economic/2026/04/16/ciorba-de-burta-cozonacul-sarmalele-si-preparatele-din-carne-de-miel-cele-mai-comandate-mancaruri-de--1547088
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/masa-de-paste-3-id594129.html

### `contexto[1]` — Pască — factual accept

DEX/DLRLC define the principal food sense as an Orthodox Easter preparation from leavened dough filled with cottage cheese, raisins, sour cream, or related ingredients. AGERPRES describes pasca as an important ritual Easter bake, with cow's cheese, sugar, eggs, spices, and raisins. RRI independently documents its leavened dough, sweet-cheese filling, round form, and place on the Easter table.

The five direct relations—to Masa de Paște, Desert, Cozonac, Brânză, and Ouă roșii—are all supportable. `Pască` also has proper-name and regional homographs and can denote blessed Easter bread; under a gastronomy category the familiar baked-food sense is coherent, but that ambiguity and the proposed `normal` band still require C1/C5 review. Exact holiday-word usefulness is a gameplay question, not a factual defect.

Sources:

- https://dexonline.ro/definitie/pasca
- https://agerpres.ro/documentare/2019/04/23/sarbatori-i-tradi-ii-preparate-traditionale-de-pasti--297598
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/masa-de-paste-3-id594129.html
- https://basilica.ro/simboluri-legate-de-invierea-domnului/

### `contexto[2]` — Muștar — factual accept

DEX records both the plant/seed and the prepared condiment. The candidate points to the existing culinary node, whose description explicitly selects the sauce sense. Radio România Internațional documents the conventional serving of grilled mititei with bread and mustard, while current general-audience coverage continues to use mustard as the expected accompaniment to mici.

The non-distractor links to Mici, Grătarul de 1 Mai, Mititeii de la Obor, Grătar, Sosuri, Mâncare stradală, Cașcaval pane, and Condiment are factually plausible. The botanical sense is a real isolated-word competitor; the later verifier must decide whether category, description, and neighbors make `usor` fair rather than inferring fairness from unique KG ownership.

Sources:

- https://dexonline.ro/definitie/mu%C8%99tar/892996
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-la-gratar-5-id594493.html
- https://foodstory.protv.ro/nutritie/ce-mananca-romanii-ep-4-micii-cu-paine-si-mustar-varianta-romaneasca-a-burgerilor-americani-care-e-portia
- https://agerpres.ro/economic/2025/04/29/un-sfert-dintre-romani-asociaza-ziua-de-1-mai-cu-gratarele-si-socializarea-studiu--1444181

### `contexto[3]` — Mujdei — factual accept

DEX defines mujdei as a sauce of crushed garlic with water and salt, sometimes with vinegar, and other dictionary material records variants with oil. Older RRI recipe coverage pairs it with fish and grilled foods; current RRI coverage still uses the unqualified term for a garlic sauce served with a familiar Romanian dish. These are independent historical/current recognition signals.

The node's essential identity is garlic, so a cold `ulei` route would not contradict the concept: oil is variant-dependent. Its direct relations to Usturoi, Sosuri, Grătar, Friptură, Piftie, ciorbe, and garlic-sauce uses are factual. The broader Mici, salată de vinete, and șaorma pairings are optional but honestly labeled rather than asserted as universal.

Sources:

- https://dexonline.ro/definitie/mujdei
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/raci-fierti-cu-mujdei-de-usturoi-3-id594449.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-la-gratar-5-id594493.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/ostropel-de-pui-3-id1009841.html

### `contexto[4]` — Ciorbă de burtă — factual accept

DEX explicitly defines the compound as soup made from cow stomach. RRI describes it as one of the most popular soups found in Romanian restaurants and roadside stops, prepared with tripe and commonly finished with egg yolk, cream, garlic, and vinegar. Current AGERPRES delivery data independently reports it among the most ordered traditional Easter-period foods.

The central Ciorbă, Mujdei/usturoi, smântână, and Ciorbă rădăuțeană relations are sound. Some incident edges—especially a generic meal contrast with Mămăligă, `drege` through the composite Brânză cu smântână node, Hanul lui Manuc, and Murături—are weak or indirect routes whose usefulness needs C3/C4 scrutiny. Most significantly, the exact ingredient word `burtă` means abdomen/stomach generally but, in this compound, denotes the defining edible tripe. A cold route for it would be a gameplay contradiction even though it is not a factual error in the target record.

Sources:

- https://dexonline.ro/definitie/burt%C4%83
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/ciorba-de-burta-3-id594562.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/mancaruri-din-muntenia-15-id890214.html
- https://agerpres.ro/economic/2026/04/16/ciorba-de-burta-cozonacul-sarmalele-si-preparatele-din-carne-de-miel-cele-mai-comandate-mancaruri-de--1547088

### `contexto[5]` — Urdă — factual accept

DEX sources consistently identify urdă as a soft, sweet cheese obtained by boiling whey left after caș or butter production. Romanian public-health material calls it fresh whey cheese, and a government Romania guide lists urdă among familiar Romanian cheeses. AGERPRES reports it among sought-after local cheeses and documents traditional pastry fillings using urdă.

The relations to Brânză, Lapte, Plăcinte, Poale-n brâu, Telemea, and variants of Papanași are supportable. `Lapte` is an upstream material relation because urdă is made from milk-derived whey, rather than a claim that sweet milk is boiled directly. `Urdei` is a documented lexical relative/synonym in some sources but is not present in this candidate; whether absent `zer` or inflection/synonym inputs make the target too opaque belongs to C2/C4. The proper surname `Urdă` does not displace the lowercase food sense in this category.

Sources:

- https://dexonline.ro/definitie/urda
- https://dspbihor.gov.ro/legislatie/ordin%20MS%20nr.975-1998.pdf
- https://www.euraxess.gov.ro/ro/romania/informatii-si-asistenta/viata-cotidiana/bucataria-romaneasca
- https://agerpres.ro/social/2023/04/13/bistrita-nasaud-targ-de-pasti-al-producatorilor-locali-deschis-in-centrul-municipiului-resedinta--1092475
- https://agerpres.ro/2024/04/29/tradi-ii-in-bucate-mures-mamaliga-tocsita-si-prajitura-din-malai---preparate-traditionale-la-sanpetr--1289062

### `contexto[6]` — Friptură — factual accept

DEX, MDA, and older dictionary editions define friptură as a meat dish cooked on a grill/spit or in a pan/oven. Current and older RRI recipe coverage uses the word ordinarily across grilled, pan, and oven preparations, confirming both the definition and durable broad-audience familiarity.

All seven direct relations—to Grătar, Carne, Sare, Mujdei, Murături, Mese de sărbători, and Pâine de casă—are factually valid. Oil is common in some recipes but not defining or universal, so a cold `ulei` route is not itself misleading. By contrast, unresolved `cuptor` and a cold `tigaie` may underrepresent two dictionary-defined preparation routes and must be weighed in C4 before accepting `usor`.

Sources:

- https://dexonline.ro/definitie/friptur%C4%83
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/supa-aromata-de-vara-2-id594725.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-din-muschiulet-de-porc-5-id1035228.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/usturoiul-in-mancaruri-2-id594160.html

### `contexto[7]` — Bulz — factual accept

DEX/DLRLC define the culinary sense as a ball or lump of hot mămăligă filled with sheep cheese or urdă. The word also has a general lump sense, a technical lumber sense, an isolated-rock sense, and the proper place name Bulz. RRI documents the shepherd preparation and gives mămăligă/mălai and brânză de burduf as ingredients; current public coverage continues to present bulz as an authentic Romanian dish.

The eight food and mountain/pastoral relations are supportable. In a gastronomy context, the prepared-food reading is coherent, but it is folk/regional and competes with non-food senses, which supports `normal` rather than an effortless recognition assumption. The documented plural varies between `bulzi` and `bulzuri`; unresolved `bulzuri`, `bulzului`, or `mălai` inputs are therefore material C2/C4 limitations even though the target's canonical identity is factual.

Sources:

- https://dexonline.ro/definitie/bulz/definitii
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/bulz-id593872.html
- https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-pastoresti-3-id787904.html
- https://www.digi24.ro/fara-categorie/gustarea-ideala-dupa-o-drumetie-istovitoare-pe-munte-1002536
- https://www.digi24.ro/stiri/actualitate/evenimente/lasata-secului-de-branza-2026-ce-alimente-sunt-permise-inainte-de-postul-pastelui-cea-mai-importanta-traditie-explicata-de-preot-3640437

## Limitations and next gate

No factual blocker prevents raw staging. This is an independent Codex-agent review, not a Romanian-language SME judgment or human playtest. It does not treat media occurrence as universal recognition, infer enjoyment, or approve any target merely because its graph facts are true.

The later dossier-bound adversarial review must use actual public routes and independently apply C1–C6/A1–A7. It must specifically resolve Pască's holiday-word gap, Muștar and Bulz sense competition, `burtă` central-ingredient warmth, Urdă's whey/synonym route, Friptură's oven/pan routes, Bulz inflections and mălai, and the optional cold-oil routes for Mujdei and Friptură.
