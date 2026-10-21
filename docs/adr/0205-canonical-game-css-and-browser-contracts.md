# ADR-0205: one authored game stylesheet and browser contracts

Status: Accepted on exact source1673389147a3ba432742008d55d28edb84d94af2; local landing delegated by E10.
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

## Qualification — 2026-10-19

Exact source16733891 passes unit27/full38/image2 and independent acceptance.
All933browser cases,9byte-exact original PNGs,axe,Home semantics,five-run vitals,
enforced CSP0,freshPG12/301,current V1.13 parity1206 and legacy rollback pass.
The original frozen CSP component import is preserved byte-exact;its comment-only
source emits a newline-only CSS file charged at21gzip bytes. Total actual CSS
is16,043/16,093;HomeJS28,879 and Challenge40,714 pass unchanged ceilings.

A first unit correctly refused the removed import's frozen source pin;the exact
original import was restored without a fixture exception. First fullD931/933
then proved an old-document checkpoint setup race. Fourteen additive initial
intro-readiness assertions fix it at7sites;every original test byte/case remains.
Actual failed evidence is retained. No limit,pin,baseline or assertion was weakened.

Warm unit7.12min/full20.07min are actual observations. Full correctly misses
whole-unit reuse on the warm command shape while reusing independently verified
unchanged native evidence and rerunning freshGUI/API packages. Release and full
image IDs differ;the actual /app payload is byte-identical,with matching source
and tree labels. [Qualification](../reviews/gui-m4/qualification.json) retains
commands,raw hashes,cleanup,image custody and independent acceptance. App-main
push,production and real-account/child activation remain the owner's.

## Erratum — 2026-10-21 (EQ-1, main publication review)

The CSS comparisons above mix compressors. The ceiling16,093 is the original baseline's
default-level (level6) gzip total of its eight sheets (`scripts/gui-baseline.mjs`,
`baselines/cat/capture.json`); the SDK report and the consumer all-actual total measure the
delivered canonical level9 sidecars (`scripts/gui-route-budgets.mjs`). M3's20,669 is also
level9. Re-measured with one compressor (pinned toolchain Node26.10.0 zlib; original bytes
from the frozen legacy archive, actual bytes from the M4 clean-C assets and this branch's build):

| Basis | Original | Actual | Headroom |
|---|---:|---:|---:|
| gzip level9 (the gate's basis) | 16,046 | 16,043 | 3 B |
| gzip level6 (the ceiling's basis) | 16,093 | 16,138 | −45 B |

"16,043/16,093, 50 bytes headroom" is a cross-compressor margin. Like-for-like, actual CSS is
3 B under the original at level9 and 45 B over it at level6. The gate keeps its level9 actual
measurement and the 16,093 ceiling: no limit, baseline or assertion changes, and its verdict
stands. A headroom claim states its compressor. Measurement:
[record](../reviews/gui-publication-followups/README.md).
