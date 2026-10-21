# ADR-0206: Owner-authorized publication of local main

Date: 2026-10-21
Status: accepted (Paul's explicit 2026-10-21 authorization)
Authority: Paul, 2026-10-21: "This is my explicit authorization for Cat/Social main landing and main
pushes after green qualification and independent review. It supersedes older 'wait for Paul' restrictions
for those operations only. It does not authorize deployment, real-account/child activation,
provider/government connections, or content, clinical and privacy policy decisions."

## Decision

Publish local `main` `fb829aaa` (GUI S1 M1–M4 on core-v1.11 plus reviewed content V1.8–V1.13) to
`origin/main` as a fast-forward from `3d602215`, by an explicit `git push origin main`. The qualified
product is `16733891` (unit27/full38/image2, [qualification](../reviews/gui-m4/qualification.json));
`fb829aaa` adds documentation only, so no product gate is repeated under [ADR-0200](0200-bound-gate-evidence-reuse.md).

## Context / why

A fresh independent five-dimension review with refutation passes and a final adjudication found no
publication blocker ([record](../reviews/gui-main-publication/README.md)). Browser storage keys equal
production `abe93377`; content equals the reviewed V1.13 tip; all six M4 evidence archives match
their recorded hashes.

## Consequences

Deployment, production CSP enforcement, real-account/child activation, provider/government
connections and content, clinical or privacy policy decisions remain outside this authorization.
`codex/content-v1-7` stays parked and unpublished. The review's follow-ups are listed in the record and STATUS.
