# Fresh six-game GUI and play critique

Valid until: this candidate's interface changes — then treat baseline findings as history.

Reviewed 2026-09-14 against c0ead5e, isolated Chromium contexts at 390×844 and 320×844.
No account or existing user progress was used. Seven entry screens and starting boards
(both Alchimie modes) were inspected. Real deterministic seed-38 journeys exercised
all six scored games to wins; wrong choices, clues and saved-round restoration were
exercised in Intrusul, Perechi, Conexiuni, Contexto and Lanț. Exploration was played
through eight natural discoveries via its public hints, then resumed.

## Ranked findings

1. **High: Alchimie discovery feedback disappears during ordinary collection browsing.**
   After eight discoveries, 24 active words make the list scroll. Combining bottom
   words leaves its result at y−405..−345 while the active ingredient is also above
   the viewport. Even the seventh successful discovery (Compot) put the message at
   y−65..−25. The player cannot see whether the second tap worked without scrolling
   away from the next choices. `AlchimieExplore.tsx` `.alchemy-bench` and
   `.alchemy-inventory-grid`; `alchimie.css` explicitly makes the bench static.
   Evidence: `exploration-depth.json`, `exploration-depth-bottom-combine.png`.
   Keep one compact craft/result area visible while browsing; let it flow on short
   or enlarged-text views so it cannot block the words. This is an observed usability
   problem, not a comparative human-performance claim.
2. **Medium: Lanț's generic direction spends an action without useful guidance.**
   Seed38 Hagi→Brâncuși: first hint says “Direcție: caută o legătură «legătură directă».”
   Both bărbat and carieră already have that caption. The next hint supplies actual
   alternatives. Skip the generic direction and offer the existing alternatives
   immediately; preserve informative specific captions and free-hint rules.
   `.lant-hint-panel`, backend `lant.py` HintView. `lant-390-hint-one.png` and
   `lant-390-hint-two.png` reproduce the issue. The weak generic semantic bridge is
   also content debt; the GUI correction does not make every route educational.
3. **Medium: exploration setup competes with the initial word library.**
   Eight starter tiles occupy y578..856 at390, and y674..952 at320. Optional goal,
   search/filter and explanatory text consume space before the first play action.
   Scored Alchimie and the other five initial boards remain reachable on these sizes.
   Collapse optional goals and library tools, retaining visible selected-goal status,
   search/filter access and readable 44px controls. `explore-390-round.png`,
   `explore-320-round.png`, `captures.json` provide before measurements.

## Per-game decisions

| Game | Observed loop and feedback | Critique / action |
|---|---|---|
| Alchimie | Two word taps craft; a useful result carries automatically. Free hint needs a result cue, exact pair, then one partner tap. Scored challenge won in three word taps for two crafts. | Retain direct mixing. Fix the offscreen exploration feedback and optional-control density above. Twenty-four active words already expose the long-library failure, so adding content alone makes it more apparent. |
| Intrusul | One tap checks; a wrong word is visibly marked as in-group, repeats are free, paid hint states150point cost. Earned group and wrong word survive reload. Four tiles fit at320. | Retain the compact board and deliberate next-round action. No new GUI defect reproduced; editorial clarity of the predicate is the quality priority. Do not add confirmation to every answer. |
| Perechi | Two taps check; first-word retap cancels. Four solved pairs leave the active board. Two mistakes unlock a150point clue; the two marked words and cue survive reload. Eight long-label tiles fit at320. | Retain face-up words and automatic check. Optional preference: clearer pair-label prose at the result screen; avoid adding a submit button or another mandatory step. |
| Conexiuni | Four taps plus Verifică; all16 words and action row visible at390/320. One-away retains selection and identifies that one change is needed. Paid100point clue survives reload. | Retain deliberate submit because mistakes are limited. Category copy and uniquely defensible membership matter more than reducing the existing five deliberate actions. Do not auto-submit fourth selection. |
| Cald sau Rece | Guess+Enter keeps typing efficient. Rank guide, most-recent comparison, ordered history and120point clue costs are visible. Unknown input does not consume attempts; saved clues/ranks resume. | Retain input-first layout. At320 the submit button wraps below input; it costs vertical space but remains44px and usable. Short keyboard view remains an acceptance check, not grounds for shrinking the input. No new blocking GUI issue reproduced. |
| Lanț | Visible position/target and one-tap next words; typed alternatives remain available. Concrete second-stage hints persist after reload and move directly. Two-move seed38 win remained1000points after free hints. | Skip only the empty generic direction. Further specific relation captions and less generic bridge content are editorial follow-ups. Keep neutral wording so reversing an edge does not invent a factual claim. |

