# ADR-0162 — Select Go for the production anonymous arcade

Date: 2026-10-03
Status: accepted

## Decision and authorization

The owner chose Go as the final server language and explicitly requested completing
the replacement, merging to main and deploying the existing Cât de român ești? site.
Go is the canonical backend for local launch, browser qualification and the anonymous
production image. This supersedes ADR-0161's runtime selection being deferred.

The six games, native fallback computation, exploration/restores, metadata, legal
pages and SPA/static responses execute in Go. The production container includes no
Python interpreter, Python application package, pip, Django/uvicorn or Rust runtime.
The optional Go-to-Python gateway is removed, so unknown API routes are native 404s.
Node builds the frontend; Go builds the server; neither compiler belongs in runtime.

The existing deployed site remains anonymous: accounts/OAuth and submissions stay
disabled, with no database or new persistence. Python content validators, authoring
tools and the differential oracle remain development/build tools. The dormant Python
accounts reference is explicit and is not the selected release. Rust remains a
comparative research implementation outside required production CI.

## Deployment and invariants

Keep the current anonymous Compose project and Caddy routes/volumes. The Go app uses
internal port 8000, matching Caddy's existing upstream. Remove obsolete Python/live
source variables from the Go environment; the embedded reviewed export is the source.
Pass only the existing anonymous legal/donation, session and request-budget settings.
Use the established bounded in-memory stores; restarts discard live sessions, and
future replicas still need affinity or shared transactional state.

Validate canonical Docker build/runtime, nonroot process, no Python executables,
HTTP/site contracts, all game journeys and actual anonymous configuration before
switching traffic. Preserve the exact running Python image as rollback before any
replacement; build the Go candidate while the old app serves. Recreate only app,
leaving Caddy and its certificates/volumes running. Roll back the app image/profile
if health, content, legal, static or gameplay checks fail.

The user-authorized rollout includes publishing the verified main revision. The
shared checkout stays on main and clean; task work lands only after green checks.
Record the release/CI/image and public post-deploy proofs in STATUS/WORKLOG, then
perform verified-merged task cleanup. Deployment authorizes no account activation,
other-repository migration, new hosting purchase or unrelated infrastructure change.

## Verification and operational identity

Preserve the API JSON bodies and reviewed artifact pins. Go responses identify the
implementation with the operational `X-Cat-Runtime: go` header, without adding
implementation details to game UI or changing the manifest. Runtime selection does
not change puzzle content or approve new material. Commands and proof records are
in [DEPLOY](../DEPLOY.md), [NATIVE_BACKENDS](../NATIVE_BACKENDS.md) and [STATUS](../STATUS.md).
