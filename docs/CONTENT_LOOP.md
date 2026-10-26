# Content loop — V3 continuous procedure

Valid until: a later owner-approved procedure supersedes this file.
Decisions: [ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md),
[ADR-0210](adr/0210-curation-waves-and-staged-stock-landing.md),
[ADR-0211](adr/0211-content-loop-v2-all-boards.md),
[ADR-0212](adr/0212-bounded-content-workflow-repair.md),
[ADR-0213](adr/0213-correct-blind-cald-gameplay-protocol.md),
[ADR-0214](adr/0214-prospective-native-lant-captions.md)–[ADR-0219](adr/0219-land-portable-prospective-captions.md)
and [ADR-0220](adr/0220-continuous-codex-content-loop.md).

V3 replaces V2's wave, tick, commit and batch-size budgets with one continuous loop. Every V2
content-quality, review, gameplay, source-binding and install gate below stays binding. V3 starts
only when Paul gives a Codex session the V3 prompt; landing this file starts nothing. The V2
automation `cat-content-codex-only-autonomous-dataset-loop` and the V1 automation stay paused; the
V3 session replaces the V2 one when Paul starts it. V2 state, decisions, queue and evidence under
`~/work/_temp/content-loop/` are read-only history.

## Product and authority

Words that reach players are the product. In order of yield: accepted-stock curation (forms and
synonyms on existing owners, ADR-0210), new everyday Romanian concepts with their forms, and
playable boards for Alchimie, Intrusul, Perechi, Conexiuni, Cald sau Rece and Lanțul Cuvintelor.
Report qualified concepts, forms/aliases and boards per game separately, first in every status
message. Tooling, checkpoints, digests and PASS verdicts are not progress. `cat-content-ops delta`
counts identities; it does not certify playability.

A new concept no longer needs a `board_ref`. It needs a named game where it is usable, 4–8 truthful
links to separate endpoints (≥2 main-served, ≤2 batch peers, ≥2 same-category, peer closure
checked) and the quality bar below. No quota filler, category repair, hidden target approval or
fabricated links. A lemma already in accepted stock is curated, not researched again.

Authority is Paul's verbatim messages and his answers to the loop's questions, copied with their
transcript references into `~/work/_temp/content-loop/continuous/AUTHORITY.md`, plus this file and
its ADRs. Rules the loop adds for itself go in `PROCEDURE_LOCAL.md` beside it, with origin, date and
reason; they never carry owner authority and never relax a gate here. An ambiguous owner word gets
one yes/no question that names the intended action. Never infer approval from elapsed time, a
schedule, a digest or an old PASS. Read AGENTS.md, STATUS counts and the applicable
CRITIQUE_RUBRIC sections; read this file again whenever its commit changes.

## Scope fence

No GUI/frontend/runtime logic, dependency/toolchain/CI/gate changes, deploy, PostgreSQL/accounts,
mobile/device testing, secret values, fetch/pull/push/remote-ref change, merge into `main` or
deletion of evidence, branches or worktrees by the loop. Content writes are the cascade's named
data/generated files, review bookkeeping and the separate test-pin packet. A repository tooling
fix that content genuinely needs is its own commit on the loop branch with an ADR, a fresh
independent code review of the exact diff, full native gates and a portable build check
(`GOOS=linux`, `darwin`, `windows`); the landing review judges it with the content. Report
`BLOCKED: <command> -> <first error line>` for anything else outside the fence. An expectation
outside the pins allowlist stays `NEEDS-OWNER: <test> expects <old>, content now <new>`; never
land red.

Use `export PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local`; `go version` must be go1.27.3.
Python importer: `~/work/cat_de_roman_esti/.venv/bin/python`, `PYTHONPATH=scripts:.` from the loop
worktree, never `python -I` for importer execution. All checks run from the loop worktree root:
shared main's .venv makes cat-doc-check refuse. Never run bare cat-content or cat-mobile-pack
without --check outside 4f. Only 4f exports content; 4a's approved importer is the only KG apply
path, with explicit importable --data-module. import-candidates requires both review artifacts
before any preflight.

## One session, one worktree, one branch

- One Codex chat runs the loop until Paul stops it. One heartbeat automation, `cat-content-v3`
  (every 5 minutes, targeting that chat), wakes it. Never delete it and never create a second one;
  Paul pauses or stops it.
- One long-lived worktree `~/work/_worktrees/cat_de_roman_esti/content-continuous` on branch
  `content/continuous`, created once with
  `git -C ~/work/cat_de_roman_esti worktree add --no-track -b content/continuous <path> main`.
  No per-batch worktree or branch, and never the auto-fetch worktree helper.
- Batches are sequential commit series on that branch, ids `n1`, `n2`, …: module
  `scripts/<slug_underscored>_v3_<id>_data.py`, build version `fixture-v3-<id>-<slug>`, review
  directory `docs/reviews/v3-<id>-<slug>/`. V1 and V2 names remain history.
- When local `main` moves, merge it into the loop branch with `git merge --no-edit main` (local
  refs only; never rebase), then rerun C0 for the new base. A merge conflict parks the open batch;
  never resolve it by editing reviewed bytes.
- When a landing review marks a batch `rework` (see landing review), keep the old tip as branch
  `content/continuous-archive-<n>`, then `git checkout -B content/continuous main` in the same
  worktree and re-apply the accepted items of the reworked and later batches as the next batch.
  Item reviews stay valid for byte-identical items; rails, audits and gates are always fresh.
