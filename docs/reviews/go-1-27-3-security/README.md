# Go 1.27.3 security release builders — qualification record

Valid until: the KIT_BUMP that moves kit core Go/x/net pins — then treat as history.

Decision: [ADR-0208](../../adr/0208-go-1-27-3-security-release-builders.md). Branch
`fix/go-1-27-3-security` on `main` 79669601; operator agent:claude-code (orchestrated session,
PROGRAM E8). Landing product **99f507f4** = the GATE-CHANGE toolchain commit 6ee5a8ba plus one
GUI race fix. Machine-readable record: [qualification.json](qualification.json).

## Result

Qualification **passed on the second full gate**, after one failed browser case. It was not a
clean first pass. The vulnerability fix is **partial**:

- the go1.27.3 standard library clears all 14 baseline vulnerabilities;
- one Trivy HIGH remains: `golang.org/x/net` v0.59.0 CVE-2026-78669, a kit core-v1.11 pin.

| Gate (exact SHA 99f507f4) | Result |
|---|---|
| unit | pass 27/27 (18.6 min) |
| full | pass 37/37 (14.6 min): browser 937 expected, 0 skipped/unexpected/flaky; CSP enforced 0/0; PG; parity; legacy owner; cleanup verified |
| image | pass 2/2; release image `sha256:c1186db45ca5…`, `/app` sha256 `d0dcfe9f254b…`, built by go1.27.3 |

## Failed history

- f2e4033f: unit 27/27 and image passed. It was superseded when its ADR number collided with
  fix/gui-publication-followups' claimed 0207 and was renumbered to 0208.
- 3ad049db: unit 27/27 passed. It was superseded when `main` moved to 79669601 and the branch was rebased.
- 6ee5a8ba: unit 27/27 and image passed. The **full failed** on 1 of 937 cases (936 passed, 0
  flaky): `lifecycle.spec.mjs:86` Alchimie mobile, "recovers an expired saved ID into a playable
  fresh start".
  - The trace shows a product race. Measured from the reload, the Play-enabled assertion resolved
    at +100 ms and the stale id was read at +105 ms. The app's GET for the saved game reached the
    404 route only at +112 ms. The fix commit message's +43/+103 ms are assertion start times.
  - The cause: `AlchimieChallenge` initialised `loading` to false, unlike Perechi, Conexiuni,
    Intrusul and Lanț. Fix 99f507f4 initialises it from the saved pointer.
  - Follow-up: Cald sau Rece's `busy` starts false too, so the same latent one-frame race remains
    there. It has not failed yet.
  - Host load was 17–24 during that run (another workload's OCR shards).

## Vulnerability scans (govulncheck v1.8.0, DB 2026-10-21; Trivy 0.75.0, DB 2026-10-21)

| Scan | Result |
|---|---|
| Baseline source, main fb829aaa, go1.27.1 | exit 3: 14 reachable stdlib vulnerabilities |
| Source and package, 99f507f4, go1.27.3 | 0 affecting in `go-backend` and `shared-go/authcore` |
| Binary, release `/app` | exit 3: five x/net v0.59.0 HTTP/2 advisories and GO-2026-5932 ([output](govulncheck-binary-release-99f507f4.txt)) |
| Trivy HIGH/CRITICAL `--ignore-unfixed`, release image | exit 1: **1 HIGH**, x/net v0.59.0 CVE-2026-78669; Debian 0, stdlib 0 ([output](trivy-release-99f507f4.txt)) |
| Trivy, same flags, main product 16733891 image | 5 HIGH (4 stdlib v1.27.1 + 1 x/net) |
| Trivy, same flags, deployed V1.0.1 image | 11 (4 stdlib v1.27.1 + 7 perl-base Debian 12) |

The binary links only `x/net/html`. Its HTTP/2 code is the go1.27.3 standard library's
`net/http/internal/http2` and `vendor/golang.org/x/net/http2/hpack`. Both scanners read x/net v0.59.0
from the build info, so clearing them needs the kit core x/net v0.60.0 pin.

## Ad-hoc go1.27.3 evidence (not a gate result)

These runs used runner `roedu-toolchain:core-v1.0-go1.27.3-20261021` (`sha256:ad81a9bf…`, roedu-ui
recipe `0d6cdbe`) and the gate's pinned `postgres:16-trixie`. They ran on a copy of the unit-gate
working tree of 6ee5a8ba, whose Go code equals 99f507f4. Results: backend race 1936 passed (only
the 17 allowed PG-package skips), backend vet, authcore race/vet, PG accounts 12 and httpapi 302 with
0 skips, and HTTP parity 1206 requests ok against a go1.27.3 `cat-server`. The pre-rebase tree
f2e4033f gave 1930/12/301/1206.

## Upstream identities (resolved 2026-10-21)

| Item | Identity |
|---|---|
| go1.27.3 linux-amd64 archive | sha256 `65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40` (go.dev JSON, matches download) |
| `golang:1.27.3-trixie` | OCI index `sha256:604106102d33b1084e37ca08adf98ac0813624ae8595bd0d7f3965ecebded09c` |
| `golang:1.27.3-bookworm` | index `sha256:21ade014faf952365b9ecbd8dbdb87176fbacb82fac9fb132d9f2a7b8cc3f132`, linux/amd64 `sha256:fea12ba16096adec0f699ce1c4da2154d320450e56c1f63671f95d2a3551c77b` |

## Retention and review

Gate results, browser artifacts, the failed case's trace, scanner and ad-hoc logs are archived at
`dobostore:/volume1/agentops-home/temp-archive/2026-10-21/fix__go-1-27-3-security-evidence.tar.zst`
(sha256 `5230d8e87cf4…`, verified on both ends) before local cleanup.

The first independent review (Claude Opus reviewer, read-only) gave LAND-WITH-NOTES on the toolchain
change and found no blocker. Its notes are applied in ADR-0208: the exact go1.27.1 gate lanes, the
three `go` lines, the ADR-0184 status, GO-2026-5932, the `PATH` split and the unpublished recipe
commit. The final pass over 99f507f4, the rebase and this record gave APPROVE-WITH-NOTES. It
confirmed the trace ordering, the fix's safety (hook order, pending always cleared, no new
stuck-loading path) and these numbers. It also flagged the Cald sau Rece follow-up and wording nits,
which are applied here.
