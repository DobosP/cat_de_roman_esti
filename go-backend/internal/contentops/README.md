# Native offline content operators

`cmd/cat-content-ops` operates on a local repository source root. It does not call a
provider, fetch a citation, publish content, or change an active server. Production
accounts and submissions stay gated off. [The content rubric](../../../docs/CRITIQUE_RUBRIC.md)
and [pack-wave guide](../../../docs/PACK_ONLY_CONTENT_WAVES.md) define the review policy.

Build from the repository root with the qualified Go SDK:

```sh
go -C go-backend build -o "$TASK_SCRATCH/cat-content-ops" ./cmd/cat-content-ops
"$TASK_SCRATCH/cat-content-ops" critique --root "$REPO_ROOT" --status pending --ids cx_literatura_901 --check
```

The command is first; all flags follow it. `--root` is the repository root, not the
`go-backend` directory. Artifact and queue paths resolve against the process working
directory. Every command is read only by default. `--check` states that explicitly;
`--write` authorizes local writes. The two flags are mutually exclusive. Scratch belongs
in the task's `_temp` directory. No operation creates a public solution endpoint.

| Retained Python operator | Native command and principal flags |
| --- | --- |
| `import_candidates.py --pack-only` | `import-candidates --dir WAVE --pack-only` |
| `critique_pack.py` | `critique --ids ID,ID --status pending --game GAME --strict --dossier DIR` |
| `build_review_artifact.py` | `build-review --analyst FILE --verifier FILE --dossiers DIR --out NEW_DIR` |
| `apply_rereview.py` | `apply-review --dir REVIEW_DIR` |
| `audit_alchimie_projections.py` | `audit-projections --ids SORTED_IDS --dossier DIR --out FILE` |
| Graph/pack and native sidecar validation | `check` (always read only) |
| `rank_games_pack.py` | `rank` |
| `build_derived_catalog_v38.py` | `derive` |
| `report_content_delta.py` | `delta --baseline COMMIT --text` (omit `--text` for JSON) |
| `review_submissions.py list` | `submissions list --dir QUEUE_DIR` |
| `review_submissions.py promote` | `submissions stage --dir QUEUE_DIR --ids IDS`, independent review, then `submissions promote --dir QUEUE_DIR --ids IDS --reviews REVIEW_DIR` |
| `review_submissions.py reject` | `submissions reject --dir QUEUE_DIR --ids IDS`; staged stock requires a bound `apply-review` rejection |

Use `--write` with import, dossier output, review assembly, projection audit, apply,
sidecar refresh, or queue changes. Read-only import/apply runs the same prospective
gates. `critique` without `--ids` selects the exact requested game/status inventory;
unknown or excluded explicit IDs fail. Approved-stock critique reports evidence and
never changes statuses. A strict `FAIL` blocks promotion.

`rank --check` independently recomputes every ranking row and compares complete JSON
meaning against both tracked copies. `derive --check` independently regenerates the
frozen V38 source set, checks 800/9164 raw derivation counts, applies the historical
label-identity correction and diversity cap, and compares the 336 resulting boards.
Both report harmless formatting differences separately; they do not rewrite them
without `--write`. A pack refresh never widens the frozen derived source set.

`check --root ROOT` validates the graph and pack with the native prospective
validators, recomputes every ranking and derived row, and verifies source snapshots,
runtime inventory and both fixture mirrors. The native sidecar formatter sorts JSON
object keys and preserves array order. A `format_drift` refusal identifies the native
`rank --write` or `derive --write` command needed to refresh both copies. `check --write`
is rejected before any source access. Graph and pack retain their supported transaction
formats. Sealed export validation and current-authority checks remain separate gates.

## Native review source transition

The portable raw reviewer and final batch formats remain version 2. Native dossiers
carry `review_source_version: native-contentops-v1`. Their `record_sha256`, normalized
KG and rubric digests, deterministic findings and judge-visible evidence are bound
alongside native `runtime_sources`/`generator_sources` and their canonical manifest
digests. The `review_binding` is `sha256:` plus the digest of the canonical envelope:

```json
{"version":1,"rubric_sha256":"HEX64","dossier":{"review_source_version":"native-contentops-v1","id":"cx_literatura_901"}}
```

That example abbreviates the dossier. The real envelope contains every dossier field
except `review_binding` and `rubric_sha256`; placeholders are not valid evidence.
Changing a record, KG, rubric, runtime, generator, dossier or projection requires fresh
review. Native application rebuilds exact-batch dossiers before touching any file.
Old Python dossiers and raw artifacts remain historical evidence. They cannot be
silently relabeled or converted into native approvals; obtain fresh native dossiers
and independent judgments for the unchanged source records.

A raw analyst file has exactly four root keys. Its items have exactly the six keys
shown below. The verifier has the same shape, `role: verifier`, a distinct reviewer ID,
and at least one valid HTTP(S) source per item. Explicit citation ports must be in
1..65535. Citations are recorded evidence; this command does not perform web checks.

