# Historical content source stock

This is the reusable research that was absent from `main` at
`052212fa62f0d3646510ec23344687f749f094b8`, consolidated after Paul's 2026-10-28 request
to inspect, merge useful historical work and remove old checkouts. The live V3
`content/continuous` branch/worktree and its baseline comparison remain separate.
Decision: [ADR-0221](../adr/0221-consolidate-historical-stock-and-retire-checkouts.md).

## What was and was not landed

- The old V1 stock branches were not merged: 30 source/consolidation tips carry 272
  patch-unique commits. Their useful source, pools, reviews and canonical stock
  snapshot are preserved here as 374 byte-exact files, 96,419,597 bytes.
- Historical GUI behavior and V2 workflow/source-pin fixes are already on main or
  superseded. Twelve V2 skeleton checkouts have no unique commits. The old V1.7
  data scripts/pool are already byte-identical on main; its governance changes and
  bulky admission receipts are not adopted.
- Six additional C1/C2/B12 files, 46,007 bytes, are held drawing-board inputs in
  [held-v2/manifest.json](held-v2/manifest.json). C1's historical 17-family/38-form
  reviewer acceptance did not finish installation; C2 is unqualified, B12 failed
  blind Cald play, and B13 remains unjudged in retained scratch.
- **No content is installed by this consolidation.** No current KG, fixture,
  generated payload, source registry, pin, validator, GUI or runtime is changed.
  The live V3 loop's own pending/qualified work is not counted as this archive.

## Find the source without an old checkout

The [V1 manifest](v1-source-manifest.json) maps every original path to its archived
path, original branch/full tip, Git blob, size, mode and SHA-256. All copied bytes
are under `archive/2026-10-28/source/<original repository-relative path>`; the
original active `scripts/`, `docs/reviews/` and pool paths are not installed.

- [Historical canonical stock](archive/2026-10-28/source/docs/content-consolidation/v1-8-through-v1-32/current-stock.json)
- [Original consolidation README](archive/2026-10-28/source/docs/content-consolidation/v1-8-through-v1-32/README.md)
- [Historical checkout/source map](checkout-source-map.json)

The canonical snapshot reports 1,083 source-accepted packages: 855 proposed concepts
and 228 existing-owner families, 5,737 normalized keys and 3,426 claims. These are
**historical source counts**, not newly qualified concepts, forms, targets, rounds
or current-main compatibility. Its primary/secondary baseline bindings remain old.
Old prompts, reviews and captured modules are evidence, not current instructions.

All original stock refs remain. Original bytes can still be read by identity:

```sh
git -C ~/work/cat_de_roman_esti show <full-source-tip>:<original-path>
```

Fresh use follows [CONTENT_LOOP](../CONTENT_LOOP.md), [ADR-0210](../adr/0210-curation-waves-and-staged-stock-landing.md)
and [ADR-0220](../adr/0220-continuous-codex-content-loop.md): recheck compatibility,
holds, independent reviews and the install cascade. V1.33 needs fresh research;
V1.17–37 have reviewer pre-exposure limits. Historical PASS/accept labels never
substitute for those gates or authorize a held item.

## Recovery and checkout retirement

Only exact historical checkout paths may be removed after complete Git/NAS byte
coverage, independent review and fresh usage checks. Git refs, all `_temp` evidence,
the live continuous checkout, baseline comparison and canonical originals stay.
Old path strings in signed evidence remain unchanged; the source map identifies
their historical origin instead of pretending those paths are current inputs.

Exact recovery/retirement receipts live in the machine-local run
`~/.local/state/agent-ops/fleet-cleanup/runs/2026-10-28T183252Z-cat-checkout-consolidation/`.
NAS recovery is under the existing `dobostore:/volume1/agentops-home`; the source
map names verified existing bundles and the fresh extras prefix. It is an inventory
snapshot, not a claim that any checkout is still present or already removed.
