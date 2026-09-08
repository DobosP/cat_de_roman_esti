# ADR-0140: Revise the existing easy Sport Alchimie seeds

- Status: accepted
- Date: 2026-09-08

## Context

The existing approved `al_sport_083` starts with three depleted seeds in its live
private recipe book. Medalie, Recordul la 100 m liber din 2022 and Bazin olimpic
participate in no usable recipe. Washington Bullets also creates a recognition
concern for the broad Romanian anonymous beta audience. Graph closure alone did
not establish useful starting choices.

## Decision

Replace only this record's ordered six seeds with Cristina Neagu, Echipă națională,
Dinamo București, Rapid București, FCSB and CFR Cluj. Retain the existing ID, target
Liga Campionilor la handbal, Sport category, easy difficulty, two-action par, source
and approved status. This is one revised round and zero new concepts, links, forms,
synonyms or rounds.

The exact candidate has two intuitive opening ideas across four productive pairs:
Neagu plus the national team gives women's handball; two football clubs give their
shared sports-club category. Either intermediate combines with Neagu to reach her
club competition. The sparse book retains six recipes and four two-action routes,
with all six initial seeds useful. Four pairs are not four distinct semantic ideas,
and the game does not promise to accept every plausible pair from the broader graph.

Use the separate offline `scripts/apply_sport_seed_revision_v91.py` migration. It
accepts only the pinned before/after row, whole baseline pack, identical mirrors,
source files, candidate dossier and profiles. It requires distinct factual and
quality accept judgments bound to those exact inputs, rebuilds the live dossier
and uncached sparse book, and compares the full reviewed initial profile. Default
execution is read-only; `--write` replaces both pack copies through the established
file transaction and validates both, restoring their original bytes on failure.
Reapplication and stale or expanded proposals fail closed. The script grants no
general permission to edit approved payloads and does not misuse the label repair
or pending-to-approved promotion paths.

## Consequences and verification

The target salience warning remains explicitly accepted by the independent judges;
recognition is an editorial assessment, not a player survey. Three older Neagu
edge labels still use present tense; their separate label proposal is not included.
No approval status or unresolved content hold is changed.

The V91 content review folder binds the independent judgments, both complete
83-book comparisons and actual two-action BFF journeys. Migration tests exercise
dry-run behavior, exact one-row writes, missing/rejected/stale/duplicate reviews,
tampered inputs, non-seed proposal expansion, mirror mismatch, live profile/dossier
drift, interrupted writes, validation rollback and reapplication. Release artifacts
must be regenerated and complete gates pass before the final local V91 landing.
Stop the iteration loop after that landing under ADR-0137.
