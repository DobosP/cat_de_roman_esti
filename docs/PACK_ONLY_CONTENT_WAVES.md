# Pack-only content waves

Use this checklist for a bounded set of new game instances that refer only to nodes already
in the served KG. The governing decision is [ADR-0102](adr/0102-pack-only-content-wave-workflow.md);
the quality and promotion requirements are [the critique rubric](CRITIQUE_RUBRIC.md).
Native operator commands and the source-version transition are documented in
[the operator contract](../go-backend/internal/contentops/README.md) and
[the tooling guide](NATIVE_TOOLCHAIN.md).
`scripts/expand_content.py` is V2-only history and is outside this workflow.

For version scope and outcome reporting, see
[ADR-0113](adr/0113-outcome-based-version-batches.md). Capture the baseline commit before
authoring so the final inventory comparison covers the whole batch.

1. Create `<scratch>/<wave>/<category>/candidates.json` with all six arrays. `nodes` and
   `edges` must be empty. Include only supported instance payloads; do not reuse retired IDs.
2. Obtain independent `verify_factual.json` and `verify_quality.json` artifacts. Each binds
   the exact candidate SHA-256 and fully covers every raw reference. A quality `keep` only
   stages `pending`; it is not approval.
3. Stage the batch, then capture the newly allocated IDs:

   ```bash
   go -C go-backend run ./cmd/cat-content-ops import-candidates --root .. \
     --dir <scratch>/<wave> --pack-only --write
   go -C go-backend run ./cmd/cat-content-ops critique --root .. \
     --status pending --ids <exact-ids> --strict --dossier <scratch>/<wave>-dossiers --write
   ```

4. Require an analyst critique and an adversarial Romanian-web verification for every ID.
   Their separate JSON files use the portable contract in [ADR-0104](adr/0104-portable-independent-review-artifacts.md):
   exact shared `input_ids`, distinct reviewer IDs, and one dossier-bound judgment per ID.
   Build the version-2 files, then apply only the fresh, complete batch:

   ```bash
   go -C go-backend run ./cmd/cat-content-ops build-review --root .. \
     --analyst <analyst.json> --verifier <verifier.json> \
     --dossiers <scratch>/<wave>-dossiers --out <scratch>/<wave>-verdicts --write
   go -C go-backend run ./cmd/cat-content-ops apply-review --root .. \
     --dir <scratch>/<wave>-verdicts --write
   ```

   For Alchimie, follow [ADR-0129](adr/0129-portable-alchimie-projection-reviews.md).
   Keep its sorted exact IDs in a separate Alchimie-only batch. Generate the live recipe
   audit after staging and dossier creation, then give the same audit to both reviewers:

   ```bash
   go -C go-backend run ./cmd/cat-content-ops audit-projections --root .. \
     --ids <sorted-alchimie-ids> --dossier <scratch>/<wave>-dossiers \
     --out <scratch>/<wave>-projection-audit.json --write
   ```

   Include `projection_audit_sha256` on every Alchimie raw judgment: the audit file's
   exact lowercase 64-character SHA-256, without a `sha256:` prefix. Each reviewer must
   assess the displayed openings, sparse routes, exact action par and choice bounds.
   Add `--projection-audit <scratch>/<wave>-projection-audit.json` to the builder command.
   The completed output includes that audit's original bytes and the bound dossiers.
   A changed pack, KG, rubric, runtime, generator, dossier or projection requires fresh
   evidence and review. Run native `apply-review --write` afterward for the unchanged strict
   prospective-inventory promotion gate; creating the artifact does not promote content.

5. Run the content gates and refresh only the digest-bound artifacts affected by the pack:

   ```bash
   go -C go-backend run ./cmd/cat-content validate-fixture --root ..
   go -C go-backend run ./cmd/cat-content validate-pack --root ..
   go -C go-backend run ./cmd/cat-content-ops rank --root .. --write
   go -C go-backend run ./cmd/cat-content-ops derive --root .. --write
   go -C go-backend run ./cmd/cat-mobile-pack --root .. \
     --out ../tests/fixtures/cat_mobile_app_pack_contract.json
   ```

The derived builder keeps its frozen source-ID set. A pack digest refreshes its metadata;
it does not authorize widening the 336-board payload.

After the integrated checks, generate the version's content inventory report:

```bash
go -C go-backend run ./cmd/cat-content-ops delta --root .. --baseline <baseline-commit> --text
```

Omit `--text` for JSON with added, removed and changed IDs. The report distinguishes forms,
pack stock, approvals and declared ranking eligibility; actual runtime selection still needs
the game checks above. Alias data alone cannot establish a count of genuine synonyms.

Native dossiers bind `review_source_version=native-contentops-v1` and all current runtime,
generator, source, rubric and ledger inputs. Obtain fresh raw judgments against those
dossiers; old Python-bound review history remains preserved and cannot grant current
approval. Raw quality `keep` still stages pending. Mutations require explicit `--write`;
read-only/default commands do not install records. Shared locks and under-lock readsets
refuse stale workers, and failed prospective validation restores every changed file.

The frozen catalog/reserve/quick authorities and independent HTTP reference retain their
explicit version pins. A reviewed source change requires its affected authority pins and
independent reference evidence to transition before native export/release freshness can
pass. Regenerating metadata alone never authorizes new boards or replaces review.