```json
{
 "reviewer":"synthetic-analyst",
 "role":"analyst",
 "input_ids":["cx_literatura_901"],
 "items":[{
  "id":"cx_literatura_901",
  "game":"conexiuni",
  "verdict":"keep",
  "review_binding":"sha256:EXACT_DOSSIER_HEX64",
  "rationale":"Synthetic fixture judgment; replace with independently authored evidence.",
  "sources":[]
 }]
}
```

Every requested ID occurs exactly once in both files, in the same `input_ids` order.
Verdicts are `promote`, `reject`, or `keep`: promotion requires unanimity, either reject
wins, and any other disagreement stays pending. The assembler archives the original
review bytes in `reviews/`, their hashes and reviewer identities in `provenance`, all
bound dossiers, complete per-item coverage and the per-game verdict files. Application
reconstructs the artifacts from those archived judgments and refuses hand-edited,
partial, stale, mixed or non-unanimous promotions. The output directory must be empty.

Alchimie uses a sorted, separate, Alchimie-only batch. Each raw judgment adds the exact
lowercase 64-character `projection_audit_sha256` (no `sha256:` prefix). Generate the
live audit after dossier creation and supply its exact bytes to both reviewers:

```sh
cat-content-ops audit-projections --root "$REPO_ROOT" --ids al_literatura_901 --dossier "$DOSSIERS" --out "$AUDIT" --write
cat-content-ops build-review --root "$REPO_ROOT" --analyst "$ANALYST" --verifier "$VERIFIER" --dossiers "$DOSSIERS" --projection-audit "$AUDIT" --out "$NEW_REVIEW_DIR" --write
```

The audit uses the private native runtime projection, including validated reviewed
recipe extensions. It binds exact action par, displayed openings, sparse recipes and
routes, choice limits, source records, pack/KG/rubric bytes, runtime/generator manifests
and the exact dossier batch. Changed or unreproducible audit bytes fail closed.

## Candidate and submission staging

Pack-only candidates contain exactly six arrays: `nodes`, `edges`, `conexiuni`,
`contexto`, `lant`, `alchimie`. `nodes` and `edges` must be empty. Every referenced node
must already belong to the local served KG. This schematic example needs a synthetic
KG with the actual required Contexto floors before it can pass:

```json
{"nodes":[],"edges":[],"conexiuni":[],"contexto":[{"difficulty":"normal","target":"n_synthetic_target"}],"lant":[],"alchimie":[]}
```

Both `verify_factual.json` and `verify_quality.json` name `category`, their independently
identified `reviewer`, nonblank `coverage_note`, and `candidate_sha256` with the exact
`sha256:HEX64` candidate-file binding. Factual `reviewed_refs` fully covers raw refs
such as `contexto[0]`; `issues` names valid refs with `block` or `note`. Quality
`instances` fully covers the same refs with `verdict: keep|drop` and a nonblank `note`.
Unresolved `fix`, unknown/duplicate/missing refs, stale hashes or shared reviewer IDs
abort the entire batch. Fully kept instances are re-derived and validated before
staging as pending. The receipt preserves input digests, exclusions and allocated IDs.

JSONL queues are bounded and reject duplicate IDs, invalid JSON and unsafe identities.
`submissions list` shows validation errors without disclosing author data. Staging
revalidates each item and keeps the queue intact for subsequent review. Promotion
requires an unchanged staged record, unanimous bound review and an exact selected batch;
pack mirrors and queue removal happen in one transaction. Queue-only rejection retains
original entries in `submissions-rejected.jsonl` and refuses staged stock. Tombstoned
IDs, rejected queue IDs and historical numeric suffixes remain reserved.

Conexiuni rejection groups and Lanț directed rejection pairs remain durable novelty
debt. The prospective promotion census includes co-promoted, unrelated pending and
same-batch rejected records before any removal. Rejected records bind their record,
group/pair, dossier and exact gate digests. Ledger tampering or ID drift fails closed.

## Transactions and qualification

Operators capture source/read sets before planning, acquire the shared
`.cat-content-ops.lock`, recheck immutable bytes and absence under that lock, snapshot
all targets, then replace each file atomically. Final gates and unchanged-source checks
run before success. Any failure restores and byte-verifies every original, including
removing newly created transaction members. Symlinked files/parents, oversized documents,
non-finite JSON numbers and concurrent/stale baselines are refused. The public
`CaptureReadSet`/`GuardedTransaction` helper shares this lock with native content rails;
its final-gate callback must not recursively acquire it.

The package tests use synthetic imports, submissions and reviews only. They cover
negative coverage/identity/source-version/projection/citation cases, locks, exact
rollback, absent new targets, concurrent source updates, prospective rejection debt,
retired IDs, native full ranking/derived parity and the 709-approved dossier census.
Run with the task-scoped `TMPDIR`, `GOTMPDIR`, `GOCACHE`, `GOMAXPROCS=2`, `GOFLAGS=-p=2`:

```sh
go -C go-backend test -race ./internal/contentops ./cmd/cat-content-ops
go -C go-backend vet ./internal/contentops ./cmd/cat-content-ops
```
