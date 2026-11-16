# Content loop V5

[ADR-0230](adr/0230-content-loop-v5.md) records Paul's decisions, and
[ADR-0231](adr/0231-v5-dumps-words-and-model-candidates.md) amends them from campaign `v5-pilot-2`:
Wiktionary dump evidence, full paradigms with per-form drops, the words lane, model-proposed
candidates, trains and the token meter. [ADR-0235](adr/0235-v5-real-use-fixes.md) amends both from
`v5-pilot-3`: one disturbed-board definition, the paired re-blind, the quota band, the full
frequency list, the early Lanț overlap screen and the root operating rules. ADR-0226 rules they do
not revise still apply.
[STATUS](STATUS.md) records what shipped. [CRITIQUE_RUBRIC](CRITIQUE_RUBRIC.md) sets the quality
bar. *(to build)* marks a tool that has not landed yet; everything else exists today.

## Campaigns and the counted goal

ChatGPT runs each campaign as a goal in one ChatGPT app chat. Machine identifiers keep the old
name: the operator `agent:codex`, any `~/.codex` path and thread parameters (ADR-0230 amendment).
Work happens on branch `content/v5` in the worktree `~/work/_worktrees/cat_de_roman_esti/content__v5`.
Scratch, cache and evidence live in `~/work/_temp/content__v5/`, never under `/tmp`. The contract is
`~/work/_temp/content__v5/contract.json`. It holds the base SHA, the end (days and goal-meter
tokens), targets, train limits, source caps, thread limit and tool budget. A live campaign's
contract is never edited: an amendment closes the campaign and starts the next one (ADR-0231).
Whenever main gains a V5 amendment ADR, merge local main into `content/v5` at the next turn start,
before any dispatch, and reread this procedure and the ADR.

The first campaign, `v5-pilot-1`, built the core kit and closed when ADR-0231 amended it.
`v5-pilot-2` closes when ADR-0235 supersedes it. The current campaign is `v5-pilot-3`, whose
contract ADR-0235 states; it starts in a fresh chat after the weekly reset and carries over every
reviewed and frozen item. It runs 7 days from its `campaign-start`, or 40 M goal-meter tokens. Its targets are 60 new forms on existing words,
12 new words, 48 new links, and 6 new boards in at least 2 games. Lanes without a target are
reported but count toward nothing.

- **Counting.** Progress counts only through
  `scripts/report_content_delta.py --baseline <base> --json`. Phase 0 extends it with names,
  links and first exposures. An existing word is a concept in the `base_sha` bundle; only forms
  on existing words count toward the forms target. A link counts only when at least one end is a
  new word. Forms of new words and links between existing words are reported apart. A turn that
  raises no counter and unblocks no named queued item is no progress.
- **Trains.** A board train assembles at 6 qualified boards, or after 96 hours with at least 3,
  and holds at most 20. Forms and new words share a train. It opens when 20 forms or 6 new words
  are in the reviewed pool (S6), or after 96 hours with at least 1 reviewed item, or with at
  least 1 when quota reaches 70%, or near the end, when under 24 hours or under 4 M tokens remain
  (`resume.py` accepts no train events after its stop). It holds at most 100 forms and 20 new
  words; its `train-open` kind is `forms`, or `mixed` when it carries a word. At most one train is
  open.
- **Report line.** Every report starts with new words, forms, names and links, each shown
  separately with examples. Then come boards by game, first exposures of existing words, tokens and active
  hours per landed unit, counters against targets, and blocked lanes with their reasons. At most
  nine plain lines follow.
- **Queue ranking.** Counters rank the queue by measured pass rate. A lane with two empty
  batches, or three hits of the same failure reason, cools down until a recorded input changes.
  Targets never lower a gate.
- **Quota.** Start at 20% or less of the weekly meter, unless the contract carries Paul's start override. Below 70%, use full fan-out. From 70% to
  90%, take no new intake (S1–S3), but frozen items may finish S4–S10 (ADR-0235); `resume.py`'s
  `finish-judged-only` mode means exactly this. At 90% or more,
  close the open train, report and stop. Never run on paid credits. Read the quota at the start and
  end of every turn; a rise the campaign's own tokens do not explain is reported as shared usage.
