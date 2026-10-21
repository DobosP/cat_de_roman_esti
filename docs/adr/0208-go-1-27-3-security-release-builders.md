# ADR-0208: Build releases with the Go 1.27.3 security toolchain

Date: 2026-10-21
Status: accepted (security fix under Paul's 2026-10-21 Cat main authorization, [ADR-0206](0206-owner-authorized-main-publication.md)); completed by [ADR-0209](0209-kit-bump-core-v1-13.md) (KIT_BUMP core-v1.13)
Amends: [ADR-0184](0184-native-spa-toolchain-and-managed-output.md) Go version, for release builders only.

## Decision

Every Cat build that produces a shipped or CI-tested Go binary moves from go1.27.1 to go1.27.3:

- the canonical `Dockerfile` builder uses `golang:1.27.3-trixie@sha256:604106102d33…` through the
  new app-scope lock entry `cat-golang-trixie`;
- the standalone `go-backend/Dockerfile` uses `golang:1.27.3-bookworm` (linux/amd64 manifest
  `sha256:fea12ba16096…`, app entry `cat-golang-bookworm`);
- CI `setup-go` and the `scripts/qualify_go_toolchain.sh` precheck require 1.27.3.

The kit core-v1.11 pins stay byte-identical. These are the core `go` runtime (1.27.1), the core
`golang` image, `golang.org/x/net` v0.59.0 and the gate `toolchain_image`. Cat's two module `go`
lines (`go-backend`, `shared-go/authcore`) also stay at 1.27.1. The vendored kit `go.mod` is untouched.

## Context / why

govulncheck v1.8.0 on main `fb829aaa` reported 14 reachable go1.27.1 standard-library
vulnerabilities in net/http, its bundled HTTP/2, crypto/tls, crypto/x509, net/textproto, os and
html/template. All 14 are fixed in go1.27.3, the current stable release. The production image was
built with the same toolchain.

Every `scope: core` lock entry and `toolchain_image` must deep-equal the vendored kit core lock.
`versions:check` core-floor enforces this. `kit:check` versions-merge refuses a higher core version.
A Cat-only edit of those pins therefore fails both. The gate runner image has go1.27.1 with
`GOTOOLCHAIN=local`, so it refuses a `go 1.27.3` line. App-scope image entries are kept by the kit
merge, and any registered image may satisfy a Dockerfile `FROM`. That is the Cat-local route.

## Consequences

Release and CI binaries carry the patched standard library. With go1.27.3, govulncheck source and
package scans of both modules find no affecting vulnerability. Trivy finds no standard-library
or Debian finding in the release image.

The kit pin keeps `golang.org/x/net` v0.59.0 in the binary's build info. Trivy therefore still
reports CVE-2026-78669 (HIGH, fixed in v0.60.0), and binary-mode govulncheck still lists its five
HTTP/2 advisories. The binary links only `x/net/html`; its HTTP/2 code is the go1.27.3 standard
library's own copy. GO-2026-5932 (`x/crypto/openpgp`, no fix) is not linked: source mode lists it at module level only, and binary mode flags it at package level.

The gate's Go lanes still compile with the core go1.27.1 runner. These are unit backend/authcore
race and vet, plus the full gate's PG lanes, HTTP parity and legacy journey. Only the full browser
matrix serves the go1.27.3-built image. The lane's
[review record](../reviews/go-1-27-3-security/README.md) adds ad-hoc go1.27.3 evidence for those lanes.
Local workflows need a matching `PATH`: the standalone qualification needs go1.27.3, while the
[content loop](../CONTENT_LOOP.md) keeps host go1.27.1.

The remaining moves need a roedu-ui core tag: the go runtime, x/net v0.60.0, the runner image and
the `go` lines. Cat then takes them through a KIT_BUMP `kit:sync`, and the `cat-golang-trixie` entry
can go. Local roedu-ui recipe commit `0d6cdbe` (branch `fix/go-1-27-3-security`, unpublished) has
already built the runner `roedu-toolchain:core-v1.0-go1.27.3-20261021`
(`sha256:ad81a9bf…`). Redeploying production remains Paul's decision.
