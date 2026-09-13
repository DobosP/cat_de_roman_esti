# ADR-0141: Rebuild the Alchimie workbench around the next playable action

- Status: accepted
- Date: 2026-09-13

## Context and authority

The owner requested the next version with a GUI rebuild focused on Alchimie because
the interface felt confusing and frustrating to play. The previous layout separated
the target, selection guidance, mixing controls, discoveries and inventory into a
long stack. Selecting a third ingredient silently replaced a selected ingredient,
and a productive combine changed the inventory filter to Recente.

This new request authorizes the bounded V92 Alchimie interface work.
[ADR-0137](0137-finish-v91-and-stop-iteration-loop.md) remains accepted: it required a
new owner request before V92 and continues to stop automatic iteration. This decision
does not restart the recurring version loop or authorize later versions.

## Decision

Rebuild the live board as a compact target followed by one workbench containing the
mixing panel and inventory panel. Desktop places the panels beside each other; mobile
stacks them in normal document flow. Alchimie's header and bench remain in normal flow
at all viewport heights, leaving vertical scrolling available when text grows. Help,
the discovery journal and round actions follow the main play area. Scope the new styles
to Alchimie and load them with that screen.

Keep both selected ingredients stable when a third ingredient is chosen. Explain that
one must be removed before replacement. Explicit slot removal returns keyboard focus
to its inventory control when available, with the inventory panel as fallback. Removing a slot
or clearing the bench dismisses the stale full-selection warning. Existing empty-pair
recovery continues to retain the attempted pair and require a changed ingredient.

A productive combine preserves the player's inventory filter. Newly earned ingredients
have immediate use buttons in the mixing panel and remain selectable from their
server-authored discovery history. Both controls only change local selection; crafting
still requires the explicit Combine action. Changing an inventory filter clears search,
and an empty search offers a visible clear-search action.

Keep the available hint action in the bench with its 150-point cost visible beside the
button. Preserve earned hint text and the server's hint availability and charging rules.
Number the ingredient slots and keep contextual selection guidance beside the controls.
Wrap long Romanian labels inside panels, slots and ingredient buttons, including at
320px width and 200% text size; use scrolling for additional height.

## Boundaries

This is a GUI-only version. It does not revise recipes, concepts, labels, game packs,
rankings, eligibility, difficulty, scoring or backend contracts. The server remains
authoritative for discoveries, depletion, target revelation and hints. Existing owned
action recovery, bounded reaction history, session lifetime and capacity limits remain
in force. No private solution values are added to the client or served assets. Other
games retain their existing presentation and recovery behavior.

## Verification

Browser acceptance uses real deterministic BFF sessions and the existing test-process
solution helper. It checks stable selection and warning recovery, explicit removal and
focus, filter/search behavior, and quick-result and journal selection without another
POST. Initial desktop and mobile geometry must show the target, both slots, Combine and
the first ingredient row together. At 390×844 the first row must finish at or above 700px.
Separate presentation-only stress checks cover long labels, 320px width, 200% text and
a 480px-high viewport without changing the real game state or responses.

Required checks include the frontend native tests, lint, build and bundle budget,
existing browser recovery and accessibility journeys, and repository integration gates.
Regenerate the served static assets from source. Final commands, results and evidence
belong in [STATUS](../STATUS.md); this ADR makes no claim of completed human playtesting
or physical-device acceptance. Verification is bounded to this requested version.
