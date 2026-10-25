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

For V2, follow [ADR-0212](adr/0212-bounded-content-workflow-repair.md), extending ADR-0211, and the exact commands in
[CONTENT_LOOP.md](CONTENT_LOOP.md). Pack records and authored Intrusul/Perechi quick boards
are **class P**; quick boards use the 4c–4e rail candidate/review/proposal/audit/finals path,
not an unsupported `import-candidates` payload. Class P has no light path: all three rails
are rebuilt and re-signed; current pack/ranking bindings also reach the world audit. A KG change is class G
and takes the full 4a–4i cascade in a separate landing. Intrusul and Perechi boards also apply
the unbound rubric I/J section in CONTENT_LOOP.md; the bound rubric stays unchanged.

Use a landing id `<id>` (`b1`, `c1`, `b2`, …), branch `content/v2-<id>-<slug>`, and evidence
under `~/work/_temp/content-loop/evidence/<id>/` with a SHA-256 manifest. `<ID>` is the
uppercase id, as in `reviewedV2B1()`. Complete M0–M5 before round 1, including the scratch
lint screen and the gameplay critic's shuffled, label/solution-blind solve. Compare that
answer mechanically; the critic is a pre-review filter whose log is frozen, not a signer.

1. Create `<scratch>/<wave>/<category>/candidates.json` with all six arrays. `nodes` and
   `edges` must be empty. Include only supported instance payloads; do not reuse retired IDs.
2. **Round 1:** obtain independent `verify_factual.json` and `verify_quality.json` artifacts
   from the fixed `factual-v2-<id>` and `quality-v2-<id>` reviewers. Each binds the exact
   frozen candidate SHA-256 and fully covers every raw reference. Each reviewer chooses at
   least one URL per item outside the author's normalized URL set; author sources remain
   sealed until both sign. Both `signed_at` timestamps must precede either reviewer reading
   the other's verdict. More than 20% identical rationales or a reviewer name in any M1–M5
   artifact voids that review. A quality `keep` only stages `pending`; it is not approval.
3. Stage the batch, then capture the newly allocated IDs:

   ```bash
   go -C go-backend run ./cmd/cat-content-ops import-candidates --root .. \
     --dir <scratch>/<wave> --pack-only --write
   go -C go-backend run ./cmd/cat-content-ops critique --root .. \
     --status pending --ids <exact-ids> --strict --dossier <scratch>/<wave>-dossiers --write
   ```

4. **Round 2:** the same `quality-v2-<id>` signs as analyst and `factual-v2-<id>` as
   adversarial Romanian-web verifier for every ID, now bound to the native dossiers.
   They work independently, with both signatures present before either sees the other's
   verdict. Their separate JSON files use the portable contract in
   [ADR-0104](adr/0104-portable-independent-review-artifacts.md): exact shared `input_ids`,
   distinct reviewer IDs, and one dossier-bound judgment per ID. Build the version-2 files,
   then apply only the fresh, complete batch:

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

5. Complete the **class P cascade**, using CONTENT_LOOP.md 4b–4i. Start with the pack
   gates and ranking/derived refresh:

   ```bash
   go -C go-backend run ./cmd/cat-content validate-fixture --root ..
   go -C go-backend run ./cmd/cat-content validate-pack --root ..
   go -C go-backend run ./cmd/cat-content-ops rank --root .. --write
   go -C go-backend run ./cmd/cat-content-ops derive --root .. --write
   go -C go-backend run ./cmd/cat-mobile-pack --root .. --check
   ```

   Advance the authored source (`authored-v13.json` is next after v12), regenerate quick,
   world and extensions, and obtain both independent initial reviews and fresh audit-bound
   finals for all three rails. Only exact unchanged item semantics may use `inherited: true`
   under 4d. The world audit binds current pack/ranking bytes, so its old signed audit cannot
   be retained after those bytes change. Refresh the 4f pins before the extensions proposal,
   export, capture the independent HTTP corpus, bind all three installed authorities and run
   default all --check plus every 4i gate and new-board HTTP play. No auditor or gate is weakened.

   Name the corpus `python-http-parity-v2-<id>.json.gz`, its golden block `reviewedV2<ID>()`,
   and its selection test `v2<id>_selection_test.go`. Attach the capture script's diff against
   the archived reference: exactly the three permitted lines (ROOT, reference label, output
   path). Report the captured count; any change from the previous reviewed block (1206 since
   V1.13) is `NEEDS-OWNER` with the case-list diff, never an edit to fit the expectation.

6. Prepare the separate `pins` commit and old → new packet required by
   [ADR-0210](adr/0210-curation-waves-and-staged-stock-landing.md), including `git show --stat`.
   Only moved expectations in `go-backend/internal/httpgolden/*_selection_test.go`,
   `go-backend/internal/contentops/{check_test.go,contentops_test.go}`, and (for class G)
   `go-backend/internal/contexto/content_v1_3_test.go` may change. Include the predecessor's
   selection ceiling update; do not change unrelated tests.

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


Under ADR-0212, queue each fully qualified packet UNLANDED with its exact HEAD, dependencies,
pins and gates, then continue eligible work autonomously. Claude performs the consolidated
final review when Paul stops or explicitly requests it. Landing, push and SHA-verified NAS
cleanup remain external owner operations; the loop never merges, pushes or deletes. An
unresolved waiting batch still expires after seven days and requires fresh M3–M6 before reuse;
queued evidence never authorizes a stale binding or unqualified predecessor.
