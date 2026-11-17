# ADR-0236: V5 approved DocCheck and Pilot 3 frequency repairs

Date: 2026-11-17
Status: accepted (Paul, 2026-11-17).
Decider: Paul Dobos.
Amends only the two tool applications and baseline-red disposition below under
[ADR-0235](0235-v5-real-use-fixes.md). Its other decisions remain accepted.

## Context

The unchanged canonical documentation check refused the shared checkout's ignored `.venv/lib64`
directory alias. The word installer accepted only the Pilot 2 contract and historical 50,000-row
frequency receipts, despite ADR-0235 decision 5 admitting the pinned full frequency artifact.
Both failures were reported under ADR-0235 decision 8 before changing the tools.

Independent fresh-context reviews accepted the two exact technical proposals. Paul explicitly
approved both patches on 17 November, including the decision record, checker rebuild, fresh
baseline/forms S10 checks and the five-word evidence migration. The application worktree first
fast-forwarded from `2c38ec7a95cb782995503ad1a8dc17da7c358400` to existing local main
`19ceb20e26dcfeb2ec3588b5ccabc99449a79caa`; every approved source preimage still matched.

## Decision

1. **Two exact freeze exceptions.** Paul's approval permits only DocCheck patch SHA-256
   `861eac3582c81b23a6d12c74d5a0d1dec266a93cedbb8b04a99be0ddce8db1c1` and word-installer patch
   `af59556c234f4b9b2fec1c9da71137c978afabe544fc4dcaa916166b22fc0c3b`, unchanged, plus their normal
   decision/status/inventory records. This is a scoped exception to the campaign's tool/validator
   freeze, not a broader amendment to the procedure, rubric, contract, pins, source policy or holds.
2. **DocCheck.** Inventory checks exclude only a real root `.venv` directory with exact Git-root,
   zero indexed descendants and the literal root `.gitignore` rule `.venv/`. Failed proof retains
   strict physical-source checking. Excluded entries cannot enter the inventory or satisfy its
   location or recognized source-document links, including links resolved through symlinks.
   Physical/declaration equality, source Markdown/directory alias refusals and existing link
   semantics remain. No environment directory is moved or rewritten.
3. **Frequency.** The installer admits exactly Pilot 2 and Pilot 3 with their exact contract base.
   Pilot 3 also checks ADR-0235's frequency contract fields, fixed `frequency/ro_full.txt` path,
   15,199,764-byte size and SHA-256
   `a0d0993701e251e91b9047753b6032be751217a5aaba36ed879163e020e33ded`.
   The existing `frequency.py` parser supplies the complete folded lookup row; every canonical
   field and type is bound, flags are retained, and a positive `exact` count is required. This
   authority is ADR-0235's fixed-artifact admission. The retained fetch note is not an HTTP
   source-client receipt and proves no response status or policy headers; none is fabricated.
   Historical Pilot 2 keeps its old receipt checks, parser and size limits. There is no fallback
   from active Pilot 3 to old evidence, no new whole-contract authentication, and no supported
   multiword shape; multiword admission still needs an explicit evidence schema and ruling.
4. **Baseline-red ruling and checks.** Paul authorizes these repairs and fresh unchanged-baseline
   checks with the rebuilt real-source checker, followed by genuine forms S10 closeout. The
   original failures and receipts remain history; no failure is relabeled green and no covered
   content is rejected by those failures. All five unchanged Pilot 2 word proofs intentionally
   fail the active Pilot 3 shape. They wait for the migration below rather than receiving a
   blanket null-test waiver. Required current checks, independent review and landing rules stand.
5. **Five-word migration.** Sparanghel, Oază, Cactus, Trăsnet and Dig need explicit new full-list
   source payloads and source hashes, with new factual and quality signatures and registry
   review bindings covering each current payload and frequency flags. Their equal old/full-list
   counts (198, 327, 553, 693 and 1,067) do not preserve canonical payload signatures. Original
   frozen payloads, signed receipts and critic transcripts remain immutable. Recompute schema-2
   own-views at the reviewed, current and proposed bases. Equality permits the original blind
   evidence to carry under ADR-0235 decision 7 through an explicit current-payload/own-view/
   original-evidence migration binding. Any required current-payload critic attestation records
   inherited evidence, not a new play. A disturbed own-view requires fresh blind play. Every
   changed full board view still gets the local HTTP replay required by decision 1. Tool approval
   supplies no factual, quality, child-safety or content-install approval.

## Threat model and verification

Manifest/list data cannot substitute pins or paths, hide flags or inflate typed counts; existing
regular-file, no-symlink and bounded-read checks remain. Git metadata and executable identity must
be trusted and stable for DocCheck's narrow exclusion proof. Existing history/image-reference and
generated-directory semantics remain; this repair does not claim universal link coverage.

The exact approved files were applied after complete source-preimage/hash verification. Real-source
DocCheck race tests pass all 17 top-level groups with zero skipped or failed events. Existing and
new installer tests pass 20/20, and existing frequency tests pass 8/8 using the shared Python 3.12
reference interpreter and actual feature source imports. Native CLI vet, Linux/amd64,
Darwin/arm64 and Windows/amd64 builds use existing Go 1.27.3 with downloads disabled.

Focused commands from the feature worktree, using owned scratch for `GOCACHE`, `GOTMPDIR` and
`CAT_V5_TEST_SCRATCH`, existing `/usr/local/go/bin/go`, `GOTOOLCHAIN=local`, `GOPROXY=off` and
`GOSUMDB=off`:

```text
go -C go-backend test -mod=readonly -count=1 -race -json ./internal/doccheck
go -C go-backend vet -mod=readonly ./internal/doccheck ./cmd/cat-doc-check
<shared Python 3.12> -I -m unittest discover -s scripts/content_v5/tests -p 'test_link_install*.py' -v
<shared Python 3.12> -I -m unittest discover -s scripts/content_v5/tests -p test_frequency.py -v
CGO_ENABLED=0 GOOS=<linux|darwin|windows> GOARCH=<amd64|arm64> go -C go-backend build -mod=readonly -buildvcs=false -trimpath -o <owned-target-path> ./cmd/cat-doc-check
<rebuilt checker> --root <feature> --inventory docs/tracked-markdown.json
git diff --check
```

The portable pairs above are Linux/amd64, Darwin/arm64 and Windows/amd64. The existing
`tools/gui-bootstrap-webkit/lint/check_docs.py` `tracked_markdown` operator regenerated all
695 declared paths after indexing this ADR. Feature DocCheck reports 71 active files with empty
finding/budget arrays; whitespace passes. Current
documentation/whitespace results and unfinished S10/migration status are recorded in
[STATUS](../STATUS.md). Gameplay, session TTLs and size bounds are unchanged.
