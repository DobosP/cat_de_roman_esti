# V81 bound Nucă factual and semantic review

Valid until: proposal SHA-256 `0612129b282feb6124c2992078178efc17fa088b0b425dbccf3291ee10b34d8a` or any bound baseline source changes.

Reviewer: `session_refactor`

Role: independent factual and semantic reviewer

Verdict: **ACCEPT**

## Exact bound proposal

This review accepts `/home/dobo/work/_temp/v81-nuca-feedback/proposal.json` at SHA-256 `0612129b282feb6124c2992078178efc17fa088b0b425dbccf3291ee10b34d8a` against baseline `dbbcf6e8b810fb990c9acffb42d6426138551637`.

The proposed canonical node is factually sound. Romanian `nucă` first denotes the fruit of the walnut tree and, in culinary use, its edible kernel. The description “Fructul nucului, cu coajă tare și miez comestibil folosit în preparate dulci” accurately states that meaning without claiming that walnut is used only in sweets. A salience of `0.90` and easy treatment are credible editorial calibration for a basic food word, consistent with the current common-fruit band; the sources establish familiarity but do not mathematically derive that number.

The single alias `nucile` is the standard feminine definite plural and has the same edible-fruit referent. Canonical `Nucă` already covers `nucă`, accentless `nuca`, and uppercase forms under the existing normalizer. The excluded forms are appropriately conservative:

- `nuci`, `nucii`, and `nucilor` collide with inflections of masculine `nuc`, the walnut tree; capitalized `Nuci` is also an Ilfov commune and village.
- `nuc`, `nucul`, and `nucului` denote the tree or its wood.
- `miez de nucă` is the edible kernel, a part of the fruit rather than a strict lexical alias for the whole node.
- `nucă de cocos` is a distinct compound and food. Other nuts such as alună, migdală, fistic, and caju are likewise outside the proposal.

[DEX/DLRLC/DOOM for “nucă”](https://dexonline.ro/intrare/nuc%C4%83/38186) records the edible fruit/kernel senses and the feminine paradigm. [DEX/DOOM for “nuc”](https://dexonline.ro/intrare/nuc/38185) records the masculine tree/wood noun. The [DOOM3 introductory study](https://doom.lingv.ro/studiu_introductiv/observatii_recomandari) explicitly notes that plural `nuci` belongs to both feminine fruit `nucă` and masculine tree `nuc`. The [official Comuna Nuci site](https://primarianuciilfov.ro/nuci/) confirms the proper-name collision.

## Four ingredient edges

All four outgoing, directed, non-distractor `part_of` edges labeled `ingredient pentru` are factually supportable:

- **Nucă → Cozonac, 0.97:** walnut is an ordinary prominent filling. [AGERPRES](https://agerpres.ro/social/2021/04/29/traditii-in-bucate-cozonac-moldovenesc-reinventat-dar-cu-acelasi-gust-desavarsit--705669) calls for abundant ground walnut; [Radio România Internațional](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/cozonac-id593926.html) describes both historical and current walnut-filled recipes. Current [PRO TV](https://www.protv.ro/emisiuni/vorbeste-lumea/articol/120853-reteta-de-cozonac-cu-nuca-cacao-si-ciocolata-a-majdei-secretul-unui-aluat-perfect) and [Digi24](https://www.digi24.ro/magazin/stil-de-viata/culinar/cele-mai-bune-retete-de-cozonac-pentru-paste-2026-ingredientele-recomandate-de-specialistii-in-gastronomie-pentru-un-aluat-perfect-3703649) recipes independently confirm the association.
- **Nucă → Colivă, 0.97:** walnut is a strong traditional ingredient. [Radio România Internațional](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/coliva-reinterpretata-id911961.html) uses half a kilogram of walnut and mixes it into the boiled grain.
- **Nucă → Baclava dobrogeană, 0.95:** walnut is a common filling, alongside variants such as pistachio. A [Romanian Ministry of Education-owned vocational textbook](https://portal.eduhr.ro/wp-content/uploads/2021/11/A448.pdf) describes Dobrogean baklava as a sweet dessert with nuts and syrup; a [Babadag recipe](https://unireaprajituri.ro/wp-content/uploads/2018/12/Cartea_Unirea_100_de_Secrete_Dulci.pdf) specifies 500 g walnut, and [PRO TV](https://www.protv.ro/emisiuni/arena-bucatarilor/articol/55451-arena-bucatarilor-salata-de-caracatita) independently demonstrates walnut-filled baklava.
- **Nucă → Cornulețe, 0.90:** walnut is a familiar filling or dough ingredient, though jam, rahat, vanilla, and other variants are also ordinary. [Radio România Internațional](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/cornulete-cu-untura-id594322.html) gives ground-walnut and plum-jam filling; [AGERPRES](https://agerpres.ro/social/2021/12/24/tradi-ii-in-bucate-mures-galustele-cu-pasat-sarmalele-si-raciturile-de-porc---nelipsite-din-meniul-d--837407) records traditional cornulețe filled with walnut or jam.

The strengths are editorial confidence/gameplay weights. They mean that each association is strong and recognizable; they do not mean walnut is universal or mandatory in every instance of those recipes. That qualification matters most for Baclava dobrogeană and Cornulețe. `ingredient pentru` is honest wording, while “ingredient obligatoriu” would not be.

## Contexto policy

The target-aware policy is semantically defensible. It uses the real Nucă node only for exact self or a direct, directed, non-distractor `part_of` edge with the exact ingredient label and strength at least `0.90`. All four reviewed recipes qualify. Everywhere else it retains the prior Miere approximation with one-rank penalty and no exact win.

This boundary is driven by reviewed graph relations rather than a Cozonac target allowlist. It lets the specific walnut guess score from the real concept where walnut is explicitly authored as an ingredient, while suppressing the unrelated multi-hop warmth found in the naive graph simulation. Miere remains an approximate fallback, not an identity claim. Exact Nucă must bypass proxying; if Miere is the secret, projected Nucă must remain nonwinning; guess scoring and typo-suggestion suppression must share the same target-aware decision.

The proposal leaves the closed 71 common-node proxy inventory untouched, removes only canonical `nucă` from projection vocabulary, preserves the other 472 projection terms and Gem policy, and adds no target or pack row. Those are implementation claims to be verified after code exists, not factual evidence supplied by this review.

## Limits

The four real edges satisfy the ordinary node-connectivity floor without filler. They also expose a genuine forward recipe move to other graph consumers. The final implementation still needs an all-target Contexto impact sweep, exact effective-target inventory, unrelated controls, suggestion/privacy tests, and preservation checks. Any future qualifying Nucă ingredient edge would enlarge the native-feedback zone and therefore needs review.

Mucenici remains excluded because its current regional-variant description has separate factual concerns. No aliases for a generic nut class or other nut species are approved. This is an independent Codex review, not a human Romanian SME or playtest.
