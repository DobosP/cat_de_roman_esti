# ADR-0210: Curation waves and staged landing of reviewed content stock

Date: 2026-10-22
Status: accepted (Paul's decisions in the 2026-10-22 Claude Code review of the content loop)

## Decision

Reviewed but unlanded content (1,083 accepted packages from the V1.14–V1.42 source waves) lands in
stages, each one a [curation wave](../CONTENT_LOOP.md) that passes the full install cascade, green
gates and an independent review before it lands:

1. **Stage 0, bookkeeping only.**
   - Back up the local-only content branches to the NAS. Done: a git bundle of 31 refs, sha256
     `ac0a2b63…`, under `branch-archive/cat_de_roman_esti/2026-10-22-content-loop-branches/`.
   - Fix the procedure's stale facts: the HTTP corpus count is 1206 since V1.13, and the next
     authored source is v13.
   - Add the screens and evidence rules below.
2. **Stage 1.** At least 20 existing-owner word-form families from V1.38–V1.42, the waves with the
   strongest evidence. It includes Avion, Cinematograf and Interfon, and leaves out the 10 families
   whose forms clash with earlier recorded rejections or deferrals.
3. **Later stages.** The remaining word-form families, then selected-sense families, then new
   concepts wave by wave, oldest and weakest evidence last.

Owner rulings:
- Bare `sucitoare` stays excluded, keeping the V84 exclusion (`tests/test_v84_graph_and_games.py`);
  Sucitor's other forms may land.
- Ie never gains the keys `ii` or `iei`.

Procedure rules for every wave:
- Step 1 greps `tests/` and every `docs/reviews/*/graph-candidates.json` for recorded exclusions.
- Raw evidence stays under `~/work/_temp/<wave>/`, never `/tmp`.
- Reviewers never see author drafts or each other's verdict before signing.
- Each reviewer consults at least one source per item that they chose themselves.

## Context / why

The [read-only review](../reviews/content-loop-review-20261022.md) found the stock trustworthy as
reviewed source, with uneven evidence:
- full strength for V1.38–V1.42;
- reviewer pre-exposure for V1.17–V1.37;
- a single verifiable fresh review for V1.14, V1.15 and V1.21;
- V1.33's evidence lost from `/tmp`.

The procedure had no path for landing reviewed stock, and its "expect 1207" install step would have
failed every install. Step 1 could not see the pre-V1.8 exclusion of `sucitoare`.

## Consequences

- Each stage is a curation wave with its own branch, consolidated module and dual review; nothing
  lands without green gates.
- V1.33 items need fresh research before any stage includes them, and V1.14 items are re-applied
  through the cascade, never merged.
- The V2 discovery loop for all six games' boards is designed separately and will amend this
  procedure again.
