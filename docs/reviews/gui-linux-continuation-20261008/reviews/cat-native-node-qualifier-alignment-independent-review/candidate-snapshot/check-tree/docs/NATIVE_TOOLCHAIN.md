# Native tooling qualification

Last verified: 2026-10-05

The tooling boundaries and retention requirements are recorded in
[ADR-0169](adr/0169-native-terminal-and-rest-tools.md) and
[ADR-0165](adr/0165-native-source-build-and-qualification.md). Complete clean-source
qualification passes under [ADR-0168](adr/0168-qualify-complete-native-toolchain.md);
CI follows accepted manual policy (ADR-0164); native gates default, references opt-in. Current gates are in [STATUS](STATUS.md).
These local tools never add a public solution endpoint.

From the repository root with Go 1.27.1:

```bash
go -C go-backend run ./cmd/cat-hop --root .. --offline --list
go -C go-backend run ./cmd/cat-hop --root .. --offline --category istorie --difficulty easy
go -C go-backend run ./cmd/cat-mobile-pack --root .. --check
go -C go-backend test -race ./internal/hopcli ./internal/roeduclient ./internal/mobilepack
go -C go-backend vet ./internal/hopcli ./internal/roeduclient ./internal/mobilepack
```

The terminal accepts `--fixture` for isolated offline fixtures and `--api-url` for explicit
online play. After a healthy probe, online permissions are checked and unavailable products fail explicitly.
`ROEDU_API_KEY` is read only by online transport and is never included in error output.
The independent original Python terminal engine/client remains available as historical
reference while the wider tooling migration is qualified.

Synthetic or separately authorized RO-EDU transport qualification:

```bash
go -C go-backend run ./cmd/cat-roedu smoke --url http://127.0.0.1:8077 --difficulty easy
go -C go-backend run ./cmd/cat-roedu export --url http://127.0.0.1:8077 --out <scratch>/kg.json
```

Transport limits are 200 records/page, 500 pages/product, 4 MiB/page, 10,000 nodes,
50,000 edges and 5,000 puzzles, under a two-minute operation context and 30-second
request timeout. Overflow refuses the entire result. A category fetch includes the
`mixed` puzzle bucket and widens nodes when solution references require it. Snapshot
identity must remain consistent across pages and products. Unknown permissions, personal
records, or missing redistribution/legal fields refuse import; all accepted provenance
survives export. Output is written through a synced sibling file only after all products
and the terminal bundle validate. No live imports were run for this migration.

The mobile `--check` compares semantic JSON and the public content hash against the
independent fixture, allowing harmless JSON whitespace differences. Without `--check`,
`--out` names the public artifact to regenerate. Node labels, undirected edge pairs and
public puzzles determine the hash; private helpers do not participate.

Native source freshness and independent HTTP qualification:

```bash
go -C go-backend run ./cmd/cat-content validate --root ..
go -C go-backend run ./cmd/cat-content export --root .. --check
go -C go-backend run ./cmd/cat-doc-check --root ..
go -C go-backend run ./cmd/cat-qualify parity --binary <scratch>/cat-server
```

The source build reconstructs eight digest-bound inputs, with a private authored policy
artifact and pinned Unicode 15 tables. The exact bundle/digest identity, source mutation
contracts and the independent frozen HTTP reference are described in
[ADR-0165](adr/0165-native-source-build-and-qualification.md) and
[the qualification record](reviews/go-native-toolchain/README.md).

Build `cat-browser-plan` beside the test server or set `CDR_BROWSER_PLAN_BINARY` to its
absolute scratch path. `CDR_NATIVE_BINARY` selects the test server; `CDR_E2E_OUTPUT_DIR`
selects browser receipts. These helpers remain local test processes.

```bash
go -C go-backend build -o <scratch>/cat-browser-plan ./cmd/cat-browser-plan
go -C go-backend build -o <scratch>/cat-qualify ./cmd/cat-qualify
<scratch>/cat-qualify smoke --url http://127.0.0.1:<port> --static-root cat_de_roman_esti/web/static
<scratch>/cat-qualify capture --url http://127.0.0.1:<port> --reference <description> --output <scratch>/cases.json
<scratch>/cat-qualify replay --input <scratch>/cases.json --binary <scratch>/cat-server
<scratch>/cat-qualify benchmark --url http://127.0.0.1:<port> --flows 24 --warmup-flows 6 --concurrency 4
```

`smoke` requires a synthetic target's legal operator/contact and anonymous flags.
Generic capture/replay records unverified reference independence; only the frozen
source-bound `parity` command checks independently captured expected responses.
Qualification HTTP is bounded to 4 MiB/response, 65,537 bytes/request, finite call counts,
15-second request deadlines and an explicit operation timeout. No redirects, URL
credentials or cookie forwarding are accepted. Benchmarks describe the measured local
fixture workload; they do not establish production capacity.

`./cat-de-roman` retains the original terminal command as a native launcher. Its build
products/cache stay in workspace scratch. A failed/unhealthy online health probe uses the
offline fixture, matching the original terminal behavior. A healthy server's content,
availability or legal-provenance refusal remains a failure.

The complete integration entrypoint is `scripts/qualify_go_toolchain.sh`. It requires
`CDR_TOOLCHAIN_SCRATCH` under `~/work/_temp/`, an explicit disposable fixture in
`CDR_NATIVE_TEST_DSN`, qualified Go 1.27.1 and Node 24, and a `PATH` containing the native
build/Git/shell utilities with Python/Rust absent. It runs source/operator/builder checks,
native race/vet, both explicit PostgreSQL release lanes, native compiled HTTP parity,
synthetic HTTP smoke/benchmark, Node gates and all browser cases. Its exit status cannot
turn missing required infrastructure into a skip. Default hermetic Go runs retain their
optional-PG markers; the explicit release lanes execute those same tests against the
supplied disposable database. Provider mocks remain local; production flags are unchanged.

Tagged app-pack input: native terminal `--offline --fixture <tagged.json>` auto-detects
public tagged envelopes. Bounded `internal/apppack` contracts preserve tags/facets and
filter app/layer/schema/kind/legal scope on detached records. Native release coupling
checks neutral `go-backend/release.json` and frontend package/lock/badge against the
canonical native build version; retained Python declarations are checked when present.
See the release closure in [ADR-0168](adr/0168-qualify-complete-native-toolchain.md).
These input/version guards are distinct from mobile output.