- State is `~/work/_temp/content-loop/continuous/state.json` (≤2 KB: current batch, step, open
  question, rolling 24-hour hours by kind) and an append-only `ledger.jsonl`, one row per stage:
  `{stage, batch, kind: content|tool|review|install|wait, start_utc, end_utc, items_in, items_out,
  verdict, first_error}`. Evidence is `~/work/_temp/content-loop/continuous/evidence/<id>/`,
  text-first, about 50 MB per batch at most; write compact manifests before pruning transient
  bytes and never prune review inputs. Write nothing else: no publications, prior-state copies,
  per-stage prompt rewrites or consumption reports.

## Continuous cycle

The loop is never idle. While a batch waits for a reviewer, a tool fix or a landing, it prepares
the next one. A batch moves through these steps; C3–C7 detail follows.

1. **C0 Baseline.** For each new base commit run `cat-content validate`, `export --check`,
   `cat-content-ops check --root .. --check`, `cat-content-rail all --root .. --check`,
   `go -C go-backend test -count=1 ./internal/contentrails/ ./internal/contentbuild/ ./internal/httpgolden/`
   (`-count=1`: the rubric is read from outside the module root) and verify the helper manifests.
   Record the result against the exact base SHA, go version and helper manifest SHA, and reuse it
   while all three are unchanged; never reuse it across a different base. Red unchanged
   validate/export/ops stops content work and is reported. Red rails disable install.
2. **C1 Select.** Aim for 20–60 items in a class G batch (curation or new vocabulary) and up to 24
   boards in a class P batch; never mix KG and board changes in one batch. Choose from accepted
   stock first, then new everyday vocabulary, then the thinnest board cells of the need map. Plan
   a smaller batch only when the eligible pool is smaller, and say so; never plan one item.
3. **C2 Research and author.** Quality bar and research method below. Dictionary requests across
   all workers stay at least 2 seconds apart as courtesy to the sites; there is no per-tick or
   per-batch item cap.
4. **C3 Screens.** Compatibility and lint below. A failing item goes to the drawing board; the
   batch continues.
5. **C4 Gameplay critic** for boards and for vocabulary that changes a named board's route.
6. **C5 Freeze.**
7. **C6 Review round 1.** Per-item outcomes; failures go to the drawing board.
8. **C7 Stage, review round 2, install cascade 4a–4i and the test-pin packet** for the surviving
   items. Gates must be green outright.
9. **C8 Landing candidate.** Write the batch README (prelanding record below), commit, and add a
   row to `~/work/_temp/content-loop/continuous/LANDING_QUEUE.md`: batch id, candidate commit
   SHA, qualified items per game, gate results and the test-pin packet. Then start the next batch on
   top of it.

**Drawing board.** `~/work/_temp/content-loop/continuous/DRAWING_BOARD.md` keeps every dropped
or rejected item with its reason and the step that dropped it. Return to it when evidence or
tooling changes; never retry the same bytes without a new reason, and never pad a batch with it.

## Failure handling and stop conditions

There are no tick, commit, time or batch-size budgets.

- A content verdict drops the item, never the batch.
- A tool or infrastructure failure pauses the batch. Fix the tool in the tool lane, then resume
  the same batch; no new plan, no new scope, no closed batch. After two failed fixes of the same
  tool, park that batch, report once with at most three options and a recommendation, and keep
  working on other batches.
- Every blocker without an executable next step gets, in the same turn, one message to Paul with at
  most three options and a recommendation. The loop then continues with independent work. Never
  delete the heartbeat to stop polling; quiet turns are cheap.
- A platform approval refusal is never worked around. Ask once in plain words; continue other work.
- The loop stops only when Paul stops it, when free disk falls below 12 GB (`df -h /` before corpus
  capture and full tests), or when the unchanged base fails C0 validate/export/ops. It reports
  each stop once and stays quiet until something changes.

**Status messages** are sent only on change, at most 10 plain lines: qualified, pending and
drawing-board items per game since the last landing; active hours in the last 24 hours by kind;
what is running; any question for Paul. Unkeyed SHA-256 digests are called digests, never
signatures; a reviewer's `signed_at` is that reviewer's own timestamp, not authentication.

## Landing review (a separate Claude Code session)

Paul starts a landing review whenever he wants; the loop keeps running. The reviewer:

1. Reads `LANDING_QUEUE.md` and takes the queued candidates in order.
2. For each, checks out the candidate commit detached in a review worktree, reruns the 4i gates,
   reviews the items against the quality bar and the floors (all items, or a stated sample per game
   plus every flagged item), the reviews and critic logs, and the test-pin packet.
3. Lands the longest fully accepted prefix: `git merge --ff-only <candidate SHA>` on local `main`
   when main has not diverged; otherwise merges the candidate into a landing branch from main,
   reruns 4i and fast-forwards main to it.
4. For the first candidate it does not accept, records each rejected item and reason in
   `DRAWING_BOARD.md` and marks the batch `rework` in `LANDING_QUEUE.md`.
5. Never pushes without Paul's word. Removes only its own review worktrees and verified-merged
   review branches (ADR-0037); the loop branch and worktree stay.

## Tool lane

Read-only helper CLIs live under `~/work/_temp/content-loop/miner/` and its `versions/` and are
pinned by SHA-256 manifest. A qualified helper version is reused by its pinned SHA in every batch;
a batch never authors or edits a helper. A new or changed helper needs, before any code, a written
threat model (default: single-user development host; accidental misuse and stale inputs in scope;
a concurrent same-user adversary out of scope unless Paul says otherwise) and a review checklist
(hash and parse one buffer, regular non-blocking input opens, outputs in a fresh per-run directory
with exclusive create, portable build, CLI refusal tests, no claim beyond the code). Then one
fresh independent code review of the exact change, meaningful real-output regressions and a new
pin. Findings about correctness, output integrity, portability or overclaiming always block;
findings that assume an actor outside the threat model are recorded as notes. Helper authors never
approve their own code.

