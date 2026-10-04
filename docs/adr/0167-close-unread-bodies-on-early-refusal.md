# ADR-0167 — Bound early TCP refusals without uploading a body

Date: 2026-10-05
Status: accepted
Amends: ADR-0163's HTTP qualification; shared authentication remains unchanged.

## Decision

The coordinator supplied a confirmed cross-Go transport failure: net/http drains a small
unread body for keepalive even when the handler has already refused it. Cat's actual TCP
headers-only tests reproduced 11 size/privacy/auth/CSRF/host refusals waiting for upload.
The anonymous configured-host path also buffered before checking the host. Recorder and
body-complete replay tests could not detect either problem.

The app HTTP adapter observes body consumption without reading ahead. An error with an
unread HTTP/1 body closes connection reuse and sets its read deadline; the write deadline
and response body/status stay unchanged. Error responses precede closing a partially read
oversized chunked body. Anonymous host checks precede upload, retaining existing known-size
priority and the legitimate CORS preflight exemption. This adds no new MIME/type policy,
public endpoint, account activation or canonical shared-auth change.

Private source/operator/replay envelopes separately reject unpaired UTF-16, invalid UTF-8,
duplicate/alias-shadowed fields, unknown fields, invalid types/URIs and excessive depth.
Valid surrogate pairs and literal backslash text remain exact. A replay body can still
carry raw escaped game JSON negatives; the domain parser and frozen 32-case corpus remain
unchanged. No credential or provider was activated for tests.

## Evidence

Before the fix all 11 TCP no-upload cases timed out at two seconds (24.020-second run).
After the fix 13 actual-TCP cases pass: original refusals, the separately confirmed
anonymous host case and an oversized chunk without its terminal zero chunk. Correct
413/403/404/400 statuses, connection closure and 413 no-store hold within two seconds.
The focused race run including frozen body, synthetic ownership/consent/lifecycle, host,
CORS and size contracts passes (53.222 seconds). Rebuilt compiled parity remains exactly
1207/1207. Canonical shared-auth files/hash and frozen corpus bytes remain unchanged.
Browser cases were not repeated solely for this transport fix.

[Native qualification proof](../reviews/go-native-toolchain/README.md) and
[STATUS](../STATUS.md) record integration qualification.
