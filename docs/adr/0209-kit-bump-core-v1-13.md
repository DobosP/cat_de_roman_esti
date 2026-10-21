# ADR-0209: Adopt kit core-v1.13 (Go 1.27.3 security pins)

Date: 2026-10-21
Status: accepted (security fix under Paul's 2026-10-21 Cat main authorization, [ADR-0206](0206-owner-authorized-main-publication.md)); completes [ADR-0208](0208-go-1-27-3-security-release-builders.md)

## Decision

Cat takes roedu-ui core-v1.13 by KIT_BUMP: `kit:sync` from the canonical five-file kit. Its core
pins replace core-v1.11's (roedu-ui ADR-0035/0036):

- go runtime 1.27.3;
- `golang:1.27.3-trixie@sha256:604106102d33…`;
- `golang.org/x/net` v0.60.0;
- gate runner `roedu-toolchain:core-v1.13-go1.27.3-20261021` (`sha256:c84ff601…`).

Core-v1.12 carries the same pins but its runner tag orders below `core-v1.0-linux-20261006`, so this
repository's `kit:sync` refused it ("Higher core toolchain version refused"). Core-v1.13 renames the tag only.

Cat follows the new pins:

- `go-backend/go.mod` moves to `go 1.27.3` and x/net v0.60.0. `kit:sync` generates both; the vendored
  kit module declares `go 1.27.3`.
- The app-scope `cat-golang-trixie` entry is retired: the canonical `Dockerfile` builder now matches the
  core `golang` entry exactly. `cat-golang-bookworm` stays, because no core image covers the standalone
  `go-backend/Dockerfile`.
- `scripts/gui-toolchain-probe.mjs` expects the delivered UI 1.0.13 and web-kit 0.1.13 packages.
- `shared-go/authcore/go.mod` keeps `go 1.27.1`. Social vendors that file under a hash pin
  (`services/authcore/SOURCE.json`). The module requires neither the kit nor x/net, and a lower
  dependency `go` line is valid under a go1.27.3 main module.

## Context / why

ADR-0208 left one Trivy HIGH in the release image: x/net v0.59.0, CVE-2026-78669, fixed in v0.60.0.
It also left five binary-mode govulncheck x/net advisories, all of them core-v1.11 pins. The new
runner also moves every gate Go lane to go1.27.3. These are the unit backend/authcore race and vet
lanes, the full gate's PG lanes, HTTP parity and the legacy journey. Under ADR-0208 those lanes
still compiled with go1.27.1.

## Consequences

The [qualification record](../reviews/kit-bump-core-v113/README.md) holds the scanner outcome on the
release image. govulncheck v1.8.0 reports GO-2026-5932 (`x/crypto/openpgp`, no fixed version) for any
stripped binary that contains the x/crypto module. That holds even when, as here, the package is not
linked.

`go-backend` needs go1.27.3 on every local `PATH`. The [content loop](../CONTENT_LOOP.md) pins host
go1.27.1 with `GOTOOLCHAIN=local`. Under that setting it now refuses `go-backend` until the owner
moves the host toolchain and that file. Redeploying production remains Paul's decision.