- `python3 need_map.py --root <task> --out <evidence>/need-map.json`
- `python3 compat_index.py --root <task> --out <evidence>/compat-index@<sha>.json`
- `python3 mine.py --root <task> --compat <index> --cell <game>:<category>:<difficulty> --per-cell 3 --budget <bounded-count> --out <evidence>/mining.json`
- `python3 critic_blind.py build --root <task> --input <candidate> --public-out <evidence>/critic-public.json --key-out <evidence>/critic-key.json`
- `python3 critic_blind.py compare --key <private-key> --response <critic-answer> --out <evidence>/critic-comparison.json`
- `python3 sha256_manifest.py create --base <evidence> --out <evidence>/manifest.json`; verify with `verify --manifest <manifest>`.
- `python3 review_independence.py --author-seal <sealed-urls> --reviews <factual-envelope> <quality-envelope> --artifacts <M1-M5-index> --out <evidence>/independence.json`

Run these by absolute helper path; they read repo bytes, never import/execute source modules, and
write only inside content-loop scratch. Outputs are hypotheses/measurements; they do not stage,
reserve, promote or certify a board. The private critic key and sealed author source set never
enter the critic/reviewer input; the critic needs visible tile text/captions to play, but no
group/predicate/solution labels. The Alchimie public challenge lists every productive pair of its
witness routes (unordered), so Alchimie M4 judges fairness with the full rule book; its par match
is not evidence of blind solvability.

## Need map and game floors

The need map replaces the theme backlog. Derive eligible boards per game/category/difficulty
against exact base blobs, reserve, tombstones and ranking; target four per cell. Publish total,
approved, held, eligible and starter shelves separately. A no-candidate cell is a shortfall, not
permission for weak vocabulary or generic links.

| Game | Existing floors and blind critic |
| --- | --- |
| Conexiuni | Four typed 4-member hubs; validate-pack and strict FAIL-clean critique: tile fairness, red-herring budget, duplicates against full inventory/tombstones, reskins, member overuse >8. Critic solves 16 shuffled tiles without group labels, rejects a second valid partition, supplies “each tile …” predicates and recognizes ≥3/4 per group. |
| Cald | ≥5 actual direct non-distractor predecessors, reachable ≥120, responsive ≥40, salience reviewed. Critic supplies five openers before distances; ≥1 within two hops and one dominant sense. Main-served predecessors, not pending-wave totals, decide the floor. |
| Lanț | Normal shortest path 3–4 hops, greu 4–6; BFS-optimal, ≥2 first hops, layers ≥2, captions on every optimal edge. Critic plays only exposed captions, explains each transition and reaches the target within par+2. |
| Alchimie | Closure mining, greu gaps first: 5–7 seeds, exact action par, ≥2 openings and live audit-projections. Critic plays audited openings, infers target and rejects free pairs. No new discovery-world concept (252/256 is historical headroom). |
| Intrusul | Same-type hub trio plus sibling-hub intruder, valid quick shape; ≥2/3 member links ≥0.60, intruder has no member link. Blind critic names one honest predicate and odd tile; another natural odd-one-out reading fails. Rubric I (below). |
| Perechi | Four edges ≥0.60, unique maximum-weight perfect matching among 105, all 24 cross-links <0.60; starter has zero real cross-links. Critic pairs eight tiles blind and rejects alternative pairings or ambiguous tiles. Rubric J (below). |

WARN until Paul ratifies them: Perechi matching margin ≥0.15, Alchimie productive-pair
cap ~40%, Lanț typed-edge share ≥50%, Conexiuni cross-link bands usor 0–1/normal-greu 1–3, and the
Cald gastronomie-target freeze (table in the unbound I/J section below). Record metrics/denominators in each batch README; these
proposals never override existing hard FAIL floors. The JS critique mapping stays unchanged:
I/J (unbound section below) require explicit critic/reviewer briefs until a separately authorized
code task maps them.
The derived catalog's 123-source freeze/336-board payload stays frozen. Repairing the 83 historical
FAIL-lint Conexiuni boards is a separate task; do not widen scope to make a batch pass.

## Batch step detail (C3–C7)

The M-numbers name the same gates as V2: M2 = C3a, M3 = C3b, M4 = C4, M5 = C5, M6 = C6 and
M7 = C7. "M1–M5 artifacts" means every C1–C5 artifact of the batch.

