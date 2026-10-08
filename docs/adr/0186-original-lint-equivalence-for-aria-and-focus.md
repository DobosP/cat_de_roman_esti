Valid until: a superseding accepted lint-equivalence decision — then treat as history.

# ADR-0186: Preserve original ARIA and focus behavior during native lint migration

Date: 2026-10-08
Status: accepted source equivalence; actual native validation pending
Refines: ADR-0184 lint equivalence only; all toolchain, output and budget requirements remain.

## Evidence

The original qualified React source at `45edcf2ce170c112621c73609e6e169633eb38a8`
used JavaScript recommended, TypeScript recommended, React Hooks and React Refresh
rules in `frontend/eslint.config.js`. It had no JSX accessibility plugin or rules.
The new Oxlint correctness category additionally reported 37 valid status/group/emoji
role patterns, three intentional tested autofocus controls and one keyboard-focusable
horizontal breadcrumb scroll group. These findings were preserved in the actual
failed GEN receipts; none was an inherited hard lint failure.

## Decision

Exactly `jsx-a11y/prefer-tag-over-role`, `jsx-a11y/no-autofocus` and
`jsx-a11y/no-noninteractive-tabindex` remain visible as advisory warnings. Preserve
the existing roles, DOM, CSS and tested focus behavior. Do not replace these patterns
with fieldsets/outputs or remove their keyboard target to silence new preferences.

All other JavaScript, TypeScript, Hooks, CSP and accessibility guards remain hard
at their existing severity. Existing Axe, CSP and browser assertions remain unchanged
and required. This equivalence introduces no original guard waiver, test exclusion,
budget exception, UI phase activation or runtime qualification.

## Validation

The source setting is unqualified until the next owning native run. Current facts
and captured results live in `docs/STATUS.md` and `docs/execplans/s1-cat.md`.
