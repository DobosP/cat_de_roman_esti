---
name: romanian-game-content
description: Refine and expand the six cat_de_roman_esti Romanian word games through conservative refinement and broader experimental concept discovery, with a durable candidate pool and the existing independent content gates. Use for content growth, vocabulary coverage, puzzle quality, or planning a content wave in this repository.
---

# Romanian game content

Improve the six games through two connected tracks: **refinement** delivers reviewed
player improvements; **discovery** explores broadly and supplies a pool that refinement
can select from. The operating decision is [ADR-0155](../../../docs/adr/0155-two-track-content-growth.md).

## Orient and bound the work

- Resolve the repository root from this skill or Git; paths below are repo-relative unless linked.
  Follow [AGENTS.md](../../../AGENTS.md), [STATUS](../../../docs/STATUS.md),
  [agent-map](../../../docs/agent-map.md), and [testing](../../../docs/agent-testing.md).
  Read the [rubric](../../../docs/CRITIQUE_RUBRIC.md) and the latest relevant review for a content wave.
- Respect the requested scope: refinement only, discovery only, or both. For a general
  expansion request, plan both tracks around a common player problem. Creating or editing
  this skill does not itself start a wave. Do not create recurring runs without a request.
- Record a baseline commit, finite theme/candidate budget, intended player outcomes and
  acceptance evidence. Use current inventory and runtime limits, not numbers copied from
  previous conversations. There is no required split between tracks or shipment quota.
- Use the task worktree and scratch conventions in AGENTS. Keep durable research in
  `docs/content-pool/<theme>/pool.json` as described in [the pool contract](references/candidate-pool.md).
  Create a pool only when research produces records; keep bulk extracts and prototypes in scratch.
- Where delegation is available, research and refinement may run independently with bounded
  briefs and separate write ownership. Name baseline, inputs, outputs and relevant checks.
  Keep factual and quality judgments independent of authorship; the integrator owns installation.
  Follow available repository routing instructions without hard-coding models or requiring
  Claude-only workflow tools in another harness.

## Track 1: refine the current solution

Start with eligible/preferred stock, repeated concepts, unavailable everyday guesses,
misleading feedback, weak route captions, ambiguous boards and player observations.
Prioritize recognizable words and understandable play. Investigate why approved stock
is ineligible before proposing repairs; eligibility thresholds remain quality boundaries.

Choose a bounded improvement using existing content first, then inspect promising discovery
records. A shortlist is an input to refinement, not approval. Independently recheck its
identity, evidence, dependencies and proposed player benefit. Narrow, hold or reject it when
necessary, recording the reason back into the pool.

Use the appropriate installation rail below, then prove normal selection and an actual
playthrough. For behavior changes, run targeted regression checks; for content changes,
run the existing validators and review gates. Preserve earlier content except for specifically
scoped, reviewed repairs. Apply the existing owner rules for approved-stock revisions and A5
holds, taking the user's current explicit authorization into account.

## Track 2: discover broadly

Explore underrepresented everyday domains, cultural themes, word senses, specific
relationships, recipe foundations and unfamiliar combinations. Search beyond the current
KG when it would add recognizable concepts. Experimental prototypes can challenge the
current approach; describe the hypothesis and what evidence would disprove its value.

For each promising idea:

1. Distinguish a genuinely new concept from an existing ID, spelling/inflection, verified
   synonym, new association, or first exposure of an existing word in one game. Check
   normalized labels, aliases and rejection records; preserve meaningful sense distinctions.
2. Research factual claims and Romanian recognition using the rubric's source checks.
   Record claim-specific sources and counterexamples. Label unverified hypotheses explicitly;
   model agreement is not source evidence. If a source becomes unavailable, identify which
   claims lost support and seek original replacement evidence; retain valid unaffected evidence.
   Hold adoption when material claims cannot be verified.
3. Sketch concrete play: likely guesses, a partition, an outsider, competing pairings,
   alternative routes, or a short recipe chain. Do not force every concept into every game.
4. Record uncertainty, weak links, affected games, runtime/save constraints and a next action
   in the durable pool. Rejected ideas retain their reasons so later waves do not rediscover them.

Breadth and risk belong to the experiments. Discovery never writes served fixtures, grants
approval, changes runtime limits, invents edges or aliases to make a puzzle pass, or relaxes
review. A prototype may simulate proposed data in its isolated workspace. Only refinement
can propose its adoption through the real installation rail.

