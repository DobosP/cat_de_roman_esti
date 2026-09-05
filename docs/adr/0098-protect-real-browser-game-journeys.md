# ADR-0098: Protect real browser game journeys before shared refactors

Date: 2026-09-06
Status: accepted

## Decision

Run deterministic browser journeys against the built SPA and an isolated, anonymous,
offline Django BFF for all six games, in desktop Chromium and mobile Chromium emulation.
Gate complete play, server-authored results, replay, progressed-session reload,
expired-session recovery, and failed-start retry in CI alongside the existing gates.

Keep representative seed-38 public starting states in a reviewed snapshot. Derive
winning actions in an independent Python test process from the same seed; never add a
solution endpoint, ship answers in the frontend bundle, or store solutions in the browser.
Future selection/content changes must explain any snapshot update. A refactor cannot
silently redefine its own expected starting state.

Use one browser worker and a private BFF process to avoid shared in-memory session state
and to bound test load. Retain failure traces/screenshots only as test artifacts.

## Context

The existing Python contracts and framework-free frontend checks provide detailed rule
coverage but did not exercise the rendered SPA through full real-backend rounds. Shared
session and resume extraction needs a behavioral baseline that can reveal integration
regressions across all six games without depending on source-code patterns.

## Consequences

The frontend CI job also installs Python web dependencies and Chromium. Browser tooling
is development-only. Tests retain the real transport, server authority, seeded selection,
session limits, and private-answer boundary. Injected failures cover recovery independently
of server uptime; successful starts, actions, reloads and results use the real backend.

Mobile emulation establishes repeatable layout/interaction coverage, not real-device
acceptance or human enjoyment. Accessibility, keyboard/focus behavior, transient-resume
failures and gameplay-quality hypotheses need separate measured follow-up waves.
