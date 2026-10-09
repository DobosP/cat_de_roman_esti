Valid until: owner validation policy, inspected graph/contracts, or toolchain availability changes — then treat as history.

# Rust assessment for Go-authoritative validation

Keep the existing Go implementation on the release path. Rust can supply an optional independent algorithm check when its measured value justifies the toolchain and dependency cost. No second server, runtime switch, FFI layer or new validation framework is needed for this content wave.

The owner now selects native Go JSON as authoritative. The old Python ranking byte-order failure does not require rewriting native sorted JSON. Retain typed equality of all 716 ranking rows, array order, source bindings, ranking formulas and refusal checks; Python remains an optional independent reference.

## Existing coverage

| Concern | Existing Go contract | Retained Rust cross-check |
|---|---|---|
| Directed graph, BFS order, predecessors, weighted distance | `internal/graph/service_test.go::TestCanonicalPythonGraph`; `dense.go` uses indexed reverse adjacency, queue BFS and heap Dijkstra. Contexto profiles call the dense methods. | `src/graph.rs::tests::canonical_python_graph` separately implements indexed BFS/Dijkstra, normalization, fuzzy resolution and ordering. |
| Puzzle paths, topology and limits | `contentbuild/validate.go` checks fixture shape, edges, paths/par, category/difficulty and distractor shortcuts; `TestFixtureMutationsRejected`. Alchimie action search is bounded to six actions/50,000 states. | Graph and game unit contracts exist; there is no standalone Rust authored-KG/pack/rank/derive validation CLI. |
| Normalization, feedback and deterministic selection | Pinned Unicode15/canonical tests; Contexto graph/feedback goldens; Lanț direction/caption/progress contracts; `pyrandom` vectors. | Graph, Contexto, Lanț and `pyrandom.rs` consume retained independent vectors. They do not replace current Go source/refusal checks. |
| Saves and bounded state | Go exploration restore, complete-history rails, session TTL/cap/race contracts. Current Source7 sealed World proof already covers 33 goal modes and ten histories/1,156 prefixes within its recorded scope. | `alchimie_explore.rs` has craft/goal/restore/invalid-save cases; `session.rs` tests TTL, caps and locking. Current Source7 execution has not been qualified here. |
| Private content and input envelopes | Go sealed digest/source/export checks, strict JSON/body/refusal contracts and operator/review rails. | `Content::load/decode` authenticates the embedded Go bundle/digest; `validation.rs` checks frozen model/error vectors. This is serving-content validation, not the Go authoring/approval pipeline. |

The shared graph corpus has 19 text cases, 65 ratio cases and eight graph targets. Two implementations against the same frozen corpus provide useful independence, but are not exhaustive coverage of every current graph target. Rust includes those corpus files from `go-backend`; it does not have a separately generated current Source7 oracle.

A concrete improvement is a direct dense-BFS versus existing ordered/sparse-BFS differential test over current targets and small directed/unreachable/tie cases. No dedicated all-target differential contract was located in the inspected Go graph tests. Weighted distances already use the dense implementation through their public wrapper, so comparing that wrapper with the dense method would not be independent. A measured native check benchmark and allocation profile should guide any further optimization; no new benchmark was run for this assessment.

## Smallest existing Rust entrypoint

There is no graph-only Cargo package or graph-validator executable. The existing filtered library test is:

```text
cargo test --manifest-path rust-backend/Cargo.toml --locked --offline --lib graph::tests::canonical_python_graph -- --exact
```

This is a future command description, not an executed test or approval to acquire tools. Although it runs only the graph unit case, Cargo still compiles the complete library and its mandatory dependency graph. `Cargo.toml` unconditionally includes Axum, Tokio, reqwest and the other server dependencies; there are no graph-only feature gates. `Cargo.lock` format4 contains 129 package entries. Filtering the test does not eliminate that closure.

`graph::Service::new(Arc<Content>)` and `Content::decode` are usable library APIs, but the current binary only offers serving/replay modes. Its `--replay` path constructs a Tokio runtime and HTTP router. Do not launch that server/replay path merely to validate graph invariants.

## Tooling observed without execution

`rust-backend/Cargo.toml` declares edition2024 and minimum Rust1.98; `rust-toolchain.toml` pins1.98.1 with rustfmt/clippy. These are manifest requirements, not a verified installed Cargo/rustc version.

Filesystem checks found no `/home/dobo/.cargo`, `/home/dobo/.rustup`, `/usr/local/cargo`, `/usr/local/rustup` or `/opt/rust`, and no rustc/cargo at the inspected `/usr/bin` or `/usr/local/bin` paths. The owned task `tools` directory contains only the qualified Go SDK/archive. No Rust registry cache was found in those inspected roots. This is a bounded inventory, not a claim about every host path. No version commands, acquisition, builds or tests ran.

## Recommendation

Complete the Go-native readonly check and its meaningful drift/refusal/parity tests now. Keep the existing dense graph implementation and bounded exact search. Measure the actual Go check before adding a language boundary.

If later measurements or a genuine uncovered algorithm contract justify Rust, first qualify an explicitly owned toolchain and locked offline dependency cache, then run the existing graph library test against explicitly bound current content/corpus bytes. Report that as an optional independent cross-check. Consider a smaller graph-only package only as a separately justified change; do not make speculative extraction or the entire Rust server a prerequisite for this Go content release.

Known serving-asset/current-authority prerequisites and original native release gates remain separate. Rust cannot substitute for source approvals, installed audits, bounded-session guarantees or those gates. Python-format and unexecuted Rust results must not be relabelled as Go failures or passes.