- **Budgets.** Tokens per landed unit, root included: a form 0.8 M, a new word with its links 3 M, a
  board 3 M. A lane whose cost per landed unit exceeds twice its budget for two trains in a row,
  after its second landed train, cools down and is reported. 8 M tokens since the last landing with
  nothing landed stops the campaign with a report (ADR-0235).
- **Stops.** Stop and report at once on any of: a hold or child-safety breach; an attempt to land
  past a red gate; quota at 90% or more; budget or days spent; or Paul saying stop. Paul re-arms a
  campaign with one message.
- **Token meter.** The goal-meter value given to `resume.py` is the cumulative uncached input plus
  output of the root and all jobs, summed from the ledgers of this campaign and its predecessors
  (ADR-0231).

## Registry, ledger and state

`docs/content-registry/registry.jsonl` (`cat-content-candidate-1`) has a single writer, the
orchestrator. It appends transitions and derives the current view. Check it with
`python3 -I scripts/content_registry.py check --evidence-root . docs/content-registry/registry.jsonl`.
The main path is idea → screened → sourced → authored → reviewed → qualified → landed. Side
states are rejected, duplicate, already_served, parked(prerequisite), held_recorded, held_owner
and retracted(reason). Only Paul's quoted ruling changes an owner hold. Partial co-landing groups
and missing dependencies are refused. Recorded exclusions are re-screened only when their retry
predicate fires, and predicates are rechecked at dispatch. The need map is recomputed when ranking
changes. Legacy captures stay labelled legacy. Every attempt is registered with its lane, the stage it
reached and a reason code, including generator output that never reached an author. A
model-proposed candidate carries origin `model`. A `sourced` transition needs a source-client or
dump receipt hash; model output is never evidence.

The ledger is append-only. It records these rows:
`job-dispatch {job_id, train_id, item_ids, lane, game, role, thread_id, at}`,
`job-complete {job_id, thread_id, at, wall_s, tokens_uncached_in, tokens_out, tokens_cached, verdict}`,
`turn {at, free_slots, queue_len, waiting, quota_pct}` and `train-open`, `train-candidate`,
`train-qualified` and `train-landed`. Root tokens are one unallocated line. `state.json` stays
under 2,048 bytes. Evidence is text-first, with at most 50 MB and a README of up to 30 lines per
train.

## Lanes

| Lane | Games | Evidence and floor | Opens |
|---|---|---|---|
| B boards | Conexiuni, Lanț, Cald sau Rece | Rubric floors on existing words. Conexiuni includes new boards for the cells of the 83 FAIL-lint predecessors, which stay in place; each new board shares fewer than eight tiles and no three-of-four quad with its predecessor or any inventory or tombstone board. The 79 owner-held boards stay untouched. Lanț gets the native prospective captions, Cald the ADR-0213 protocol. | Now |
| Q quick | Perechi first; Intrusul authored in the pilot too | Rubric I/J and the ratified five-case gold set, through the ADR-0229 native quick path. The parked C51 Perechi prospect (V4 `state.json` `prepared.c51`) goes first, once its 13 history references are closed. | When the quick batch proof lands and installs one board |
| A Alchimie | Alchimie target rounds | Built from existing words, with exact action par, at least 2 openings and no one-move target. New recipe links are class G. The world stays at 256 concepts or fewer. | With the Alchimie install step *(to build)* |
| F forms | Typed input in every game, Cald first | Every form in the word's own ro.wiktionary inflection table that the game lacks: nouns and adjectives first, verbs after the verb sample passes; vocatives only for nouns naming people or animals. A script proposes the forms from the table; neither rules nor a model creates one, and the author does not fetch. Both reviewers read the table and judge the family. Per-form drops, same-word diminutives and profanity probes: ADR-0231 decisions 6–7. No diminutive forms are authored. | After the core kit |
| W new words | Shared graph | A Romanian section in ro.wiktionary, a live ro.wikipedia article and positive frequency. 4–8 truthful links: at least 2 to existing main words and at least 2 within the same category, each citing a quoted span the span checker finds in the cited source's cached receipt. The queued backlog goes first. Before the first words train, the one-word dry run (ADR-0231 decision 8); over 10 disturbed boards, the lane waits and the loop asks Paul once. Child-safety labels and the sensitive classes for Paul's queue: ADR-0231 decision 8. | With the link install, the all-boards view diff and the span checker *(to build)* |
| G model candidates | Feeds W and E | Proposals from the model inside the goal, one cultural cell at a time, three fresh threads per cell, 10 items per thread (ADR-0231 decision 9). Never evidence, never forms; senses never ship. A cell under 10 script-clean candidates per 100 cools down. | When every backlog `idea` row has passed S1 and the dump Wiktionary check |
| N names | Shared graph | A ro.wikipedia article and the matching Wikidata item, under the Names rules below. | With W's tools and the rubric Names section *(to build)* |
| E edges, captions | Lanț, Cald, Alchimie | One source stating each relation. The ten-caption Lanț trial needs a caption generator and full requalification. | Edges with W; captions with the generator *(to build)* |
| S synonyms | Shared graph | Both words share the selected sense in ro.wiktionary, a second Romanian source agrees, and the synonym passes a substitution test. Both reviewers judge it. | After the core kit |
| R rescreen | All | Historical stock under current exclusions and fresh evidence. Old acceptance is never inherited. | Any time |

