# ADR-0104: Build portable artifacts from independent review judgments

- Status: partially superseded by ADR-0129 (Alchimie exclusion only)
- Date: 2026-09-06

## Context

The promotion gate already accepts fail-closed version-2 artifacts, but creating those
artifacts depended on one workflow-specific response shape. Independent reviewers need a
portable handoff when that workflow is unavailable, without letting the serializer invent
judgments, verification, or dossier bindings.

## Decision

`scripts/build_review_artifact.py` accepts one strictly shaped analyst file, one strictly
shaped verifier file, the exact current dossier directory, and an output directory. It
requires distinct reviewer identities, complementary roles, identical unique ID batches,
complete per-ID coverage, known games and pending IDs, nonblank rationales, exact current
dossier bindings, and HTTP(S) evidence for every verifier judgment.

The tool preserves each raw judgment, rationale, and source list plus both input-file paths,
reviewer identities, roles, and byte-level SHA-256 digests. It derives the version-2 gate
rows with `apply_rereview.synthesized_gate_verdict`: only two promotions promote, either
rejection rejects, and every other combination keeps the item pending. It validates every
finished file through `apply_rereview.validated_artifact` before writing output. Temporary
validation files live under the caller's existing output parent and are always removed.

## Consequences

Missing, duplicate, stale, partial, role-confused, same-identity, or malformed input fails
before an output file is changed. Existing unrelated per-game artifacts and dossier files
also block the write so an old batch cannot be mixed into a new one.

Alchimie reviewers must explicitly bind the private live-recipe projection. Because this
portable input does not carry that reviewer-authored binding, the tool rejects every
Alchimie ID before output and leaves the existing projection-bound workflow unchanged.

The tool serializes already-authored judgments; it does not review content, alter the rubric
or model workflow, promote a pack item, or set verification flags outside its validated
two-reviewer program. The existing applier remains the only pack mutation boundary.
