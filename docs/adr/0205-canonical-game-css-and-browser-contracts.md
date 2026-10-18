# ADR-0205: one authored game stylesheet and browser contracts

Status: Implementation decision; native M4 qualification required.
Date: 2026-10-19
Authority: S1 M4, PROGRAM E8/E10 and the requested efficient game migration.

## Context

The M3 source implements every current route with preserved legacy rollback.
Its ten emitted stylesheet files total20,669 canonical level9 gzip bytes. The immutable original
baseline at ae9be5b5a0f891dd5d36d6bb18945e9dcd8102a5 records16,093 bytes;
that is the CSS ceiling, not permission to set a larger measured limit.

## Decision

Keep the canonical kit stylesheet import first. Centralize the fifteen authored
sheets through app.css in their proven precedence order, retaining their source
files, font URLs, unlayered priority and Alchimie exploration-before-common order.
Remove only independently proven unread private aliases, unused legacy selectors
and always-overridden declarations. Preserve component bodies, DOM, state, motion,
accessibility and every original functional/visual assertion.

This trades per-route CSS loading for shared compression and one cached authored
stylesheet. Charge its full startup cost on every route, including Home. Native
measurements decide the result; source grouping alone is not a saving claim.

Set the SDK global/route CSS cap to16,093 and enforce that same ceiling across
ALL actual current CSS files with a separate consumer measurement. Include orphan
stylesheets once; validate regular confined paths and canonical gzip sidecars.
Keep the delivered SDK report unchanged. Aggregate SDK and consumer failures for
both canonical gates and direct preflight. Preserve the frozen original30 raw
files, their unmodified verifier and their existing baseline projection; they do
not acquire a sidecar requirement. JS40,960 and Home target30,720 stay unchanged.

## Plain Preact browser contracts

Complete the existing S1 test requirement with Vitest5.0.3, its browser and
Playwright providers, and the already selected Playwright1.63.0. Generate exact
manifest/lock additions through the owning deps gate; no version re-resolution.
Use plain Preact render and real Chromium role locators, not a testing-library
adapter. The six bounded cases cover remount focus, locked actions, live header
measurement, shared deferred loading and rejected-route recovery.

Keep every original Node contract and Playwright journey. The browser runner
checks the installed pins, native types, exact six actual reporter identities
and zero failures/pending cases; child failures/timeouts fail npm test. Preserve
the complete actual reporter bytes and source/wrapper binding in canonical
stdout. Five additive report-guard controls cannot substitute for browser runs.

## Consequences

Require actual full emitted sizes, original screenshots, axe, CSP, five-run
vitals, native/data parity, exact-SHA unit/full and release image checks. No new
cap increase, vendor edit or weakened assertion admits this implementation.
Required test locks are generated separately; runtime dependency pins stay fixed. Keep the
source/proof packet and failed evidence if the single native candidate does not
meet the ceiling. Independent acceptance precedes local main landing; production
and app-main pushes remain the owner’s.
