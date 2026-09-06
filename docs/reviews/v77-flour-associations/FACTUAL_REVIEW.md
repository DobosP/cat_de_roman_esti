# V77 independent factual review: flour associations

Valid until: the V77 flour-association decision lands — then treat as history.

Reviewed at repository base `9ef9dc7`; the draft adds only these directed, non-distractor records:

- `n_v24_food_pantry_faina → n_gas_cozonac`
- `n_v24_food_pantry_faina → n_gas_paine_de_casa`
- `n_v24_food_pantry_faina → n_v3gas_clatite`

Each uses `relation: part_of`, `label_ro: ingredient pentru`, `strength: 0.97`, and `bidirectional: 0`. No target, node, alias, or reverse edge is part of this factual review.

## Verdict

**Accept all three associations; no factual blocker.** Flour is a conventional, foundational ingredient in ordinary Romanian cozonac, house bread, and clătite. The label `ingredient pentru` states an association rather than claiming that every variant uses wheat flour, so gluten-free recipes and unusual substitutions do not contradict it.

| Edge | Verdict | Evidence and qualification |
|---|---|---|
| Făină → Cozonac | Accept | ROMPAN's professional cozonac standard lists white wheat flour first among the manufacturing ingredients. Independently, an AGERPRES household recipe uses 1 kg flour for two cozonaci and discusses sifting it for the dough. Fillings vary, but flour belongs to the defining sweet dough rather than an optional filling. |
| Făină → Pâine de casă | Accept | ROMPAN's milling/baking account describes flour combined with water, salt, and yeast to form bread dough and explicitly includes Romanian house bread in the resulting bread family. Its white-flour professional page says the flour is intended for bread manufacture. The association remains true across white, wholemeal, rye, sourdough, and most gluten-free house breads because the generic KG node is `Făină`, not specifically white wheat flour. |
| Făină → Clătite | Accept | AGERPRES states that clătite usually contain flour, eggs, sugar, milk, and melted butter. Dr. Oetker Romania's classic clătite recipe independently uses 250 g flour, and Mega Image's recipe collection uses flour across classic, sweet, savory, oven-baked, and fasting variants. Flourless novelty recipes exist, but they do not make the ordinary association misleading. |

## Graph-convention review

The current authored graph already expresses recipe composition from ingredient to dish with `part_of`, including `Ou → Clătite`, `Apă → Pâine de casă`, and optional `Fruct → Cozonac`. The proposed direction therefore matches existing semantics. The draft's `bidirectional: 0` is also consistent with the V25 strong-link enrichment convention and avoids adding reverse dish-to-flour fan-out or showing the directional label backwards.

Existing ingredient edges use varied strengths according to their editorial wave: `Ou → Clătite` is 0.76, `Apă → Pâine de casă` is 0.68, optional `Fruct → Cozonac` is 0.60, while ingredient-principal links reach 0.88–0.95. V25 uses 0.97 as its default strong-link editorial weight and one-way direction for most explicit repairs. The three reviewed facts support treating flour as stronger than those optional/secondary comparisons. **The sources do not measure a numeric 0.97 probability**; that value is acceptable only as the documented V25 editorial convention and remains subject to the separate graph-impact/gameplay review.

## Input implications

A player entering ordinary `făină` for any of the three dishes would receive a direct, legible ingredient association rather than a misleading semantic shortcut. The one-way edges do not make a dish input a direct shortcut toward a Făină target. No new surface forms, homonyms, hidden answers, or target eligibility are introduced. Promotion of the three previously rejected Contexto candidates requires a later independent content review.

## Sources

- [ROMPAN professional standard SP-602-97: Cozonaci](https://rompan.ro/servicii/informatii-de-specialitate/standarde/standarde-profesionale/cozonaci/)
- [AGERPRES household cozonac recipe](https://agerpres.ro/social/2021/04/29/traditii-in-bucate-cozonac-moldovenesc-reinventat-dar-cu-acelasi-gust-desavarsit--705669)
- [ROMPAN: 16 octombrie – Ziua Mondială a Pâinii](https://rompan.ro/16-octombrie-ziua-mondiala-a-painii/)
- [ROMPAN professional page: Făina albă](https://rompan.ro/servicii/informatii-de-specialitate/standarde/standarde-profesionale/faina/faina-alba/)
- [AGERPRES-hosted ROMPAN bread-industry statement](https://agerpres.ro/comunicate/2025/10/15/comunicat-de-presa---patronatul-roman-din-industria-de-morarit-panificatie-si-produse-fainoase---rom--1493906)
- [AGERPRES: clătite ingredients and variants](https://agerpres.ro/zigzag/2022/02/01/it-s-today-my-favorite-day-2-februarie---ziua-cartitei-a-cititului-cu-voce-tare-si-a-clatitelor--857650)
- [Dr. Oetker România: Clătite clasice](https://www.oetker.ro/retete/r/clatite-clasice)
- [Mega Image: classic and variant clătite recipes](https://www.mega-image.ro/inspiratie/idei-pentru-tine/top-cele-mai-gustoase-clatite)

## Limits

This is an independent agent factual review, not a human culinary-SME judgment. It validates the three ordinary ingredient claims and their wording. It does not approve target promotion, quantify enjoyment, or replace the separate topology-impact and full integration gates.
