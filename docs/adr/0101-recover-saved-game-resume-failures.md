# ADR-0101: Recover saved-game resume failures without losing newer games

Date: 2026-09-06
Status: accepted

## Decision

All six game screens retain a saved game after a non-404 resume failure and show a
persistent intro notice with an explicit retry. A 404 clears only the ID whose GET failed.
Every terminal GET is adopted so the existing result and score effects run; those effects
also clear only their own ID and keep their existing game-specific score semantics.

The resume attempt snapshots one saved ID and rechecks it before classifying and delivering
an outcome. If another tab, an explicit action, or a newer create changes the pointer, the
old success or failure cannot update the screen or clear the newer ID. The intro reports
that the saved game changed and can load the current pointer. A fresh create cancels the
old subscription before taking ownership of screen loading state, and an unmount suppresses
all late React delivery.

Keep the boundary narrow: the shared helper owns GET outcome classification, pointer safety,
retry, cancellation, and recovery notice state. Each screen continues to own state adoption,
difficulty/category restoration, mutations, feedback, explicit exit policy, and scoring.

## Context

ADR-0100 deliberately preserved two older policy families while extracting the common
lifecycle. Four games dropped terminal GET states and all non-404 failures; two games retained
transient failures and adopted terminal states. A temporary outage could therefore erase a
valid resume pointer, while a late response from one tab could replace UI state or clear a
newer pointer created elsewhere.

## Consequences

Players can retry a temporarily unavailable saved game or deliberately start fresh. Completed
server sessions now recover into the normal result screen and enter local history exactly once.
An expired ID still falls back silently to a playable intro unless another current pointer has
appeared, in which case the changed-game notice protects and exposes it.

Framework-free tests cover no ID, live and terminal adoption, conditional 404 cleanup,
transient retention, stale success/error outcomes, Strict Mode resubscription, and unmount.
Real-BFF Playwright journeys cover transient retry and terminal score recovery for all six
games plus representative cross-tab and route-unmount/create races. No answer endpoint or
solution data enters the application bundle or browser storage.

Server TTL/cap/locks, private-answer boundaries, API payloads, create/action behavior, explicit
exit choices, and score formulas are unchanged.
