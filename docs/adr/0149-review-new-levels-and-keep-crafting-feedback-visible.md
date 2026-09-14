# ADR-0149: Review new levels and keep crafting feedback visible

- Status: accepted; extended by [ADR-0150](0150-expand-vocabulary-and-clarify-game-controls.md)
- Date: 2026-09-14
- Partially supersedes [ADR-0043](0043-lant-visible-route-corridors.md) for mandatory
  first-stage direction hints, and [ADR-0145](0145-persistent-alchimie-discovery-world.md)
  for always-visible exploration search and goal controls.

## Scope and reviewed content

The owner requested a new entry/level creation session and a game GUI critique.
This bounded V92 session uses `feat/v92-entry-creation-02`, based on completed commit
`c0ead5e`. It adds **11 rounds or targets and three recipe alternatives**, with no new
graph concepts, game mechanics, account features or deployment:

| Game | Added | New content |
|---|---:|---|
| Conexiuni | 1 board | Aeration, rotation, filled pastries and clothing predicates |
| Cald sau Rece | 3 targets | Chitară, Brașov and Nadia Comăneci |
| Lanțul Cuvintelor | 1 route | Capra cu trei iezi → Amintiri din copilărie |
| Intrusul | 3 boards | School supplies, kitchen vessels and road vehicles |
| Perechi | 3 boards | Twelve previously unused everyday associations |
| Alchimie exploration | 3 recipes | Omelette sandwich, boiled-egg potato salad, mash from baked potatoes |

Quality review rejected the proposed Nadia→Amânar and Zamfir→Maria Tănase routes:
their numerical branching mostly repeated a discipline, genre or profession rather
than supplying distinct, concrete connections. Authoring also excluded reused Conexiuni
groups and weak Contexto neighborhoods. The six quick boards retain precise predicates:
an airport is transport infrastructure, and the flower/pot association refers to the
plant bearing the flower, respecting the exact botanical identity in the graph.

The five pack additions pass exact raw factual/quality review, pending import, fresh
allocated-ID dossiers, separate analyst/verifier judgments and strict promotion. All
five are ranking eligible; the existing eight pending records remain pending. The six
quick boards pass original structural and rating gates and both complete reviews over
the expanded 51-board supplement. All six qualify for the starter shelves.

The previous 686 pack records, 336 core quick-game records and 45 authored board
payloads/scores remain exact. Adding to the supplement recomputes 38 private competition
rank fields; selection still uses the existing score bands. No private rank, source ID
or unearned answer is added to the public API.

## Alchimie reuse and save compatibility

The kitchen retains 221 concepts, eight starters, 96 later supplies, twelve tiers,
117 craftable results and 32 optional goals. Recipes grow 285→288. Reusing omelette,
boiled egg and baked potatoes increases crafted intermediates 47→50 and reduces terminal
results 70→67. The explanations explicitly include cooking/cooling or mashing where
needed; these remain simplified culinary associations, not complete recipes.

Editorial `RECIPE_SOURCES` can specify preparation references per recipe. The generated
candidate preserves these primary references before factual review; existing recipes
retain their previous candidate records and final reviewed sources. Both full semantic
reviews cover all 288 recipes and 221 concept digests, inheriting prior judgments only
after exact record comparisons. Final package writing requires the current live audit
and both original reviewers' final artifact-bound acceptances.

The immutable 221-concept candidate is now the compatibility predecessor. Its existing
75/111-concept history is carried forward, and its own fingerprint joins that history.
All 39, 58 and 117 historical discovery prefixes remain restorable. A completed
221-concept collection stays complete and keeps its earned journal; alternative recipes
do not manufacture new discoveries or reset an existing collection.

## Critique findings and GUI changes

Fresh responsive-browser journeys cover all six games at 390px and 320px widths,
including incorrect attempts, hints, resumed rounds and real wins. Primary reference
interfaces and rules informed the critique; this is not a measured human-playtest result.

Exploration had two observed defects. Optional controls pushed starter words below the
viewport. More seriously, after eight discoveries, combining from the bottom of a
24-word list left the crafting feedback at y−405…−345, entirely offscreen. The player
could perform an action without seeing its outcome.

The optional goal and library search/filter controls now start in native disclosures.
Their summaries retain the selected goal, completion and any active search/filter. Word
tiles and controls keep their touch sizes; all eight starters fit both tested 844px-high
phone viewports. The existing free hint is labeled `Gratuit` beside the workbench.

The compact workbench stays visible while scrolling a long collection when the visual
viewport is at least 480px high and the bench occupies at most 35% of it. ResizeObserver
and visual-viewport changes re-evaluate that condition. Smaller keyboard viewports or
larger text/content return the bench to normal flow so it cannot obscure the workspace.
Tile scroll clearance accounts for the actual pinned bench height. Optional controls
remain available without changing the selected ingredient or save protocol.

Independent keyboard review also reproduced focus returning to an offscreen ingredient
after its partner disappeared. Keyboard activation now brings the restored word, or
the collection heading, into view below the bounded bench. Pointer crafting retains
its scroll position; moving focus deliberately during a request still prevents focus
restoration from stealing it. The retained-origin case is checked as well.

The other four non-Lanț interfaces retained their efficient interaction loops: one tap
for Intrusul, two for Perechi, deliberate four-tile submission for Conexiuni, and Enter
submission for Cald sau Rece. The critique found no new blocking GUI defect in those
four; predicate quality and useful guess neighborhoods remain editorial priorities.

## Useful Lanț hints immediately

A deterministic 20-round audit found 13 first hints that merely repeated
`legătură directă`. Eight hints matched every visible choice and could not narrow the
decision. Lanț hints are free; the defect was a wasted action, not a score charge.

When the first direction is exactly this generic fallback, the server now returns the
existing alternatives stage immediately and retains help level two. Specific direction
captions still appear first. Subsequent help reaches the existing one-hop stage, capped
at three. GET never escalates help; move and undo clear the earned payload while retaining
the help level. The public response variants, route secrecy, scoring, move budget,
session TTL and capacity remain unchanged.

The same audit now has 13 immediate alternatives and seven byte-identical specific
direction hints. A checked two-move win needs one fewer help request and still scores
1000. This correction does not make generic graph bridges semantically stronger; those
remain subject to content critique.

## Verification and evidence

Exact raw candidates, corrections, independent reviews, promotion artifacts and live
audits are retained in [the session review](../reviews/v92-entry-creation-and-gui/README.md).
The five-artifact inverse restores exact `c0ead5e` bytes before older historical tests;
previous review hashes and historical count assertions remain intact. A generated
117-craft browser checkpoint tests the third saved-world generation.

Final backend/browser/frontend results and artifact pins belong in [STATUS](../STATUS.md).
The previous 17-entry authoring queue remains unapproved background work; it is not
counted as delivered content. This session does not authorize another automatic batch.
