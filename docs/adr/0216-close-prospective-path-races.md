# ADR-0216: Close prospective path races

Date: 2026-10-26
Status: proposed; r3 author candidate awaits fresh independent review and native verification

## Context

Independent review rejected the ADR-0215 r2 candidate. After its final output-parent identity
check, the process created relative to a held directory descriptor. A concurrent rename could move
that descriptor's directory into the repository before creation. Native input reads also rejected
only a symlink in the final component, while the pinned consumer rejected a symlink anywhere in the
KG or pack path.

The complete production dependency closure and command-specific `--out` parsing passed review and
remain unchanged. All installed export, catalog, ranking, source, derived and rail guards remain
strict.

## Decision

- Require explicit KG and pack paths to be absolute, lexically canonical and free of symlinks in
  every component. Open the whole path from the filesystem root with Linux `openat2`,
  `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS` and `O_NOFOLLOW`, then validate and read bytes only from that
  descriptor. Never resolve an alias into an accepted producer path.
- After canonical containment and native artifact construction, create the complete final output
  pathname in one `openat2` call with the same resolution constraints plus
  `O_CREAT|O_EXCL|O_NOFOLLOW`. Do not create later relative to a previously validated directory
  descriptor.
- Exercise the production boundaries with deterministic hooks: replace an input ancestor after
  the descriptor opens and prove the original bytes are read; move the approved output parent into
  the repository and replace it at the final pre-create boundary, then prove the relocated
  repository directory receives no file.
- Publish a distinct v3 helper manifest and unqualified author pin even though the consumer's
  canonical no-symlink input policy already matches this decision. Preserve every v1/v2 helper,
  pin, signed report, artifact and failed receipt.

## Consequences

Native and consumer input policy now agree, and accepted bytes are bound to the verified opened
descriptor. Output creation resolves its ancestors and creates the final file in one kernel
operation, closing the reviewed pre-create relocation window while preserving no-overwrite
semantics. The guarantee covers the creation boundary; it does not claim protection against an
arbitrary filesystem move after the function returns.

This r3 source and helper are unqualified author evidence. Different fresh independent code review
and native verification must both pass before the controller may issue a workflow pin or resume
content work. No content, source, installation, landing, push, deploy or production approval follows.
