# V80 Clătite independent verifier review

Valid until: dossier binding `dfa63711feac4a57e664e72420e73ae4d1a775382056e9c1e78f575fc06234b9`, candidate, KG, rubric, V79 Contexto behavior, or runtime probe changes — then treat as history.

Date: 2026-09-06

## Binding and verdict

- Input IDs: exactly `ct_gastronomie_320`
- Game: `contexto`
- Candidate SHA-256: `87e8b3b4133a82c83542070f6f3228d7482b8e775d66fed660574148220e67dd`
- Pending record SHA-256: `118dac85a20d71928b5a8d0e0ecf360ee78d93a4edddec0fc329bff4cce6d3b0`
- Dossier SHA-256: `ecc49e659884599caa44a276e205e8ad1e03f23b99b437b38cdf2936517a0d7a`
- Review binding: `sha256:dfa63711feac4a57e664e72420e73ae4d1a775382056e9c1e78f575fc06234b9`
- Rubric SHA-256: `29781ef5daa65b0637425ea258702f9f644486807ea61e49020be66d168e0ca3`
- KG SHA-256: `c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370`
- Runtime probes SHA-256: `251be6d78f287b878fdd1b7a1734773cad670f58683efae8110026cb99859ca3`
- Independent factual JSON SHA-256: `d749f061f40b013b7dbe24b3727dd62c7e318af7b66f6c7cdf8d104cded38428`

**Verifier verdict: promote.** The candidate passes A1–A7 and C1–C6 on the exact V79 graph. This is an independent agent judgment and not a human playtest.

## Refute-first assessment

The strongest objection is incomplete feedback for several plausible culinary guesses. Unt, Ulei and Miere are six hops/rank 1698/Înghețat; Nucă is rank 1699/Înghețat. `ciocolată` and `aluat` are unknown and return irrelevant or narrow suggestions without charging an attempt. Butter and oil can be cooking fats, while honey, nuts and chocolate are optional fillings, so these outcomes are imperfect and should remain visible in the review record.

They do not outweigh the current whole-player route. V79 fixed the severe V78 contradiction: accepted `gem` now borrows the close Dulceață neighborhood for this target and returns one hop/rank 8/Fierbinte while remaining a distinct, nonwinning public projection. Făină (2), Desert (3), Ou (5), Dulceață (7), Gem (8) and Zahăr (11) are Fierbinte; Lapte (40), Smântână (22), Brânză (30), Fruct (31), Prăjitură (16) and generic Mâncare (12) are Cald. These are independent category, batter, dairy, preserve and pastry routes that a novice can plausibly enter without knowing the answer.

## Rubric findings

- **A1/A2 and C2:** Pass. RRI's 2024 report describes a 23rd-edition Romanian festival with about 15,000 visitors and 20,000 clătite in the prior edition, and says clătite are found throughout Romania. Current PRO TV coverage, a 2014 Romanian school worksheet, and DLRLC's 1955–1957 entry give independent current, school and historical signals. This supports the `usor` recognition band without relying on one media hit.
- **A3/A4/A7:** Pass. The description accurately names thin cooked batter sheets and sweet/savory fillings. RRI documents flour, egg and milk batter, pan cooking, dulceață/chocolate fillings and savory variants. All nine incoming graph associations were inspected; the ingredient, filling and pastry links are specific and factually defensible.
- **A5:** Pass. No boundary trigger.
- **A6:** Pass. There is no approved Contexto row or reserve record for this target. Two Conexiuni appearances use a different mechanic. Earlier raw candidate drops are preserved diagnostic history rather than playable duplicates.
- **C1:** Pass. A concrete, nameable dish.
- **C3:** Pass. Nine incoming non-distractor neighbors, including at least eight recognizable strong concepts, and 2,288 reachable nodes. The dossier has zero lint findings.
- **C4:** Pass. Multiple obvious openers are actually warm through the API, led by flour, egg, dessert, jam, Gem and milk.
- **C5:** Pass with a recorded grammatical ambiguity. `Clătite` can be the feminine plural participial/adjectival form of `a clăti`, but that reading normally modifies another noun. As a standalone concrete plural, the food noun is dominant; tested singular, plural and inflected culinary forms resolve exactly.
- **C6:** Pass. Salience 0.7951 exceeds the 0.60 easy-band warning floor.

## Sources

- DLRLC food definition: https://dexonline.ro/definitie/cl%C4%83tit%C4%83/909496
- DEX food and adjectival senses: https://dexonline.ro/definitie/cl%C4%83tit/25488
- RRI 2025 recipe, ordinary ingredients and restaurant presence: https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/clatite-pentru-festival-id914372.html
- RRI 2024 festival scale and Romanian sweet/savory use: https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/clatite-cu-dulceata-de-smochine-id793197.html
- Current PRO TV savory clătite segment: https://www.protv.ro/emisiuni/vorbeste-lumea/articol/131189-clatite-umplute-cu-carne-varianta-la-cuptor-ce-carne-sa-folosesti-si-cum-prepari-umplutura-reteta-video
- 2014 Romanian school worksheet headed “CLĂTITE CU GEM”: https://media.hotnews.ro/assets/document/2014/10/20/18343952-0.pdf

The raw JSON is an independent verifier input under ADR-0104. It is not a hand-authored combined V2 verdict artifact and does not apply promotion.
