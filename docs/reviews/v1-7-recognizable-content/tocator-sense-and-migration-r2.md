# Tocător: physical-board meaning and identity migration

Valid until: cited sources, installed graph/projection, proposed forms/relations or human scope change — then recheck before use.

Research completed 2026-10-08 on main checkpoint ff7fb05. Installed Source6 remains dccd401; the separate Source7 leafă checkpoint f495be6 is unfinished. This report advances only pool record v17-house-tocator. Its prior revision and exact installed readset are in [source analysis](tocator-source-analysis-r2.json).

## Meaning and player benefit

The intended object is a passive, roughly flat surface supporting food while a separate knife cuts it. It has no integral chopping mechanism. Exclude bowl-and-blade choppers whether electric or hand-powered. “Kitchen,” “manual” and “non-electric” alone do not distinguish these objects.

Proposed editorial display label: **Tocător (placă pentru tăiat alimente)**. This is a disambiguating description, not a verified dictionary headword or approved input form. Bare tocător, tocător manual, tocător neelectric and planșetă have no alias approval. The existing label Tocător de bucătărie remains an already exposed projection surface; ownership cannot change incidentally.

A real board concept could distinguish a food-support surface from Cuțit, improve meaningful culinary routes and provide direct board guesses. There is no demonstrated warmer feedback, new globally exposed word, recipe, round or playable target. Product exposure and school terminology establish usage; human recognition/enjoyment have not been measured.

## Claim-specific sources and counterexamples

All new observations were accessed 2026-10-08. Locators identify the retrieved text, not stable webpage line numbers. Only factual paraphrases and URLs are retained; no source prose/images/corpora are redistributed and no open reuse license was verified.

