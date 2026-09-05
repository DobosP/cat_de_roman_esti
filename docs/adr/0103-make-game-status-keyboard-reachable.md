# ADR-0103: Make scrolling game status reachable by keyboard

Date: 2026-09-06
Status: accepted

## Decision

Keep the existing compact scrolling mobile status and Lanț breadcrumb layouts, and make
their containers keyboard-focusable groups with Romanian accessible names: “Starea
jocului” and “Traseul parcurs”. Keyboard users can reach information that extends beyond
the visible part of the row without relying on touch or a pointer.

Add rendered WCAG A/AA audits of intro, live board and result for every game on desktop
and mobile Chromium emulation. Complete desktop test rounds using Tab and Space/Enter,
including Perechi's focus movement to the next unsolved tile and then the result action.
Protect visible earned counters after reload and recovery from a failed game action.

## Evidence

The initial mobile audit reported serious `scrollable-region-focusable` violations on
the HUD and the completed Lanț breadcrumb. The existing source-level keyboard/focus
contracts did not reveal that scrolling information was inaccessible to keyboard users.
Focusable named containers eliminate those observed violations without changing the
game rules, hidden answers or mobile layout.

Opacity animations initially produced transient contrast failures in the audit. Wait for
enabled primary controls and their ancestors to finish fading and for finite browser
animations/fonts to settle before measuring colors. Disabled controls retain their
intentional opacity. No accessibility rule or page region is excluded from the audit.

## Consequences

The two information groups are additional tab stops even when their contents fit. This
keeps a stable keyboard path across viewport changes and avoids a resize-dependent focus
target. Existing focus-visible styling remains in force.

Automated audits and desktop keyboard play do not establish screen-reader usability,
real-device acceptance or player enjoyment. Those remain in the anonymous-beta checklist.
