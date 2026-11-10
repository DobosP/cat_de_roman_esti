# ADR-0226: Content loop V4

Date: 2026-11-09
Status: accepted (Paul, 2026-11-09); separate test-pin owner step partially superseded by ADR-0227 (2026-11-10).
Decider: Paul Dobos.

## Context

V3 landed 210 inflected inputs for 92 Cald owners. Its n5 bulk wave qualified no items.
Its 7.7 KB state, timer heartbeats, approval waits and batch-wide failures hindered the loop.
The exclusion screen, own-head attribution, lint, blind gameplay, two judgments and exact-byte
landing checks remain. ADR-0225 archived and pruned the V3 raw local trees after byte
verification. V4 uses the retained seed without restoring V3.

## Decision

1. One append-only registry across six games holds forms, synonyms, concepts, names, edges
   and boards. Exclusions come from landed records and owner rulings. Old wave scripts
   remain historical. Only the orchestrator writes transitions.
2. Codex executes in the current chat with fresh, separated author, blind critic, factual,
   quality and landing review jobs. A headless driver still requires a separate owner-approved
   agent-ops decision. Any future signed source table, templates and profiles bind exact bytes.
3. Screen, source and lint per item. A failed item returns to the drawing board while its cohort
   proceeds. A tool error gets three retries then parks the item. Review and install per
   cohort. Gate each landing on the exact SHA, including pinned build, full 4i with generated
   SPA, GUI gates when affected, and HTTP play of every added board and alias.
4. Use local Git for landing from a clean main, after the independent landing review. If main
   moves, merge it into the loop branch and redo exact-SHA qualification. Keep the branch and
   remove only owned review worktrees. Keep state below 2 KB and evidence text-first.
5. Apply the standing source grant below. Allow dexonline captures and new GETs, preserve
   legacy provenance, cache and space requests per host, and obey robots and terms. A rate
   refusal opens the host breaker, and a policy refusal drops the host and goes to the owner queue.
6. Replace the approved-but-ineligible Conexiuni boards with new boards under full-inventory
   novelty. Keep predecessors in place and all 79 owner-held boards untouched. Minors are
   never entries and living persons go to Paul. Keep all owner holds in the log below.

## Supersession

- ADR-0220's V3 procedure, heartbeats, per-batch approvals, stop-on-error and sealed sidecar
  mechanism are superseded. Its C4 critic scope, C6 independence, quality and tool-lane checks
  remain. The staged/frozen hash check replaces the second judgment round.
- ADR-0221 archival treatment for V3 is resolved by ADR-0225. ADR-0211's boards-only scope is
  superseded. The existing owner holds and separate owner-approved pins commit in ADR-0210 remain.
- ADR-0189 behaviour-bound rails and ADR-0212 world acceptance remain. ADR-0186's corpus
  count and independent evidence rule remain. ADR-0067/0069/0073 quality, novelty and tombstones,
  ADR-0019 child safety, ADR-0113 lexical distinctions and ADR-0224 target-based Alchimie remain.

## Consequences

The [V4 procedure](../CONTENT_LOOP.md) gives the lane order, stage gates and recovery.
Milestone 0 promotes portable helpers, imports the seed registry and measures the L1 baseline.
Later install verbs need tested equivalence before replacing the existing rails. Class P
boards can use the existing rail while lexical tooling and class G install tooling mature.

## Owner log

Paul, 2026-11-09 (verbatim):

````text
Start the Cat content loop V4 in this chat and keep it running until I stop it.

## My decisions (Paul, 2026-11-09). These are my own words, and they are your authority.
- I accept the V4 content-loop design in `~/work/_temp/adhoc-content-loop-v4-20261108/v4-proposal/`.
  Read `02-v4-procedure.md`, `03-adr-draft.md`, `06-implementation-plan.md`, `07-migration.md` and `08-open-questions.md`, including my answers at the end.
