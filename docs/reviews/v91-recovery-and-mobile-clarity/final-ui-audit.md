Valid until: any audited UI, focused-test, data or built asset input changes — then rerun the affected verification.

# Independent final V91 UI audit

Date: 2026-09-09. Reviewer: `v91_final_ui_audit`. Verdict: **accept within the UI scope; no blocking finding**.
This is a source and evidence audit, with representative original-detail screenshot inspection.
The auditor did not start a browser, build assets or change runtime code. Full integration
gates remain the coordinating root's responsibility and are not declared passed here.

[The audit receipt](final-ui-audit.json) records the hashes, exact checks and limits.
Its independent verifier completed on the first attempt with exit 0 and zero errors.

| Bound evidence | Independently verified result |
| --- | --- |
| Six recovery archives | 199 exact members: baseline 36, initial candidate 48, review findings 9, third candidate 40, independent final 32, final candidate 34 |
| Archive integrity | All archive SHA-256 values, unique complete member sets, member sizes/hashes and gzip mtime 0 match; decoded tar hashes are recorded |
| Baseline static | All 23 asset/manifest/HTML pins match git objects at `e2e0363` |
| Final recovery | 80 passing browser log entries, exit 0; separate 4 Back passes; 6 state captures with locked mutations, no ordinary feedback, no adopted result or local score |
| Final bindings | All 42 source/data/test/seed/static pins match current files; all 23 current static files are included |
| Independent recovery | All 39 before/after pins match current files; 4 Back results pass without retries; 2 removed-pointer cases retain null storage and played 0 with one POST and one GET |
| Mobile artifacts | All 255 raw and decoded file hashes/sizes match, including 40 gzip payloads with mtime 0 |
| Mobile focused report | 14 passed, 0 failed/flaky/skipped, one result per case and no retries; all 134 embedded attachment bodies decode |
| Root rebuild receipts | Build and bundle exit 0; raw logs match their receipt hashes; final bundle is 119.08/120 KiB |

The mobile focused evidence intentionally binds an earlier combined build. Its four shared
files (`App`, `GameShell`, `Hud`, `arcade.css`), remaining frontend inputs and installed
Toast API still match. Only the two recovery screens and 14 generated static entries
differ from that earlier binding. Final recovery pins match the current rebuilt static
files exactly. This audit does not reinterpret the earlier mobile report as a new test run
on the final build; the root's integrated browser matrix covers that boundary.

Static review found the implementation consistent with its bounded claims. The shared
layout gives notices their own normal-flow row and keeps the screen scrollable. Mobile
titles and counters wrap; measured header height positions secondary sticky controls,
with observer cleanup and a short-viewport fallback. Named HUD semantics and the
package's announcement, lifetime and dismissal behavior remain intact.

Intrusul and Perechi use the existing owner to admit only the current action, saved pointer
and response identity. Failed reads retain a bounded snapshot and a visible GET-only retry;
the original saved-pointer observation survives retries. Owned 404 clears only the matching
pointer; changed ownership offers the current round. Exit invalidation plus presence-based
layout-effect invalidation prevents departure replies from reaching score effects. Perechi
also binds queued focus to the accepted game and pointer and clears it on departure.
The focused test source checks actual committed BFF responses, failed and held responses,
cross-tab storage changes, mutation/read counts, terminal score counts and keyboard focus.

Five original-detail images were inspected: final Intrusul failed-read recovery, final
Perechi changed-pointer recovery, Alchimie 320px before/after resume, and Cald sau Rece
1280px resumed notice. They support the visible recovery message, disabled stale controls,
full wrapped header and separate notice placement. The desktop notice is present.

Historical distinctions remain explicit: paid hints and the one-hint server cap already
worked; actual unmount already suppressed score recording. Two initial Back probes did
not reproduce the later four departure failures. The red third-candidate receipt remains
red despite its unexplained exit 143; the corrected final run is a separate passing receipt.
No second-charge, post-unmount regression, physical-device acceptance or deployment claim
is made. The final authorized scope remains local V91 landing followed by stopping the loop;
this audit does not authorize V92.
