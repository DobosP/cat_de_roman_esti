# V75 Contexto food — independent adversarial verifier review

Valid until: this frozen V75 candidate batch changes — then treat as history.

Date: 2026-09-06  
Reviewer: `session_refactor`  
Role: verifier

## Exact input and bindings

The input inventory contains exactly these two pending Contexto dossiers and no historical approved-stock decision:

| ID | Target | Review binding | Lint findings | Verdict |
|---|---|---|---:|---|
| `ct_gastronomie_318` | Mici | `sha256:409604fd59411c095bd7ebff8ec78cfaa2c93a915770881053e7d6068975c43d` | 0 | promote |
| `ct_gastronomie_319` | Salată de boeuf | `sha256:1ec1629e5b7ae1e5205a3cc5bf03a8899893c5841f5bc750fdf9424c60d49108` | 0 | promote |

Both dossiers bind rubric SHA-256 `29781ef5daa65b0637425ea258702f9f644486807ea61e49020be66d168e0ca3`, which matches the current normalized `docs/CRITIQUE_RUBRIC.md`, and KG SHA-256 `fa9575db4819fa314e43218a0ad953f52c3e6ee2e34cac105dbc88e2d2247106`. I did not assess or revive the three candidates dropped before staging.

## `ct_gastronomie_318` — Mici — promote

### Refute-first risks

The serious objection is C5: *mici* is also the plural adjective “small.” That homograph exists in DEX. In isolation, however, the bare plural is the conventional food noun; adjectival use normally modifies a noun or appears with a determiner. The actual resolver maps `Mici`, `mici`, `mititei`, and `micii` to the food target, while `mic` does not resolve. The target is therefore not asking players to choose between two nameable bare-noun concepts, and grill/mustard feedback disambiguates immediately. This risk does not justify `keep` or `reject`.

Bere is a direct rank-5 neighbor, but play value is not alcohol-dependent: Grătar, Muștar, Carne, and Mâncare provide independent warm routes. Generic tail associations also do not carry the route.

### A and C findings

- **A1/A2/C2:** Multiple independent signals establish broad and cross-generational recognition. The Romanian Wikipedia article is substantial and received 578–1,334 user views every month from September 2025 through August 2026, rather than one isolated spike. AGERPRES reports a 2025 survey of 1,015 respondents in which mici were the leading grill food; Digi24 independently records continuing 1 Mai demand. DLRLC/DEX records the culinary noun in 1955–1957, providing a pre-2010 signal.
- **A3/A4/A7:** The description and the grill, mustard, meat, Obor, and 1 Mai links are specific, verifiable, and honest. The weaker Mâncare/Sosuri/category links do not substitute for the distinctive core.
- **A5:** No owner-boundary trigger. The optional beer association is not required to play.
- **A6:** No Contexto record, Contexto demotion, or impact-reserve record already uses `n_gas_mici`; cross-game appearances do not repeat the same mechanic.
- **C1:** Concrete, spontaneously nameable dish.
- **C3:** The dossier has 20 incoming neighbors and exposes ten strong recognizable neighbors. The core set includes Grătar, Muștar, Grătarul de 1 Mai, Bere, Carne, Mititeii de la Obor, Grătar la iarbă, Mâncare, Cartofi prăjiți, and Sosuri.
- **C4:** Actual route results: grătar rank 2 and muștar rank 3, both distance 1/Fierbinte; bere and carne rank 5.
- **C5:** The adjective homograph is bounded for the reasons above; the dish is the dominant bare-noun reading in this context.
- **C6:** Salience 0.9765, safely above the 0.60 `usor` warning floor.

Evidence:

