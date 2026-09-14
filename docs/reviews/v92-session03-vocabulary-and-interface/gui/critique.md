# Six-game interface critique, session 03

Valid until: these interface or content bytes change — then treat this as historical evidence.

Reviewed 2026-09-14 against baseline `0b51e03`. Fresh isolated Chromium contexts used
390×844 and 320×844 views, with no existing user profile or progress. Twelve real
seed-38 rounds reached wins: all six scored games at both sizes, including keyboard
completion at320. Additional responsive checks covered 200% text, short viewports,
uncertain actions, resume, hints and collection completion. This is browser evidence,
not a human enjoyment study or physical-device acceptance.

## Reproduced findings and implemented corrections

1. **Conexiuni status overlap.** At320, the selection badge occupied x185–203 and the
   remaining-mistakes section began at x193: a10px overlap. At390 with200% text the
   same overlap recurred. The hidden icon left a four-column grid containing three
   visible children; its flexible column collapsed to zero. Desktop also stretched
   the small selection badge to409px. Explicit desktop columns now assign flexible
   space to the instruction, and mobile gives mistakes a separate row. Selection,
   instruction and remaining mistakes remain separate through all five selection
   counts at320/390 and100%/200% text. The four-column word board and deliberate
   submission remain intact. `coach-before.json`, `coach-after.json` and screenshots
   provide geometry and rendered evidence. Baseline detail measurements use the
   prior8150 preview of the same baseline; initial full-game screenshots use8160.
2. **Hidden-search recovery in Alchimie.** Search for `zzzz`, then close collection
   tools. The library shows no words and no visible reset; clearing it requires
   reopening tools and editing the input. A visible44px `Șterge căutarea` now clears
   an active search in one action, including when tools are closed. It retains the
   selected ingredient and collection filter, emits no request, and leaves the save
   byte-exact. Keyboard activation returns focus to the collection with its heading
   visible; pointer use retains browsing position. No reset control appears while
   the initial library is unfiltered.
3. **Completed collections appeared empty.** Restoring the complete221-word baseline
   displayed zero word tiles, an inaccessible-in-the-closed-menu checkbox instruction,
   and contradictory prompts to continue discovering and combine words. An API-confirmed
   completed collection now shows every earned word immediately, labels them as collected,
   and guides the player to browsing and the recipe journal. Search continues to work;
   depleted/final words remain inactive. Completion checks use current public API state,
   so later world additions cannot be mistaken for a completed collection. The new test
   restores earned historical progress and finishes any later additions through public
   hints before testing the completed view.
4. **Small typing and help controls.** Cald sau Rece’s `Ghicește` and Lanț’s `Salt`,
   `Înapoi` and `Indiciu` measured34px high at both phone widths. Scoped CSS raises them
   to at least44px. The other four games already met44px for visible starting controls.
   All-six measurement and regression checks now enforce the intended target size.
   Existing Enter submission, reveal confirmation, hint focus and delayed-action focus
   ownership pass unchanged.

## Per-game decisions

| Game | Fresh observed loop | Decision |
|---|---|---|
| Alchimie | Two word taps craft. Scored seed38 won at both sizes. Empty search and complete saved collection reproduced the issues above. | Keep direct mixing and bounded sticky feedback; add local reset and truthful completion browsing. No recipes or save rules change in this UI patch. |
| Intrusul | One answer tap; all four choices and next action are readable at320/390, with44px controls. Both seeded rounds won. | Retain the direct loop. More precise, defensible groups remain a content priority. No additional confirmation or decorative redesign. |
| Perechi | Two face-up choices check a pair; matches leave the board. Eight long labels remain readable at320/390. Keyboard focus follows solved tiles. | Retain automatic checks and one-tap cancellation. No new persistent GUI defect reproduced in these rounds. |
| Conexiuni | Four choices plus deliberate verification; selection can already be cleared in one action. | Fix the status grid. Retain limited-mistake submission and existing one-away recovery; no automatic fourth-tile submission. |
| Cald sau Rece | Text+Enter returns to the input; latest feedback and ranked history remain clear. | Raise the typing button to44px. Keep input-first layout; short320px/200%-text and explicit reveal cancellation pass. Target neighborhoods remain editorial work. |
| Lanț | Start/target remain visible; local choices or typed Enter make a hop. Free exact hints offer usable choices. | Raise typing/undo/hint controls to44px. Retain neutral relation captions and current useful-hint staging. Weak generic graph bridges remain content review concerns. |

## Primary reference comparisons

The following current primary pages were reopened on2026-09-14. They inform the critique
as analogous interfaces, not a popularity ranking or proof of equal human usability.

- [NYT Connections help](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections)
  explains sixteen words, groups of four, deliberate final submission and editor-curated
  categories. Our instruction, selection and mistake budget should each be readable.
- [Little Alchemy2 item types](https://help.littlealchemy2.com/general/item-types) and
  [encyclopedia](https://help.littlealchemy2.com/encyclopedia/using-the-encyclopedia)
  distinguish useful mixing items from final/depleted discoveries and provide separate
  access to the latter. That supports keeping our earned collection accessible after
  mixing is finished; automatic completion browsing is this arcade’s adaptation.
- [Wordwall Quiz](https://wordwall.zendesk.com/hc/en-gb/articles/360015811938--How-to-create-a-Quiz-activity)
  documents direct selection and immediate feedback. Intrusul already has that efficient
  loop, so content clarity has higher value than extra controls.
- [Wordwall Matching Pairs](https://wordwall.zendesk.com/hc/en-gb/articles/360015775077--How-to-create-a-Matching-Pairs-activity)
  documents two-tile selection and matched-tile removal. Its memory-game tiles are hidden;
  Perechi intentionally keeps semantic associations face-up.
- [Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/) makes link choices and a destination
  the central navigation task. Lanț already follows that loop; touch controls must remain
  usable alongside typed alternatives.
- [Contexto](https://contexto.me/en/daily) returned a JavaScript-only document to the text
  browser. No fresh external Contexto round is claimed. The local typing/rank evaluation
  rests on our actual browser journeys and interaction regressions.

## Verification scope

- Baseline:12 scored wins, six games × two widths; `baseline.json` and per-game captures.
- New fixes plus typing/hop interaction checks:42 pass in desktop/mobile projects.
- Existing exploration and Conexiuni uncertainty/one-away suites:68 pass.
- Native frontend:212 pass. Typecheck, build and lint pass. Initial gzip119.22/120KiB.
- No API, score, recipe, session, save migration or answer-exposure changes in this patch.
  The complete view only displays items already present in the earned public inventory.
- Exact file and evidence digests are recorded in `verification.json`. Root integration
  testing, independent implementation review and final expanded-world checks are separate.
