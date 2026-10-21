# KIT_BUMP core-v1.13 — qualification record

Valid until: the next KIT_BUMP; then treat as history.

Decision: [ADR-0209](../../adr/0209-kit-bump-core-v1-13.md). Branch `fix/kit-bump-core-v112` on `main` 8a5e6f28;
operator agent:claude-code (PROGRAM E8). Release product **ce04b124**. Machine-readable record:
[qualification.json](qualification.json).

## Result

Qualification passed on the first clean full gate. Trivy 0.75.0 exits 0 on the release image.
govulncheck v1.8.0 finds nothing in source mode, package mode, or binary mode on the
symbol-retaining same-source twin (exit 0). The stripped release binary keeps one documented,
non-actionable residual: GO-2026-5932 (`x/crypto/openpgp`, no fixed version, not linked); see below.
The superseded core-v1.12 tag stays published but unadopted (roedu-ui ADR-0036).

| Gate (exact SHA ce04b124) | Result |
|---|---|
| unit | pass 27/27 (21.2 min, host load ~28) |
| full | pass 37/37 (11.7 min): browser 937 expected, 0 skipped/unexpected/flaky; CSP enforced 0/0; PG; parity; legacy owner; cleanup verified |
| image | pass 2/2; release image `sha256:8634dd7f3e2f…` (revision label ce04b124), `/app` sha256 `4f3807f99e23…`, go1.27.3, x/net v0.60.0 |

## Sequence and failed history

| Step | Command (`GATE_OPERATOR=agent:claude-code` for owner targets) | Result |
|---|---|---|
| core-v1.12 stage + runner (832574e8, 3423601c) | `kit:sync --sha 3423601c…` | **fail** `consumer-config` "Higher core toolchain version refused" (`62913516…`), tree unchanged → roedu-ui core-v1.13 (ADR-0036) |
| core-v1.13 candidate trial (dirty) | `kit:sync --sha 3423601c… --dirty` | fail `deps` "Installed package differs: @roedu/ui 1.0.13 expected 1.0.11" (`23e4a2a5…`); with the probe updated, pass 9/9 (`146fce0c…`) |
| Stage a6975640, runner 1d82f362, probe 8fced572 | `trust --sha 8fced572…` | pin `80e5a3a2…` |
| kit:sync | `kit:sync --sha 8fced572…` | pass 9/9 (`4ea0807f…`) |
| deps | `deps --sha 8fced572… --dirty` | pass 4/4 (`9a81bbc9…`), no further change |
| Adoption 1fe5133e | `bash scripts/gate.sh unit --sha 1fe5133e…` | **fail** (`ae562f1d…`): one rule, the bootstrap `tools/gui-bootstrap-webkit/templates/Dockerfile` `FROM golang:1.27.1-trixie` no longer registered |
| Bootstrap rebind ce04b124 | unit / `python3 -I scripts/gui-full-runner.py --sha ce04b124…` / image | pass (`a2d12cc0…` / `bef4d7c0…` / `9b385e31…`) |

## Vulnerability scans (govulncheck v1.8.0, DB 2026-10-21T00:27:29Z; Trivy 0.75.0, DB 2026-10-21T13:15:34Z)

| Scan | Result |
|---|---|
| Trivy HIGH/CRITICAL `--ignore-unfixed`, release image tar | **exit 0**: Debian 13.7 0, gobinary 0 ([output](trivy-release-ce04b124.txt)) |
| Source, `go-backend` and `shared-go/authcore` (Go source equal at 1fe5133e and ce04b124) | exit 0, 0 affecting; module-level only GO-2026-5932 ([backend](govulncheck-source-go-backend.txt), [authcore](govulncheck-source-authcore.txt)) |
| Package, both modules | exit 0, 0 affecting ([backend](govulncheck-package-go-backend.txt), [authcore](govulncheck-package-authcore.txt)) |
| Binary, symbol-retaining same-source twin (audit) | **exit 0**, no vulnerabilities ([output](govulncheck-control-unstripped-ce04b124.txt)) |
| Binary, stripped release `/app` | exit 3: **only** GO-2026-5932, no fix ([output](govulncheck-binary-release-ce04b124.txt)); the five x/net advisories are gone. The stripped twin gives the same ([output](govulncheck-control-stripped-ce04b124.txt)) |

