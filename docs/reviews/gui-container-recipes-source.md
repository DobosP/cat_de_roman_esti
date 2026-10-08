Valid until: parent integration and actual container qualification — then treat as history.

# Container recipe source reconciliation

Source proposal, 2026-10-08, based on `9a2b84ca4ac8126dc719660e44713c455041553c`.
No images, tests, compilers, dependencies, runtime or deployment were executed.
This record supplies no image identity, green gate or production authorization.

The root and standalone Go recipes now reuse the existing GUI recipe's
Node 26.10.0/npm 12.2.0 frontend and Go 1.27.1 build pipeline. They run the actual
strict native compiler/build/budget command, sync fresh managed assets plus the
sealed legacy input, and generate SHA/tree/manifest/lock identity before compiling
the native server. Caller-supplied `GATE_SHA`/`GATE_TREE_SHA256` are mandatory;
there are no fabricated defaults or runtime metadata substitutes.

Root runtime compatibility remains port 8000/PORT, shell-expanded listener,
`cat-server` on PATH, curl health checks, UID/GID10001 and the private submissions
directory. Existing compose migration command arguments remain valid. Standalone
Go retains port8080 and its binary entrypoint. Both keep the existing native
accounts-off default and preserve their Bookworm runtime flavour; image digests and the apt closure
remain unqualified until the parent supplies actual registry evidence.

The optional Python3.12 and Rust1.98.1 recipes retain those interpreters and their
filesystem SPA serving boundary. Their selected frontend stage uses real `npm ci`
and managed `frontend/dist`; that fresh tree is copied into the reference runtime's
`cat_de_roman_esti/web/static`. Python constraints and the locked Rust build remain.
No reference server is selected as the default or given a consent/privacy waiver.

The shared Docker context now includes only the actual root asset-sync helper,
keeps frontend build/config/confinement helpers available through `COPY frontend/`,
and excludes host generated dist/identity/legacy trees. The source-owned sealed
`legacy/` archive remains a required input. The unchanged GUI recipe benefits from
the same context correction; its runtime/port/health contract is not modified here.

Parent integration requirements:

- Resolve and register actual image digests for `node:26.10.0-bookworm-slim`,
  `golang:1.27.1-bookworm`, `debian:bookworm-slim`, `python:3.12-slim` and
  `rust:1.98.1-bookworm`; these five tag identities deliberately remain unresolved.
  Do not infer a digest, upgrade an interpreter, waive recipe discovery or claim
  a complete image gate from these source changes.
- Wire actual SHA/tree build arguments into the existing root/standalone build
  callers. Current run.sh/compose/CI commands do not yet supply them; image builds
  must fail closed until that owner integration is complete.
- Run actual source, context/COPY, clean native and optional reference image
  qualification. Preserve existing ports, migrations, volume ownership, health,
  managed/current/legacy byte identities, strict budgets and all safety gates.
- Reconcile this record into current STATUS and the living plan, and regenerate
  the source-owned tracked-Markdown inventory through its actual owning path.
  This branch's STATUS was already at its120-line budget and is not overwritten.

The parent owns exact image resolution, gates, review, landing and deployment
decisions. Worker source commits remain local, unmerged and preserved.
