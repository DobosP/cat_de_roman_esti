# Go 1.27.3 security release builders — qualification record

Valid until: the KIT_BUMP that moves kit core Go/x/net pins — then treat as history.

Decision: [ADR-0208](../../adr/0208-go-1-27-3-security-release-builders.md). Branch
`fix/go-1-27-3-security`; operator agent:claude-code (orchestrated session, PROGRAM E8).
Raw scanner and gate outputs stay in owned scratch until landing; the numbers below are copied from them.

## Baseline (main fb829aaa, go1.27.1)

govulncheck v1.8.0 source mode exits 3 with 14 reachable standard-library vulnerabilities.

## Upstream identities (resolved 2026-10-21)

| Item | Identity |
|---|---|
| go1.27.3 linux-amd64 archive | sha256 `65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40` (go.dev JSON, matches download) |
| `golang:1.27.3-trixie` | OCI index `sha256:604106102d33b1084e37ca08adf98ac0813624ae8595bd0d7f3965ecebded09c` |
| `golang:1.27.3-bookworm` | index `sha256:21ade014faf952365b9ecbd8dbdb87176fbacb82fac9fb132d9f2a7b8cc3f132`, linux/amd64 `sha256:fea12ba16096adec0f699ce1c4da2154d320450e56c1f63671f95d2a3551c77b` |
| go1.27.3 runner (ad-hoc evidence only) | `roedu-toolchain:core-v1.0-go1.27.3-20261021`, image ID `sha256:ad81a9bf25f45c944ce692ba189df732db6e71598f53c0ed7da3908e4b69566f`, from roedu-ui `0d6cdbe` |

## Source scans (go1.27.3, govulncheck v1.8.0, DB 2026-10-21)

| Module | Source (symbol) | Package | Module-level only |
|---|---|---|---|
| `go-backend` | 0 affecting | 0 affecting | 5 x/net v0.59.0 HTTP/2, GO-2026-5932 |
| `shared-go/authcore` | 0 affecting | 0 affecting | GO-2026-5932 |

## Qualification

Pending: exact-SHA unit, full and image; release-image govulncheck binary mode and Trivy; ad-hoc
go1.27.3 backend lanes; independent review.