- You (Codex) are the executor. Run author, critic and reviewer roles as separate fresh subagents (`fork_turns=none`, distinct task names, never shown each other's verdicts before both sign).
  Where the design says Claude workflows or `claude -p` jobs, do the same with your own subagents.
- Land through local git only. No pull requests, no push, no deploy.
  When a cohort passes every gate and the landing review below, fast-forward local `main` to it from `~/work/cat_de_roman_esti` (`git merge --ff-only <sha>`, only when that checkout is clean on `main`). Main moved? Merge `main` into your branch, rerun the gates, then fast-forward.
- dexonline is allowed as a research source: existing captures and new GETs.
- Standing research permission, so you never need a per-batch approval. Read-only HTTPS GETs to these hosts only:
  - `dexonline.ro`
  - `ro.wikipedia.org`
  - `ro.wiktionary.org`
  - `raw.githubusercontent.com` (FrequencyWords only)
  - `localhost:8077` (`ro_data_server`)

  Rules for those GETs:
  - Send the User-Agent `cat-de-roman-esti-content-research/4 (+https://github.com/DobosP/cat_de_roman_esti)`.
  - Wait at least 2 s between requests to the same host (10 s for Wikimedia).
  - Cache every response under your scratch dir and re-use it.
  - Obey robots.txt. A 429 or 5xx parks that host for 1 hour, then resume. A robots or terms refusal drops that host for the run and adds one line to the owner queue.
  - Never ask me again for any of this.
- V3 is retired and archived on the NAS (ADR-0225). Do not restore it. Your inputs from it are in `~/work/_temp/adhoc-content-loop-v4-20261108/v3-seed/`.
- The 79 held Conexiuni boards stay held. Do not reopen, edit or retire them. New Conexiuni supply means new replacement boards.
- Owner holds that never change:
  - no bare *sucitoare*;
  - Ie never gets *ii*/*iei*;
  - Mănăstire/Sucitor rows only with my explicit go.

  Minors are never name entries. Living persons go to my queue.
- Never restart Docker and never change host configuration.

## Setup, once
1. Create the loop branch and worktree:
   `python3 ~/work/agent-ops/scripts/create_task_worktree.py --repo ~/work/cat_de_roman_esti --branch content/v4 --task "Content loop V4" --write`
   That gives `~/work/_worktrees/cat_de_roman_esti/content__v4`. Scratch, cache and evidence go in `~/work/_temp/content__v4/`; copy `v3-seed/` there.
2. First commit on `content/v4`, docs only:
   - Turn `02-v4-procedure.md` into `docs/CONTENT_LOOP.md` (V4) with my decisions above applied. It replaces V3, stays under 200 lines, and says Codex is the executor and that landing is local git.
   - Add `docs/adr/0226-content-loop-v4.md` from `03-adr-draft.md`. Its owner log quotes this message verbatim.
   - Flip ADR-0220's Status line to "superseded by ADR-0226", and add the index line and the inventory entry.
   - Pass `cat-doc-check --inventory` and `git diff --check`.
3. Build Milestone 0 from `06-implementation-plan.md`:
   - move the miner helpers and the landing kit into `scripts/`;
   - the registry and its seed import;
   - the L1 baseline.

   Each tool change is its own commit, with tests and a portable build, plus one fresh-context code review by a subagent that did not write it.

## Every cycle
- Work the lanes in the procedure's order:
  - L1 Conexiuni replacement boards;
  - L4 boards from the need map on existing nodes;
  - names and concepts;
  - edges;
  - stock rescreen;
  - synonyms;
  - forms.

  Big intake, per-item states, no quotas.
- One failed item goes to the drawing board with its reason. It never stops the cohort.
- A tool error gets 3 retries, then that item is parked. Never stop the loop on an error.
- Gates per item and per cohort exactly as `docs/CONTENT_LOOP.md` (V4) says:
  - the lints;
  - the blind gameplay critic for every board and every touched board;
  - two independent judgments per new item;
  - install;
  - `cat-content validate` and `export --check`, `cat-content-ops check`;
  - the rails;
  - the HTTP corpus and pins.
- Landing review for each cohort, by a fresh subagent that authored and judged nothing in it:
  - the pinned `scripts/gate.sh build` and the 4i gates on the exact SHA, including the full Go race suite with the generated SPA assets;
  - both GUI gates when boards, edges, captions or e2e ids change;
  - an HTTP playthrough of every new alias and every new board.

  Never land red. Then fast-forward local `main`, update `docs/STATUS.md` in that series, and remove only your own review worktrees.
- Keep `state.json` under 2 KB and the ledger append-only. Evidence is text-first; bulky bytes go in scratch.

## Talking to me
- Message me only when something lands, a cohort qualifies, or a decision is truly mine.
  Batch my questions into one message with options and your recommendation, then keep working on everything else.
- First line of every report: words, names and boards actually added per game, with examples. Then at most 9 plain lines.
````
