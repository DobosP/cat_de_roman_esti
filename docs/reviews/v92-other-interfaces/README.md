# V92 — The other five game interfaces

Valid until: a later change to this candidate's source or serving artifacts — then treat as history.

The owner explicitly expanded V92 after Alchimie to review the other game interfaces
against comparable popular games. Baseline: `f57162d` (direct Alchimie candidate).
Decision/research: [ADR-0143](../../adr/0143-simplify-the-five-other-games.md).
Current integration state: [STATUS](../../STATUS.md).

## Reference-informed changes

| Game | Reference | Resulting interface |
|---|---|---|
| Intrusul | [Wordwall Quiz](https://wordwall.zendesk.com/hc/en-gb/articles/360015811938--How-to-create-a-Quiz-activity), [Sporcle formats](https://support.sporcle.com/hc/en-us/articles/33897795822989-Understanding-different-quiz-types-and-formats) | Keep one-tap answers; compact instruction and balanced board; unavailable hint is text, earned hint persists. |
| Perechi | [Wordwall Matching Pairs](https://wordwall.zendesk.com/hc/en-gb/articles/360015775077--How-to-create-a-Matching-Pairs-activity) | Keep two-tap checks and face-up semantic words; retap cancels; remove redundant clear; solved pairs follow remaining words. |
| Conexiuni | [NYT Connections help](https://thenewyorktimeshelpcenter.helpjuice.com/360011158491-New-York-Times-Games/28525912587924-Connections) | Compact 4×4 phone board; shuffle, clear and deliberate check below it. Limited mistakes justify explicit verification. |
| Cald sau Rece | [Contexto daily](https://contexto.me/en/daily) | Field and ranked words first; inline rank meaning; optional ordering/settings/reveal; repeat-guess focus; explicit reachable reveal confirmation. |
| Lanț | [Wikispeedia](https://dlab.epfl.ch/wikispeedia/play/) | Compact current→target route and visible next links; exact hint choices move in one activation; uncertain spelling stays editable. |

These are interface adaptations, not claims that every game has identical rules.
Wordwall's matching example is a memory game; Perechi retains its visible semantic
words. Contexto was exercised in a browser. NYT's game rendered only partially and
The Wiki Game stopped at consent; the documented references above supply the claimed
rules/navigation evidence. No popularity ranking or completed reference round is claimed.

All five games use closed native options for optional rules and tools. Configurable
setup extras are collapsed. Safe confirmation, available paid-hint costs, known result
feedback, response ownership and saved-game recovery remain explicit.

## Before/after phone geometry

Real BFF seed 38, 390×844 Chromium responsive viewport, settled fonts/animations,
scrolled to the top before measurement. Touch and keyboard input are tested separately.

| Initial control | Before top/bottom | After top/bottom |
|---|---:|---:|
| Intrusul board | 254 / 420px | 148.39 / 314.39px |
| Perechi board | 269 / 584px | 182 / 497px |
| Conexiuni board | 295 / 815px | 135 / 425px |
| Cald sau Rece input | 276 / 322px | 126 / 172px |
| Lanț input | 712.67 / 758.67px | 456.81 / 502.81px |

The full Conexiuni board now fits in four rows. Intrusul and Perechi preserve their
already efficient one/two-tap main interactions. An exact Lanț hint drops the separate
fill-then-submit step, while corrections retain deliberate submission.

Evidence: [geometry](geometry.json),
[Intrusul before](before-intrusul.png)/[after](after-intrusul.png),
[Perechi before](before-perechi.png)/[after](after-perechi.png),
[Conexiuni before](before-conexiuni.png)/[after](after-conexiuni.png),
[Cald sau Rece before](before-contexto.png)/[after](after-contexto.png),
[Lanț before](before-lant.png)/[after](after-lant.png).

## Verification and limitations

The new `*-simpler-ui.spec.mjs` suites use actual deterministic BFF sessions and verify
touch/keyboard input, visible boards, explicit check/reveal/hint actions, free local
shuffle/clear, paid-cue persistence, narrow/zoomed layouts and focus ownership.
Existing six-game recovery, lifecycle and accessibility suites remain part of the gate.
Exact final results and fingerprints are in [verification](verification.json).

Independent review reproduced two focus problems: Lanț's old state-wide autofocus
could steal navigation, and removing consumed quick-game hint buttons lost focus.
Owned action focus now preserves deliberately chosen controls and restores lost focus
to usable words. Passive saved hints do not initiate a move or acquire that focus.
Cald sau Rece's reveal now focuses safe cancel; its round-abandoning option has the
explicit label “Începe alt joc”.

Development failures are retained as such: four case-sensitive expectations needed
server-authored labels; two older replay tests assumed a compact result always
overflowed a 560px desktop, so their scrolled-recovery setup now uses 320px height.
Neither correction changes scores or serving data. Final results distinguish those
intermediate failures from completed checks.

[Content delta](content-delta.json) is zero across concepts, links, forms, puzzles,
curated rounds, approvals, declared eligibility and frozen derived boards. API wrappers,
backend/content and Alchimie source have no diff from baseline. Prior full Python and
content-validator evidence remains the unchanged backend's baseline; new browser checks
exercise the actual BFF. No push, production deployment, human playtest or physical-device
acceptance is claimed. Recurring iteration remains stopped.
