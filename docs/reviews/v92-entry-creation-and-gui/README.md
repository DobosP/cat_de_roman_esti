# V92 — entry creation and six-game GUI critique

Valid until: any bound candidate, catalog, runtime source or review changes — then treat its evidence as history.

This session starts from `c0ead5eb524fe40ec4a1760488badec395c0ae0c` and installs **14 reviewed
additions: 11 rounds/targets and three Alchimie reuse recipes**. Sixteen proposals entered
independent review; two Lanț routes were rejected for relying only on overlapping genre,
profession or national-team classifications. The existing shared graph and gameplay
content are preserved. [Final integration verification](verification.json) passed; no deployment or human
enjoyment acceptance is claimed here.

| Game | Added | Accepted content |
|---|---:|---|
| Conexiuni | 1 board | Dough aeration, rotational motion, filled dough and lower-body clothing |
| Cald sau Rece | 3 targets | Chitară, Brașov and Nadia Comăneci |
| Lanțul Cuvintelor | 1 route | Capra cu trei iezi → Amintiri din copilărie |
| Intrusul | 3 boards | School tools, kitchen vessels and road vehicles |
| Perechi | 3 boards | Twelve previously unseen practical associations |
| Alchimie | 3 recipes | Reuse Omletă, Ou fiert and Cartofi copți in existing results |

The curated pack is **691 records: 683 approved and eight pending**, with 521 eligible
records. Intrusul has 211 boards and Perechi 176. Their six new boards pass the original
structural and starter gates, with preferred scores 84–94. They expose nine previously
unseen visible concepts in Intrusul and fifteen in Perechi. These are new appearances in
the games, not new shared graph identities.

Alchimie retains **221 concepts, 117 craftable discoveries and 32 optional goals**. Recipes
increase 285→288 and reusable crafted concepts 47→50; 77 results still have alternative
recipes. The new pairs lead to Sandviș, Salată de cartofi and Piure de cartofi. Explanations
state the cooking, peeling, cooling or mashing needed, rather than treating a raw potato
as ready to eat. Existing recipes, starters, unlocks and goals remain exact, and the
75-, 111- and previous 221-concept save collections retain compatibility.

## Review and promotion evidence

- [Pack raw candidates and decisions](pack/raw/) preserve all five category files and
  complete independent factual/quality coverage. The two rejected personality routes remain
  in the [original quality decision](pack/raw/personalitati/verify_quality.json), not in
  served content. The [analyst](pack/analyst.json), [verifier](pack/verifier.json),
  [five final dossiers and gate artifacts](pack/gate/) and [promotion log](pack/promotion.log)
  bind the exact five approved IDs. No pending hold or approved-stock demotion was bypassed.
- [Quick full candidate](quick/candidate.json), [factual review](quick/factual-review.json)
  and [quality review](quick/quality-review.json) cover all 51 authored rows. The original
  45 review judgments are inherited only after exact row, graph, rubric and identity checks;
  they are not represented as freshly researched. Six new rows receive separate review.
  [Final factual](quick/final-factual.json) and [quality](quick/final-quality.json) verdicts
  bind the actual [51-round live audit](quick/live-audit.json).
- [Final world candidate](alchimie/candidate.json), [factual](alchimie/factual-review.json)
  and [quality](alchimie/quality-review.json) reviews cover the complete kitchen. The
  [final factual](alchimie/final-factual.json) and [quality](alchimie/final-quality.json)
  approvals bind the [final 288-recipe audit](alchimie/live-audit.json). Earlier tentative
  world proposals are excluded from this approval chain.
- [Independent quick API receipt](quick/independent-final-api.json),
  [world API receipt](alchimie/independent-api.json) and
  [pack API receipt](pack/independent-api.json) preserve replay, hint, hidden-answer and
  restoration observations. The [core artifact inverse](artifact-delta.json) restores exact
  `c0ead5e` bytes before earlier historical checks; all 686 old pack records and 336 original
  quick-board payloads remain exact. The focused history/migration checks passed 65 tests.

The installed [quick catalog](../../../cat_de_roman_esti/fixtures/quick_games_v92.json) and
[discovery world](../../../cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json) are
linked rather than duplicated as proposed catalogs. Their exact hashes and each archived
file's original source path, byte size and SHA-256 appear in [evidence-manifest.json](evidence-manifest.json).
Prior inherited judgments remain available in the [all-game review](../v92-all-games-content/README.md)
and [221-concept kitchen review](../v92-alchimie-large-concepts/README.md).

