# V85 fresh playable-content screen

Valid until: the raw candidate bytes or bound graph change — then treat as history.

Candidate binding: `sha256:d1aa287a6a1e88d8ecbe635e64aa03dd5877db67fd4f8d132ad47c4358915edc`.
Screened 2026-09-07 by the ingredient scout, independently of root's future analyst
judgment. This is a **pending-stage screen**, not final promotion or a human playtest.
The six required arrays contain four Contexto records, one Lanț record and no new
nodes/edges/Conexiuni/Alchimie entries. None of the four targets exists in any current
Contexto record, and the Lanț exact endpoint pair is new. The original holds remain.

## Contexto screen

| Raw ref | Proposed easy target | Direct incoming neighbors | Reachable / responsive | Strong playable core |
|---|---|---:|---:|---|
| contexto[0] | Ecler | 5 | 2312 / 882 | Vanilie and Ciocolată rank5/hot; Amandină, Savarină and Prăjitură rank2/hot |
| contexto[1] | Amandină | 7 | 2312 / 1461 | Cacao and Ciocolată rank5/hot; Prăjitură rank2/hot; Ecler and Savarină rank3/hot |
| contexto[2] | Halva | 5 | 2312 / 1743 | Cacao and Semințe de floarea-soarelui rank2/hot; Mâncare de post4/hot; Baclava dobrogeană6/hot |
| contexto[3] | Înghețată | 6 | 2312 / 1639 | Vanilie and Cacao rank3/hot; Lapte7/hot; Fistic6/hot; Clătite5/hot |

Responsive means 1–5 directed hops, excluding the winning node. The independent
API harness made100 first guesses (98 distinct target/input pairs after repeated
self-label probes); every exact target wins at rank1. Full incoming neighbors and
actual responses are in `contexto-probes.json`. These are deliberate first guesses
against real game endpoints; they are not yet public selector journeys for pending
pack records. Root's final gates should add the normal create/resume/clue/win path.

All four meet rubric C1/C3/C4/C5 with recognizable concrete names and at least five
legible incoming associations. Ecler and Amandină share familiar pastry neighbors,
but have distinct typed ingredient cores and distinct target names. They are not
the same target under a different alias. Halva adds a seed-confection target and
Înghețată adds the ordinary frozen-dessert target. Exact wins and natural aliases
remain the existing contract; no synonym or spelling policy changes are requested.

### Recognition and salience

The graph's saliences are0.55,0.56,0.50 and0.2826. All four therefore need explicit
C6 review for the easy band. The values are not changed or ignored. In particular,
the common word Înghețată should not be called obscure solely because its old graph
salience is low. The following independent signals support ordinary recognition:

