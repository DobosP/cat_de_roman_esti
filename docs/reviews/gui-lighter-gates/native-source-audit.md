# Native reuse source audit

Valid until: any native audit-signature input changes; then reuse is disabled.
Date: 2026-10-13. Source audited at e82e5562; no game content changed.
Reviewers: independent Codex agents `full_reuse_builder` and `gate_design_review`.

The latter independently recomputed all 238 regular `.go`, `go.mod` and `go.sum`
files under `go-backend/` and `shared-go/`, including tests and vendored sources.
Each sorted record is `{path,mode,sha256}`, with POSIX relative path, mode masked
by 0777 and file SHA-256. Compact UTF-8 JSON array SHA-256:
`047f3f53f1131820bbc5ef04f7d7eb64f74fe05812a1b9b0f40d660465d54e06`.

Only `internal/contentrails` receives a source-based exception. Its sole HTTP
constructor use is `quick.go:161`; requests at 179/192/221/241 exercise creation,
resume, winning actions and terminal resume for Intrusul/Perechi JSON APIs.
No document, asset, font, manifest or GUI-identity route is requested. HTTP server
initialization separates managed UI/build identity from native game services.
The fresh whole HTTP suite asserts API availability even when UI assets refuse.

Keep the dynamic embed dependency closure for all other packages, plus fresh
whole httpapi, httpgolden, guibuild, cat-server, browserplan, content and doccheck.
PostgreSQL and no-test packages remain fresh. Original race logs must prove every
cached test's run/pass; reused rows remain historical, never synthetic new runs.

The input key includes all Markdown, four frontend release/fixture reads and all
other native/data inputs. Generated assets matching native provenance readers
(`.go`, module files, Unicode/provenance/bundled JSON or contentrails source JSON)
also enter the key. A changed native signature disables cross-SHA reuse until
another audit; a passing new baseline alone cannot extend this exception.

Observed cold unit: 27 checks pass, result SHA-256
`8bfb2a36f293ca571b69ffe1262f284033a8b391930c097844f01a75d4fa6e71`.
Contentrails took 1,123.73 seconds of its 19.95-minute run. Qualified warm unit later took5.42minutes; see qualification.json.
This audit establishes the E10 source/data boundary, not compiler-input equality.

Successor audit (core-v1.10 adoption): all238 inputs re-audited independently.
Only go-backend/go.mod selects core-v1.10; all41 vendored Go files are identical.
Approved replacement pin: `6eb3a47f4fb5d7445dc916c01a47d1db6e627c4ea39752ab16a30e1c63946b3c`.
[Exact source-only re-audit](../gui-core-v110-adoption/native-audit.json); new unit/full still required.
