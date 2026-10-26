# ADR-0219: Land the portable prospective Lanț caption preview

Date: 2026-10-26
Status: accepted

## Context

ADR-0214 to ADR-0218 built `cat-content prospective-lant-captions` and its blind-helper consumer
in five author/review rounds (unlanded branch `codex/source-pin-prospective-r5`, b84ba930). The r5
static review passed; the r5 native verification reported a pass that the loop never consumed.
Paul then stopped the loop for review. The owner-stop review (`~/work/_temp/content-loop/
review-20261026-owner-stop-audit/REVIEW.md` §4.1) confirmed that the strict validators and the
full-export `kg_sha256` refusal are untouched, but found defects the earlier reviews missed:

- `internal/contentbuild` imported Linux-only `openat2` symbols without a build constraint, so
  `cat-content`, `cat-content-ops`, `cat-content-rail`, `contentops` and `contentrails` no longer
  compiled for macOS or Windows (verified by cross-compiling `cat-content`; the rest follow from
  the import graph);
- a FIFO input blocked the command forever, because the no-symlink open ran before the
  regular-file check without `O_NONBLOCK`;
- a `-trimpath` binary without `GOROOT` would run a relative `bin/go` beneath `--root`;
- the relocation race test fails with `EXDEV` when `TMPDIR` is on another filesystem;
- ADR-0214 overstated the producer binding, and ADR-0215 wrongly said installed bundle refreshes
  do not affect previews.

The review recommended parking r5 and writing a small portable caption derivation instead (its
option D3 b). Paul then asked on 2026-10-26 to fix what was found and land what can be landed.
This ADR therefore lands r5 with every finding in review §4.1 corrected (D3 c). D3 b remains open
if the preview ever needs simplifying.

## Decision

- Land the ADR-0214–ADR-0218 work with these corrections:
  - The `openat2` path opener lives in `prospective_linux.go`. `prospective_other.go` makes every
    other platform refuse the preview with a clear error, so all content tools build everywhere.
  - Read opens add `O_NONBLOCK`, so a FIFO is refused by the regular-file check.
  - The producer closure refuses an empty or relative Go root and runs `go list` with
    `GOTOOLCHAIN=local`.
  - The relocation test skips with a stated reason on a cross-filesystem `TMPDIR`; Linux keeps
    the full race tests, and other platforms test the refusal.
- **What the producer binding means.** The artifact binds the KG, pack, rubric, frozen rules and
  the source files of the `cat-content` production closure under `--root`. It does not bind the
  executing binary. Consumers must build the producer from the bound root.
- **Bundle refreshes.** `content/digest.go` is generated from the installed bundle and stays in
  the closure, so every installed bundle refresh invalidates older previews. Regenerate the
  previews then; there is no cycle, because the preview never reads the bundle.
- **Not covered.** Same-user concurrent directory relocation beyond the stated `openat2`
  guarantees, files moved after creation, and privileged mutation.
- Helper v5 stays in content-loop scratch and is **not qualified**. Before first use it must pass
  the ADR-0220 tool lane: fix the review §4.2 gaps (FIFO hang, strict-JSON non-finite/BOM/UTF-16
  overclaim, uncaught non-object JSON, unpinned GOTOOLCHAIN, post-run tool bindings, key written
  before the public file), get one fresh independent review of the exact change and receive a new
  pin.
- Accepted residual: `go.mod` still marks `golang.org/x/sys` as `// indirect` although
  `prospective_linux.go` imports it directly. Builds pass with `-mod=readonly`; a later tidy may
  move it.

## Consequences

- KG-changing batches can give the blind Lanț critic native captions without weakening any
  export, catalog, ranking, source or rail guard.
- The preview is Linux-only by design. Content tooling builds and its other commands work on
  every platform.
- ADR-0214 to ADR-0218 stay as history. Their statuses point here.
