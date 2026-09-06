# V79 bounded `gem` feedback-neighborhood factual review

Valid until: proposal `cde39575f4b3ac13a3139f00216af79f2e2edcfcfc9d7735286c7a213bf615b5`, bound Contexto sources, or KG `c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370` changes — then treat as history.

Date: 2026-09-06

## Verdict

Approve the bounded factual policy for implementation and gameplay-impact review. `Gem` remains anchored to Miere by default and borrows Dulceață only for Dulceață itself or a current strong directed Dulceață-to-target association (`strength >= 0.60`, non-distractor). This is narrower and more honest than the rejected global Dulceață mapping. It does not make `gem` an alias or exact answer.

The threshold is a reviewed boundary over the bound KG, not a general claim that every numeric 0.60 edge is linguistically interchangeable. The fixture hash and explicit effective-target tests must force re-review when topology changes.

## Semantic boundary

Romania's product norm defines gem as a fruit-pulp/puree and sugar gel. DEX describes dulceață as fruit or petals boiled in sugar syrup, while Romanian law defines miere as bee-produced. Gem and dulceață are distinct preparations but share the specific fruit-preserve sense; honey is a reasonable generic breakfast fallback but lacks that identity.

The bound graph has six effective local targets after the floor:

| Target | Bound edge | Judgment |
| --- | --- | --- |
| Dulceață | self | Close fruit-preserve concept; must remain nonwinning. |
| Papanași | `related_to`, 0.70, “se toarnă peste papanași” | Strong. Radio România Internațional describes both gem and dulceață as ordinary papanași toppings. |
| Magiun de Topoloveni | `same_category`, 0.60, “dulciuri de borcan din fructe” | Strong enough. The EU product specification describes a concentrated plum paste made from fully ripe fruit. It is distinct from gem but belongs to the same preserve family. |
| Conserve de iarnă | `is_a`, 0.80, “conservă dulce de iarnă” | Honest subset relation for fruit preserves, while the broad target may also include savory preserves. |
| Clătite | `related_to`, 0.70, “umplutură de clătite” | Strong. Romanian culinary sources list gem and dulceață as parallel clătite fillings. |
| Fruct | `related_to`, 0.85, “făcută din fructe” | Definitional ingredient relation under the official gem norm. |

Socată is correctly excluded. Its sole Dulceață route is the weak 0.45 generic label “preparate de casă sezoniere”. DEX defines socată as a drink made from elderflowers, sugar, lemon and water, so fruit-preserve warmth would be misleading.

## Mechanics and limits

The proposal preserves surface `gem`, domain `ingrediente`, penalty 1, explicit mapping kind, stable synthetic public ID, and Miere fallback for missing, reversed-only, distractor, weak, indirect and unrelated routes. A `gem` guess against either Miere or Dulceață must remain nonwinning, and typo suggestions must be filtered using the same target-sensitive private anchor as scoring.

This is an independent Codex-agent semantic review. It does not claim human playtest evidence, target promotion, or that all future strength-qualified graph edges are valid. The earlier global-mapping review remains historical evidence for why unrestricted Dulceață feedback was rejected.

## Sources

- Romanian product norm for gem: https://legislatie.just.ro/Public/DetaliiDocument/47448
- DEX/MDA record for dulceață: https://dexonline.ro/intrare/dulcea%C8%9B%C4%83/17877
- Romanian apiculture law defining miere: https://legislatie.just.ro/Public/DetaliiDocument/226401
- Radio România Internațional on gem/dulceață with papanași and dulceață-filled clătite: https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/papanasi-cu-smantana-si-dulceata-2-id594703.html
- EU specification for Magiun de prune Topoloveni: https://eur-lex.europa.eu/legal-content/RO/TXT/?uri=oj%3AJOC_2010_241_R_0003_01
- Romanian culinary clătite filling evidence: https://www.protv.ro/emisiuni/vorbeste-lumea/articol/116358-majda-face-senzatie-la-vorbeste-lumea-care-este-secretul-clatitelor-care-au-innebunit-toata-echipa
- DEX record for socată: https://dexonline.ro/lexem/socat%C4%83/53139
