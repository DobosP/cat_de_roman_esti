# V83 food morphology — independent linguistic review

Valid until: frozen morphology candidate `8f2097c79462f5a83b3784f41d2b441e7cf76b8562e66324afd3c0cb07ddd21e`, the V82 KG, or cited lexical evidence changes — then treat as history.

Date: 2026-09-06

Reviewer: `session_refactor`

Verdict: **accept all 24 proposed forms; reject none.** These are grammatical or explicitly food-qualified forms of eight existing concepts. They are not new concepts or synonyms.

## Binding and collision review

- Baseline commit: `38f0d62ff1cd72003ae94ed691db4c44eb78c794`
- Baseline KG SHA-256: `fc3ea5a27e3bcb1da72fb3146316d7709da37012dddc494de0d6d4370862a331`
- Morphology candidate SHA-256: `8f2097c79462f5a83b3784f41d2b441e7cf76b8562e66324afd3c0cb07ddd21e`
- Coverage: exactly 24 forms across eight owners

The scout evidence finds no exact-owner, projection, ledger or beginner-benchmark collision. Nine forms already fuzzy-resolve only to their intended owner; 15 are unresolved. That mechanical result is necessary but is not the semantic argument. I independently checked the paradigms and preserved qualifiers wherever a bare form has competing ordinary senses.

## Per-owner findings

| Owner | Accepted exact forms | Linguistic judgment |
|---|---|---|
| Urdă | `urdei`, `urde`, `urdele`, `urdelor` | DOOM3 gives genitive-dative definite `urdei` and plural `urde` for product sorts; the longer plural forms follow regularly. Bare `urdei` is a case form, not a synonym. It does not import the plant compound `urda-vacii`. |
| Telemea | `telemelei`, `telemele`, `telemelele`, `telemelelor` | DOOM3 gives `telemelei` and permits `telemele` for sorts. The forms retain the brined-cheese referent. |
| Mujdei | `mujdeiului`, `mujdeie`, `mujdeiele`, `mujdeielor` | DOOM3 prefers `mujdeie`; the DOR paradigm supports all four. Rare `mujdeiuri` forms stay out. A rare argot homograph does not dominate these culinary forms or frame the content. |
| Friptură | `fripturii`, `fripturilor` | Regular definite genitive-dative forms of the same prepared-meat noun. |
| Cartofi prăjiți | `cartof prăjit`, `cartofului prăjit`, `cartofilor prăjiți` | Correct noun-adjective agreement for singular and case forms; all denote the same fried-potato food concept. |
| Bulz | `bulzuri cu brânză`, `bulzurile cu brânză` | DEX/MDA attest neutral plural `bulzuri`. `Cu brânză` is required because bare forms also support lump, rock, lumber and place readings. |
| Cornulețe | `cornuleț cu gem`, `cornulețul cu gem`, `cornulețului cu gem`, `cornulețelor cu gem` | The inflection is regular. `Cu gem` is required because bare `cornuleț` also has horn, botanical and figurative senses; RRI and AGERPRES document the filling. |
| Gogoși | `gogoașa prăjită` | Regular definite singular. `Prăjită` selects the pastry against lie, swelling, gall and cocoon readings. |

The frozen omission list is correct. Bare `bulzuri`, `bulzului`, `gogoșii`, `gogoșilor`, `cornuleț`, `cornulețului`, `păști` and `păștii` remain semantically unsafe. Current DOOM3 preference supports omitting rare `mujdeiuri`, `mujdeiurile` and `mujdeiurilor` in this bounded batch. This preserves V72 instead of silently weakening its qualifier decision.

## Sources and limits

- Urdă paradigm: https://dexonline.ro/definitie/urd%C4%83
- Telemea paradigm and brined-cheese meaning: https://dexonline.ro/definitie/telemea
- Mujdei paradigm and meanings: https://dexonline.ro/definitie/mujdei
- Friptură paradigm: https://dexonline.ro/definitie/friptur%C4%83
- Cartof paradigm: https://dexonline.ro/definitie/cartof
- Bulz forms and competing senses: https://dexonline.ro/definitie/bulz
- Cornuleț paradigm and competing senses: https://dexonline.ro/intrare/cornule%C8%9B/13187
- Gogoașă paradigm and competing senses: https://dexonline.ro/definitie/gogoa%C8%99%C4%83
- RRI cornulețe with walnut and plum jam: https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/cornulete-cu-untura-id594322.html
- AGERPRES current regional-recipe inventory including `cornulețe cu gem`: https://agerpres.ro/comunicate/2026/04/29/comunicat-de-presa---universitatea-de-stiinte-agricole-si-medicina-veterinara-cluj-napoca--1551177

This is an independent Codex-agent linguistic review, not a human Romanian-language SME judgment. Final application still requires exact-module equivalence, collision tests and reconstruction of the prior KG. No form outside the frozen 24 is approved here.
