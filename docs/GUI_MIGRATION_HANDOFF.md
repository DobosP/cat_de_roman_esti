# GUI migration — feature branch handover

Valid until: the next source or completed gate change. Updated 2026-10-10. Older source-bound results remain in linked proof files and WORKLOG.

Cat is still an unfinished migration: React19/Motion and UI0.3 are active; Core-v1.6 is released and UI1.0.6 staged. Implementation source `8957b55d05f26f15509bd3bd2cf1399c5d27af1e` adds the generated legacy shell. Its code now has actual build/focused validation at `7cf0704`; parent proof/docs follow that commit. Use `git rev-parse HEAD` and clean status for the literal next run. Publish only the origin feature branch `fix/gui-cat-prerequisites-linux`; no main merge or deploy. Recheck remote state before publication or another-device continuation.

## Latest completed run

[Full714 review](reviews/gui-normalized-react/full-714-review.json) and [actual result](reviews/gui-normalized-react/full-714-result.json) bind source `714c0664be4592ef452ca2934a491a672b557eef`, tree `52853424ab97036865934f55fe65f8f9eb6c25a370056ead84567fe2ab873521`, and image `sha256:80b3cffe8eed8bb01db2165b12c6d01ca3e76b9fe1095550599e9741bf197e55`. The wrapper finished with exit201:35 recorded checks passed; route budgets and their aggregate failed. Do not poll the finished51131 session.

- All453 frontend tests, lint and types passed. Oxlint reported41 warnings and no errors.
- All900 browser identities ran once,450 per project, with zero fail/retry/skip/flaky/global errors. Original16 fixtures/78 assertions per project remain exact.
- Backend1382 pass actions and17 explicit baseline PG skips;19 packages used cache, as did authcore28. Explicit PG12accounts+276httpapi were fresh and had no skips. Native/Django1207 parity passed.
- Actual image assets and fonts, nine active report-only CSP documents, Home/axe and nine exact PNGs passed. [All16 baseline outcomes](reviews/gui-normalized-react/full-714-baseline-comparisons.json) passed. A [separate count erratum](reviews/gui-normalized-react/full-714-baseline-count-erratum.json) corrects an earlier metadata label without altering the sealed run.
- Controlled desktop medians: Conexiuni LCP2836→1876ms and INP184→48ms; Alchimie challenges LCP4228→1860ms and INP200→48ms. These are real measurements, not Samsung evidence, a causal attribution or proof of optimal performance.

The required legacy journey did not execute. Its literal `legacy_violations:0` was a default, not a measurement. Therefore E3's budget-only-red preliminary acceptance and CSP stage B remain withheld. Passing recorded checks cannot qualify an omitted obligation.

## Next concrete work

[Legacy8957 source review](reviews/gui-normalized-react/legacy-8957-source-review.json) and [intentional transitions](reviews/gui-normalized-react/legacy-8957-reconciliation.json) bind six paths. Legacy HTML now comes from its selected manifest through public SDK asset tags, the real request nonce and four owned font preloads. Frozen30 files and current renderer remain unchanged. Two old raw-serving expectations are explicitly replaced by generated-shell/policy assertions; archive/raw-asset and current-mode controls stay. All19 serving roots/87 actions, including those five new roots and compiled current/legacy, passed in the actual7cf build with race/count1 and no failure/skip/cache. [Build proof](reviews/gui-normalized-react/build-7cf-review.json).

1. Supported build7cf now passed13checks, six-path formatting and exact19 roots/87 native actions after genuine current/frozen assets and identity/binary production. Three fresh139-source audits and genuine same-actor factual/quality finals are promoted in [Source6 evidence](reviews/gui-source6-legacy-runtime/promotion-ledger.json). Apply only the exact review descriptors/pin through the existing native authority API, then rebuild/verify. All eight corpus inputs remain unchanged; no new1207 corpus or Source7 work.
2. Finish the actual legacy image lifecycle/probe integration. Existing core16 has a public consumer result hook, but no automatic second-process provisioning. Parent is reviewing an owner-coordinated same-full mechanism: separate strictly owned container of the actual immutable app image, real legacy startup flag, managed browser observation and verified cleanup. It must fail when unavailable and report the actual advisory legacy count. No fake identity endpoint or backfill of714's zero.
3. After focused passes and all Cat writers idle, use genuine same-clean-SHA owner sync/trust and complete full validation. E3 permits budget-only-red preliminary evidence only after every other mandatory check actually passes. Then apply the reviewed one-line CSP stage-B change and validate it. No empty sync commit or duplicate backend-wide unit.

Source6's [previous fresh authority and reconstruction](reviews/gui-source6-brotli-direct-runtime/native-confirmation-review.json) remains historical proof: allfour exact/semantic rails, validate/export and two fresh race tests including1207 passed at5efa. New legacy runtime bytes need their own freshness checks. Existing original corpora, all25 Source1–6 archives, failed receipts and canonical releases stay immutable.

[Compression5896](reviews/gui-normalized-react/compression-5896-targeted-review.json) earned managed build11, Node30, native4families/24subcases and eight real identity/gzip/Brotli HTTP checks. [Owner-approved vitals policy](adr/0190-owner-approved-vitals-regression-criterion.md) allows improvements with unchanged max(10%,50ms) slowdown limits;43 focused controls passed. Neither historical targeted proof alone qualifies the current full image.

[Startup accounting](reviews/gui-normalized-react/startup-accounting-clarification.json) distinguishes methods: historical level9 JS115016+CSS7727=122743 bytes against configured122880; public route level6 HomeJS115181 is different. Four mandatory fonts total167632 raw bytes and are separately inventoried. All20 configured route-JS rows remain red. Paul's estimate is a planning target; no invented replacement ceiling, hidden root/font exclusion or blanket waiver applies.

## Remaining migration and parallel lanes

Formal M0/M1/KIT_BUMP, enforced-CSP qualification, positive managed build/run/HMR launchers and actual Samsung Chrome plus Samsung Internet under throttled4G are still pending. M2 native Preact/UI1 and later Cat milestones remain dependent on their real prerequisites. S0b/templ and production activation remain closed. Safety, privacy, content, focus/touch, Presence, exact routes and template arms remain mandatory.

Teacher and Social independent implementation now proceeds in parallel on `feat/gui-app-migration-a`. Teacher has33 actual native original pages, strict codec/SDK replay and verified automatic container cleanup; its PWA script externalization is in source work. Social has14 original native pages, SDK normalization and63 passing filesystem-renderer checks; external-script nonce binding is in source work. These are bounded sections, not completed migrations. At most two product runtime jobs run concurrently; no writer touches its tested worktree. Formal adoption and release dependencies remain.

## Retention and pickup

Read AGENTS, [STATUS](STATUS.md), the [S1 plan](../.agent/S1.md) and exact latest proofs. Parent owns protected config, sync/trust, review and feature publication; workers commit locally only. Do not resume an old gate, use an old receipt for a new SHA or infer remote freshness.

[Cleanup](reviews/gui-normalized-react/experiment-storage-cleanup.json) removed159 superseded experiment copies, reducing parent scratch133.7→5.6GB at that checkpoint. Keep one rolling verified setup and compact results. The retained591c setup supplies explicitly verified unchanged references; new results retain genuine changed outputs and controls. The714 capture adds about88MB of unique evidence, not another workspace/dependency copy. Check disk usage before large runs. Historical pruned raw paths are deliberately absent; a manifest is history, not those deleted bytes. Preserve original baselines, canonical releases, unmerged branches/worktrees/source packets and other owners' work.