- **Ecler:** [JamilaCuisine's2013 vanilla-pod/chocolate-cream recipe](https://jamilacuisine.ro/eclere-pas-cu-pas-reteta-video/)
  presents the standard pastry. [Știrile ProTV's recent New Year dessert guide](https://stirileprotv.ro/stiri/actualitate/deserturi-de-revelion-retete-delicioase-de-prajituri-pentru-masa-de-revelion.html)
  also lists vanilla/chocolate eclairs as familiar celebration desserts. Its2025
  update is not falsely presented as the date of the pastry's invention.
- **Amandină:** [JamilaCuisine2013](https://jamilacuisine.ro/prajitura-amandina-amandine-facute-in-casa/)
  documents the cocoa sponge/cream and chocolate-glaze variant. The national
  broadcaster has both a [2016 recipe](https://www.protv.ro/articol/39442-reteta-amandina)
  and a [2026 Vorbește Lumea demonstration](https://www.protv.ro/emisiuni/vorbeste-lumea/articol/125114-iata-reteta-secreta-de-amandina-care-iese-perfect-de-fiecare-data-cum-o-pregatesti-si-tu-pas-cu-pas).
- **Halva:** the [Feleacul manufacturer catalogue](https://feleacul.ro/produse/halva)
  explicitly lists sunflower and cocoa variants. [Radio Romania's2025 culinary
  history](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/preparate-din-sardine-id874697.html)
  mentions halva in nineteenth-century Iași grocery trade; the [Romanian Wikipedia
  article](https://ro.wikipedia.org/wiki/Halva) is substantial. These support long-running
  recognition, not universal sunflower composition or exclusive Romanian origin.
- **Înghețată:** [JamilaCuisine's2013 recipe](https://jamilacuisine.ro/inghetata-de-vanilie-reteta-video/)
  describes the familiar vanilla dessert and a cocoa variant. [Digi24's2025 report](https://www.digi24.ro/magazin/timp-liber/inghetata-cu-gust-de-guma-de-mestecat-dar-din-ingrediente-naturale-3533887)
  shows it as an ordinary children-and-parents treat; the [Romanian Wikipedia article](https://ro.wikipedia.org/wiki/%C3%8Enghe%C8%9Bat%C4%83)
  is substantial. Promotional nutritional claims were not used as game evidence.

The simple Romanian Wikipedia URLs for Ecler and Amandină returned404 in this
session; no Wikipedia-presence claim is made for those two. Recipe/broadcast sources
supply their recognition evidence instead. Pageview measurements and human recall
studies were not performed. Final judges must explicitly accept or reject the easy
salience exceptions rather than silently treating warning-free validation as proof.

### Negative controls and remaining defects

The direct ingredient cores are markedly stronger than the tested unrelated words.
Bread is cold254 for Ecler, cold321 for Amandină, lukewarm86 for Halva and lukewarm132
for Înghețată. Stilou is very cold991 for Ecler, cold773/739/411 for the other three.
Cinnamon is lukewarm72 for Ecler/Halva but remains warm50/57 for Amandină/Înghețată.

Production inputs remain imperfect: yeast is warm43 for Ecler although choux is not
a yeast dough. Oven/tray/yeast remain warm45 for Halva and51 for Înghețată; this is
indirect graph noise, not evidence those desserts require baking. Baclava is still
unexpectedly hot9 for Înghețată; Sarmale is warm67 for Amandină. These are explicit
limitations for adversarial review. The actual positive cores remain clear enough
for a pending-stage recommendation; no claim of fully realistic rankings is made.

## Lanț screen

`lant[0]`: **Stafide → Brânză**, easy, optimal2.

- Stafide → Pască → Brânză.
- Stafide → Poale-n brâu → Brânză.

Both intermediate concepts are familiar sweet-cheese preparations with raisins;
[the Pască recipe](https://jamilacuisine.ro/pasca-cu-aluat-de-cozonac-reteta-video/)
and [the Poale-n brâu recipe](https://jamilacuisine.ro/poale-n-brau-pas-cu-pas-reteta-video/)
explicitly contain both ingredients. These are real alternatives, not two labels
for the same node. The graph branch profile is2 first hops, narrowest layer2 and2
intermediate nodes. This is a semantic bridge through recipes, not a claim that
raisins chemically turn into cheese. It needs no geography, holiday, or generic
category step. Complete oriented labels and source IDs are in `route-evidence.json`.

## Deferred alternatives

- **Cacao → Clătite:** graph has two routes through Ciocolată/Înghețată, but a
  [manufacturer recipe](https://www.oetker.ro/retete/r/clatite-cu-cirese-si-ciocolata)
  puts cocoa directly in pancake batter. The graph is missing a plausible direct
  association; this scout therefore does not promote a forced two-hop challenge.
  The [ice-cream serving bridge](https://www.oetker.ro/retete/r/clatite-cu-inghetata-si-fructe-proaspete)
  itself is true, but it does not settle that missing-direct-edge concern.
- **Alune de pădure → Salam de biscuiți:** it also has two clean graph routes, but
  an optional direct nut-ingredient shortcut may be reasonably expected and the
  same dessert was a new target immediately last version. Deferred, not staged.
- **Scorțișoară regional routes:** one old Mucenici→Moldova label incorrectly calls
  the boiled variant Moldavian. The verified recipe is [Muntenian](https://jamilacuisine.ro/mucenici-muntenesti-fierti-reteta-video/).
  No proposed route relies on that edge; this is reported existing graph debt.
- No extra round is added merely to fill a quota. Native ingredient nodes are not
  automatically valid hidden targets, and frozen derived-board scope stays intact.

No pack, fixture, source, status or generated sidecar was changed by this scout.