Binary audit method: the fleet's existing practice, as in Social `.github/workflows/native.yml`. The release
binary is stripped, and govulncheck then falls back to whole-module advisories, so the binary audit runs on
a symbol-retaining same-source twin. The twin is built in `roedu-toolchain:core-v1.13-go1.27.3-20261021`
(go1.27.3) from this tree at ce04b124:

    cd go-backend && CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS=-mod=readonly go build -trimpath -o cat-server-unstripped ./cmd/cat-server

The release build is `Dockerfile:39` in `golang:1.27.3-trixie@sha256:604106…` with `GOTOOLCHAIN=local`:
`CGO_ENABLED=0 GOMAXPROCS=2 GOFLAGS=-p=2 go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/cat-server`.
The only difference affecting Go code is `-ldflags="-s -w"`: `-p` and `GOMAXPROCS` set parallelism, and
`-mod=readonly` is the default. The twin also lacks the release build's embedded `dist/`, `legacy/` and
build-identity data. Those are `//go:embed` bytes that change `.rodata` but not the package or symbol set.
The independent review measured `.text`, `.gopclntab`, `.go.type`, `.noptrdata` and `.data` as the same
size in the release `/app` and the stripped twin. `go version -m` of the release `/app`, the twin and a stripped twin is
identical: go1.27.3, the same module versions and hashes, and the same build settings. Go omits `-ldflags`
under `-trimpath`.

GO-2026-5932 is a documented, non-actionable residual. Its OSV record lists only package imports and has
no fixed version. The twin's symbol table holds no `crypto/openpgp` symbol. Its x/crypto packages are argon2,
bcrypt, blake2b, blowfish, chacha20, chacha20poly1305, cryptobyte, internal/poly1305, pbkdf2 and scrypt,
and the release `/app` contains no `crypto/openpgp` string. The release build flags stay unchanged.

## Independent review

A separate Claude Code reviewer agent (Opus, read-only) gave **APPROVE-WITH-NOTES**
([record](independent-review.json)). It re-derived the following:
- the scope, and kit and generated-file equality;
- authcore against Social `SOURCE.json`;
- the trust pin `80e5a3a2…` and tree `e5e03dd3…`, using the wrapper's own `snapshot()`;
- all three gate results, the 937 browser cases and the cleanup.

It re-ran the scanners itself: Trivy exit 0; govulncheck release exit 3 on GO-2026-5932 only; twin exit 0.
It rebuilt the twin from `git archive ce04b124`, bit-identical (`efcbe944…`; stripped `67cff513…`). It
found 0 openpgp names in the release `/app`'s own `.gopclntab`. Its notes:
- the twin wording is now "the only difference affecting Go code";
- the literal "stripped binary clean" is not met, and GO-2026-5932 is the named, documented residual;
- the bootstrap rebind is a refresh, not a weakening;
- the content loop is blocked until the owner moves the host Go.

## Retention

The scratch evidence of both lanes is archived on DoboStore, sha256 verified on both ends:
`dobostore:/volume1/agentops-home/temp-archive/2026-10-21/fix__core-v112-v113-kit-bump-evidence.tar.zst`
(sha256 `cbc1a3da0d20e1e22af46dc6279562266dc951696b9bb1834895c7c892e6fe0f`). It holds gate results and logs,
scanner outputs, the release `/app`, the twin builds, the release image tar and this worktree's `.gate`.
The Trivy DB cache is excluded. The local copies are removed after landing. Raw transcripts are never copied.