Owner holds:
- no bare *sucitoare*;
- Ie never gets *ii*/*iei*;
- Mănăstire and Sucitor rows only on Paul's explicit go;
- the ADR-0210 held families;
- the 87 owner-held registry rows.

Prefer content a Romanian 12-year-old would recognise.

## Names rules (the N lane opens when the rubric has a Names section)

- **Sources.** A ro.wikipedia article and the matching Wikidata item.
- **Minors and living persons.** Minors are never entries. A living person goes to Paul's queue
  and waits for his ruling.
- **The rubric section.** ChatGPT writes the Names section of `docs/CRITIQUE_RUBRIC.md` as its own
  commit, and a fresh reviewer that did not write it checks it (ADR-0230). It keeps the two rules
  above and the rubric's existing bar. A rubric change requalifies the rails (ADR-0229), so it
  lands with or before the first train that carries a name.
- **Links.** A name whose links would change existing routes or distances waits for the
  all-boards view diff.

## Roles, threads and the turn checklist

Every role runs in a fresh ChatGPT thread (`fork_turns=none`, a distinct task name, one job per
thread). The roles are generator, author, blind critic, factual reviewer, quality reviewer,
assembler, pin reviewer and landing reviewer. A generator thread never authors, judges or critiques
its own proposals; its reasons, agreement counts and scores stay hidden from every judging role.
Prompts describe its work as proposing candidate words. Reviewers never see each other's verdict
before both sign. Author
sources stay hidden until both sign. The critic gets answer-stripped input only and is told
nothing about the train, generator scores, peer verdicts or reuse. The landing reviewer neither
authors nor judges any item in the train. The assembler never reviews.

At most six threads run at once. During intake the slots are 2 authors (generator threads use
these, never both while authored items wait), 1 blind critic,
2 reviewers and 1 assembler. During qualification the author slots go to the pin reviewer and
the landing reviewer. Judgment roles run at the top effort rung; authors, the assembler and tool
repair run one rung lower. Hashing, equality checks, replays and counts are scripts, never agents.
The root reads no file over 200 lines itself, except this procedure, ADR-0230, ADR-0231 and
ADR-0235. A gate-operator job runs the S7–S9 scripts and returns one receipt; the root never polls
a running gate and never rehearses a train that cannot open yet. Every new or changed gate runs
first on the unchanged baseline. A gate the unchanged baseline fails is reported to Paul; until he
rules, the items it covers wait, it rejects nothing, and nothing lands past it. A headless driver
needs a separate owner-accepted agent-ops ADR.

Each turn:
1. Run `resume.py` with the goal-meter value defined above.
2. Read the quota meter and apply the quota rule.
3. Reap finished jobs and write their completion rows.
4. Update the counters and apply the cool-down rule.
5. Fill free slots from the queue head.
6. If every slot is busy and no script step is pending, issue one long wait. Never sleep with a
   free slot and a non-empty queue.
7. End with one line. A turn with no eligible work spends at most 3 calls, then marks the goal
   blocked and states the exact wake time; a blocked goal resumes only on Paul's message. Running
   jobs or a pending gate receipt are not "no eligible work"; step 6's single wait applies.

Send a full report only when something lands, a train qualifies, a lane is blocked or a decision is
his.
Batch questions into one message, each answerable, with the exact commit and a recommended option.
Only the gated item waits.

## Stages

| Stage | Who | Output | Gate |
|---|---|---|---|
| S1 need and screen | Script | Survivors with reason codes. Every reject is registered. | Screens pass: resolver, registry, exclusions, full inventory, collisions, fuzzy neighbours, Cald inbound floor, co-landing. The form screen covers forms. The collision probe builder (`build_form_probes.py`) feeds every real form near a proposed key and the profanity probe list to `resolver_diff.py --probes` (ADR-0231 decision 7). Words: positive frequency is a positive `exact` count from `scripts/content_v5/frequency.py` over the pinned FrequencyWords `ro_full` list (`~/work/_temp/content__v5/frequency/ro_full.txt`), with `undiacritised_only` and `minority_spelling` flagged for the reviewers (ADR-0235 decision 5). Lanț prospects: `cat-lant-overlap`; a `near_duplicate` is parked before authoring (ADR-0235 decision 6). A cell with no survivors is recorded as graph-blocked. |
| S2 evidence | Script and source client | Cached receipts per item, or a park with a retry predicate. A dump receipt names the file hash, page title, revision id and page byte hash. | First fetcher and role recorded |
| S3 author and freeze | Author | Frozen payload and hash, with the private key kept apart. No board number yet. | Bytes frozen. The lint passes: `critique_pack.py --strict` joined to `cat-content-ops critique --strict` or `cat-content validate-pack` as applicable (rubric A6 included). Rejected and tombstoned items are screened on resubmission. |
| S4 blind play | Critic | Transcript and derived-view hash | A fail drops the item; no reroll of an unchanged payload. Standalone forms keep the ADR-0210 exemption. |
| S5 two judgments | Factual and quality reviewers | Two signed verdicts with `child_safe` | Two accepts. For source-backed claims, each reviewer cites at least one URL whose first fetcher was neither the author nor legacy. For dump evidence, instead of a URL, each reviewer recomputes the file's SHA-256, extracts the page's raw text without the table parser and transcribes the cells without seeing the proposal; a script diffs it against the proposal, and the script-fetched file receipt meets the first-fetcher rule (ADR-0231 decision 5). One family in ten also gets a live ro.wiktionary spot check. For KG-only boards, each reviewer checks the predicates against the game data independently. Over 20% identical rationales, reviewer-name leaks and cited-URL reuse are checked. |
| S6 pool | Script | Item in state `reviewed` | Author, critic and both reviewers are four distinct threads |
| S7 train assembly | Assembler and scripts | Candidate commit, go/drop table, touched boards, changed resolver answers | See below |
| S8 reference and pins | Script, pin reviewer | One pin commit and the changed-case list | Case count unchanged, else Paul |
| S9 gates and landing review | Script, landing reviewer | Receipts and verdict | All green and a fresh GO |
| S10 land and close | Root and `close_landing.py` | Landing receipt and docs commit | Doc, registry and whitespace checks |

**S7 assembly.** The assembler takes these steps in order:
1. Re-run the novelty, tile-fairness, history, second-grouping and fuzzy-neighbour screens over
   the whole train plus stock.
2. Recompute derived views at the candidate, and re-blind any item whose derived view changed. A
   board's derived view is its `cat-board-view-diff` view SHA-256 under the one disturbed
   definition (ADR-0235 decision 1); a whole-bundle digest is not a derived view.
3. Assign board numbers.
4. Install:
   - `cat-content-ops import-candidates --pack-only` for boards;
   - the alias install script for forms;
   - the existing reviewed graph transaction (`scripts/import_candidates.py` → `densify_content.run`)
     for words, names and edges;
   - the ADR-0229 quick path for Quick.

   Pre-check importer entry points, schemas and output paths first, and keep generated input
   modules in scratch.
5. Check that every staged item's bytes equal its frozen payload hash.
6. Run `rank`, `derive`, `cat-content validate`, `export --check`, ops `check --check`,
   `cat-mobile-pack --check` and `cat-content-rail all --check`.
7. Refresh every changed rail binding once, under ADR-0189 and ADR-0212. A pack change can
   invalidate the world audit even when the world payload is identical, so run fresh audits.
8. For any train that adds answer keys (forms or new words), run `resolver_diff.py` over every Cald target. The landing reviewer clears
   each changed answer, or that form is dropped by itself and the diff reruns on the kept set. A
   change that only removes an existing wrong resolution may be cleared. A profanity probe that
   newly resolves is never cleared (ADR-0231 decisions 6–7). For trains with new words, links or
   captions, run `cat-board-view-diff` over all landed boards. Every board whose view changed is
   played over HTTP. Every disturbed board is blind-played again: a new board must be won; a
   disturbed existing Cald board passes with a win or a `--reblind-compare` verdict of no-worse,
   and both judges sign its top-100 change (ADR-0235 decision 2).

If an item fails at S7–S9, eject it and rebuild the train once. A second failure ends the train,
and its items then qualify one at a time.

**S8 reference and pins.** Run ADR-0186 over the full 1,206-case reference capture; a changed
count goes to Paul. Every regenerated expectation comes from the reference server or another
named independent implementation, never from the Go code under test. Cald distance expectations
come from `cat_de_roman_esti/wordgames/service.py` `distances_to` in link trains. Expectations
ship in a separate pin commit with an old-to-new list signed by the pin reviewer (ADR-0227).

**S9 gates.** All gates run on the exact candidate SHA with generated SPA assets:
- the pinned build;
- 4i: rails, validate, export, ops, mobile, the full Go race suite, vet, authcore race, doc
  inventory and whitespace;
- `GATE_OPERATOR=agent:codex bash scripts/gate.sh unit --sha <SHA> --parallel 4` and
  `env -u GATE_OPERATOR python3 -I scripts/gui-full-runner.py --sha <SHA> --parallel 4`, when
  boards, edges, captions or e2e ids change.

Every new board, every new form or alias, and every touched board is played over local HTTP to a
verified result, checking direct owner, repeat and wins where applicable. There is no pre-existing
missing-assets waiver. Exact flags: `scripts/landing/USAGE.txt` and `docs/agent-testing.md`. The landing reviewer checks the go/drop table, the player diff (same-game weight
changes included), fuzzy-neighbour shifts, resolver findings and the pins. It reviews every
flagged, Conexiuni replacement, name and synonym item, and a stated sample of the rest.

**S10 land.** Then, from the clean shared `main`, run `git merge --ff-only <reviewed SHA>`. This
is local only: no push, no pull request, no deploy. If `main` moved, merge it into `content/v5`
and redo S7–S9 on the new SHA. Keep the loop branch; remove only owned review worktrees.

## What binds where

- **The exact candidate commit and tree.** These are redone for every new commit and never
  reused: build, 4i, unit and full receipts, the reference capture and native replay, HTTP play,
  pins, the landing review, the landing receipt and any impact report.
- **The item payload hash plus its derived-view hash.** Blind play, the two judgments and source
  receipts bind here. They survive a moved base, a late board number or another train's landing
  while both hashes are unchanged.
- **Catalog reuse.** Side-catalog reviews are redone once per train. Whether an untouched
  catalog may be skipped is decided after the pilot (ADR-0230). Until then
  `impact.py` *(to build)* runs in shadow only and decides nothing.

## Source controls

The research network path is the plain cache-first source client. The hosts, cap and refusal
rules below are Paul's approved source list (ADR-0230, ADR-0231); a new host still needs him.

**Hosts.** The content hosts are `ro.wikipedia.org`, `ro.wiktionary.org`, `www.wikidata.org`,
`raw.githubusercontent.com` (FrequencyWords only) and `localhost:8077`. ADR-0228 adds policy-only
hosts. `dumps.wikimedia.org` serves the `rowiktionary` and `rowiki` dump files and their
checksum files only, through the client's dump route *(to build)*: one sequential GET per file,
10 s spacing, each dump and checksum file one read against the daily cap, one download per file and dump date,
checked against Wikimedia's checksum and pinned by SHA-256. The dump route opens for evidence only
after its parser gate (ADR-0231 decision 5); until then forms use live table reads. The
ro.wikipedia title lists are a pre-filter only. dexonline is left untouched: no reads, and its
legacy captures are not evidence for new words or forms.

**Requests.**
- Read-only HTTPS GETs only.
- Send the User-Agent `cat-de-roman-esti-content-research/5 (+https://github.com/DobosP/cat_de_roman_esti)`.
- Space requests to the same host at least 2 s apart, or 10 s on Wikimedia hosts, or longer if
  robots sets a stricter crawl delay.
- Make at most 20 new reads a day per Wikimedia host.
- Cache every response and reuse it. Record the URL, body SHA, time and first-fetch role.
- Redirects never add hosts.
- Tracked docs carry receipt metadata and a short paraphrase only.

**Refusals.**
- A robots `Disallow` drops only that path and its sub-paths.
- A terms page, a `Content-Signal` or crawler block, or an AI-crawler group drops the host for
  the run and adds one owner-queue line.
- A 429 or 5xx parks the host for one hour, or longer if `Retry-After` says so.
- When two of Paul's own rules collide, record it, keep other lanes running, name the blocked
  lanes in the report line and ask Paul once.
- Jobs cannot change the procedure, the rubric (except the Names section under ADR-0230), ADRs,
  AGENTS, validators, pins outside the pin commit, source policy or hold fixtures. The only
  exceptions are the registry check and source-client dump route that ADR-0231 decision 11 names.

## Tools, recovery and housekeeping

**Phase 0** built the core kit in `v5-pilot-1`:
- `resume.py` and the ledger metering writer;
- the extended `report_content_delta.py`;
- `close_landing.py`;
- the form screen;
- the alias install script;
- `resolver_diff.py`;
- the cache-first source client.

**Lane tools** each open their lane when they land: the quick batch proof, the Alchimie install
step, the link install with the all-boards view diff and the link span checker, the rubric Names
section (its own reviewed commit), and the caption generator. ADR-0231 decision 11 adds the
source client's dump route, the dump reader and table parser, the collision probe builder with the
profanity probe list, the counter split in `report_content_delta.py` and the registry check's
receipt-hash requirement; these may be built inside the campaign. ADR-0235 landed
`cat-board-view-diff --reblind-compare`, the paired closeout rule, `scripts/content_v5/frequency.py`
and `cat-lant-overlap`.

**Rules for every tool.**
- Each tool is its own commit with a threat model, focused tests, a portable build (Go on
  linux/darwin/windows) and a fresh-context review by a thread that did not write it.
- Inside a campaign, other tool work is repair only. It names the items it unblocks, takes at
  most 4 hours and 15% of job tokens, and gets two attempts. After that, the manual steps apply.

**Recovery.**
- Errors never stop the campaign. A tool error is retried three times with backoff; then the
  item is parked.
- An integrity failure sends the item to the drawing board with its reason and retry predicate.
- A denied capability goes to the owner queue while other lanes continue.
- Verify retained receipts before pruning owned bulky outputs.
- Docker preflight is report-only: never restart Docker or change host configuration.
- The loop never changes runtime gameplay code such as the resolver. It parks the item and tells
  Paul.