Two quick predicates were corrected before final acceptance: an airport was called a
terminal, and the graph's flower sense was called an entire ornamental plant. The
[original six rows](quick/raw/candidates-original.json), [corrected rows](quick/raw/candidates-v2.json)
and [correction receipt](quick/raw/label-correction.json) preserve that history. The
Morcov–Iepure pair is a familiar cultural association and makes no dietary-care claim.
Contexto's [actual author API probes](pack/author/contexto-probes.json) retain limitations:
Coardă, Biserica Neagră and bare Montreal are unresolved, while broad category guesses can
be cooler than expected. Independent reviewers accepted several useful entry paths without
claiming complete neighborhoods.

## GUI findings and implemented changes

The [per-game critique](gui/critique.md) examines all six games and both Alchimie modes,
including responsive Chromium journeys and fresh reference-interface checks. It preserves
Intrusul's direct tap, Perechi's two-tap match, Conexiuni's deliberate submission and Cald
sau Rece's Enter-based guessing. No extra confirmation or mandatory action was introduced.

Exploration now keeps craft feedback visible during long-library browsing when the viewport
can accommodate it. Optional goals and library tools begin collapsed, while the selected
goal and active filters remain visible in their summaries. On short or enlarged-text views,
the bench returns to normal flow so it cannot cover the playable words. The measured 320px
starter view now fits all eight words; after eight discoveries, bottom-word feedback moved
from outside the viewport at y−405..−345 to y98..158.

| Evidence | Before | After |
|---|---|---|
| 320px starter collection | [Screenshot](gui/explore-320-round.png) | [Screenshot](gui/after/explore-320-round.png) |
| Deep-library craft feedback | [Screenshot](gui/exploration-depth-bottom-combine.png) | [Screenshot](gui/after/exploration-depth-bottom-combine.png) |

Lanț skips an uninformative “direct relation” hint and offers concrete alternatives
immediately, while preserving useful specific directions. The independent
[before/after audit](gui/lant-hint-change-verification.json) compared 20 deterministic starts:
13 generic first stages became alternatives and seven specific directions stayed exact.
Earned hints survived GET without escalation; moves/undo cleared only the earned payload,
repeated help stayed bounded, and a hinted win retained 1000 points. This removes a wasted
action; it does not establish that every legacy route is a satisfying semantic bridge.

The GUI lane's [bound verification](gui/verification.json) records its focused 30-check
exploration run and measurements. Responsive browser screenshots are not physical-device
or human playtesting. The completed [final verification](verification.json) covers the current backend,
accounts, frontend, browser, lint and content artifacts.

## Preserved unapproved author backlog

An earlier worker had already persisted a separate **17-entry unapproved queue** under
`session-02/`; an ignored-file search initially missed it. That queue was not silently
removed or approved. Its [original README](unapproved-author-backlog/README.md),
[exact batch index](unapproved-author-backlog/batch-index.json), candidate files, author
sources and checks are preserved under `unapproved-author-backlog/`. Overlaps with the new
accepted batch are not additional installed entries. Its approval and live-integration gates
remain outstanding. Archived Python snapshots use `.py.txt`; their bytes are unchanged.

## Final keyboard-focus correction

Independent review reproduced offscreen focus after a deep-list craft removed its
second ingredient. Keyboard activation now brings the restored word or collection
heading into view, including when a still-active tile moves during feedback changes.
Pointer browsing stays in place and deliberate focus changes during a delayed request
remain respected. The [independent final review](gui/independent-final/final-review.json)
and [evidence manifest](gui/independent-final-manifest.json) preserve before/after checks
for these cases, short viewports and enlarged text. The earlier GUI implementation
receipt remains historical; final integration results cover the corrected source.

The [catalog delta](content-delta.txt), [stable-ID delta](content-delta.json) and
[world delta](world-delta.json) distinguish 11 added rounds from three added recipes.
Thirty-eight private quick-game competition ranks recompute; original words, pair
meanings, scores and eligibility remain exact.

## Final integrated build

[Verification](verification.json) binds the exact final artifacts to **1948 backend,
458 browser, 212 frontend-native and 53 accounts passing tests**. The initial bundle is
**119.23/120 KiB gzip**. [Backend](backend-tests.log), [browser](browser-tests.log),
[frontend build](frontend-build.log) and [accounts](accounts-tests.log) logs are preserved.
Ruff, whitespace, both content validators and documentation checks passed.
The current preview uses port 8150. No push, main merge or deployment was performed.
