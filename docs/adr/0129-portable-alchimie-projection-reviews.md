# ADR-0129: Carry independently reviewed Alchimie projection evidence

- Status: accepted
- Date: 2026-09-08
- Partially supersedes: ADR-0104 (Alchimie exclusion only)

## Context

Alchimie serves a sparse private recipe projection, while generic critique dossiers
describe the larger source graph. The existing promotion applier requires an exact live
projection audit and explicit bindings from both reviewers. The portable serializer in
ADR-0104 rejects Alchimie because its raw review contract cannot express those bindings.
That blocks otherwise supported independent review of new recipe rounds.

## Decision

Extend `scripts/build_review_artifact.py` with an explicit `--projection-audit` input.
Every Alchimie analyst and verifier item must carry `projection_audit_sha256`: the exact
audit file's lowercase 64-character hexadecimal SHA-256. Other games retain their exact
existing item schema. Shared batch IDs, distinct reviewer identities, complementary
roles, complete source-backed judgments and fresh dossier bindings remain mandatory.

Alchimie input IDs must form one sorted Alchimie-only batch, matching the existing audit
and applier contract. Mixed-game versions can review Alchimie in a separate batch against
the complete current inventory. The serializer does not synthesize an audit, add missing
reviewer bindings, infer semantic approval or change a judgment.

Private staging contains the exact supplied audit bytes and reconstructed dossier files.
Before any output file is copied, the existing applier checks reproduce every archived
projection, validate exact batch and dossier coverage, and require current source records,
pack, KG, rubric, runtime files and audit-generator hashes. Per-item reviewer audit hashes
are preserved in raw judgments and carried into the existing version-2 fields. Altered or
stale evidence fails even when both supplied hashes have been restamped consistently.
An irrelevant audit or stale audit in a non-Alchimie output directory also fails closed.

The existing applier remains the only pack mutation boundary. Its strict promotion check
against prospective inventory, same-batch novelty debt, pending status, transactional
validation and rollback behavior remain unchanged. Artifact construction alone is not
content approval.

## Consequences

Independent reviewers can hand portable Alchimie judgments to the same serializer used
by other games without weakening projection evidence or fabricating verification. The
audit remains byte-exact; the serializer never rewrites it to match current content.

The builder tests cover successful replay, distinct raw bindings, missing and malformed
evidence, coordinated digest restamping, projection/source/batch/dossier tampering and
untouched output on rejection. Existing V48 archive and stale-source tests retain the
distinction between replayable historical evidence and evidence eligible for live apply.
