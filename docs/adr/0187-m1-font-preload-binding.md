# ADR-0187: M1 owned four-font preload binding

Date: 2026-10-09
Status: accepted implementation source — applied after parent/independent source review; Linux validation and M1/release acceptance pending

## Decision
Implement PROGRAM753 M1 font preload using only the four existing Fredoka/Inter Latin and Latin Extended WOFF2 source files. Vite owns emitted filenames. The current Go shell must require exact manifest Src-to-File bindings, four owned static-startup assets and unique head preload links with exactly rel=preload, as=font, type=font/woff2 and explicit anonymous crossorigin; insert the request nonce without rewriting raw HTML. Full must independently bind manifest sources, HTTP body bytes and genuine browser font requests/DOM nonces in separate font evidence. This is an implementation source decision, not runtime, kit, host or release authority.

## Context / why
The owning86a source has installed exact4 subsets and budget admission but no HTML preload links; managed_nonce ignores rel=preload. Existing SDK Static resolves manifest keys/filenames, not Src. Relying on guessed hashes, CSS discovery alone or empty default crossorigin would leave the M1 binding unproved. Existing managed filesystem checks and SDK parsing retain physical file ownership/existence; no SDK/vendor change is proposed. Synthetic fixtures must meet the new real shell contract, never permit absent production fonts to keep old tests green.

## Consequences
Add only source HTML/Go/browser checks and required valid synthetic fixture updates; preserve every prior assertion/refusal and frozen legacy bytes. Three new Go methods and hostile/missing/duplicate/malformed binding cases are authored NOT RUN. Existing all900/zero retry/skip/flaky, CSS/modulepreload report fields, all-manifest byte checks, strict CSP/PNG/axe/vitals and budgets remain. No font binary/CSS/weight/display/dependency/lock/framework/score change. React19/UI0.3 throughM1 remains. Actual Vite mappings/preload reuse, native tests, complete900, nonce/CSP, fonts and device/performance validation belong to later admitted Linux execution. No save/LCP claim; actual FULL2db894/900 with six failures, startup122743/122880 and red route JS remain unchanged. Formal M0/M1/image/device/M2/S0b/teacher/social/production acceptance is unearned. Applied after exact capability-v2 code with separately reviewed current-document/control reconciliation; no combined qualified identity exists and shared main reconciliation/owner adoption remains pending. No landed ADR is superseded.