| Source | Observation and scope |
|---|---|
| [Tefal manual choppers](https://www.tefal.ro/articole-de-bucatarie/tocatoare-manuale), category product titles, retrieved lines140/153 | Hand-powered products are called tocătoare and have blades/bowls. This defeats the earlier electric-only exclusion. |
| [IKEA knife-care guide](https://www.ikea.com/ro/ro/rooms/dining/cum-sa-iti-ingrijesti-cutitul-pub0fed03ff/), board section, lines32–34 | Manufacturer guidance uses a wooden/plastic cutting surface with a knife. Supports function, not universal composition or a general safety claim. |
| [IKEA BLANDSALLAD](https://www.ikea.com/ro/ro/p/blandsallad-tocator-bambus-20514027/), product-details text, lines86–91 | A specific board is used to cut and serve bread. The cutting claim is explicit text, not image-alt inference. Its bamboo is not the existing tree-material Lemn; treatment-oil identity is unverified; do not map it to existing culinary Ulei. |
| [ISJ Constanța kitchen lesson](https://www.isjcta.ro/wp-content/uploads/2021/02/Educatie-tehnologica-si-aplicatii-practice_clasa-a-V-a_material-tip-text_Lectia-Buc%C4%83t%C4%83riai_Autor-Cad%C3%A2r-Emilia-Scoala-Gimnaziala-nr.30-Gheorghe-%C8%9Ai%C8%9Beica-Constan%C8%9Ba.pdf), page3/zero-based2, utensil list | Lists planșeta and tocătorul separately in a culinary setting. It establishes neither synonymy nor different dictionary senses. |

The unchanged [R1 sources](primary-object-link-sources-r1.json) support vegetable preparation (IKEA knife/board category), an actual oak model (ARTISTISK), the polyethylene counterexample (LEGITIM), optional cheese serving and an electric Beko counter-sense. Those access/screenshot limits remain history. No original normative semantic dictionary entry was verified for planșetă. ANC's historical wooden-planșetă/caș context describes slicing caș then placing slices on a wooden planșetă; it establishes neither cutting on that board nor synonymy and is not used as an extra neighbor.

## Relationship proposal for independent critique

These are four distinct factual hypotheses, not authored edges, weights, reversals, approved captions or accepted targets. Gastronomie is a proposed category because the intended function is food preparation; it has not been installed.

| Existing owner | Category | Scoped relationship hypothesis | Editorial issue |
|---|---|---|---|
| Cuțit — n_v29_kitchen_table_cutit | gastronomie | Knife cuts food supported on a board. | Function is clear; these are distinct objects, never synonyms. |
| Legume — n_v4gas_legume | gastronomie | Vegetables can be cut on a board. | Specific preparation association, not a requirement for every vegetable/use. |
| Pâine — n_v4gas_paine | gastronomie | Bread can be sliced on a board. | Explicit supported use; does not create bread or sandwich recipes. |
| Lemn — n_v1_3_material_lemn | viata_de_roman | Some boards are made of tree wood, e.g. oak. | Must say some models; plastic/bamboo defeat universal material wording. |

Four distinct incident hypotheses, three potentially same-category, could satisfy the graph's planning4/2 count after independent semantic approval. Direction cannot be inferred from this union count. The new-target rule still needs five unique actual incoming non-distractor neighbors, recognition and coherent feedback. Current approved count is zero. Four rows cannot establish five predecessors even if all were approved incoming. Optional cheese/fruit serving, duplicate directions and projected words are not padding for that deficit.

Play sketches are unexecuted: a culinary Lanț route could use Legume → physical board → Cuțit only if both directions and route quality are independently justified. Cald sau Rece could compare bread/vegetable/knife approaches to a board, but no rank, temperature or winning case has been run. Alchimie has no proposed recipe; a KG node is not automatically a World concept/ingredient.

## Existing identity and migration choices

Current sealed projection is ctxp_7687de8a10648bdf4e3c, surface tocător de bucătărie, explicit Cuțit anchor n_v29_kitchen_table_cutit, penalty0. The normalized native keys tocator, tocator de bucatarie and planseta have no owner. This is static ownership evidence, not a measured rejected guess or public-handler behavior.

| Option | Required contract and trade-off |
|---|---|
| Retain projection exactly | New native labels/forms must normalize disjointly from every active projection. The old phrase keeps its separate Cuțit-backed identity and cannot win a new native board target. This is awkward coverage, not a completed migration. |
| Retire exactly this projection | A separately reviewed graph/identity transaction gives the phrase one native owner and adds the static exclusion. Synthetic ID retirement and changed feedback are explicit. [ADR-0135](../../adr/0135-household-discovery-concepts.md) is precedent, not authorization for this candidate. Missing-owner custom graphs lose the old fallback. |
| Re-anchor the synthetic ID | Changes feedback while remaining nonwinning. It would need a separate explicit decision and does not solve native winning ownership. |
| Keep row and add the same native form | Reject this design: native resolution precedes projection resolution, silently shadowing the row and breaking the collision-free invariant. |

No migration option is selected or implemented. Cuțit's existing owner/forms stay separate. Even keeping its projection bytes exact cannot guarantee old ranks: added graph topology changes reachable populations and weighted rank buckets.

Relevant interfaces: reference projection surface/anchor (contexto_projection.py:224/978), native-first resolver (Go contexto/service.go:687–692), identity/deduplication/win (746–770), graph-wide profiles/ranks (115–139/334–392), collision invariant (test_wordgames_contexto.py:846), graph4/2 (apply_common_words_v24.py:611) and five actual predecessors (Go contentops/critique.go:554). The pack importer refuses nodes/edges (contentops/import.go:72–74); any graph adoption must use its supported graph transaction.

## Concrete acceptance cases before selection/adoption

1. Freeze approved spellings, normalized owners and intended board sense; audit Cuțit and appliance/bare-word collisions. Approve forms separately from the display description.
2. Declare retain/retire/re-anchor explicitly. Check every unrelated projection/proxy/exact-pair row and custom graph missing-owner behavior.
3. Demonstrate equivalent approved native forms share one attempt/identity. If the projection remains, its distinct attempt and nonwinning behavior must be deliberate.
4. Demonstrate native-target wins only through approved native forms; compare direct/fuzzy/clue feedback without hidden-answer leakage.
5. GET/resume must preserve actual guess IDs, order and attempts within the current process. Sessions are process-local; frontend retains a server game ID. Preserve historical receipts instead of claiming an unsupported cross-restart conversion.
6. Measure all old approved-target rank/reachability/temperature impacts and affected existing routes/boards/recipes; explain intentional changes even when proxy bytes are retained.
7. Prove unique incident4/2 separately from target5incoming and C1–C6. Do not select a target from source counts alone.
8. Preserve historical sources/archives/judgments; update current graph/export/authority/history bindings only through reviewed supported transactions and fresh affected audits/finals.

## Outcome and exact next work

The candidate remains researched. New evidence tightens the sense and replaces weak cheese-serving padding with explicit bread-cutting support. Label/alias ownership, four directed semantic judgments, target coverage and normal-play/migration evidence remain unresolved; there is no selection or installed growth.

Next: independently assess the four scoped relations and recognition, then produce one explicit native spelling/identity proposal against current Source6. If a target is proposed, identify a genuinely useful fifth predecessor before candidate generation. Keep the selected leafă Source7 integration checkpoint separate; its next integration action remains fresh Quick audit on the preserved scratch World1f state. No old transaction is replayed here.
