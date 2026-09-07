# V84 independent pending-round verification

Valid until: the four bound records, graph, relevant runtime or rubric changes — then treat as history.

Reviewed 2026-09-07 by `v84_interface_review`, independently of the raw-batch author
and root analyst. Final verdicts: **promote all four**, with the residual ranking noise
below recorded expressly. Exact IDs and dossier bindings are in `verifier-review.json`.

The three concrete targets are recognizable Romanian foods, with five, six and eighteen
incoming neighbors respectively. Their usual category, defining-ingredient and preparation
guesses supply useful approaches. This decision does not infer quality from reachable-node
counts alone. My separate-process impact audit covers all 221 old approved records and
17 inputs; the new-target audit adds 31 first-guess inputs per target, three private
warmer-clue/exact-answer journeys and both shortest Lanț paths.

- **Plăcintă cu mere:** its fruit, dough, rolling-pin and tray inputs are rank 3,
  with Plăcinte rank 2 and flour rank 11. The full Băneasa page was accessible and
  directly supports the preparation links. Oetker supplies independent recipe evidence;
  the older Digi24 menu and indexed 2024 TVR episode support broad familiarity.
  Butter remains cold and yeast is too hot, but five more direct, recognizable paths
  still make the target clear. [Băneasa](https://www.pastebaneasa.ro/retete/placinta-cu-mere/),
  [Oetker](https://www.oetker.ro/retete/r/placinta-clasica-cu-mere),
  [TVR episode metadata](https://www.youtube.com/watch?v=9YOl1-wgaw8).
- **Salam de biscuiți:** biscuit and butter rank 3, dessert rank 2 and pastry rank 7.
  RRI's recipe and historical discussion plus the 2023 PRO TV segment support both
  the food identity and recognition. The no-bake preparation makes the oven/tray rank 36
  misleading; cocoa is warm at 62 and should eventually outrank those utensils.
  Cinnamon at 19 also illustrates residual projection noise. The defining biscuit input
  and multiple clear sweet-food approaches still justify promotion; this is not a claim
  that ingredient ordering is fully realistic.
  [RRI](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/salam-de-biscuiti-id594218.html),
  [PRO TV](https://www.protv.ro/emisiuni/vorbeste-lumea/clip/52864-salam-de-biscuiti-cu-fistic-si-merisoare).
- **Pâine:** dough, yeast and qualified oven each rank 7, food ranks 3, and flour is
  now warm at 45/two hops. Historical dictionaries and a documented modern bread recipe
  support the literal staple sense and specific preparation links. The general ingredient
  projection still makes cinnamon spuriously hot at rank 4, ahead of the production core;
  butter is cold and pen is lukewarm. I considered holding this target for that defect.
  The defect is real but does not remove the three independent direct production cues,
  usual food opener, or unambiguous everyday target, so the target passes C1–C6 with
  the limitation disclosed. The earlier V77 deferred flour-to-house-bread edge remains
  absent; its flour-to-fountain-pen control remains cold, rank 618/distance 4.
  [Dictionary evidence](https://dexonline.ro/intrare/p%C3%A2ine/40183),
  [Documented bread preparation](https://www.oetker.ro/retete/r/paine-cu-maia).
- **Făină → Cornulețe:** both API routes win in two moves with distinct intermediates,
  Aluat and Cozonac. The flour/dough/rolled-pastry route is concrete. The older cozonac
  alternative is a weaker shared holiday-baking association, not physical conversion;
  it is acceptable alongside the precise route and is not the only playability basis.
  The 0.55 salience warning was reviewed without changing the score: the endpoint is
  visible and its pastry meaning is supported by dictionary, current radio and recipe
  evidence. It does not require specialist knowledge.
  [RRI](https://www.rri.ro/rubrici/secretele-bucatariei-romanesti/cornulete-cu-untura-id594322.html),
  [Ferrero method](https://www.nutella.com/ro/ro/lasa-te-inspirat/retete/cornulete-cu-fructe-uscate),
  [Older holiday menu](https://www.digi24.ro/stiri/actualitate/social/cat-costa-masa-de-craciun-produsele-traditionale-maresc-de-trei-patru-ori-cheltuielile-338418).

All four record/rubric/graph bindings were independently recomputed. None duplicates an
old Contexto target or either orientation of an old/tombstoned Lanț endpoint pair. Real
API journeys kept answers private, the warmer clues reproduced their advertised ranks,
and exact answers won. Scoped games correctly offer the warmer clue directly because
the player already selected the category; the scratch probe was corrected to request that
single available clue. No runtime rule or score threshold was changed for verification.

The indexed TVR episode metadata was available; direct video opening failed, so no video
viewing is claimed. These source checks and agent journeys are not Romanian-player
playtests or a guarantee of perfect semantic ranking. Scratch reproduction and raw
observations: `impact/pending_probe.py`, `impact/pending-evidence.json`.
