# V79 `gem` feedback-anchor factual and semantic review

Valid until: proposal `58629365916673283e56c77edcd88afa7b75e63615e78863a909705865ef7fbd`, the V77 KG, or either bound Contexto source changes — then treat as history.

Date: 2026-09-06

## Scope and binding

This review covers one proposed Contexto-only substitution:

- surface: `gem`
- current anchor: `n_v24_food_breakfast_miere` (Miere)
- proposed anchor: `n_v17gas_dulceata` (Dulceață)
- preserved: domain `ingrediente`, rank penalty `1`, explicit mapping kind, public ID `ctxp_fab0f46e7bcd5932442e`, and nonwinning behavior

Bindings:

- baseline commit: `010cfd176dcaa78aac660aea71e154691bd010f3`
- proposal SHA-256: `sha256:58629365916673283e56c77edcd88afa7b75e63615e78863a909705865ef7fbd`
- KG SHA-256: `sha256:c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370`
- current `contexto_projection.py`: `sha256:f87364166b58ed2096a1d060ee94af95a2fb731813160d03ca8e58e2e0a31fe4`
- current `contexto.py`: `sha256:e248eed373c3a732f4316b52b2c9114942f3db29cf3594fcc8ec8ce99eed676d`

Recommendation: the mapping is factually supported for bounded implementation and impact testing. This does not approve a new alias, graph fact, game row, or Clătite promotion.

## Why Dulceață is the more honest anchor

Romania’s official product norm defines gem as a gelled mixture made from sugars, fruit pulp and/or puree, and water. Romanian dictionary evidence describes dulceață’s food sense as fruit or petals boiled in sugar syrup. These are not identical preparations: their fruit form, consistency and customary process can differ. They do share the specific identity of a fruit-and-sugar preserve.

Miere is materially farther away. Romanian apiculture law defines it as a natural sweet substance produced by bees from nectar or plant/insect secretions. Gem and honey can both be sweet and eaten at breakfast, but those are broad usage properties. Dulceață shares gem’s defining fruit-preserve ingredients and culinary role.

The current KG reinforces rather than creates this judgment. Its Dulceață node says fruit is boiled in sugar syrup and explicitly links Dulceață to Fruct, Conserve de iarnă, Magiun de Topoloveni, Papanași and Clătite. The Miere node’s small neighborhood is breakfast foods, food generally and home. Borrowing Dulceață’s feedback therefore uses an existing semantically specific cluster.

Sources:

- Official Romanian gem composition rule: https://legislatie.just.ro/Public/DetaliiDocument/47448
- DEX/MDA dictionary record for dulceață: https://dexonline.ro/intrare/dulcea%C8%9B%C4%83/17877
- Romanian apiculture law defining miere: https://legislatie.just.ro/Public/DetaliiDocument/226401

## Culinary evidence

Romanian culinary usage supports the same proximity. A current PRO TV recipe presents dulceață de smochine as a clătite filling. An independent Romanian clătite business profile lists `dulceață de trandafiri`, `gem de prune cu nuci`, and other dulcețuri as parallel filling choices. This is evidence for close feedback, not synonymy.

- https://www.protv.ro/emisiuni/vorbeste-lumea/articol/116358-majda-face-senzatie-la-vorbeste-lumea-care-este-secretul-clatitelor-care-au-innebunit-toata-echipa
- https://foodstory.protv.ro/eveniment/interviu-foodstory-doua-fete-indragostite-de-clatite-vand-bunatati-pe-doua-roti-la-creperie-d-rsquo-amour

## Polysemy and exact-win challenge

The surface `gem` is not unambiguous in all Romanian sentences. It is also the first-person singular and third-person plural present form of `a geme`. English-influenced writing may use “gem” for a jewel, although the standard Romanian noun is `gemă`. The DEX entry exposes the verb homograph directly:

- https://dexonline.ro/definitie/gem/definitii

That concern does not arise from the proposed change. The bound source already accepts exact normalized `gem` as an authored projection under the `ingrediente` domain. V79 changes only which existing node supplies feedback for that existing food reading. It cannot disambiguate an isolated verb form, so all-target impact review should still look for newly misleading warmth outside food contexts.

Gem must remain distinct from Dulceață in game mechanics. The legal and dictionary distinctions rule out making `gem` an exact alias of the Dulceață node. The proposal preserves a synthetic surface-derived public ID, rank penalty 1, and projection-only nonwinning behavior. Even when Dulceață is the hidden target, `gem` may provide near feedback but must not win; direct `dulceață` input remains the exact answer.

## Boundary

The proposed anchor is a defensible approximation because it moves from a generic sweet breakfast product to the closest existing fruit-preserve concept. Acceptance remains conditional on implementation tests proving the unchanged public ID, domain, penalty, nonwinning semantics, hidden anchor, repeat behavior and suggestion privacy, plus an all-approved-target impact review. No human playtest or automatic target promotion is claimed.
