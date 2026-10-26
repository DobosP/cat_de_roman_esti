# ADR-0220: Continuous Codex content loop with landing reviews

Date: 2026-10-26
Status: accepted

## Context

V2 (ADR-0211, as repaired by ADR-0212) ran from 22 to 26 October 2026 and qualified no content.
The owner-stop review (`~/work/_temp/content-loop/review-20261026-owner-stop-audit/REVIEW.md`)
found these causes:

- fixed per-landing costs paid by waves that shrank to one item;
- bespoke per-wave helpers that turned trivial defects into dead waves under fail-twice;
- tick and commit caps that were reinterpreted rather than enforced;
- no output-based stop rule;
- silence when blocked;
- a new worktree and plan for every wave.

The review found the quality gates themselves worked: the blind critic and the two reviewers
caught real content problems.

Paul's instruction on 2026-10-26:

> I don't like the ping pong between Claude Code and codex. I would like to let codex run
> autonomously and keep adding words without this 24 limits or limits in general, and at the end
> just review it with from another session and land what's high quality and good enough. The rest
> go into drawing board again and so on, without creating a new environment for every looping.
> Just continuous improvement on the same session with intermediary landings.

## Decision

- **Shape of the loop.** [CONTENT_LOOP.md](../CONTENT_LOOP.md) becomes the V3 continuous
  procedure:
  - one Codex session, one heartbeat, one long-lived worktree and branch (`content/continuous`);
  - sequential batches;
  - no tick, commit, time or batch-size budgets.
- **Product.** Words that reach players come first: stock curation, then new everyday concepts,
  then boards. A new concept needs a named game, truthful links and the quality bar, not a
  `board_ref`.
- **Per-item outcomes.** Each dropped or rejected item goes to a drawing board with its reason; the
  rest of the batch continues. This reads Paul's "land what's high quality … the rest go into
  drawing board". Whole-review rules (signing order, rationale overlap, reviewer-name leakage)
  still void a review pair.
- **Failures.** A tool failure pauses the batch while the tool lane fixes the tool; it never
  closes the batch. Every blocker gets one question to Paul with options, and work continues
  elsewhere. The loop stops only for Paul, low disk or a red unchanged baseline.
- **Landing.** Qualified batches are queued as landing candidates on the loop branch. A separate
  Claude Code landing review lands the longest accepted prefix on local `main`, and sends rejected
  items back to the drawing board. The loop keeps running; it merges local `main` into its branch,
  and rebuilds from `main` after a `rework` mark. Pushing still needs Paul's word.
- **Gates kept unchanged:** every V2 content-quality, review-independence, gameplay-floor,
  source-binding, install-cascade, test-pin and owner-hold gate. The URL-novelty "author set" is
  the author's captured and cited sources, never every URL-like string in actor inputs.
- **Tool lane.** Each tool has a written threat model and checklist, is qualified once and is
  reused by SHA. The same-user concurrent adversary is out of scope unless Paul says otherwise.
  Correctness, output-integrity, portability and overclaim findings always block.
- **Gameplay critic.** It still plays every board, and every board touched by a new concept, edge
  or alias. Only form curation on existing owners is exempt, as in V2.
- **Self-editing.** The loop never edits CONTENT_LOOP.md, the bound rubric or an existing ADR.
- **No stop rules.** Paul's "no limits" rules out the review's proposed output-stall stops (S1/S2).
  Output-first status messages, plus a report after 12 active hours without a qualified item,
  give visibility instead.

## Consequences

- The V2 automation and its wave/queue files become history. The V2 automation stays paused, and
  Paul may delete it. V3 starts when Paul gives a Codex chat the start file
  (`~/work/_temp/content-loop/CODEX_V3_PROMPT.md`). The heartbeat text is in CONTENT_LOOP.md.
- The landing review becomes the only human-scale checkpoint. Its cost grows with batch size, so
  candidates carry per-game item tables and gate results.
- Unlanded V2 work stays available as drawing-board input: C1's reviewer-accepted families,
  C2/C3 stock, B12 Glazură and B13 Ruladă.
- This supersedes ADR-0211's and ADR-0212's cadence, budget, wave and landing-stop clauses. Their
  quality rules remain.
