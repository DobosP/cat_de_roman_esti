# V4 registry notes and landing lessons

## Milestone 0 seed

registry.jsonl is an append-only journal of full candidate snapshots with schema
cat-content-candidate-1. A create row introduces an ID. A transition row carries the
same ID, the updated snapshot and previous_sha256, the SHA-256 of the previous canonical
JSON row without its newline. The check command validates and counts the derived view.
Transitions preserve the prior provenance prefix. Releasing a parked, already-served or
recorded-held item returns it to idea. Pass the orchestrator-controlled receipt directory
as the evidence root to check or view. The transition’s retry_evidence binds the prior
retry_when as prerequisite, a relative ref in file:line form and the receipt file’s
sha256. The referenced JSON line must carry candidate_id, prerequisite, previous_sha256
and verdict set to resolved. Owner-answer and permanent holds stay locked in Milestone 0.
The view command emits one current row per ID and optionally filters by state. Candidate
evidence, review and installation gates live in the [V4 procedure](../CONTENT_LOOP.md).

Regenerate into a new directory from the repository root with Python 3.9 or newer and Git.
The converter reads committed inputs from the pinned V3 retirement baseline.

~~~sh
python3 -I scripts/content_registry.py seed --repo . --seed /path/to/v3-seed --output /path/to/new-output
python3 -I scripts/content_registry.py check docs/content-registry/registry.jsonl
~~~

| Input scope | Rows |
| --- | ---: |
| V3 bulk-001 | 1,761 |
| Tracked candidate pools | 516 |
| Held V2 proposals | 40 |
| Identified V3 drawing-board and ledger items | 37 |
| Distinct fixture controls and rejection tombstones | 329 |
| Total input and output | 2,683 |

The 1,741 bulk canonical stock IDs cross-check against 1,364 archived inventory rows
and 377 archived pool rows from V1.33–V1.42. Each ID retains one bulk record with both
references. Scope-qualified IDs keep distinct historical records distinguishable.
Source paths, hashes and pointers bind provenance metadata. Capture bodies and their
independent review status remain separate. All imported provenance has the legacy role.

The 75 Conexiuni demotions and four direct pack reserves give 79 distinct protected
IDs. The quick-game reserves share source cx_geografie_028, already demoted.
Eight source-scoped lexical rows reflect the standing owner rules. A separate list of
landed lexical declarations retains their exact literals and lines for screening.
Those declarations can represent superseded or sense-scoped history. Screen current
compatibility and approval independently. The ten ADR-0210 curation families retain their
62 proposed input strings, landed literal references and exact owner-decision prerequisite.

The retained seed has 499 bound N5 selection IDs and aggregate historical status counts.
Where an exact disposition is unavailable, those rows wait for a fresh screen and
source reconciliation. Etichetă and Pungă retain their exact ledger source-proof prerequisite.
Twenty-nine V1.33 active rows wait for fresh source evidence. The N3, N6 and N8 batch
summaries retain archive references for
unavailable unenumerated items. No archive restore or qualification occurs during seed.

### Threat model

The orchestrator owns the output and the owner log. The converter pins the committed
input tree, verifies SHA-256 for the V3 inputs it reads, parses declarations through the
AST, and reads only the named files. It treats embedded file paths, URLs and verdicts as
historical data. It checks seed cardinality and locked board membership, rejects duplicate
journal keys and IDs, and verifies predecessor digests during replay. The journal can
detect structural tampering, stale transitions and attempted owner-hold changes.
Only the orchestrator supplies the trusted receipt root and adjudicates receipt claims.
Reviewers still verify input identity, authorization and the native gates. The tool
provides no writer authentication or concurrent writer coordination.

## Landings

Append each cohort’s observed gate and gameplay lessons here with exact evidence
references.
