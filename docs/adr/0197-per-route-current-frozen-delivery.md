# ADR-0197 — Per-route current/frozen GUI delivery keyed by the build's declared shell

Date: 2026-10-12
Status: Accepted infrastructure on `feat/gui-cat-m2-delivery`; the per-route split stays dormant until a current build declares `data-ui="preact"`; combined full NOT RUN.

## Context

S1 M2 (`.agent/S1.md`) requires a Go-side `ported` route set served by the new shell, every
other route served by the frozen legacy bundle, `CAT_UI=legacy` forcing legacy everywhere, and a
Go test asserting the exact set and the `data-ui` served per route. PROGRAM E6 allows the M2
delivery to be implemented before the device checkpoint; E3/E6 fix the pilot set at Home,
Intrusul and Conexiuni plus the necessary shell. At the base `cc41929` (M1-close lineage) the
server admits one current bundle, the generated legacy shell carries `data-ui="legacy"`, and the
current React `index.html` declares no `data-ui`. The owner-reviewed parked packet proposed a
split constructor that production never called and no activation signal; it is not adopted.

## Decision

1. **Activation is the build's own declaration.** `newManagedNonceShell` records the `<html
   data-ui>` attribute of the current bundle's `index.html`. `""` and `react` keep the M1
   single-bundle delivery byte for byte; `preact` activates the split; any other value, including
   `legacy` on a current build, refuses admission (the existing 503 `Managed UI unavailable`, API
   unaffected). The attribute travels with the build bytes (committed `frontend/index.html` →
   Vite → `dist/index.html` → managed assets sync → `go:embed`), so it has the same provenance as
   every other served shell byte. It is not an environment mode (`CAT_UI` stays `current|legacy`),
   not a Go constant, and never a request value.
2. **The ported set is Go-side and exact.** `managedPortedRoutes` is `{"/", "/intrusul",
   "/conexiuni"}`, matched on the exact request path. Queries, cookies and headers never select a
   bundle; `/intrusul/` is not a ported path and is served by legacy.
3. **Split delivery.** A Preact current bundle also admits the frozen legacy bundle (its absence
   refuses the current build). Ported paths get the current nonce shell; every other path,
   unknown deep link or client-side fallback gets the frozen legacy shell with its existing
   renderer, nonce, CSP stage, headers and `no-store` unchanged. Public assets are mapped to one
   owner at startup from both trees: a file present in both with identical bytes is served once
   from the current bundle; different bytes behind one URL refuse the whole split. Documents and
   dot-prefixed private paths are never assets. The `managedWebsite` order (CSP report, API,
   private paths, 503, `/index.html`, methods, asset, extension 404, document) is unchanged, so
   HEAD, cache and CSP checks keep their strictness per bundle.
4. **`CAT_UI=legacy` wins.** It admits only the frozen tree and never reads the current one, so a
   Preact declaration cannot change whole-app rollback.

Rejected keys: the build identity descriptor (`.gui-build.json` is the SDK's four fields, written
by `cat-gui-build`, not by the frontend build), the Vite manifest (fixed schema, no free field),
and a new `CAT_UI` value (E3/E6 forbid request/environment selection of the active UI).

## Known gap (closes at M3)

The frozen bundle navigates with React Router `<Link>` and cannot be edited: a click from legacy
Home into Intrusul or Conexiuni stays inside legacy React, and the legacy wildcard `Navigate
to="/"` lands an unknown deep link on legacy Home client-side rather than the Preact Home. Deep
links into ported routes are correct. The gap ends when the legacy route set is empty (M3) and
the frozen bundle is deleted at the owner's milestone (PROGRAM §8.2). It refines §8.2's whole-app
fallback; frozen bytes and deep-link assertions are not weakened to hide it.

## What the activation commit flips

The later `perf(cat): preact runtime + pilot shell` commit sets `<html lang="ro"
data-ui="preact">` in `frontend/index.html` in the same commit as the Preact runtime; the managed
build emits it and no Go change is needed. Its browser journeys then assert `data-ui="preact"`
on `/`, `/intrusul` and `/conexiuni` and `data-ui="legacy"` elsewhere.

## Verification

Go tests (`managed_delivery_test.go`) assert the exact ported set and `data-ui` per declared app
route for undeclared/`react`/`preact` current builds and `CAT_UI=legacy`, request-selector
immunity, split asset ownership/HEAD/immutable cache/405/404/API/302 contracts, enforced-stage
fresh nonces across both shells, conflicting-byte refusal, identical-byte dedupe, missing-legacy
and unknown-identity refusal, and concurrent split serving under `-race`. Commands and results:
`docs/STATUS.md`. No Preact runtime, 40,960-byte acceptance, device or combined-full claim.
