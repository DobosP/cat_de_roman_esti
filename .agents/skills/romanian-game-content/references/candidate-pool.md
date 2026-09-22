# Durable discovery pool

Use this reference when discovery produces research or refinement selects it. The format is
an editorial convention defined by [ADR-0155](../../../../docs/adr/0155-two-track-content-growth.md),
not an enforced runtime schema or a substitute for existing review artifacts.

## Storage

Keep one manageable theme in `docs/content-pool/<theme>/pool.json`, created in the task
worktree and committed with the research. Resolve the directory from the repository root.
Use an envelope with `schema_version: 1`, `theme` and a `records` array. Never name or locate
it as an importer `candidates.json`, add it to fixture loaders, or pass it directly to an
importer. A research-only run can finish by committing pool records without changing gameplay.

Link the theme's pool from the current wave record or STATUS so another run can find it.
Commit the concise sources, decisions and review references needed to continue; do not leave
essential evidence linked only to scratch that will be removed. Bulk extracts, trial scripts
and disposable prototype outputs follow the repository scratch convention. Store summaries
and source URLs, not copied source corpora.

## Record fields

Use stable research IDs, independent of future KG/pack IDs. Unknown values remain explicitly
unknown until researched; do not fill fields with invented certainty. At the `idea` stage,
identity, proposed benefit, state and next action suffice; fill the remaining fields before
marking a record `ready_for_refinement`.

| Field | Meaning |
|---|---|
| `id`, `revision` | Stable research identifier and increasing integer revision. |
| `state`, `origin_track` | Pool lifecycle state; originating track is discovery or refinement. |
| `baseline_commit`, `checked_on` | Exact source revision and research/check date. |
| `label_ro`, `sense`, `category` | Proposed Romanian label, intended meaning and useful theme. |
| `novelty` | One of new_shared_concept, new_world_concept, new_game_exposure, new_relation, new_round, or accepted_form; include relevant existing IDs. An accepted form needs linguistic evidence. |
| `identity_checks` | Label/alias collisions, homonyms, nearby IDs, prior pool decisions and runtime rejection/tombstone matches. |
| `player_benefit`, `games` | Concrete improvement and games where it plausibly belongs. |
| `claims` | Definitions and proposed relations: exact subject/sense, predicate, object, direction, evidence state and supporting source references. |
| `sources` | Claim-specific URLs, access dates and brief original notes about what each supports or contradicts. |
| `recognition` | Romanian familiarity evidence and intended difficulty; uncertainty is explicit. |
| `play_sketches` | Proposed openers, groups/pairs, alternatives or recipe chains; separate prototypes from verified runtime outcomes. |
| `risks`, `dependencies` | Ambiguity, weak associations, compatibility/capacity issues and changed inputs that require rechecking. |
| `decision`, `next_action` | Reason for the current state and a concrete next step or rejection reason. |
| `history` | Dated revisions/transitions, author/reviewer identities and evidence references. Preserve earlier rejection reasons. |
| `handoff` | Initially absent; later binds the selected revision, target rail, exact inputs, acceptance checks and review artifacts. |
| `integration` | Initially absent; after adoption, canonical IDs, commit/receipt, checks and actual runtime eligibility/selection evidence. |

Pool claims can be unverified, supported, contradicted or unresolved. These are research
annotations only. Do not use a `confidence` score or a source count as an approval threshold.

## Lifecycle

`idea -> researched -> ready_for_refinement -> selected_for_refinement -> integrated`

- `researched`: the concept and possible uses have evidence and known uncertainties.
- `ready_for_refinement`: identity/novelty checked, material claims supported, recognition
  investigated, concrete play sketched, no unresolved factual blocker. Record remaining
  design questions; this state only makes the idea eligible for selection by refinement.
- `selected_for_refinement`: an integrator has taken responsibility for a bounded proposal
  and recorded its exact handoff. Discovery cannot assume this leads to installation.
- `integrated`: the intended contribution passed its actual rail and landed; record its
  canonical IDs and evidence. Report a new node with no selectable round as vocabulary
  growth only, never as a new playable round.
- `held`: evidence, compatibility, authorization or another dependency is missing. State
  exactly what would allow progress. Resume the blocked adoption only after that dependency
  changes; independent research may continue. Completed factual research does not clear an
  installation compatibility blocker. Keep such records held with their research evidence intact.
- `rejected`: record why and link counterevidence or matching prior rejections. Reopening
  requires a new revision and material new evidence, preserving the old reason.

A selected record can return to held or rejected. Refinement writes this feedback into the
pool; discovery uses it to avoid repeating weak concepts and to research missing evidence.
Split independently adoptable parts into linked records if one idea mixes incompatible
outcomes. Keep states per record, not a blanket promotion for the entire theme.

Do not use `approved`, `pending`, `promote` or a raw review verdict as pool states. Those
belong to existing installation contracts and have different meanings.

## Handoff and stale evidence

Freeze the selected record's revision with a SHA-256 of its exact UTF-8 serialized bytes,
and retain those bytes with the handoff evidence. Do not hash a record that contains its
own digest: snapshot the pre-handoff record, and store the digest/path in the handoff.
Bind selection to the baseline commit, destination rail, intended playable outcome and
acceptance checks. Enumerate required topology, spelling, recipe or behavior changes and
any unresolved design questions. New research must not silently mutate a selected snapshot.

Create a separate, bounded importer/generator proposal from the selected records. The
normal raw reviews, pending gate, projection audits and final installation reviews still
apply. A pool hash never substitutes for an importer candidate-file SHA or dossier binding.

If claims, records, source inputs or relevant runtime dependencies change, increment the
revision and repeat affected checks. Reuse only evidence whose exact dependencies remain
valid under that rail's rules. On completion, write adopted IDs and receipts, or the reason
refinement declined the proposal. Keep summaries concise enough for the next run to use.
