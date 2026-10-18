# ADR-0202: Remaining Preact screens and Alchimie mode boundaries

Date: 2026-10-13
Status: M3 qualified at9c44d01f; Signals choice superseded by ADR-0204
Authority: PROGRAM E10; Cat ADR-0199; S1 M3 dispatch

## Context

M2 and the core-v1.10 prerequisites are accepted on local main. Alchimie in both
modes, Cald sau Rece, Lanț and Clasament still use the frozen bundle. Their
pre-deletion source is 06fd0a38182be7ec062cc3155e45ce18915423c5 (`076aaaa8^`).

## Decision

Restore and port the remaining source while preserving the existing APIs,
authoritative state, recovery ownership, saved progress, score/privacy behavior,
native drag-and-drop, focus and visual assertions. Existing shared Preact
components and the kit motion APIs remain the implementation boundary.

Alchimie uses component-local batched signals from the existing versions.lock.json
pin, @preact/signals 2.11.3. Add that exact dependency through the frontend manifest;
only the owning deps gate generates locks. No dependency re-resolution is needed.

Keep App's literal route switch, lazyScreen loader and pathname frame keys. Pass
its captured URL to a small Alchimie selector; load independent challenge and
exploration leaves lazily. Preserve query precedence and legacy saved-round
selection. Both original stylesheets initially keep their observed order:
exploration styles before common Alchimie styles.

Each mode's budget includes entry, mandatory AccountBar, selector and selected
leaf with real static imports. Both possible default-mode branches must be
covered. Preserve the 40,960-byte cap and 30,720-byte target; dynamically mounted
leaves are never omitted from accounting. No eager union substitutes for mode
measurement. The clean default uses exploration; saved default challenges use
the same independently charged challenge leaf as the explicit challenge URL.

The emitted preflight exceeded the unchanged40960-byte cap: Challenge54739,
Cald48949, Lanț48809 and Conexiuni42822. Home now has a genuine lazyScreen
boundary, and `/` explicitly charges entry, AccountBar, Home and every static
dependency in both route and frontend startup evaluators. Deep links exclude
Home only when its code is not fetched; browser assertions cover that boundary
and its later client-side loading on exit. No game or resumed-state leaf is
removed from its route's accounting.

The Alchimie selector tests only whether the exploration storage key is absent;
null alone means the unchanged reader's `empty` result. Empty, malformed,
oversized and valid stored values all suppress the saved-challenge fallback,
and storage failures still return false. Comparison tests use the unchanged
exploration reader and its literal key. Full exploration validation/save bytes
remain intact in the exploration leaf.

The duplicate5122-gzip-byte Motion engine is a producer packaging issue,
tracked as REQ-11. The approved corrective core-v1.11 externalization keeps the
already exact runtime dependency and animation behavior; it requires its own
packed-consumer/release/adoption qualification. Cat adds no motion shim. These
two consumer changes and the producer correction need actual emitted results;
no savings or M3 qualification is inferred from the source plan.

All managed current documents use the current shell. A single trailing slash
on a known app path is replaced by its canonical path with query preserved;
unknown document paths replace-navigate Home, as the original wildcard did.
There is no broad slash normalization and no API/account routing expansion.
The frozen tree remains admitted for rollback and old asset URLs; explicit
CAT_UI=legacy selects it at server construction.

After every screen is ported, all nine existing observed URLs use the current
bundle and omit the frozen CSP descriptor and both frozen observation fields.
CAT_UI=legacy and all frozen archive/receipt/baseline bytes remain intact.

The frame's captured URL also supplies daily-intent reads to GameIntro and
saved-game resume. Pathname frame keys remain stable when daily intent is
consumed. Exit and unmount invalidate action ownership before late replies;
saved round pointers retain their original settlement and privacy rules.
The outer retained frame is inert. Returning before its exit completes forces
a fresh saved-session read; failed reads keep the saved pointer and expose the
normal resume retry. A locally owned state without persisted storage keeps its
id and existing action reconciliation instead of being replaced by an empty
round. Exploration also re-reads a known local collection. Score persistence
may finish after departure; stale presentation and sounds cannot.

Challenge signal setters preserve render snapshots and batch authoritative
updates. Motion uses kit Presence/animateHeight and actual-element motion/mini
animations: Alchimie320/18, Cald guess380/28 and comparison320/24, Lanț breadcrumb
420/26. The Lanț hint uses the kit gentle height spring; feedback and shake remain
visible. Inactive layout props are removed because the original domAnimation
graph did not supply layout animation. Authored CSS regains animation tracks
after completion, preserving depleted/disabled opacity. Native drag/drop stays.

Home disables only its card backdrop filter when a finite positive
`navigator.deviceMemory` report is at most 2 GiB (0.25, 0.5, 1 and 2 GiB reports).
Reports above 2 GiB and unavailable/invalid reports retain the original 14px
blur. This conservative policy is covered with synthetic reports and computed
CSS assertions; it makes no device-performance claim and requires no devices.

## Validation and boundaries

Source and manifest preparation is not qualification. The parent runs dependency
generation, cheap checks and exact-SHA unit/full at milestone cadence. Go route
changes require independent native re-audit; existing pins fail closed until then.
Preserve every behavioral assertion and exact PNG. Browser case additions require
the committed discovery generator, never a hand-edited inventory. Independent
review precedes local M3 landing; app-main pushes and production remain owner-only.

The owning dependency generation passed4 (result SHA-256
27dd259e59815ba73fe5c259d585002aa9e835d9802777eebf9b231a294453a4).
Progress and further executed evidence belong to the [S1 plan](../execplans/s1-cat.md)
and [status](../STATUS.md). Corrected pinned source checks10 pass, including69
focused frontend cases, lint/types/style audit and native routing race/vet/docs.
The independent source/native review is clear; the reviewed pin is applied.
Earlier shell-context fixture/setup refusals do not establish unit/full results.
No M3 unit/full qualification exists yet.

### Bounded help ownership follow-up

Each game imports its own answer-free help record statically and passes it to
the shared renderer. GameShell and GameOptions no longer import the six-game
map. The compatibility GAME_HELP aggregate remains available to its existing
consumers. All18 texts, key order and initial disclosure DOM remain unchanged;
no help is delayed until opening or removed from a resumed board. Source tests
bind the original text digest and walk static imports to reject unrelated help
in a route. This is a GUI module-boundary change only: immutable framework-free
logic, content/API/storage/score bytes and budgets are untouched. Actual emitted
savings and qualification remain pending the owning checks.

### Shared-control packaging refinement (2026-10-13)

The current Vite groups keep strict entry signatures. Shared game controls and
their real static dependencies share one chunk; every importer pays for the whole
closure. Higher-priority CSP and immutable share modules keep Home and Ranking
separate. This trades extra Explore bytes (37864 total) for smaller Cald/Lanț
initial payloads (40592/40478); all remain below40960. Challenge45806 stays red.
[Actual measurements and independent review](../reviews/gui-m3/help-controls-checks.json)
record this partial improvement without M3 qualification or cap changes.

## Qualification — 2026-10-19

Exact source9c44d01f passes unit27/full37, original9PNG/Axe/vitals/CSP and
independent M3 acceptance; locally landed under ADR-0199. The
[qualification record](../reviews/gui-m3/qualification.json) binds actual evidence.