- **C3a Compatibility (M2).** Screen every planned/observed form and selected sense against normalization_map,
  normalized_index, labels, aliases, discovery_world, Cald projections, current accepted/held stock,
  exact accent-preserving ReviewedUnresolved and v72 DEFERRED_AMBIGUOUS_TERMS. Other-sense owners
  remain owned; never steal aliases. Screen BLOCKED_ALIAS_FORMS, collision pairs, fuzzy deny and all
  DEFERRED_* in scripts/{contexto_common_words_v44,basic_words_v30,basic_words_v32,basic_words_v33}_data.py,
  tests/ and every docs/reviews/*/graph-candidates.json, including pre-V1.8. Cite each hit as
  `held: recorded exclusion <file:line>`; unknown dynamic expressions fail closed. Also screen board
  signatures (Conexiuni quads/reskins, Lanț endpoint pairs, Cald targets, Intrusul/Perechi sets),
  reserve/tombstones, demotions and owner holds. No observation is an approval/reservation.
- **C3b Lint pre-screen (M3).** Use validate-pack and critique --strict on an evidence-directory pack copy,
  using validate-pack --root <task> --kg <kg-copy> --pack <pack-copy>. For critique there is no
  pack override: prepare a bounded separate scratch source-readset root with matching fixture
  mirrors, runtime/rubric/ledger binding files and temporary pending IDs; run critique --root
  <scratch-readset> --ids <exact-temporary-ids> --strict without --write. Record every copied byte
  and before/after repo hashes; no workspace, dependencies or build caches are copied. No importer,
  import-candidates dry run or repo mutation. Unknown parser/CLI support is BLOCKED, not invented.
- **C4 Gameplay critic (M4).** Independent critic blind-solves the game per the floors above. Use sanitized
  input and a separately sealed private key; compare its submitted solution mechanically, then
  adjudicate ambiguity/predicate/recognition in the critic's own words. One line per failure.
  The critic is a pre-review filter, never a signer; its sanitized log joins the freeze bundle.
  When a batch changes the KG and a Lanț critic needs captions for new edges, generate the
  explicitly unapproved caption artifact with native `cat-content prospective-lant-captions --root ..
  --kg <abs> --pack <abs> --out <abs path outside the repository>` from the exact frozen KG and pack.
  It runs on Linux only; other platforms refuse it (ADR-0219). Build the producer from the root it
  binds: the artifact binds the KG, pack, rubric, frozen rules and the source files of the
  `cat-content` production closure under `--root`, not the running binary. Give the artifact and
  its separately recorded SHA-256 to the pinned blind helper, which re-binds those inputs, requires
  complete directed-edge coverage and keeps provenance in the sealed key. The preview is not a
  serving bundle or any export, source, ranking or rail approval; the unchanged full exporter must
  still reject stale pins. Path, descriptor and output rules for producer and helper are in
  ADR-0214–ADR-0219. Before first use on a new base, run helper v5 (ADR-0218) once against it in the
  tool lane, then reuse it by its pinned SHA.
  For Cald, the public challenge includes only the exact native player-visible `difficulty` and
  `board_category` read from the bound board; never add a target/board/source/graph field, neighbour,
  clue, example or authored guess. The critic commits exactly five ordinary normalized-distinct
  guesses before feedback using opening response schema 2 (`schema`, `challenge_id`, `openers`);
  pre-feedback target knowledge is unassessed, while final target/sense ambiguity must be false.
  Preserve opener bytes/hashes/sequence/receipts and diagnose each property independently. Persist
  the exact full comparator return exclusively before local assertions. One of those same five
  openers must have raw distance ≤2; adaptive guesses never satisfy the floor and cap 8 is unchanged.
- **C5 Freeze (M5).** One batch module/board unit, candidates.json per category, canonical manifest of
  every binding/capture and frozen critic log. Refuse missing/hash-mismatched captures, unresolved
  compat or a missing live mechanic. Seal author sources/URLs separately. Never mutate signed bytes.
- **C6 Review round 1 (M6).** Fixed factual and quality reviewers each judge the whole frozen batch once,
  adversarial fresh web sources, signed before seeing each other. Give reviewer-visible hashes/candidate/dossiers/critic log, withholding author URLs/captures
  in a separate sealed bundle until both sign. Author sources stay sealed; each new or changed item needs ≥1 reviewer-chosen normalized URL outside the author's set. Reject a report with
  >20% repeated normalized rationale strings, >20% identical rationale rows across the pair, or a
  reviewer name appearing anywhere in an M1–M5 artifact. Record each per-item capture binding.
  Run the sidecar independence guard before accepting the pair. Outcomes are per item: an item a
  reviewer rejects or holds, or one without a reviewer-chosen source outside the author set, goes
  to the drawing board with its reason, and the rest continue. A broken whole-review rule (signing
  order, >20% identical rationales, reviewer name in an author artifact) voids the pair: rerun the
  round once with fresh reviewer contexts, then park the batch and report. Record the go/drop table
  under the standing owner delegation (ADR-0212, ADR-0220) and continue; an explicit item hold or
  separately required owner row remains a hold, and delegation is not an item-specific approval.
- **C7 Stage plus review round 2 (M7).** Only after go/drop and fresh gates. Pack: run PACK_ONLY steps 2–4:
  import-candidates --pack-only --write, critique --dossier --write, live Alchimie audit for its
  separate review batch, same two fixed reviewers as verifier/analyst, build-review then
  apply-review --write. Quick boards follow 4c–4e candidates/reviews/proposal/audit/finals. G uses
  curation 0–3 then full 4a–4i. Preserve independent ordering in both rounds; native raw JSON exact
  keys stay unchanged, so signed_at, source seals and access receipts are SHA-bound sidecar
  envelopes. Run review_independence.py before build-review; native build-review does not yet
  implement V2 sidecar checks. Run the guard on M6 (round 1), round 2 and curation step-3 review
  pairs, including flows that never call build-review. Rail initial/final pairs do not run the
  guard: record both sidecar envelopes in the manifest and require each `first_peer_read_at` to be
  later than both `signed_at` values; inherited items are checked by predecessor item-hash equality
  (4d). The per-item URL and 20% rules reach a rail pair only through a sidecar raw file listing
  its new or changed items, run through the guard when that list is nonempty (rail finals carry one
  rationale each and have no 20% metric). Each review round has its own author seal/unseal
  envelope: the guard requires every `signed_at` before that round's unseal. The helper reads only `{reviewer, items[{id, rationale,
  sources}]}` raw files and a complete M1–M5 artifact index. Where the native file has another shape
  (pack-only `verify_*.json`, round-2 reviews, curation graph reviews), the reviewer also signs a
  sidecar raw file in the helper's shape, SHA-bound to the native file, and the guard runs on the
  sidecar. Curation has no M3/M4 artifacts: a fresh independent Codex APP code review and real
  regressions must qualify a separately pinned helper version accepting the curation steps 0–2
  index; the original manifest is preserved. Without that prerequisite curation step 3 is
  BLOCKED. Stop if any check cannot be
  established, never hand-check instead or claim future code.

## Fixed roles and mechanical independence

Each batch fixes author, factual-v3-<id>, quality-v3-<id> and critic-v3-<id>; they are distinct.
The landing reviewer is Paul's separate Claude Code session. Each working helper, reviewer and critic runs in a separate fresh
Codex APP context (`fork_turns=none`), using the owner-pinned role model/effort; critic and factual
use different rungs. Retain exact prompts, native dispatches and action/research logs under
`evidence/<id>/roles/<name>/`; never fabricate CLI transcripts. Only the frozen role-appropriate
bundle is provided. Helper authors never approve their own code. No intermediate Claude login,
CLI/app review or copied verdict is a working prerequisite.
The same factual/quality names sign round 2 as verifier/analyst; roles do not change their identity.

Source seals, actor artifacts, report signatures, capture IDs and access receipts are retained by
manifest. Both signed_at timestamps must exist before either receives/reads the other's report;
first-peer-read receipts must be later than both signed_at values. A timestamp assertion is not
proof of process isolation: retain dispatch/delivery transcripts. After both sign, unseal sources
for mechanical set-difference checks; stale/missing receipts or >20% identical rationales void the
review. Native raw review JSON gets no unsupported metadata fields. The scratch preflight checks
the envelopes; the existing native build-review/apply-review binding checks still run unchanged.
For the 20% rule, normalize whitespace/case; within each report divide duplicate rationale rows
beyond their first occurrence by all item rows, and across the pair divide identical per-ID rows
by all IDs. More than 20% in either comparison fails. Normalize URL scheme/host/default ports,
remove fragments and sort query pairs; preserve path/word accents. URL set difference uses the
whole sealed author set: the sources the author actually captured and cited for the batch, never
every URL-like string found in actor inputs; every reviewer-chosen capture is independently retained and hash-bound.
The actor/artifact index lists every M1–M5 path and SHA; scan full bytes, not just actor fields.
Helper CLI envelope fields and smoke examples are in
`~/work/_temp/content-loop/miner/INDEPENDENCE.md`; where its scope differs (it still names every
rail pair), this procedure wins.

## Install cascade — exact substeps 4a–4i

One commit per lettered sub-step; each rail in 4e is a separate sub-step. Go tools via
   `go -C go-backend run ./cmd/<tool> ... --root ..`. Class P skips only 4a; both P and G
rebuild, independently review, audit and re-sign quick, world and extensions under the new source.
The world audit binds current pack/ranking bytes even when world item semantics are unchanged;
retaining that old signed audit after those bytes move is forbidden (ADR-0212).
   - 4a Apply the step-3 module (templates: scripts/everyday_inputs_v1_6_data.py for aliases,
     scripts/everyday_graph_v1_3_data.py for nodes and edges). Class G only, after the recorded go/drop table;
     no automatic removal from any deferred or blocked list. Run `apply_common_words_v24.py --data-module <module>
     --dry-run` (expect preflight GREEN), then without `--dry-run`.
   - 4b `cat-content-ops rank --write`, `derive --write`, `check --check`; `cat-mobile-pack --check`
     (4a refreshed the contract for G; P changes no KG, so retain it; never write it with the Go tool).
   - 4c Copy authored-v<K>.json to authored-v<K+1>.json: version K+1, `parent_source_sha256` =
     sha256 of authored-v<K>, `base_commit` = the full 40-hex wave_base, and repoint the world
     archives to the last installed wave's native/world files listed in installed-authorities.json:
     world_candidate and world_previous → candidate.json, world_factual → factual-review.json,
     world_quality → quality-review.json, each with its sha256. K is derived at C0 from the current source chain. For B-quick append only the
     frozen, go-accepted quick records to authored-v<K+1>.quick.boards before candidate generation;
     retain category/difficulty/game/id/payload/rationale/source_id/sources and exact per-record
     hashes, no new IDs or semantic edits outside the reviewed payload. A mere copy would add no
     boards. A pack-only batch changes no authored quick payload, but still regenerates bindings.
     For both P and G use quick, world, extensions, with fresh bindings and world acceptance: `cat-content-rail <r> --source <abs> --candidate-out
     <abs>/docs/reviews/<wave>/native/<r>/candidate.json`.
   - 4d The two reviewers write native/<r>/factual-review.json and quality-review.json covering every
     item (schema in review.go). Only authored items whose bytes/semantics are unchanged from their
     exact predecessor may be inherited: true. New/changed quick boards need fresh judgments even
     without a KG change. For inherited items keep the
     predecessor item's `sources` URLs (a factual accept needs at least one http(s) URL; repo paths
     are refused) and name the previous record in `rationale`. World reviews also carry
     `world_verdict: "accept"`, `world_rationale` and one `concepts` row per candidate concept {id,
     concept_sha256 = sha256 of the concept rendered like rail output (sorted keys, two-space indent,
     trailing newline), verdict, rationale, sources, inherited}.
   - 4e Every rebuilt rail command in 4c–4h passes `--source <absolute path of authored-v<K+1>.json>`; the
     class-P world is rebuilt and reviewed under that same source. The `--write` and
     `--installed-authority-out` commands also repeat `--candidate C --factual-review F
     --quality-review Q`. Serially for quick, then world, then extensions: `--candidate C
     --factual-review F --quality-review Q --proposal P` (P =
     docs/reviews/<wave>/native/<r>/proposal.json); `--audit-catalog P --audit-out A`; the reviewers
     write final-factual/final-quality reviews bound to A; then `--proposal P --live-audit A
     --final-factual-review FF --final-quality-review FQ --expected-sha256 <sha256 of P> --write`.
     Write A as docs/reviews/<wave>/native/<r>/audit.json and FF/FQ as final-factual-review.json /
     final-quality-review.json in the same directory: these are the documents installed-authorities.json
     will bind in 4h. Installed-authority-entry drafts go under
     `~/work/_temp/content-loop/evidence/<id>/rail/<r>/`. Before the extensions proposal, do the 4f pin
     edits (derived_catalog_v38 = the digest 4b produced, quick_games_v92 = the digest the quick
     `--write` installed): the extensions builder refuses `reviewed artifact digest drift` while any
     `reviewedPins` value is stale. Each rail is its own commit (4e-quick, 4e-world,
     4e-extensions).
   - 4f Pins (edited in 4e, before the extensions proposal): the derived_catalog_v38 and
     quick_games_v92 values in `reviewedPins` (go-backend/internal/contentbuild/build.go),
     `CATALOG_SHA256` in cat_de_roman_esti/wordgames/quick_catalog.py and
     `DEFAULT_DERIVED_CATALOG_SHA256` in cat_de_roman_esti/wordgames/derived_catalog.py. Then
     `cat-content export --root ..` and `export --root .. --check`.
   - 4g HTTP corpus: first `df -h /`; below 12 GB free, stop and report (disk). Build `cat-server` into scratch; copy
     docs/reviews/go-native-toolchain/archived-reference/capture_reference.py.txt to scratch, changing
     exactly three lines: ROOT (archived line 21), the reference label (line 393) and output path
     (line 394); attach `diff -u` against the archived reference to the corpus report and refuse any
     other change. Match assignments by content if line numbers move. Run it with the repo venv,
     `CAT_ACCOUNTS_ENABLED=0` and `--binary <cat-server> --runtime go` (expect the case count of the
     previous reviewed corpus block, 1206 since V1.13; any other count is `NEEDS-OWNER` with a
     case-list diff). Record the actual count, never edit it to fit and never bypass an HTTP case.
     Move the .json.gz to go-backend/internal/httpgolden/testdata/ and, in golden.go, add only a
     renamed copy of the previous reviewed block as `reviewedV3<ID>()` (e.g. `reviewedV3N1()`), its SHA
     constant, embed line and ForSources call/slice entry. Corpus: `python-http-parity-v3-<id>.json.gz`;
     selection test: `v3<id>_selection_test.go` (e.g. `v3n1_selection_test.go`). V1 and V2 names stay historical.
   - 4h Bind the installed authorities. Per rail run `cat-content-rail <r> --source <abs> --candidate C
     --factual-review F --quality-review Q --proposal P --live-audit A --final-factual-review FF
     --final-quality-review FQ --expected-sha256 <sha256 of P> --installed-authority-out
     <scratch>/rail/<r>/entry.json` with the 4e documents; the command re-runs the native audit under
     the current binary and refuses with "final live audit incomplete/stale/unaccepted" if the installed
     behaviour no longer equals A (after 4f this happens only when the export changed what the
     quick/world replays observe). On that refusal only: rerun `--audit-catalog P --audit-out A`, have
     both reviewers re-sign FF and FQ to the new A, retry once (a second refusal parks the batch and is reported). Then
     assemble
     go-backend/internal/contentrails/sources/installed-authorities.json (append authored-v<K+1> to
     source_chain; replace all three rail entries for both P and G) and
     swap the sha in installed_authorities_pin.go via the metadata template (the file must equal
     PinBytesForInstalledAuthorities exactly). No second installed audit, no second reviewer round and
     no runtime freeze.
   - 4i Gates: run after the separate `pins` commit exists (moved count and selection
     expectations are red until then). First `df -h /`; below 12 GB free, stop and report (disk). `cat-content-rail all --check`, `cat-content validate`, `export --check`,
     `cat-content-ops check --check`, `cat-mobile-pack --check`, `go -C go-backend test -count=1 -race
     -timeout 60m ./...`,
     `go -C go-backend vet ./...`, `go -C shared-go/authcore test -count=1 -race ./...`, `cat-doc-check
     --root ..`,
     `git diff --check` — no new red versus C0. Known pre-existing reds on main: httpapi
     TestManagedSPA* (frontend not built) are historical examples, not a standing waiver. Any other red without a C0 record counts as
     pre-existing only if the same command is also red on the exact main baseline in a comparison
     task worktree, never the shared checkout. Rail checks/contentrails tests must be green outright.
     Play every new board once through the local cat-server HTTP API to a verified result. For every
     new alias, retain a before/after fuzzy-neighbour probe plus a Cald guess; verify owner slot,
     repeats/win identity and snapshot impact. Corpus parity alone does not test alias input behavior.
     Keep the playthrough log at most 200 lines; link exact per-item results in the manifest.
   Install may touch only: the module; the apply transaction files (both kg_sample.json, both
   games_pack.json, tests/fixtures/cat_mobile_app_pack_contract.json); board_rankings_v37 and
   derived_catalog_v38 (both fixture dirs); quick_games_v92, alchimie_discovery_world_v92 and
   alchimie_recipe_extensions_v92 (cat_de_roman_esti/fixtures only); bundled.json and digest.go via
   export; the pins in 4f; authored-v<K+1>.json, installed-authorities.json,
   installed_authorities_pin.go; the corpus and the golden.go block; the rail files under
   docs/reviews/<wave>/native/ (including audit.json, final-factual-review.json and
   final-quality-review.json under docs/reviews/<wave>/native/<r>/); Go or frontend testdata that
   an existing generator rewrites (name it in the README); the pool, the wave README and
   docs/STATUS.md. The Python reference suite is not a gate (ADR-0186): leave
   tests/current_content.py alone and note any Python red in the README. Never new or edited
   `_test.go`, new Python tests, new repo scripts other than the wave data module, or
   rules_unicode15.json, except the test-pin packet (ADR-0210): in one separate `pins` commit,
   update only the expectations the landing moves — the new `v3<id>_selection_test.go` block in
   go-backend/internal/httpgolden with its predecessor's "did not move past" edit, the board and
   approved counts in internal/contentops (`check_test.go`, `contentops_test.go`) and the Cald
   inbound maps in internal/contexto — list each old -> new value in the README, and the landing
   review approves that packet before it lands.
   The separate `pins` commit touches only `go-backend/internal/httpgolden/v3<id>_selection_test.go`
   and its predecessor's selection test,
   `go-backend/internal/contentops/{check_test.go,contentops_test.go}`, and
   `go-backend/internal/contexto/content_v1_3_test.go`. List each old → new value and `git show --stat`;
   class P changes no KG/Cald map. No unrelated test logic changes. New/edited Python tests,
   `tests/current_content.py`, rules_unicode15.json, runtime and GUI remain outside scope.
   If the loop worktree is dirty or a merge is unfinished on waking, preserve every byte, finish or
   report the owned step, and never reset/clean, delete a packet or touch another task's work;
   merging main follows the branch rules above.

## Cascade classes and prelanding record

**Class P (pack/quick):** no KG change; M7 pack/quick review as appropriate, then full 4b–4i.
Quick, world and extensions all receive the new authored source, initial reviews, proposal,
current audit, fresh final acceptance and replacement authority entries. Exact unchanged item
semantics may use the inherited-item rule in 4d; the world audit/finals themselves are fresh.
Pack/ranking bytes are world audit inputs, so unchanged world gameplay does not permit stale
signed bindings. Default all --check, corpus, pins, gates and per-board HTTP play remain mandatory.
**Class G (curation/vocab-gap):** full 4a–4i including world. No KG and board additions co-land;
Alchimie has its own review/audit batch even within a multi-game P landing.

The prelanding record prepares pool dispositions/reasons and docs/reviews/v3-<id>-<slug>/README.md (≤80 plain lines):
player gain, table summary, actual owner decisions, retrospective, ≤3 proposals, every BLOCKED/
NEEDS-OWNER and every item sent to the drawing board, plus every comparison worktree the batch
created (the landing session removes them). Keep the exact installed-authority rail files plus ≤10 small text files (README,
graph reviews, playthrough log, reference/capture_v2_<id>.py.txt). Raw captures, role transcripts,
build output and failed attempts stay under evidence, never in repo docs. Preserve all bytes;
retention cleanup belongs to the later Claude landing session after verified NAS copy.
Only after the prelanding checks update STATUS counts/Last verified within its 120-line budget;
if doing so requires an out-of-scope history-file edit, report NEEDS-OWNER. Run cat-doc-check
--root .. --inventory docs/tracked-markdown.json and git diff --check; commit, add the landing-queue row.
If main moved, the loop merges main into its branch first (branch rules above) and reruns 4i, and
4g when httpapi or content packages changed.

## Curation wave (class G; ADR-0210)

Curation steps **0–3** replace M1–M4; M2 compatibility still applies fully. Step 0 is C0. Step 1 chooses ≥20 accepted existing-owner morphology families from final module
payloads (never planned/observed lists), recording original wave/id/closure and every exclusion.
The canonical stock is `docs/content-consolidation/v1-8-through-v1-32/current-stock.json` on its
branch; V1.38–V1.42 payloads are read from their preserved content/v1-* branches with `git show`,
never executed. Step 2 rebinds retained own-head DEX/DOOM3/table and second-source evidence; missing captures are
ineligible. Step 3 consolidates one module and obtains fresh whole-batch dual review with the V2
independence sidecars and guard, then records go/drop under the standing delegation, retaining
item-specific owner holds. Step 4 is full 4a–4i and test pins; step 5 queues the landing candidate.

Curation started (V2 C1) with V1.38–V1.42 final payloads, including Avion, Cinematograf and Interfon; lane labels
alone do not prove morphology eligibility (Interfon's historical lane differs). Hold any family
with a key hit in the exact M2 exclusion sources as `held: recorded exclusion <file:line>`. Mănăstire and Sucitor (without bare sucitoare)
get separate go/drop rows, each `snapshot rebuild: <files>`; Paul's go on a row accepts it.
Bare sucitoare always stays excluded; Ie never gets ii/iei. Do not override earlier exclusions,
clip a required family or reopen a hold automatically. Fresh verification is required for weaker
review tiers; V1.33 specifically needs new source research, never missing /tmp captures. V1.14
items are re-applied through this cascade; never merge its partial branch or ask its declined
HTTP exception. Preserve all content/v1-* refs (NAS bundle ac0a2b63… under
branch-archive/cat_de_roman_esti/2026-10-22-content-loop-branches/).
While stock remains, at least one in each three batches is curation. Order by evidence tier,
then documented board yield; any read-only yield simulation uses in-memory data, never source
module execution or import dry-runs. Board candidates are re-screened after each class G landing,
including Lanț optimal routes and Alchimie par. Stock matches turn vocab-gap into integrate.
Keep corrected stock measures: 4,968 single-token +766 multiword inputs (three display-only
labels separate); 3 nodes cross incoming 5 using main-served predecessors, 45 only when complete
pending waves co-land. Holds are records, may overlap later accepted lemmas, and never leak.

## Quality bar

Hold when unsure; reject only factual error, archaic/poetic-only register or duplicate. Familiar
Romanian everyday/school/culture relevance and an honest readable predicate are mandatory: a
Romanian 12-year-old knows it, or it is school or culture vocabulary; absence from the frequency
list never rejects a concrete everyday noun, animal, school object or tradition (mărțișor, barză).
People/places/works use Romanian Wikipedia or better. Frequency is positive only. DEX sense/
register, exact-head DOOM3 and that head's attributed ordinary flexion table plus one Romanian
second source are required for lexical additions. Do not borrow another head's table; qualified
compounds require component morphology and separate compound-sense evidence. Only selected-sense
substitutable inputs are synonyms; morphology, regional/diminutive/qualified inputs stay distinct.
Normalize ş/ţ to ș/ț; inspect accent-preserving spellings before trusting folded ranks. No two
fold-equal spellings are separate additions, no other-sense key theft, no threshold relaxation.
Regional or popular forms are inputs only when no other owner exists, reported as "regional input",
never as synonyms; înv./poet. forms are not aliases. Give a closed set one honest parent (Anotimp,
Punct cardinal, Crăciun) instead of wiring every member to every other. Truthful label_ro reads
from source to target. Lanț shows only relation captions (is_a, part_of, created_by,
contemporary_of; others show "legătură directă"), so prefer an honest is_a or part_of.
Current game/critic floors above and all applicable rubric FAILs remain binding.

Research method (vocab-gap, curation re-binding and reviewer research): dexonline
(`https://dexonline.ro/definitie/<word>/json`; DEX for sense and register labels, DOOM 3 for forms;
follow redirects and keep only definitions whose headword equals the lemma), one second source
(ro.wikipedia, ro.wiktionary, or Romanian news for a popular sense), and frequency from
`https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt`
(best rank among forms). Store URL plus a one-line paraphrase, never copied definitions. The writer
can only add nodes, edges and aliases and remove edges; anything needing an alias moved or a label,
description, category or Lanț caption changed is `held: needs owner-approved writer`.

## Rubric I/J and review protocol (unbound trial text)

This section is not digest-bound. `docs/CRITIQUE_RUBRIC.md` is bound into rankings, the derived
catalog, all three rails and the installed authorities (`contentbuild.RubricSHA256`), so folding
this text into it changes that digest. That fold is a separate owner-authorized class-G rubric
transition (rubric constant and Python pin, rank/derive, re-audit of all three rails, authorities,
corpus), never part of a class-P landing. Rubric section A applies to all six games.

The proposed rules below are **WARN until Paul ratifies them**; record the observed metric and the
reviewers' reasoning in each batch README.
Existing validator floors and FAIL lints remain hard requirements; this trial does not weaken them.

| Game | Proposed V2 warning target |
|---|---|
| Conexiuni | cross-links: `usor` 0–1, `normal`/`greu` 1–3 |
| Cald sau Rece | freeze new `gastronomie` targets; any proposed addition is a warning |
| Lanțul Cuvintelor | at least 50% typed edges on the route |
| Alchimie | productive pairs at most 40% |
| Perechi | maximum-weight matching margin at least 0.15 |

These are review measurements, not new implemented lints. The workflow's current B–E mapping in
`.claude/workflows/critique-games.js` stays unchanged; mapping I/J is a separate code task. Until
then, Intrusul and Perechi briefs apply I/J explicitly, alongside the native quick shape checks and
rail audit.

**Judge-fleet protocol.** M4's gameplay critic is a label/solution-blind pre-review filter, never
a signer; its log joins the frozen bundle. The fixed `factual-v3-<id>` and `quality-v3-<id>`
reviewers sign round 1 independently against the frozen candidates, then sign round 2 as verifier
and analyst against the native dossiers (and Alchimie audit). In each round, both `signed_at`
timestamps must exist before either reads the other's verdict. Author sources stay sealed until
both sign; each reviewer chooses at least one URL per new or changed item outside the author's
normalized URL set. Reject a review with more than 20% identical rationale strings or whose reviewer
name appears in an M1–M5 artifact. Preserve the rubric's two-signature contract. This
overrides rubric section G.3's sequential "overturn the critique" step: the verifier independently
refutes the candidate and dossier without reading the analyst report, and the two compare
critiques only after both sign.

**I. Intrusul boards (three members and one intruder)**

- **I1 Honest common predicate.** Build a hub trio with a sibling-hub intruder of the same
  node type. Every member must satisfy one nameable common predicate; type alone must not
  reveal the answer. The quick shape validator remains mandatory.
- **I2 Mechanical separation.** At least two of the three member-to-member links have
  weight ≥0.60. The intruder has no link to any member. This screen is necessary, but does
  not prove that the intended odd tile is unambiguous.
- **I3 Blind odd-one-out.** Shuffle the four displayed tiles, withholding the intended
  predicate and solution. The gameplay critic chooses the intruder and names the predicate;
  compare its answer mechanically with the authored answer. A different answer, or any
  other tile that is arguably odd under a natural predicate, fails the pre-review filter.
- **I4 Recognizable reasoning.** All four tiles pass A1/A2; a player must be able to explain
  why the trio belongs together and why the intruder does not. Obscurity, surface spelling
  accidents and a merely weaker association do not establish a fair intruder.

**J. Perechi boards (four pairs over eight tiles)**

- **J1 Strong pairs, bounded cross-links.** Each of the four intended edges has weight
  ≥0.60; all 24 non-pair cross-links have weight <0.60. A starter board has zero real
  cross-links. The quick shape validator and native audit remain mandatory.
- **J2 Unique matching.** The intended pairing is the unique maximum-weight perfect
  matching among the 105 possible matchings. Record the best and runner-up matchings and
  their margin. The proposed margin ≥0.15 is WARN under the trial above;
  uniqueness and the existing hard floors remain required.
- **J3 Blind pairing.** Shuffle the eight displayed tiles and withhold labels, intended
  pairs and the solution. The gameplay critic pairs them, then compare unordered pairs
  mechanically with the authored matching. A different pairing or an ambiguous tile fails
  the pre-review filter, even when the numeric matching is unique.
- **J4 Explainable links.** Each intended pair passes A1/A2/A7 and has a short, factual,
  nameable relation. A strong KG edge alone cannot justify an association a Romanian
  player would not recognize or distinguish from another plausible partner.
