# Native authored input and provenance

`authored-v1.json` was bootstrapped once from the authored Python source constants
at base `ae70c16935d402719b95405685bccbbbea13a3bd`, plus the independent authored
recipe candidate dossier and immutable review/archive paths. It contains 85 quick
board definitions, 351 world recipe definitions, 77 original world-local concept
definitions, and 49 recipe candidates with 68 archived core books. It does not use
any generated serving fixture as its authored input.

The recorded legacy source hashes bind the extraction. The native file itself is
pinned to SHA-256 `bbeffd444e85205a08fdfcdec43914dd69d4ee11dc24e758fdac99a0909529c6`.
No legacy interpreter is needed to read, build, check or audit these inputs.

The native builders re-resolve authored labels against the source KG, recompute
quick ratings/ranks and recipe graph projections, reconstruct original node/edge
snapshots, replay independent raw review coverage, and reproduce all four approved
catalogs byte for byte. The world baseline keeps its reviewed historical binding
metadata; newly generated proposals bind the current KG, rubric and native source
snapshot/version and preserve the complete current saved-world history.

Canonical checks:

```sh
go -C go-backend run ./cmd/cat-content-rail all --root .. --check
```

A new authored input must have `version` greater than 1 and
`parent_source_sha256` equal to the reviewed native source hash. New candidates
require both complete independent semantic reviews. Installation requires the
exact saved proposal, a fresh native audit over the complete runtime/source
manifest, the same reviewers' final acceptances, and an explicit reviewed output
SHA-256. The shared operator lock checks the full original input readset before
writes and after post-validation; rollback restores original bytes and modes.

A staged approved catalog does not activate serving: the native exporter and
server retain their compiled reviewed pins until the separate reviewed pin/code
transition and rebuild. Stale or unknown source, review, history and runtime
bindings refuse rather than being silently re-pinned.