- https://ro.wikipedia.org/wiki/Mititei
- https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ro.wikipedia.org/all-access/user/Mititei/monthly/20250901/20260831
- https://agerpres.ro/economic/2025/04/29/un-sfert-dintre-romani-asociaza-ziua-de-1-mai-cu-gratarele-si-socializarea-studiu--1444181
- https://www.digi24.ro/stiri/actualitate/ce-mananca-romanii-de-1-mai-desi-micul-este-regale-incontestabil-al-acestei-sarbatori-alte-alimente-vin-tare-din-urma-3220059
- https://www.romania-actualitati.ro/stiri/romania/romanii-vor-manca-de-1-mai-mici-cat-pentru-o-luna-id70618.html
- https://dexonline.ro/definitie/mititel
- https://dexonline.ro/definitie/mic

## `ct_gastronomie_319` — Salată de boeuf — promote

### Refute-first risks

The label is longer than a typical one-word target, but it is the stable conventional name and is more precise rather than polysemous. Resolver checks map the diacritic and plain-text full forms, `salată boeuf`, `salată boef`, `boeuf`, and `boeuf-ul` to the same target. Beef, chicken, and meatless recipes are documented variations of one dish, not competing senses.

The runtime input `Revelion` is unknown despite the direct neighbor `Revelionul la televizor`. This weakens one seasonal route, but does not come close to failing C3: nine other recognizable direct predecessors remain. Four ordinary guesses were tested successfully, three of them distance 1 and rank 6 or better.

### A and C findings

- **A1/A2/C2:** Recognition rests on several signals. The Romanian Wikipedia article has year-round traffic (490–3,009 monthly views outside its expected December peak), so interest is seasonal but not a single-event spike. Current HotNews and PRO TV coverage treats the dish as established Romanian holiday food; Digi24 independently records ordinary holiday consumption. A digitized 1926 Romanian cookbook contains the name and familiar meat, vegetable, pickle, mustard, mayonnaise, and decorative composition, establishing pre-2010 and cross-generational use.
- **A3/A4/A7:** The description accurately captures a common festive form while leaving room for documented recipe variation. Salată, Cartof, Murături, maioneză/Sosuri, and Ou are specific verifiable links. Holiday links are supporting context rather than the only route.
- **A5:** No owner-boundary trigger.
- **A6:** No Contexto record, Contexto demotion, or impact-reserve record already uses `n_gas_salata_boeuf`; Conexiuni appearances are a different mechanic.
- **C1:** Concrete named dish.
- **C3:** Ten direct predecessors were inspected. Excluding the unavailable `Revelion` shorthand leaves nine recognizable direct neighbors: Mese de sărbători, Salată, Masa de Crăciun, Cartof, Murături, Sosuri, Masa de Paște, Ou, and Salată de icre.
- **C4:** Actual route results: salată rank 2, cartof rank 4, murături rank 6, all distance 1/Fierbinte; maioneză distance 2, rank 28/Cald.
- **C5:** The full name has one dominant referent; recipe variation does not create another lexical sense.
- **C6:** Salience 0.9139, safely above the 0.60 `usor` warning floor.

Evidence:

- https://ro.wikipedia.org/wiki/Salat%C4%83_de_boeuf
- https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ro.wikipedia.org/all-access/user/Salat%C4%83_de_boeuf/monthly/20250901/20260831
- https://hotnews.ro/salata-de-boeuf-e-mancare-dumnezeiasca-istoria-celui-mai-controversat-preparat-romanesc-de-sarbatoare-diferentele-dintre-primele-retete-si-cele-de-acum-2133928
- https://www.protv.ro/articol/124617-retete-de-paste-iulia-parlea-ne-a-dezvaluit-reteta-de-salata-de-boeuf-care-nu-lipseste-niciodata-de-pe-masa-de-paste
- https://www.digi24.ro/video/stiri/la-veterinar-dupa-mesele-de-sarbatori-caini-si-pisici-hraniti-cu-sarmale-salata-de-boeuf-sau-slanina-au-primit-pomana-porcului-2203555
- https://llll.ro/henriette-krupenski-sturdza/carte-de-bucate-vesela/

## Scope limitation

These are raw independent verifier recommendations only. I did not author `contexto_verdicts.json`, apply promotion, make a historical approved-stock decision, or claim human enjoyment. The serializer and version-2 final gate contract remain root-owned.
