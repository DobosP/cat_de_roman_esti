# ADR-0223: Hermetic relocation-test filesystem

- Status: accepted; focused pinned race verification passes with zero skips
- Date: 2026-10-28
- Supersedes: ADR-0222's proposed native TMPDIR adjustment only.

## Context

The simplified Alchimie unit gate rejected an existing relocation-test skip. The real
checkout is mounted at /work while the container's temporary directory is on another
mount. Renaming the test output parent into the checkout returns EXDEV.

Putting all native temporary files inside the real checkout would be incorrect:
prospective preview output is required to stay outside that checkout. That proposed
runner adjustment was reverted before qualification. No runner or gate input remains
changed by this correction.

## Decision

The relocation case copies the native modules and reviewed rubric into a private
checkout under its temporary parent. A sibling output directory shares that parent
and filesystem, while the explicit KG/pack inputs remain read-only originals. The
same complete-path relocation and exclusive-create assertions execute unchanged.
Cross-filesystem skipping is removed; setup or relocation errors fail the test.

No production helper, content, installed pin, acceptance limit or skip exception is
changed. The existing native gate still rejects unexpected skipped tests. This setup
is tested through the owning pinned shell before repeating canonical qualification.
