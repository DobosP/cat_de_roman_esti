# ADR-0237: V5 approved conditional root pytest-cache repair

Date: 2026-11-17
Status: accepted (Paul, 2026-11-17).
Decider: Paul Dobos.
Adds only the exact additional exception below to [ADR-0236](0236-v5-approved-tool-repairs.md).
ADR-0236's two approved repairs and [ADR-0235](0235-v5-real-use-fixes.md) otherwise remain accepted.

## Context

Root ran the approved real-source DocCheck executable against unchanged main
`19ceb20e26dcfeb2ec3588b5ccabc99449a79caa`. Its root `.venv` proof passed, but the canonical null
still failed: 694 declared versus 695 physical Markdown paths. A read-only exact-set comparison
found only the existing ignored `.pytest_cache/README.md`, a 302-byte pytest cache-plugin README
with 21 June timestamps and root `.gitignore` rule `.pytest_cache/`. That cache belongs to prior
work; its creator beyond filesystem uid/gid 1000 is not established. It remains untouched.

A separate scratch-only exact proposal against `02ad6c20bf050ccab11572ca74710dbc15f93b11`
received independent technical GO. Before any application, the source, patch, focused tests,
portable binaries and limits were presented for Paul's ruling. On 17 November he explicitly
answered: **“Approve this exact cache repair and rerun (Recommended)”**.

## Decision

1. **Exact additional freeze exception.** Apply unchanged only patch SHA-256
   `9c53a41e8d50e9aa8b1322e0179de156a453a12044c737dbb6f2bff88ec42319` (14,502 bytes), plus its
   normal decision/status/inventory records. Paul also authorizes the real-source checker rebuild,
   fresh unchanged-main null check and forms S10 rerun. His earlier two approvals did not cover
   this directory; this is their separately reviewed, explicitly approved supplement. There is
   no broader change to the campaign freeze, procedure, rubric, contract, pins, source policy or holds.
2. **Identical narrow proof for two named root trees.** Only `.venv` and `.pytest_cache` can be
   excluded, each independently requiring a real root directory, exact Git top-level, zero
   indexed descendants of any type and the literal matching rule in root `.gitignore`. Indexed
   files remain indexed for this proof even when deleted from the working tree or newline-named.
   Missing Git, failed proof, tracked/unignored content, a parent Git root, corrupt index or an
   alternate ignore source/pattern retains the existing physical-source behavior. No nested,
   other ignored or near-prefix tree gains an exemption.
3. **Preserved admission and links.** Physical/declaration equality and ordinary Markdown or
   directory alias refusals remain. Excluded files cannot enter the inventory; its JSON cannot
   reside there; recognized source-document links cannot be satisfied by direct, traversal,
   directory or symlink-resolved targets in either excluded tree. The developer Git-based check
   keeps its established semantics without either inventory-only exclusion.
4. **Genuine baseline result.** Preserve the original red receipt. No failure is relabeled green,
   no content is rejected by it, and no blanket null-test waiver is granted. The actual rebuilt
   checker must pass the genuine unchanged-main rerun before Root performs forms S10 closeout.
   Independent final review and the existing landing requirements still apply. The canonical
   cache is neither deleted, moved, rewritten nor admitted as source inventory.

## Threat model and verification

The source root, Git executable/index/ignore data and filesystem must be trusted and stable during
checking, as in ADR-0236. Failure to prove exclusion keeps strict checking. There is no general
Git-ignore bypass or arbitrary directory list at the admission call site. Existing generated-tree,
history and image-reference semantics remain, including the prior limits on image-link coverage.

All five source preimages matched clean `02ad6`; the two changed production files and new fixture
file match the approved prototype postimages byte for byte. The proposal preserved all 17 earlier
race groups and added eight; original expected-red and paired CLI fixtures distinguished a source
mismatch from a canonical green result. Independent proposal review accepted the exact bytes.

The actual feature source runs the 25 DocCheck race groups, native package/CLI vet and Linux/amd64
checker rebuild with existing Go 1.27.3 and downloads disabled. The identical proposed source has
Linux/amd64, Darwin/arm64 and Windows/amd64 build receipts; only Linux runtime is exercised. Actual
commands use owned `GOCACHE`, `GOTMPDIR` and `TMPDIR`, `GOTOOLCHAIN=local`, `GOPROXY=off` and
`GOSUMDB=off`:

```text
go -C go-backend test -mod=readonly -count=1 -race -json ./internal/doccheck
go -C go-backend vet -mod=readonly ./internal/doccheck ./cmd/cat-doc-check
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go -C go-backend build -mod=readonly -buildvcs=false -trimpath -o <owned-checker-path> ./cmd/cat-doc-check
<rebuilt checker> --root <feature> --inventory docs/tracked-markdown.json
git diff --check
```

The actual 25 race groups pass with zero failure/skip events; vet and Linux build pass. The real
Linux checker is byte-identical to the reviewed prototype. The existing `tracked_markdown`
operator regenerates 696 paths; feature DocCheck reports 71 active files and empty finding/budget
arrays, and whitespace passes. Final results and unfinished S10 status remain in [STATUS](../STATUS.md).
Gameplay, sessions, content payloads and private caches remain unchanged.
