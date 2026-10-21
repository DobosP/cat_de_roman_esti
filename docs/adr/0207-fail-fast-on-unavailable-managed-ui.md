# ADR-0207: cat-server refuses to serve an unavailable managed UI

Date: 2026-10-21
Status: accepted (review follow-up DCR-1; landing under [ADR-0206](0206-owner-authorized-main-publication.md)'s authorization)
Authority: [main publication review](../reviews/gui-main-publication/README.md) DCR-1 (medium).

## Context

`httpapi.New` admits the embedded managed UI once at startup (`newManagedSPA`). On any admission
error (an unbounded `CAT_UI`, an invalid `CAT_CSP_ENFORCE`, a malformed current or frozen tree, or
the unbuilt `.keep` scaffold) every page answers `503 {"detail":"Managed UI unavailable"}` while
`/healthz` keeps answering 200. The container healthcheck probes `/healthz`, so a misconfigured
deployment looked healthy and served nothing: a silent site-wide outage.

## Decision

In serving mode `cat-server` exits non-zero before it opens a database pool or a listener when
`(*httpapi.Server).ManagedUIError()` is non-nil, logging `managed UI unavailable: <cause>`.
`ManagedUIError` reports the admission error only while managed delivery is active; an explicit
`StaticRoot` override (`cat-qualify` only) replaces managed delivery and reports none.

`-replay` keeps running without a managed UI: the frozen HTTP parity corpora are API-only, and the
standalone CI/toolchain replays build `cat-server` without synced assets. The in-handler 503 for
an unadmitted UI and every existing managed-delivery test stay unchanged; `/healthz` semantics stay
unchanged.

## Consequences

A bad `CAT_UI`/`CAT_CSP_ENFORCE` or a broken embedded tree is now a crash loop at deploy time, not a
healthy-looking outage. The owning gate `build`/`unit`/`full` lanes, `./run.sh` (it serves the gate
build's binary) and the canonical Dockerfile sync the managed assets before compiling, so none of them
changes. The gate's `baseline` and plain `gen` lanes compile against whatever `embedfs/` already holds
(each gate start resets `embedfs/legacy` to its scaffold), so a current build there already failed
admission and served 503 pages; it now stops at server start. Pre-existing: the
manual `native-go-browser` CI job and the unqualified `scripts/qualify_go_toolchain.sh` serve a
binary compiled before any asset sync; their page journeys could not pass before this change (every
page was 503) and now fail at server start instead. Tests: `go-backend/cmd/cat-server/managed_ui_test.go`
(re-executes the test binary as `cat-server`; fails on the unfixed binary) and
`internal/httpapi/managed_ui_error_test.go`.
