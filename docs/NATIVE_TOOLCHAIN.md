# Native tooling qualification

Last verified: 2026-10-05

The staged tooling boundary and retention requirements are recorded in
[ADR-0164](adr/0164-native-terminal-and-rest-tools.md). Full exporter/review/operator
qualification is in progress; current completed gates are in [STATUS](STATUS.md).
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
online play. Online permissions are checked; unavailable products fail explicitly.
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
