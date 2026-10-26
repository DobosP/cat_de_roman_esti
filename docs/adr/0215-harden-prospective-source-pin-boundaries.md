# ADR-0215: Harden prospective source-pin boundaries

Date: 2026-10-26
Status: partially superseded by ADR-0216 for output creation and input-path handling; production closure and command parsing retained

## Context

Independent review rejected the first ADR-0214 implementation. Its hand-picked source glob included
tests while omitting caption-affecting graph, content and strict-JSON code; an aliased repository
root could bypass the outside-tree output check; and the shared flag parser accepted `--out` for
default export and other commands before silently ignoring it. The separate native verifier's pass
did not qualify that candidate.

The preview must bind code that can affect its explicit parse/validate/graph/caption path without
requiring approval of an installed serving export. `internal/content/bundled.json` is embedded by
the imported content package, but the preview constructs `content.Content` directly from its
explicit KG and never calls `content.Load` or `content.Decode`. The bundle bytes therefore cannot
affect this path. The generated `content/digest.go` remains ordinary production source.

## Decision

- Ask the pinned Go 1.27.3 tool, offline and with workspace/user flags disabled, for the production
  dependency closure of `cmd/cat-content`. Bind every build-selected local non-test source and
  embedded input plus `go.mod` and `go.sum`; exclude only `internal/content/bundled.json` for the
  semantic reason above. The separately versioned consumer recomputes the same closure per run.
- Resolve the repository root before containment checks. Require a canonical output parent, open it
  through Linux `openat2` with no-symlink/beneath resolution, verify its identity, and create the
  basename relative to that descriptor with no-follow, exclusive semantics.
- Give each command its own flag set. Only an explicitly named `prospective-lant-captions` command
  registers `--out`; default export and every other command reject separated, empty and equals
  spellings during parsing before export or any write.
- Keep native caption derivation and every installed/full-export/catalog/ranking/source/derived/rail
  validator unchanged. Preserve the rejected candidate, helper, pins, reports and failed evidence.

## Consequences

A mutation to graph, content, strict-JSON, rules, module metadata or another production dependency
invalidates an older preview even when its externally supplied artifact SHA is unchanged. Changes
only to tests do not. Installed serving-bundle refreshes do not create a circular prospective
dependency. Symlink aliases cannot turn an apparently external output into a repository write, and
irrelevant `--out` input cannot reach export.

This author correction is not workflow or content qualification. Different fresh independent code
review and native verification must pass on the frozen source commit, helper manifest/pin and exact
artifact before the controller may qualify it or resume content work.
