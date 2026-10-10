# ADR-0189 — Behaviour-bound installed content authorities

Status: Accepted (2026-10-11). Supersedes the acceptance rule of [ADR-0166](0166-native-content-operators-and-builder-rails.md) only where it required runtime-manifest equality; ADR-0166's rails, review schema and pin chain stay in force.

## Context

Installed content authorities (go-backend/internal/contentrails) bind each installed rail artifact to its candidate, two independent reviews, proposal, native audit and two final reviews. Until now `ConfirmFinal` also required the audit's `runtime_sources` — sha256 of every non-test Go file, go.mod/go.sum and bundled data under go-backend and shared-go/authcore — to equal the current tree. A GUI loop lands Go changes to main every few hours, so the rail check and `TestAllFourBaselineArtifactsRebuiltFromAuthoredInputsExactBytes` have been red since 5baf581 although no audited behaviour changed: re-running the three installed audits under the current binary reproduces the signed documents byte for byte except `runtime_sources`, and the stored source bindings equal the current fixtures. The content loop ([ADR-0188](0188-park-v1-7-and-reset-content-loop.md)) cannot install while this rule stands, and every runtime commit would re-break it. Separately, contentbuild/source6_build_test.go pinned the live bundle length and digests as literals with no generator, so any content install turned it red.

## Decision

1. An installed rail is accepted when its reviewed documents verify and a fresh native audit, run under the current binary at check time, equals the signed audit except for runtime provenance. `ConfirmFinal` re-runs `Audit` for the rail and compares the two documents minus `runtime_sources` and minus the three installed-artifact digests inside `source_bindings`. The artifact bytes stay bound by the explicit pin (artifact_sha256 == sha256 of the installed fixture == catalog_sha256 in the audit and both finals).
2. `runtime_sources` is recorded provenance, not an acceptance criterion. Every audit still records it, must present it in well-formed shape (a non-empty list of `{path, sha256}` rows), and `Audit` still refuses if the tree changes while it runs. The install transaction still locks every runtime file in its guarded readset.
3. Audit document schema is unchanged (`native_audit_version` 1). The V1.6 installed audits, finals, installed-authorities.json and its pin are reused unchanged; main goes green with no regenerated reviews.
4. The live bundle test keeps only generator-backed equalities (Build == installed bundle, digest.go == PinBytes, source files == bundle sources == reviewedPins, installed artifacts == authority pins). The V1.5→V1.6 two-alias delta becomes a historical test over an archived copy of the V1.6 bundle (docs/reviews/v1-6-everyday-inputs/reference/historical-source6-bundle.json.gz).
5. The content loop no longer freezes the runtime: step 4h reuses the 4e audit and finals and only re-audits when `--installed-authority-out` refuses after export.

## Preserved boundaries

- Red when an installed artifact differs from its reviewed proposal or pin (byte-exact proposal, pin and fixture checks; `Check` compares rebuilt and installed bytes).
- Red when the audited behaviour under the current binary differs from the signed audit (replays, results, catalog and candidate digests, kg/derived/rankings/reserve/pack/rubric bindings).
- Red when reviews, finals, source chain, pin or any registered document is missing, tampered, symlinked or signed by non-independent reviewers.
- Green when Go changes leave the audited behaviour identical. Behaviour the three audits do not observe (SPA, kit sync, auth, other games) is out of their scope and is covered by their own gates.
- The pin .go file remains metadata-only and excluded from provenance; `reviewedPins` in contentbuild stays the deliberate reviewed-pin step at install time.

## Cost and residual reds

`ConfirmFinal` now runs a real audit per rail (quick about 1–2 s, world about 10–18 s, extensions about 1 s): `cat-content-rail all --root .. --check` takes about 40 s including compile and the contentrails package test runs synthetic quick audits on every `ConfirmFinal`/`rebuild` call. The quick and world audits read the embedded bundle, and the loop's 4e audits run before the 4f export; if an export changes what the replays observe, 4h refuses correctly and the wave re-audits and re-signs. In Go tests a source edit cannot change the compiled binary, so "behaviour-neutral Go edit stays green" is proven by construction and behaviour changes are proven through audit tampering; a real runtime regression is caught by the real-root baseline test and the rail check on main.
