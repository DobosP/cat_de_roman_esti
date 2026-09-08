# ADR-0139: Keep mobile status and notices visible

- Status: accepted
- Date: 2026-09-08

## Context

At V90, the shared mobile header gave the HUD a horizontal strip with a hidden
scrollbar. Its parent clipped later counters; at 320px the game title was visually
hidden. The fixed top toast also covered Exit and status during resume in Alchimie,
Conexiuni, Cald sau Rece and Lanț. Intrusul and Perechi already used inline resume
feedback. The V91 before/after evidence records these distinct paths.

## Decision

Keep Exit and the full game title on the first mobile header row, with all status
badges wrapping underneath. Long labels wrap within their available width. The HUD
retains its named group semantics; a noninteractive group no longer needs a tab stop
for horizontal scrolling.

Measure the actual header height with a scoped ResizeObserver so existing sticky
input/coach surfaces follow changes in badge count, fonts and text size. Disconnect
and remove the measurement on unmount. In mobile viewports up to 600px high, these
surfaces use normal document flow so a short viewport retains room for focused inputs.

Place notifications in their own row above the screen viewport. Use an app-scoped
wrapper around the existing @roedu/ui ToastStack; its exact 0.3.0 API has no placement
prop. Preserve package visuals, polite announcements, keyboard dismissal, the existing
3.6-second lifetime and reduced-motion behavior. Limit the notification row to 30dvh
with vertical scrolling for stacked messages, and retain safe-area padding. No package
or upstream source changes are needed.

## Consequences and verification

The taller mobile header and a visible notification reduce the available screen height;
content remains vertically scrollable. Notices no longer cover a bottom action or the
header. The independent screen viewport keeps both live and finished game controls
reachable without hiding counters elsewhere.

Focused browser coverage checks all six intros, live/resumed/scrolled/result states,
copy-failure notices and keyboard dismissal at 320px, 390px and desktop widths. A
presentation-only stress case covers long Romanian labels at 200% text size and a
480px-high viewport. Geometry receipts and settled screenshots are retained in the
[V91 review](../reviews/v91-recovery-and-mobile-clarity/README.md). This is browser
emulation, not physical-device or human-player acceptance; final gate results belong
in [STATUS](../STATUS.md).
