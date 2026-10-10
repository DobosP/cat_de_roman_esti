# ADR-0189: Manifest-owned precompressed assets

Date: 2026-10-10
Status: accepted implementation source; managed execution and full qualification pending

## Decision

Emit deterministic gzip level9 and Brotli quality11 text representations of finalized, manifest-owned JavaScript and CSS in the Linux managed Vite build. The post/sequential closeBundle hook runs only after successful written output. Preserve every raw asset and its metadata, HTML, manifest, fonts and frozen original bundle. No application, route, dependency or SDK serving behavior changes.

Require complete .gz/.br pairs in actual inventory and asset synchronization. Validate canonical confined paths, regular files, exact decoded raw bytes, deterministic encoded bytes and unchanged raw membership; reject missing, stale, malformed, orphan, aliased or extra representations. Copy all validated files through the existing managed synchronization operation. The shipped SDK already serves and accounts for physical compressed representations; use that public behavior without a parallel serving or budget policy.

## Context and validation

Actual image27555c5e at source6aa returned identity bodies for all four gzip/Brotli requests to the genuine entry and largest startup JavaScript owner. The latter was352124 raw bytes. Gzip planning numbers therefore did not prove compressed delivery. The frozen negative observation remains in docs/reviews/gui-source6-core16-runtime/native/static-negotiation-before-compression.json.

Closed source d2010b2 contains exactly seven paths. Its initial parent/independent clear was incomplete: later literal readback found a missing function brace in the new Node test. Separately closed c27c6f6 adds only that brace and newline; inverse restores all earlier bytes. Parent and independent review accept the corrected source while preserving the original packet/reviews as incomplete history. Thirty Node cases and four Go families/24 subcases cover production emission, pair/sync validation and consumer-through-SDK responses. All new tests, new production outputs, encoded HTTP bodies and browser effects are NOT RUN at this source checkpoint. Require a fresh managed image and retained exact encoded/decoded observations before claiming compression qualification.

Existing startup and route limits, complete route/AccountBar accounting, fonts, all900 browser identities, original16/78 fixtures, safety/CSP/accessibility and actual Samsung obligations remain unchanged. Physical gzip level9 sidecars can truthfully change the SDK's previous level6 fallback measurements; retain both observations and actual red results. The separate proposed one-sided timing acceptance change is unapplied pending an explicit owner decision; ADR0188's absolute comparisons remain current. No E3, M0/M1, KIT_BUMP, device, production or fastest-possible acceptance follows from this source decision.
