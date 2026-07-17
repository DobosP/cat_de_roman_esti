# ADR-0033: Enrich aliases and semantic edges without widening sense ambiguity

Date: 2026-07-17
Status: accepted

## Decision

Add an alias only when its normalized form is unowned and the form denotes the same
concept. Keep known homonyms and accent-fold collisions explicit and blocked. Limit this
wave to 25 human-readable semantic links, require a concrete relation and Romanian label,
cap new endpoint fan-out at three, and forbid generic `related_to` links or reverse fan-out
through broad category hubs. Do not add or promote game boards.

Allow the rollback-safe v24 applier to select a local data module, and extend its transaction
to the generated mobile contract. A graph write, pack validation, or mobile refresh failure
must restore both KG mirrors, both pack mirrors, and the mobile snapshot together. Recheck
the exact 33 v23/v24 pending items after every topology change.

## Context / why

V24 made canonical common words available, but 121 of its 150 nodes still sat exactly at
the four-link floor. Several paths were only technically connected through placeholders
such as bathroom to eating or speaking. At the same time, normal inflections—including
`morcovii`, `merele`, `mănânci`, and `citești`—were absent even though their concepts were
already present.

Automatic morphology is unsafe under the accent-folded one-owner resolver. `vin` can mean
wine or “I come”; `metroul` already denotes the Bucharest Metro; moon and calendar-month
forms collide; and bed/blanket plurals fold together. Of the 16 unresolved eligible v24
benchmark words, only singular `vecin` has a same-referent existing owner (`Vecini`). The
other fifteen need real concepts or future sense-aware resolution, not convenient aliases.
The `sandvici`/`sendviș` spellings were checked against
[DOOM entries surfaced by dexonline](https://dexonline.ro/definitie/sandvici).

An initial station-to-bus/tram pair passed structural validation but failed the exact
Conexiuni critique because `Stație` gained stronger pull toward a foreign group. Those two
links were replaced by fatigue-to-sleep and eraser-to-pencil relations before landing. This
is why validator-green topology changes still require game-specific dossiers.

## Consequences

The graph gains 168 collision-screened aliases across 132 nodes and 25 concrete semantic
links, reaching 7,033 aliases and 8,792 edges without adding nodes. Eligible canonical
coverage rises only from 218/234 to 219/234 (93.6%); the larger gain is that 168 common
surface forms now resolve exactly. All 794 pack records remain byte-unchanged, the 33 exact
pending dossiers are deterministic-critique clean, and all approved gameplay stays valid.

The stronger direct links intentionally broaden the responsive zones around `Frigider` and
`A citi`. Six legacy terminal puzzles regenerate deterministically, while their count and
hop-band contracts stay fixed. Future enrichment must preserve the blocked-form inventory,
the 25-edge/fan-out bounds or supersede this ADR, refresh mobile in the same transaction,
and add actual nodes for the fifteen remaining benchmark concepts.
