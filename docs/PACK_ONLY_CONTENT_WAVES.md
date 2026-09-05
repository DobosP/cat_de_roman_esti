# Pack-only content waves

Use this checklist for a bounded set of new game instances that refer only to nodes already
in the served KG. The governing decision is [ADR-0102](adr/0102-pack-only-content-wave-workflow.md);
the quality and promotion requirements are [the critique rubric](CRITIQUE_RUBRIC.md).
`scripts/expand_content.py` is V2-only history and is outside this workflow.

1. Create `<scratch>/<wave>/<category>/candidates.json` with all six arrays. `nodes` and
   `edges` must be empty. Include only supported instance payloads; do not reuse retired IDs.
2. Obtain independent `verify_factual.json` and `verify_quality.json` artifacts. Each binds
   the exact candidate SHA-256 and fully covers every raw reference. A quality `keep` only
   stages `pending`; it is not approval.
3. Stage the batch, then capture the newly allocated IDs:

   ```bash
   PYTHONPATH=. <interp> scripts/import_candidates.py --dir <scratch>/<wave> --pack-only
   PYTHONPATH=. <interp> scripts/critique_pack.py --status pending --ids <exact-ids> --strict \
     --dossier <scratch>/<wave>-dossiers
   ```

4. Require an analyst critique and an adversarial Romanian-web verification for every ID.
   Their separate JSON files use the portable contract in [ADR-0104](adr/0104-portable-independent-review-artifacts.md):
   exact shared `input_ids`, distinct reviewer IDs, and one dossier-bound judgment per ID.
   Build the version-2 files, then apply only the fresh, complete batch:

   ```bash
   PYTHONPATH=. <interp> scripts/build_review_artifact.py \
     --analyst <analyst.json> --verifier <verifier.json> \
     --dossiers <scratch>/<wave>-dossiers --out <scratch>/<wave>-verdicts
   PYTHONPATH=. <interp> scripts/apply_rereview.py --dir <scratch>/<wave>-verdicts
   ```

   The current V2 projection contract accepts Alchimie-only batches; a batch that mixes
   Alchimie with another game fails closed before output.

5. Run the content gates and refresh only the digest-bound artifacts affected by the pack:

   ```bash
   <interp> scripts/validate_fixture.py
   <interp> scripts/validate_games_pack.py
   PYTHONPATH=. <interp> scripts/rank_games_pack.py --write
   PYTHONPATH=. <interp> scripts/build_derived_catalog_v38.py --write
   PYTHONPATH=. <interp> scripts/export_mobile_app_pack.py \
     tests/fixtures/cat_mobile_app_pack_contract.json
   ```

The derived builder keeps its frozen source-ID set. A pack digest refreshes its metadata;
it does not authorize widening the 336-board payload.
