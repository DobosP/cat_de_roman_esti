# ADR-0150: Expand vocabulary and clarify game controls

- Status: accepted
- Date: 2026-09-15
- Extends [ADR-0149](0149-review-new-levels-and-keep-crafting-feedback-visible.md)
  with new discoverable words, completed-library recovery and clearer controls.

## Scope and accepted content

The owner explicitly requested another similar session with new words for all games
and interface improvements. This bounded V92 session uses `feat/v92-entry-creation-03`,
based on `0b51e03`. Publication, deployment and another automatic session remain outside
its scope.

The additions are **11 rounds or targets, four Alchimie words and six recipes**:

| Game | Added content |
|---|---|
| Conexiuni | One board with scoarță wordplay and concrete powder, control and watering groups |
| Cald sau Rece | Ion Creangă and Alba Iulia targets |
| Lanțul Cuvintelor | Poarta Sărutului→Oltenia and Ștefan cel Mare→Bucovina |
| Intrusul | Three boards using electrical connections, bodily needs and kinship terms |
| Perechi | Three boards with twelve previously unused intended pairs |
| Alchimie | Mere coapte, Ardei copți, Pilaf de legume and Dovleac copt, plus onward pepper/pumpkin recipes |

The new boards expose six words previously absent from Conexiuni, ten from Intrusul
and twenty from Perechi. These are per-game exposure counts, not new shared graph
identities. All six quick boards pass the existing preferred-score floor; five also
qualify for starter selection. Graph checks are supplemented by independent judgments
of meanings, alternative pairings and recognition.

Vioară→Ateneul Român was excluded because the target's existing definition makes an
unsupported principal-festival-stage claim. The shared graph was not changed to rescue
that level. A second Conexiuni draft reused prior groups or created semantic crossfits;
it was not included to fill a quota. The accepted board's hardest group uses a nameable
polysemy, supported by three concrete anchors.

The five pack additions pass complete raw factual/quality review, pending import,
fresh allocated-ID dossiers, separate analyst/verifier judgments and strict promotion.
All five are eligible. All 691 previous pack records, the 336 core quick-game records
and the previous 51 authored quick payloads/scores remain exact. The existing eight
pending records stay pending. Private ranking fields recompute as the pools grow;
selection formulas, score bands and answer privacy remain unchanged.

## New Alchimie discoveries with complete compatibility

The kitchen grows **221→225 concepts, 288→294 recipes and 117→121 craftable results**.
Eight starters, 96 later supplies, twelve tiers and 32 optional goals remain exact.
The new preparations have recognizable unoccupied ingredient/tool pairs. Roasted
peppers lead onward to zacuscă; baked pumpkin leads to cream soup. Crafted intermediates
grow 50→52. Two new results are terminal, bringing terminal results to 69.

The four definitions are original world-local records under `alw_food_` IDs, with
primary references and exact authored provenance snapshots. They do not shadow a KG
label/alias or old world identity and do not create an implied redistribution license.
All 221 prior concept records and 288 recipes retain their text, outcomes and sources.

The immutable session02 candidate becomes the compatibility predecessor. Its existing
three fingerprints are preserved and its 221-word/288-recipe fingerprint is added,
so both distinct 221-word books remain supported alongside the 75/111-word books.
Completed old collections retain all 117 earned recipes and gain four discoveries;
they are complete again after earning those new words.

Full independent reviews cover all 225 concept digests and 294 recipes, explicitly
inheriting unchanged prior judgments. Final artifact-bound reviews follow a live audit
of all 33 free/goal runs and every historical prefix. A generated browser checkpoint
uses all three session02 alternative recipes, checking that their earned provenance
survives as well as the default recipe path. No capacity or save-format limit changes.

## Clearer relationship wording

Twelve new noun phrases explain the two retained Lanț levels: sculpture/creator,
monument/place, ruler/foundation and region relationships. They bind exact existing
edge snapshots and work in both supported traversal directions. The previous 68
caption entries remain exact. Facts, route topology and weights do not change.

Independent review covers the selected twelve separately from six discarded music-route
proposals. Actual dossiers include the final display captions and module digest. Changed
edge snapshots fall back to neutral text; missing edges make no relationship claim.

## Interface corrections

Fresh isolated browser journeys exercised all six scored games at 390px and 320px,
including keyboard completion. The critique identified concrete defects:

- A hidden Alchimie query could empty the library with no visible way to reset it.
  `Șterge căutarea` now remains visible whenever a query is active. It clears the query
  in one local action, preserves the selected word/filter/save, and sends no request.
  Keyboard recovery places the collection heading in view; pointer use retains position.
- Completed Alchimie collections showed no words while suggesting more crafting and a
  checkbox hidden in a closed disclosure. Server-confirmed completion now shows every
  earned word, removes the irrelevant active/all checkbox and hint action, and gives
  collection/journal guidance. Search remains local and the earned journal stays intact.
- Conexiuni's hidden icon left a four-column grid with three visible children, causing
  selection/mistake overlap at 320px and with enlarged text. Explicit desktop columns
  and a separate mobile mistakes row keep the indicators distinct at every selection count.
- Contexto's submit button and Lanț's hop/undo/hint buttons measured only 34px high.
  Scoped CSS now maintains the established 44px touch target without changing actions.

Intrusul and Perechi retain their existing tap-efficient interfaces. The prior pinned
workbench, keyboard craft recovery, request ownership, scoring and session bounds remain.
Independent final review checks delayed search reset during crafting, deliberate focus
ownership, short viewports, enlarged text and a completed 225-word collection.

## Verification and evidence

[The session archive](../reviews/v92-session03-vocabulary-and-interface/README.md)
contains exact candidates, corrections/exclusions, independent judgments, API replays,
caption evidence and before/after GUI captures. The strict five-artifact inverse restores
exact `0b51e03` bytes before older historical assertions; their hashes and counts are
retained. The previous unapproved queue is linked as history, not counted as new delivery.

Expanded pools can change deterministic test selections. Current daily fixtures follow
the approved inventory. Perechi privacy checks distinguish canonical visible word labels
from unearned category metadata and explicitly reject forged hints/categories. Lanț
recovery tests check the actual earned stage, including a skipped generic first hint.

Final integrated results and artifact pins belong in [STATUS](../STATUS.md). Responsive
Chromium checks establish the recorded behavior, not human enjoyment or physical-device
acceptance. Existing KG factual debt, other thin target neighborhoods and broader content
calibration remain separate follow-ups.
