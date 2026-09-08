Valid until: V91 kickoff rebaselines landed V90 source and behavior — then treat as history.

# Prospective V91 scout

Read-only inspection, 2026-09-08. No new failure reproduction, test, server, external
research or implementation. [Exact read hashes and acceptance evidence](prospective-v91-scout.json)
bind these leads; V90 must land green before selecting/rebaselining V91.

## 1. Complete ownership recovery for Intrusul and Perechi

Both screens **already perform one GET after failed tile/hint actions**, sharing a
synchronous mutation lock. The source gaps are narrower: successful POST/GET adoption
checks neither an action ticket, response `game_id`, nor the current saved pointer.
A failed read leaves “încearcă din nou” feedback and releases controls; there is no
persistent GET-only retry or distinct confirmed-404 path. The existing lifecycle browser
case covers an uncommitted failed action followed by reload, not these ownership cases.

Reproduce whether a changed tab pointer allows an old mutation/terminal reply to take
over the displayed round, and whether failed verification encourages further actions
against stale state. Perechi's deferred focus work also needs superseded-reply checks.
These are **untested consequences**, not demonstrated regressions. Score deduplication and
conditional pointer deletion already exist; do not claim duplicate scores. Both servers
cap hints at one and GET retains the paid clue, so do not claim a second hint charge or
assume another backend earned-state field is needed. Unmount callbacks alone do not prove
post-unmount scoring.

Acceptance: real committed/uncommitted action/clue/win/loss baselines; held replies,
foreign/null saved pointers, wrong identities, unmount, owned/stale404; persistent locked
controls through repeated failed reads; one GET without POST replay; once-only results,
Perechi focus and existing replay/starter/daily behavior. Preserve session/request bounds.

## 2. Make the shared mobile status and resume notice easier to use

Existing [mobile clue evidence](../v89-feedback-and-conexiuni-recovery/conex-action/behavior-recovered-clue-mobile.png)
visibly places “Joc reluat” over Exit/title/HUD. The CSS explains the overlap: a top-fixed
toast at `z-index:1000` crosses the sticky header at12 for the App's 3.6-second lifetime.
The mobile HUD is focusable and horizontally scrollable, but its parent clips overflow
and its scrollbar is hidden. V90 settled images still place later counters offscreen.

A small all-six-game opportunity is clearer essential counters plus a resume confirmation
that leaves the header usable. Compare a compact second status row or explicit overflow
cue and an inline resume notice after fresh measurement. Validate all six intro/live/
resume/recovery/result states at320/390/640px, long Romanian labels and text zoom, both
during and after the notice. Preserve keyboard/status semantics, safe-area offsets and
primary-action access; do not infer inaccessible content merely from intentional scrolling.

## 3. Review existing discovery quality before another noun batch

The observed easy Sport Alchimie board is **`al_sport_083`, approved, `usor`, depth2**.
Its target is **Liga Campionilor la handbal**. Its six exact seeds are Washington Bullets,
Medalie, Recordul la 100 m liber din 2022, Cristina Neagu, Bazin olimpic and Tricolorii.
[The recovery screenshot](alchimie-action/focused-results--alchimie-action-recovery-l-a3d5e-sume-without-another-charge-desktop--recovered-hint-2.png)
shows Washington Bullets + Cristina Neagu → Club sportiv. The exact seeded payload marks
Medalie, the swimming record and Bazin olimpic depleted at the start.

This warrants an **A1/E1 review question**: do the specialist/detailed seed labels meet
broad, cross-generational Romanian recognition on easy, and does every seed look useful?
Review E2/E3 opening and target legibility too. No web recognition judgment, failure or
demotion follows from this scout. Rebuild its full dossier and independently judge all
six seeds rather than changing status from a screenshot.

The same stock-quality review can resolve the four approved C3 proposals: Lacul Roșu
(`ct_geografie_030`,1 incoming), Peștera Scărișoara (`ct_geografie_031`,2), Abdicarea Regelui
Mihai (`ct_istorie_309`,4), B.U.G. Mafia (`ct_muzica_070`,4). They remain eligible. Prioritize
the geography pair's thin approaches; seek real discovery evidence and propose keep/revise/
demote under the rubric, without automatic demotion or quota-filling edges.

Keep the17 remaining household stress surfaces in the JSON backlog; they are not a
frequency sample. If later content authoring is selected, a coherent small investigation
is floor surfaces and cleaning outcomes: pardoseală/parchet/gresie/murdărie/curățenie/gunoi.
Sense/ownership and factual review come first; none is an approved alias, edge or target.
Ambiguous `curent`, `păr`, generic `sac` and activity nouns need separate decisions.

**Curated approval and mined fallback differ.** New graph nouns add no curated target
record by themselves, but Contexto falls back to `_pick_target` when curated selection
returns none. Its normal pool contains graph IDs and has reachability/warm-band fallbacks.
Thus “not approved as curated targets” does not mean “can never be mined targets.” Measure
actual selector provenance before making that stronger claim or promising a target count.
