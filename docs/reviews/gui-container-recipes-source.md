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
`legacy/` archive remains a required input. This fixes the default/root and
standalone context. `Dockerfile.gui` uses its existing separate
`Dockerfile.gui.dockerignore`, which already explicitly admitted the helper;
neither that override nor the GUI recipe changes here. The original report's
GUI-context attribution was incorrect; predecessor commit `eaa5472` is preserved.

Parent integration requirements:

- At `eaa5472`, the five historical-flavour image pins were pending. The parent
  subsequently resolved/registered them in `3ea…`; this successor starts from
  `1449d4a`. That source integration does not qualify image builds or deployments.
- `run.sh docker` now validates explicit40/64-hex owner-supplied identities and
  passes quoted build arguments. Default/prod/anon compose requires both build
  arguments with no defaults; the owner supplies already validated same-source
  evidence. Existing standalone Go instructions pass the same explicit arguments.
  No tree hash producer, global `.gate.env` key or runtime identity setting is added.
- The manual CI image build still needs parent-owned explicit input/argument
  integration; application workflow files are unchanged here. Local `run`/`dev`
  paths retain their separate known managed-output/identity alignment obligations.
- Run actual source, context/COPY, clean native and optional reference image
  qualification. Preserve existing ports, migrations, volume ownership, health,
  managed/current/legacy byte identities, strict budgets and all safety gates.
- Reconcile this record into current STATUS and the living plan, and regenerate
  the source-owned tracked-Markdown inventory through its actual owning path.
  This branch's STATUS was already at its120-line budget and is not overwritten.

The parent owns exact image resolution, gates, review, landing and deployment
decisions. Worker source commits remain local, unmerged and preserved.
