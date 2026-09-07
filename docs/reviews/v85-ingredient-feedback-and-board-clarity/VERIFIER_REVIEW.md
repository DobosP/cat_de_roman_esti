# V85 independent bound verifier review

Valid until: any bound dossier, rubric, raw candidate or graph changes — then treat as history.

Reviewed 2026-09-07 by `v85_baseline_and_tests_independent_verifier`, separately from
the graph/raw-batch author and root analyst. Verdict: **promote all five**, with the
four salience warnings explicitly adjudicated and the remaining defects below.
Exact input IDs and bindings are in `verifier-review.json`.

| Pending record | Verdict | Recognition and practical core |
|---|---|---|
| ct_gastronomie_337 — Ecler | promote | Familiar cofetărie pastry; five direct recognizable inputs. Prăjitură 2; vanilla/chocolate 5. |
| ct_gastronomie_338 — Amandină | promote | Familiar cocoa cake; seven incoming links, including six everyday names. Cocoa/chocolate 5. |
| ct_gastronomie_339 — Halva | promote | Longstanding ordinary confection; five recognizable incoming words. Sunflower seeds/cocoa 2. |
| ct_gastronomie_340 — Înghețată | promote | Ordinary frozen dessert; six incoming associations. Dessert 2; vanilla/cocoa 3; milk 7. |
| lt_gastronomie_221 — Stafide→Brânză | promote | Two honest ingredient→preparation→ingredient routes via Pască and Poale-n brâu. |

## Independent checks

The completed private API harness made 82 first-guess requests over 74 normalized
input/target pairs. It also replayed each Contexto cold-guess→warm-clue→repeat→resume→
exact-win journey twice:8 deterministic complete journeys. Clues were Prăjitură,
Prăjitură, Cacao and Desert respectively, all rank 2, private and nonwinning. Answers
won only when entered exactly. Both Lanț branches won in 2 moves and resumed exactly;
a premature direct Brânză move was rejected without consuming progress.

The dossier graphs each have 2,312 reachable Contexto concepts and no deterministic
FAIL. A direct baseline-pack inspection found no old matching target or exact/reverse
Lanț endpoint pair. Ecler and Amandină are distinct familiar pastries with shared
neighbors, not the same hidden concept under two aliases. No promotion relies on
alcohol, origin exclusivity or a generic regional bridge.

## Recognition and salience decisions

Saliences 0.55/0.56/0.50/0.2826 remain unchanged. They are warning signals, not measured
Romanian recognition rates. Familiarity is my judgment from ordinary usage plus the
independent sources below; no pageview or human recall measurement is claimed.

- Ecler: [2013 recipe](https://jamilacuisine.ro/eclere-pas-cu-pas-reteta-video/),
  [Mega Image Romania’s 2019 demonstration](https://www.youtube.com/watch?v=91W3GM1_2O8)
  and [casual evening-news use in 2024](https://www.digi24.ro/stiri/actualitate/politica/primarul-din-bacau-despre-comasarea-alegerilor-e-ca-si-cum-ai-manca-gogonele-cu-eclere-2676535)
  support broad, ordinary recognition. The political story is used solely as evidence
  that the food word needs no specialist explanation.
- Amandină: [2013 recipe](https://jamilacuisine.ro/prajitura-amandina-amandine-facute-in-casa/)
  and [PRO TV’s2026 demonstration](https://www.protv.ro/emisiuni/vorbeste-lumea/articol/125114-iata-reteta-secreta-de-amandina-care-iese-perfect-de-fiecare-data-cum-o-pregatesti-si-tu-pas-cu-pas)
  document sustained familiarity and the cocoa/chocolate core.
- Halva: [the Romanian article](https://ro.wikipedia.org/wiki/Halva),
  [current manufacturer variants](https://feleacul.ro/produse/halva) and
  [Radio România’s historical account](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-din-sardine-id874697.html)
  provide complementary recognition evidence. Recipe variants do not imply that every
  halva contains sunflower seeds or cocoa.
- Înghețată: [2013 vanilla recipe](https://jamilacuisine.ro/inghetata-de-vanilie-reteta-video/)
  and [Digi 24’s2025 family-event reporting](https://www.digi24.ro/magazin/timp-liber/inghetata-cu-gust-de-guma-de-mestecat-dar-din-ingrediente-naturale-3533887)
  support the ordinary easy-band name. Promotional health claims are not evidence here.
- Both Lanț bridges have explicit raisin-and-sweet-cheese fillings in the
  [Pască](https://jamilacuisine.ro/pasca-cu-aluat-de-cozonac-reteta-video/) and
  [Poale-n brâu](https://jamilacuisine.ro/poale-n-brau-pas-cu-pas-reteta-video/) recipes.

## Refutation attempts and remaining limits

Yeast 43 remains warm for Ecler despite choux not being a yeast dough. Amandină still
has warm Sarmale 67 and cinnamon 50. Halva has warm oven/yeast 45 and flour 26. For
Înghețată, refrigerator 197 is too weak, oven/yeast 51 too warm, and bare `rece` is not
accepted; the author’s separately disclosed Baclava 9 observation remains questionable.
These defects are real, but each candidate retains multiple substantially stronger,
legible defining clues and reproducible safe recovery to an exact answer. Promotion
is a judgment of fair navigability, not a statement that all rankings are realistic.

The initial Lanț suggestion list includes Pască, Cozonac and Salam de biscuiți.
Poale-n brâu is a legal typed alternative, verified end to end, but is not shown among
those first three suggestions. No hidden route or invented choice is claimed.

Public selection, frontend integration and final full gates remain root’s next checks.
The private review never consulted a stale derived sidecar or changed pack status.