## Fresh primary-source comparisons

References re-opened 2026-09-14. These are analogous interfaces/rules, not a popularity
ranking or proof that this arcade matches their measured usability.

- [Wordwall Quiz](https://wordwall.zendesk.com/hc/en-gb/articles/360015811938--How-to-create-a-Quiz-activity)
  documents direct answer taps, immediate correct/incorrect feedback and options below
  the activity. This supports preserving Intrusul's efficient choice loop.
- [Wordwall Matching Pairs](https://wordwall.zendesk.com/hc/en-gb/articles/360015775077--How-to-create-a-Matching-Pairs-activity)
  documents first/second tile selection and matched-tile removal. Its tiles are hidden;
  Perechi deliberately remains a visible semantic-association game.
- [NYT Connections help](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections)
  specifies16 words, four-word groups, editor-curated categories and one solution.
  Deliberate submission is compatible with a small mistake budget; stronger content
  matters as much as surface simplicity.
- [Contexto](https://contexto.me/en/daily) remains a JavaScript-rendered page in the
  text browser. This fresh request does not claim a newly completed reference round;
  the prior ADR0143 browser observation of Enter submission and ranked rows stands
  as historical comparison only.
- [Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/) explains start-to-target navigation
  through article links. The destination and available link should guide the next
  action; repeating “direct relation” adds little to Lanț's visible options.
- [Little Alchemy2 duplication](https://help.littlealchemy2.com/general/duplicating-items)
  explicitly reduces repeated library trips. Its
  [encyclopedia](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia)
  separates collected-item details from normal mixing, and
  [item types](https://help.littlealchemy2.com/general/item-types) explain removal of
  final/depleted items from the working library. These support keeping our mixing
  feedback accessible and secondary browsing optional; a sticky word bench is this
  arcade's adaptation, not a claim about the reference implementation.

Screenshots are responsive Chromium evidence, not physical-device or human enjoyment
acceptance. `captures.json` includes some descendant DOM rectangles from closed native
details; screenshots and visible controls, rather than raw descendant count, establish
what a player sees. `journeys.json` was taken after response completion with short waits;
transient old animated feedback in a frame is not classified as a persistent defect.

## Implemented exploration correction

The optional goal and collection tools now start closed. The goal summary still names
the selected result and completion, and the library summary exposes an active search
or all-words filter when closed. Opening either is a free local action and keeps the
selected ingredient. The free hint remains beside the workbench with an explicit
“Gratuit” label.

The workbench stays visible while browsing a long collection when it occupies at most
35% of the available visual viewport and that viewport is at least 480px tall. A resize
observer and viewport updates switch it back to normal flow when the keyboard, shorter
screen or longer/larger text would crowd out the words. Word scroll margins account
for the visible workbench. No recipe, mutation, focus or saved-collection protocol was
changed by this layout correction.

| Measured case | Before | After |
|---|---|---|
| Eight starter tiles,390×844 | y578..856 | y553..831 |
| Eight starter tiles,320×844 | y674..952 | y553..831 |
| Bottom-word craft feedback after 8 discoveries | y−405..−345 | y98..158 |

Tile height remains 62px; all eight starters are completely visible without scrolling.
Compare `explore-320-round.png` with `after/explore-320-round.png`, and
`exploration-depth-bottom-combine.png` with `after/exploration-depth-bottom-combine.png`.
The focused exploration suite passes 30 desktop/mobile checks, including both sizes,
free disclosure state, bottom-word feedback,320×360/200% text, old collection migrations,
save ownership, uncertain actions and accessibility audits. Typecheck, build and lint
pass. The initial bundle is 119.22 KiB gzip against the unchanged 120 KiB limit.
Exact file bindings and results are in `verification.json`; root integration validation
and independent implementation review are separate.
