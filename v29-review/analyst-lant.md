# V29 analyst pass — Lanț (proposals only)

Three current routes are promotion candidates. Seven need explicit semantic predicates or
new route design; generic `beginner_*` labels are not accepted as meaningful steps.

| Item | Binding suffix | Proposal | Main reason |
|---|---|---|---|
| `lt_gastronomie_212` | `d80a6ed6…b44c76` | reject/revise | Bucătărie→Legume/Mâncare→Morcov is intuitive, but every step is a meta `beginner_*` predicate. |
| `lt_gastronomie_218` | `4cd431fd…1eb766` | reject/revise | Robust branching hides arbitrary steps such as Apă→A bea→Mâncare and generic entry edges. |
| `lt_literatura_210` | `9eb72615…2a2384` | promote candidate after verification | Abecedar→Carte/Copil→Prâslea gives two recognizable, legible routes. |
| `lt_stiinta_215` | `38f4d2b1…e0293f` | reject/revise | Om→Corp/Ochi→Nas is obvious, but route labels describe board plumbing, not anatomy. |
| `lt_stiinta_216` | `d4eebbfd…47af55` | reject/revise | Apă→Ploaie/Aer→Nor is sensible, but generic route labels fail D2. |
| `lt_stiinta_219` | `1393775b…c244a6` | reject/rewrite | Corp→Zăpadă relies on arbitrary science chains and has no satisfying semantic arc. |
| `lt_viata_de_roman_211` | `66af16e6…fe1b65` | promote candidate after verification | Ghiozdan→Carte/Copil→Capra cu trei iezi is recognizable and explicit. |
| `lt_viata_de_roman_213` | `09d4b676…8d748b` | reject/revise | Good Ghiozdan→Carte/Școală/Stilou→Lecție choices, but two paths use meta board labels. |
| `lt_viata_de_roman_214` | `c9b9ac42…a9552d` | reject/revise | Baie→Casă/Ușă→Cameră is intuitive, but its predicates remain generic plumbing. |
| `lt_viata_de_roman_217` | `402f9f60…8e4d6f` | promote candidate | Furniture→Sufragerie→Dormitor offers three recognizable choices and a satisfying home arc. |

## Remediation direction

- Overlay stronger explicit predicates for kitchen/food, anatomy, weather, school, and
  room relations so the runtime chooses honest labels without rewriting historical v24
  edges. Rebuild every affected branch profile and dossier.
- Replace `corp → Zăpadă`; edge-label polish cannot rescue its arbitrary endpoint arc.
- Rework `Ciorbă → Morcov` only if every surviving shortest route reads naturally; raw
  branching counts are not evidence of fun.

## Verifier queue

Structural route failures need no web settlement. Promotion candidates still need
cross-generational recognition and exact Creangă/Prâslea authorship or story attribution
checks where applicable.
