# ADR-0217: Bind helper inputs to opened descriptors

Date: 2026-10-26
Status: input snapshot decision retained; r4 output implementation rejected, corrected by proposed ADR-0218

## Context

Independent static review rejected the ADR-0216 r3 helper. It parsed the prospective native
artifact, closed that read, then reopened the pathname to verify the externally retained SHA-256.
Replacing the path between those opens could make accepted captions come from different bytes than
the reported trusted digest. Producer KG/pack and repository readset paths likewise checked
canonical and no-symlink properties before a separate pathname read.

The native producer's complete dependency closure, descriptor-bound inputs, atomic output create,
command-specific `--out` refusal and all installed export/catalog/ranking/source/derived/rail guards
remain unchanged.

## Decision

- Publish only a v4 helper successor. Preserve the original and every v1/v2/v3 helper, manifest,
  pin, report, failure and artifact byte-for-byte.
- Require absolute lexical canonical paths and walk every artifact, producer and source-readset
  component from the filesystem root through directory-relative opens with `O_NOFOLLOW`. Require
  the final descriptor to be a bounded regular file, read a bounded buffer, and fail if its
  descriptor identity or size changes during the read. Unsupported descriptor-safe APIs fail closed.
- For the native artifact, compute and compare the independently supplied SHA-256 over that buffer
  before parsing. Strict duplicate-key and non-finite-number rejection, exact schemas and types,
  complete caption coverage and every source binding apply to those same bytes. The sealed metadata
  reports the digest of the accepted buffer.
- Apply the same snapshot primitive to producer inputs, repository sources, candidate/readset JSON,
  audit/key/response inputs and file digests. Do not leave a validation-then-reopen path in the
  consumer.
- Add controlled fixtures that replace an artifact path or input ancestor after the final descriptor
  opens and prove the original descriptor bytes remain authoritative. Retain stable-symlink,
  byte-bound, parser, native parity and stale runtime/add-file/embed/module negatives.

## Consequences

Path replacement cannot split the artifact's parsed captions from its trusted digest, and helper
source bindings describe bytes read from the descriptor that passed the no-symlink policy. This is
an input snapshot guarantee; it does not claim protection against arbitrary in-place writes by a
privileged concurrent actor.

The fresh native preview retains 17,499 captions and the exact external artifact digest, while the
default-4096 `lt_gastronomie_220` public task retains 4,730 choices. These are author engineering
results only. Different fresh independent code review and native verification must both pass before
a controller workflow pin; a separate reviewed content-plan/input pin is still required before any
content stage resumes. No content, source, installation, landing, push, deploy or production
approval follows.
