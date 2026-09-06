# V83 food targets — independent adversarial verifier review

Valid until: any bound dossier, rubric, KG, candidate, feedback source, morphology set, or runtime-evidence byte changes — then treat as history.

Date: 2026-09-07

Reviewer: `session_refactor`

Role: independent adversarial verifier

## Binding and outcome

- Input IDs: exactly `ct_gastronomie_329` through `ct_gastronomie_333`, ascending
- Contexto candidate SHA-256: `51ab54de798a66dbef8d764496b5769b1b8bb0169f5e27481bf1da57e3ddd001`
- Feedback candidate SHA-256: `2ebb9b31d077276327028c2573d48cee573d927930d4f88cb57d11777306d42e`
- Morphology candidate SHA-256: `8f2097c79462f5a83b3784f41d2b441e7cf76b8562e66324afd3c0cb07ddd21e`
- Reviewed KG SHA-256: `4ce12d15ec247ebcaba3e119caed91f8d2624b09fa5568a8d7ece728f76a8a5e`
- Rubric SHA-256: `29781ef5daa65b0637425ea258702f9f644486807ea61e49020be66d168e0ca3`
- Runtime evidence SHA-256: `0b9ea3de12bf12a27d559acdc5a675611cd433ceeb7ac0b2b3755d813bbe58ab`
- Runtime correction SHA-256: `23b7beebbec8e8f806be015288869617c955908c15a282cbe0a805943a77ced0`
- Outcome: 5 `promote`, 0 `keep`, 0 `reject`

| ID | Target | Dossier SHA-256 | Review binding | Verdict |
|---|---|---|---|---|
| `ct_gastronomie_329` | Cornulețe | `68eec8eb2669c557da860d9721715ed54464e9619c0c340a2faed06fb3dd0a86` | `aaa425337ac53fd6aaec8d14a4ff3e28ad9bd452e84288d9b86f80ce388ce3de` | promote |
| `ct_gastronomie_330` | Gogoși | `4d217f9c4b28ba9f631d4c7adf66f5ce86c79a8c75738bd1be85910344cfe6a6` | `ae29cdd807424511698e88fa4c725e52e8fff7aacd575dd90b8ba848161de932` | promote |
| `ct_gastronomie_331` | Telemea | `e9317edd3c20f836ad7503edb6beacf34417f475b993eae71533b6d36daefa36` | `85f6ce32d3be12c2cc94bd3e929b7ba9ee9cf12eb4b0dd513b9df419c0a4990b` | promote |
| `ct_gastronomie_332` | Cartofi prăjiți | `a53d493cadbf5b39eb96d6a193be80529782ffc61defdf7aa3dc347302b2a70f` | `f6a1486d36c7e9ad9d44be55ee1880e4ca299a9761117ca59a7f44d9bf5d3a8d` | promote |
| `ct_gastronomie_333` | Ardei umpluți | `9d4f609284a9a89b906b4c19be27b5a108caf4cceb0ab568820d852004b9e93a` | `1c57f75d35b312bcf950cdc4b94a9fc34a7a4f239ecdaf17342bc6f961ea15cf` | promote |

All five pass A1–A7 and C1–C6 on their exact dossiers. Each is a concrete food with sufficient cross-generational Romanian recognition, at least five recognizable direct neighbors, an obvious actual opener and salience above its band threshold. None duplicates an approved Contexto target or triggers A5. Ingredient, filling and preparation relations are specific rather than generic regional links.

## Refute-first findings

- **Cornulețe, normal:** Gem and Nucă rank 2, Prăjitură 4, Cozonac 6 and Făină 9 establish independent filling, category and dough routes. Sarmale remains falsely hot at rank 8, while butter/oil are cold and rahat is unknown. The false result is serious disclosure, but four legible paths rank at or above it. Bare singular polysemy is contained by `cu gem` in every new singular form.
- **Gogoși, easy:** Gem, Ulei and Desert rank 2, Papanași 3, Prăjitură 12 and flour/yeast/milk are warm. Butter and walnut remain frozen and pan cold. Gem is a common serving/filling variant rather than universal; oil describes the standard fried form while baked versions exist. Food dominates the isolated plural in gastronomy despite lie/cocoon/swelling senses.
- **Telemea, easy:** Sare and Brânză rank 2, Mămăligă 4, Plăcinte 6 and Lapte 14. `Saramură` remains unknown, and Drojdie is spuriously warm at 13. The defining salt plus multiple dairy/use routes precede the noise; the four new case/sort-plural forms are exact and unambiguous.
- **Cartofi prăjiți, easy:** Ulei and Cartof rank 2, Șnițel 3, Mici 4, Mâncare stradală 5 and Air fryer 7. Drojdie is falsely warm at 18, pan only lukewarm and butter very cold. Both defining concepts lead the ranking, and low/no-oil variants do not make conventional oil frying false.
- **Ardei umpluți, normal:** Ardei and Orez rank 2, Legume 3, Sarmale 4, Roșie 5 and Mămăligă 7. Drojdie is misleadingly Fierbinte at 11; oil/butter are cold. Six more obvious shell/filling/serving routes precede that anomaly. Meat is common rather than universal because vegetarian versions are documented.

The six repaired inputs remain nonwinning and keep their submitted public identities. The complete comparison covers four canonical inputs over 216 approved records plus five candidates: exactly six of 884 observations change and 878 remain exact; all 864 baseline-approved observations are unchanged. Ten control targets and 60 observations remain exact. The 11 deliberately omitted ambiguous forms retain their prior exact/fuzzy/suggestion behavior, while all 24 reviewed forms resolve to the intended owner.

## Recognition evidence and limits

Every C2 judgment uses at least two independent signals listed item-by-item in `verifier-review.json`. The evidence spans Romanian dictionaries, older and current national media, AGERPRES, and EU production/specification records. Gogoși, Telemea and Cartofi prăjiți meet the stronger easy familiarity band. Cornulețe and Ardei umpluți are conservatively normal because their form/sense or recipe-variant questions are more substantial.

This is an independent Codex-agent review, not a Romanian-language SME or human playtest. Runtime evidence does not cover every possible input. Promotion here does not claim uniformly correct rankings; the false-hot and unknown/cold routes above remain accepted limitations. The raw JSON is verifier input under ADR-0104, not a hand-authored combined V2 verdict artifact, and does not itself apply promotion.
