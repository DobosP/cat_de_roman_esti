# ADR-0186: Go-authoritative content validation and native JSON

Date: 2026-10-09
Status: Accepted by the owner; implementation qualification recorded in STATUS.
Amends: ADR-0165/0168 validation routing and ADR-0185 loop execution.

## Context and authorization

The owner explicitly requested migrating content checks to Go, accepting the new
Go format, moving away from Python requirements and rewriting validations. Rust
may provide independent graph checks or measured performance improvements. The
owner also requested prompt notice when migration incompatibilities block work.

V1.7's full Python run exposed object-key order differences between native Go
and Python ranking serialization. The independently observed 716 rows, array
order, numeric values, scores, weights and bindings are equal. That failure
remains historical evidence; it is not retroactively passed.

## Decision

Go content/source/operators, graph and gameplay contracts are the required
content workflow. Python and Rust remain optional independent references and
archived implementations. A whole Python suite is not a mandatory prerequisite
for Go content adoption; any substantive contract missing from Go must be ported
or reported explicitly, rather than silently waived or marked covered.

Go's deterministic JSON encoding is authoritative for native-generated sidecars:
UTF-8, sorted object keys, one-space indentation and a final LF. Object-key
insertion order in a Python dictionary is not a cross-language content contract.
Array order, strict field types, source/review hashes, mirror identities and all
ranking/selection values remain meaningful. The optional Python ranking test
compares parsed values and exact mirrors; its own renderer's field-order tests
remain tests of that retained renderer. Generated fixtures are never hand-edited
to change format, and raw approval/hash bindings are never canonicalized away.

The read-only `cat-content-ops check` combines existing native graph/pack,
ranking and derived-catalog checks, refuses stale values and non-native sidecar
format, and checks source snapshots and mirrors. It does not grant source seal,
editorial approval, installed authority, HTTP/browser or release acceptance.
Those native gates remain separate and required where applicable. Independent
frozen HTTP/mechanics/graph corpora remain data inputs to native qualification;
self-captured candidate responses do not become independent expected results.

Use existing Go dense graph algorithms first. Reuse Rust as an optional
independent validator where its existing contracts fit. Adding Rust production
integration, FFI or a new dependency/build pipeline requires a measured benefit
and explicit implementation scope; language choice alone is not a speed claim.

Batch code review and affected native checks around substantive changes. Keep
one concise current handoff and reuse immutable evidence by reference. Preserve
failed evidence, but stop repeating whole protection maps and successful legacy
campaigns as routine progress. Notify the owner promptly about unsupported
contracts, semantic disagreement, missing required assets or migration blockers.

## Preserved boundaries

Independent factual/quality approval, semantic critique thresholds, graph caps,
private answers, bounded deterministic sessions/saves, historical provenance,
strict refusals, supported transactions and final native qualification remain.
No push, deployment, provider/PG activation or paused frontend/GUI work is
implicitly authorized. Source6 remains live until qualified Source7 adoption.
Resource limits stay in force; no failed state or clock is resumed/reset.
