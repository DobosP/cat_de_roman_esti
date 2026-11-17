# ADR-0233 — Redesign v2 interface

- Date: 2026-11-16
- Status: accepted by Paul and qualified on local product `8b6679af` ([acceptance](../reviews/redesign-v2-m1/acceptance.json))
- Supersedes the frozen DOM, copy and visual clauses of
  [ADR-0205](0205-canonical-game-css-and-browser-contracts.md) (its byte ceilings stay), the
  protected introduction of [ADR-0222](0222-simplified-alchimie-collection-interface.md) and
  [ADR-0224](0224-target-based-alchimie.md), the frozen help copy of
  [ADR-0202](0202-m3-remaining-preact-screens.md), and the Home circuit, diploma and history
  display of [ADR-0057](0057-actionable-local-daily-circuit.md) and
  [ADR-0064](0064-device-local-daily-streak-and-derived-diploma.md) (their data stays).
- Rules: [ADR-0232](0232-steps-and-hint-ladder.md).

## Decision

Paul approved the design in the review canvas "Varianta 2, cu imagini" (2026-11-16):

- The app is "Cât de român ești?" with six standalone mini games. No combined score, no
  "next game", no in-game game picker, no points.
- Start screen: six illustrated cards, one tap each, a "Gata azi" badge only. Point-based
  ranking navigation is hidden; its route and API stay.
- Light and dark themes follow the device setting, with a switch on the start screen.
- One frame for every game: game-coloured top bar (back, name, help), attempts and a
  daily/free/replay pill, one coach line, the hint button bottom-left. A selected word is an
  inverse tile with `aria-pressed`.
- One tap: today's daily first, then free rounds; the entry decision is per browser profile.
- Help is a modal sheet; the result is a panel after the board with steps, Perfect and room for
  the board comparison of ADR-0234.

Owner answers, 2026-11-16 (quoted): UI locks "Yes, re-lock"; fonts "Keep current fonts".
"Re-lock" replaces the frozen screenshots, source hashes and axe expectations with new ones;
the previous capture and PNG hashes are kept as history. It does not raise a byte cap: CSS
16,093 B and route JS 40,960 B stay; exceeding them needs a separate owner ruling.

Amendment 2026-11-17: denied browser storage or failed writes retain daily completion, free options and saved-round pointers for the current page lifetime; a reload uses only successfully persisted values and otherwise starts as a first visit.
