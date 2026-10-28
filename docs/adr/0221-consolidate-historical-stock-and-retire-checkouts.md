# ADR-0221: Consolidate historical source stock and retire old checkouts

Date: 2026-10-28
Status: accepted (Paul asked to inspect historical Cat loop work, consolidate useful unmerged work on one branch, merge it and delete the old checkouts; he explicitly kept the live continuous loop).
Amends physical-checkout retention in ADR-0188/0210. Content acceptance rules are unchanged.

## Context

Historical Cat checkouts consume tens of GiB because each retains working files and
old evidence. A different Git commit is not necessarily a missing product feature:
GUI fixes have been ported into newer runtime code, while old content branches hold
reviewed or failed proposals rather than qualified installation.

At main `052212fa`, 30 V1/consolidation tips have 272 patch-unique commits. Their
useful absent material is 374 text source/evidence files (96,419,597 bytes), plus
six C1/C2/B12 held inputs (46,007 bytes). V2 qualified no installed content; V3 is
running independently. V1.7's data scripts and pool are already on main and its
governance changes were rejected. Replaying all old trees would regress runtime,
pins, status and content acceptance.

## Decision

1. Consolidate byte-exact source and provenance on one branch from current main,
   under `docs/content-stock/`. V1 files are a dated archive mirror; held V2 files
   remain explicitly unqualified. Preserve original blobs, paths, full tips and
   digests. Do not install old modules at active source paths or import old runtime,
   generated data, pin changes, obsolete STATUS or the rejected V1.7 policy changes.
2. This lands reusable research, **zero new installed content**. ADR-0210/0220 and
   every current compatibility/review/gameplay/install/owner hold remain binding.
   Historical acceptance and source counts are not current qualification.
3. Keep all original stock refs for current Git-based readers and provenance.
   Do not fake old-branch ancestry or claim every old commit is product-merged.
   Removing a physical checkout does not require deleting its small Git ref.
4. Retire only the exact historical checkout inventory after complete recoverable
   bytes are proven on the NAS, independent destroy review and current usage checks.
   Reuse verified self-contained bundles where they cover exact tips/ancestors;
   preserve every remaining dirty/untracked/ignored nonregenerable file separately.
   In particular, preserve C2's full dirty state and the ignored GUI gate proof.
5. Keep shared main, the live `content/continuous` checkout and controller/state,
   the V3 baseline comparison, all original baselines/qualification keepers and all
   `_temp` research/evidence. Do not rewrite signed evidence or replace its old
   paths with symlinks. The portable source map records historical identities.

## Consequences

The old physical trees can be reclaimed without erasing research or publishing
unqualified vocabulary. The archive is a historical source input, not a competing
live loop, catalogue authority or install mechanism. Future curation can read main's
archive or original Git objects, with fresh checks. Machine-local NAS receipts are
the authoritative record of what was actually removed and how to restore it.

See [source stock](../content-stock/README.md) for counts, quality limits and recovery.