## Transfer from discovery to refinement

Read [the pool contract](references/candidate-pool.md) when recording or selecting research.
Select exact record revisions with a concrete player benefit, identity/source checks and
explicit unresolved issues. Bind the handoff to the baseline, selected revision digests,
intended rail and acceptance checks. Recheck changed dependencies before using old evidence.
Keep discovery records separate from importer input and runtime status fields.

| Content being adopted | Existing rail and evidence |
|---|---|
| Four pack games, existing KG only | [Pack-only workflow](../../../docs/PACK_ONLY_CONTENT_WAVES.md): empty nodes/edges, exact raw reviews, pending staging, fresh dossiers, independent analyst/verifier, version-2 artifacts and strict promotion. Alchimie challenges also require the separate projection audit. |
| Genuinely new shared KG concepts or relations | Inspect the current importer schema and the [reviewed graph](../../../docs/adr/0118-reviewed-culinary-graph-corrections.md) / [household discovery](../../../docs/adr/0135-household-discovery-concepts.md) precedents. Use supported generators/transactions and complete raw factual/quality evidence. Check all affected games and refresh bound artifacts; do not use pack-only input for topology changes. |
| Intrusul / Perechi boards | Follow [ADR-0148](../../../docs/adr/0148-expand-all-game-content-with-independent-review.md) and the quick source, builder and API audit named there. Preserve the frozen V38 payload; supplement additions need their own factual/quality judgments and final bound reviews. |
| Alchimie exploration concepts / recipes | Follow [ADR-0147](../../../docs/adr/0147-grow-alchimie-with-reviewed-vocabulary.md), the current world generator/audit and later STATUS decisions. Review world-local definitions and recipes, distinguish them from shared KG nodes, and verify historical collections. Resolve any capacity or compatibility blocker before changing the live book. |

Adopting a new shared concept into a round requires both the graph transaction and that
game's downstream review rail against the resulting graph; passing one does not pass the other.

Use each script's current help/schema rather than synthesizing a new review format. Research
sources and pool digests do not replace the rails' candidate, dossier, rubric and audit bindings.
A raw quality `keep` remains pending; it is not promotion. Only complete, current approvals
can cross the installation boundary. Do not hand-edit fixtures or generated static assets.

## Game-specific acceptance

| Game | Evidence to inspect |
|---|---|
| Conexiuni | Honest predicates, one defensible partition, a difficulty gradient, no mirrored groups/type shortcuts; novelty across inventory, batch and tombstones. |
| Intrusul | Exactly one defensible outsider under the stated predicate; no accidental type shortcut or reused trio. |
| Perechi | Four recognizable pairs; actively search for competing valid matches and count fresh associations. |
| Cald sau Rece | Nameable target, at least five unique existing incoming non-distractor neighbors, a familiar warm opener and coherent feedback; outgoing edges or projections do not satisfy the incoming floor. |
| Lanțul Cuvintelor | Familiar endpoints, meaningful alternative paths, no forced intermediate choke point, and truthful displayed captions in each supported direction. |
| Alchimie | Intuitive productive openings, useful intermediate discoveries, credible alternatives, bounded closure and preserved earned progress; distinguish challenges from exploration. |

## Verify and report

Run affected checks and integrated gates from agent-testing and the chosen rail. Rebuild
changed bindings; do not reuse stale judgments. For shared-graph changes compare existing
Cald feedback profiles, Lanț routes/captions, partitions, pairs and crafting behavior as affected.
Keep session bounds, deterministic behavior, private answers and historical saves intact.

Report baseline-to-result counts separately for new shared concepts, world-local concepts,
accepted forms, per-game fresh exposures, rounds, approvals and eligible/preferred selection.
Use `scripts/report_content_delta.py --baseline <commit> --text` for the inventory it covers;
add world and per-game exposure counts separately. Aliases do not prove synonym growth.
Include selected/held/rejected pool records, evidence, player-visible outcomes and next actions.
Update STATUS and any required ADR in the same commit; follow repo landing rules. Push and
deployment still require their own authorization.

Automated gates and AI reviewers do not establish enjoyment. Use available human playtest
observations to calibrate familiarity, fairness and difficulty; label missing evidence honestly.
If the entire candidate batch fails, preserve the useful research and report zero additions.
