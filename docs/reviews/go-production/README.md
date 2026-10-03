# Go production rollout

Valid until: the deployed image/profile or public contract changes — then requalify.

Owner-selected Go production is [ADR-0162](../../adr/0162-select-go-production-backend.md).
The release `ca61b5d34236` is deployed at <https://cat-de-roman-esti.dobolabs.ro>.
[GitHub CI](https://github.com/DobosP/cat_de_roman_esti/actions/runs/37150262141) passed
before the main fast-forward and publication. Current truth: [STATUS](../../STATUS.md).

Both the exact candidate and public Go release pass **151 HTTP smoke requests**:
six games completed, exploration checkpoint crafted/restored, 28 assets checked
byte-for-byte including HEAD/cache/ETag, manifest/categories, legal configuration,
anonymous feature refusals, missing APIs and request-size limits. The app is healthy
with zero restarts, runs as UID10001 on a read-only filesystem and executes only
`cat-server`. No Python interpreter, ASGI module or Python application source exists
in the image. Caddy, TLS/config volumes and account/submission flags are preserved.

The final Go image was built from the public committed source while Python kept
serving; only `app` was recreated with `--no-deps --no-build`. The original known-good
Python image/profile remains available for rollback. Existing in-memory live games
expire across replacement, while validated exploration/browser progress remains.

A post-smoke snapshot shows the Go app at 46.87 MiB versus the prior Python snapshot
105.6 MiB, and its image at 156 MB versus 397 MB. These snapshots are not capacity or
billing predictions; controlled workload measurements are in the prior native receipt.

Detailed aggregate [verification](verification.json), [candidate smoke](candidate-smoke.json)
and [public smoke](public-smoke.json) record no secret values or real-player data.
`scripts/smoke_go_release.py` is an external test client, not a Python server. Public
Caddy rejects oversized bodies with 413 before Go, so that specific edge response is
accepted without the Go runtime header; all other tested responses require it.

Production serving is entirely Go. Python content authoring/validation, the
reference oracle and dormant account implementation remain outside the deployed
runtime. Rust is retained research. No accounts, other apps or new infrastructure
were activated. Physical devices and Safari/WebKit remain unqualified.
