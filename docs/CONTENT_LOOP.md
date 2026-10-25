# Content loop — V2 operating procedure

Valid until: a later owner-approved procedure supersedes this file.
Decisions: [ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md),
[ADR-0210](adr/0210-curation-waves-and-staged-stock-landing.md) and
[ADR-0211](adr/0211-content-loop-v2-all-boards.md) and
[ADR-0212](adr/0212-bounded-content-workflow-repair.md).

The V2 loop (Phase B) starts only after Paul explicitly says to start; landing this procedure
starts nothing. The retired `romanian-content-discovery-improved-loop` automation stays paused
permanently; never resume it or create a replacement schedule without that instruction.

## Product and authority

Playable boards and targets across all six games are the product: Alchimie, Intrusul, Perechi,
Conexiuni, Cald sau Rece and Lanțul Cuvintelor. Mine the current KG for named board needs; vocabulary
is added only for a documented `board_ref` gap or through an ADR-0210 curation wave. Report added,
approved, eligible, actually selected and played boards separately from concepts, aliases, graph
claims and tooling. `cat-content-ops delta` is a count/identity report, not a playability certificate.

Read this file from the recorded exact procedure/base commit at cycle start and whenever its
recorded digest changes; re-read the exact current sub-step before productive work. The base is
clean main or the exact HEAD of a fully qualified unlanded predecessor, with main anchor and
dependencies explicit. A draft or partially qualified repair is never a content-wave base. Read AGENTS.md, STATUS counts,
applicable CRITIQUE_RUBRIC sections, the unbound rubric I/J section below, PACK_ONLY_CONTENT_WAVES,
ADR-0210 and ADR-0211. The approved
V2 design and read-only review (2026-10-22) explain decisions; their old line numbers and snapshot
counts are not current authority. Preserve fixed-name reviewers, the hash-bound chain, dictionary
spacing, source fidelity, holds, tick/commit discipline and the Python-suite-not-a-gate rule.
Do not open SKILL.md, TASK_BRIEF.md, WORKLOG.md or unrelated older ADRs/review trees; the archived
4g reference and recorded exclusion searches below are explicit exceptions. User messages win.
The content loop proposes procedure changes. Only an explicit bounded owner-authorized workflow
repair may edit this procedure/ADRs; ADR-0212 records the current repair scope and unchanged gates.

Owner words are context-specific: `go` or `drop <ids>` answers only `waiting: review`; `land` answers
only `waiting: land?`; `continue` starts the next interactive burst; `resume <id>` answers
`waiting: expired <id>; restart?`, `unfinished task worktree`, `main keeps moving`, `disk`, `budget`,
a BLOCKED/NEEDS-OWNER wait or a fail-twice wait, and only after Paul's instruction names that wait.
Other messages are questions, not approvals. A landing instruction never authorizes the loop to merge/push/delete: Paul's
Claude Code session is the landing reviewer/operator. Report actual owner decisions, never infer
approval from elapsed time, a schedule, signatures, an old gate or an unchanged hash.

## Scope fence, environment and names

No GUI/frontend/runtime logic, dependency/toolchain/CI/gate changes, deploy, PostgreSQL/accounts,
mobile/device testing, secret values, remote-ref change, push, merge or deletion by the loop.
Allowed content writes are the cascade's named data/generated files, review bookkeeping and the
separate owner-reviewed test-pin packet. Read-only scratch helpers are tooling, not progress;
porting them into repository code is a separate task. No new repo validators or admission policy.
Report `BLOCKED: <command> -> <first error line>` without repairing non-content code. An expectation
outside the pins allowlist stays `NEEDS-OWNER: <test> expects <old>, content now <new>`; never land red.

Use `export PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local`; `go version` must be go1.27.3.
Python importer: `~/work/cat_de_roman_esti/.venv/bin/python`, `PYTHONPATH=scripts:.` from the task
worktree, never `python -I` for importer execution. All checks run from a task worktree root:
shared main's .venv makes cat-doc-check refuse. Shared main stays clean and read-only to the loop.
Create each task locally from its approved exact base SHA with
`git worktree add --no-track -b content/v2-<id>-<slug> <task-path> <exact-local-SHA>`.
Never use the auto-fetch helper. Confirm HEAD equals the base and no upstream is configured;
otherwise stop BLOCKED. Record base kind, main anchor and qualified predecessor dependencies.
IDs are `b1`, `c1`, `b2`, …; branch `content/v2-<id>-<slug>`, module
`scripts/<slug_underscored>_v2_<id>_data.py`, build version `fixture-v2-<id>-<slug>` and review
`docs/reviews/v2-<id>-<slug>/`. V1 branch, module and corpus names remain preserved history.
Evidence, role prompts/model IDs/transcripts, author captures and SHA manifests live under
`~/work/_temp/content-loop/evidence/<id>/`, never /tmp. Delete nothing; Claude copies evidence to
the NAS with SHA verification before owner-operated cleanup. Never create workspace/cache copies.

State is `~/work/_temp/content-loop/state.json` (≤2 KB). Phase B's first tick appends the old
`owner_decisions` and `protected_refs` as one JSON object to `decisions.jsonl`, then replaces state
with V2 pointers: loop, landing, lane, branch, exact main base, step, budgets, waiting null,
waiting_since null, procedure_rev and evidence pointer. Keep decisions.jsonl append-only; never drop old holds/refs.
Never run bare cat-content or cat-mobile-pack without --check. Only 4f exports content; 4a's
approved importer is the only KG apply path, with explicit importable --data-module. No importer
dry-run outside approved 4a: import-candidates requires both review artifacts before any preflight.

## Cadence, waiting and expiry

One productive scheduled checkpoint is one tick/sub-step; observing a running job is not a
productive tick. 4e-quick, 4e-world and 4e-extensions remain separate. An interactive burst has
at most four sub-steps, then the existing same-chat heartbeat resumes without a routine question.
Each productive sub-step commits/checkpoints separately and updates the next saved step; limits
are 24 working ticks and 20 commits per landing. Research stays ≤12 items/tick and ≤300 seconds
per item; all dictionary requests across workers are ≥2 seconds apart, with author/reviewer phases
serialized. Frequency is positive-only evidence. A sub-step failing twice sets waiting with its
first error; two no-progress research ticks, budget, unresolved BLOCKED/NEEDS-OWNER, or disk <12 GB
free also set waiting. Before corpus capture or full tests run `df -h /`.
Persist waiting_since as UTC when waiting is first set or changes; never reset it on an unchanged tick.
Post each new waiting value once with a summary ≤10 lines, then stay silent until it changes.
Never issue empty keepalive requests, promise cache retention, or alter model/cache settings.

Read state first. For saved active APP agents, inspect the same canonical jobs once; if still
running and authority/input versions are unchanged, return quietly without setup or duplicate
dispatch. PID/starttime checks apply only to OS subprocesses. Reuse immutable instructions and
evidence by exact version/reference, never a stale native/content qualification. Generate path,
hash and action records mechanically; validate permissions, physical paths, schemas and complete
output encoding before freezing a bundle. Draft code is editable until frozen; frozen review
inputs, signed verdicts and captures are immutable. Shared blockers stop all dependent lanes.

The owner-authorized repair r1 has a separate limit of eight productive ticks and six local
commits. Existing wave counters/waits and five carried successor-planning ticks remain exact;
no failed wave is reopened or reset. This is not permission to create new repair accounts.
Implement the existing designs, independently review exact code, run meaningful real regressions
and pin a separate immutable helper version. Preserve the original 101-file helper manifest and
its bytes. Do not add generic design/negative-conclusion review stages before a concrete patch.
Content waves retain the 24-tick/20-commit limit and all required fresh checks.

Each active batch has one frozen review bundle. Fully qualified packets are queued UNLANDED
with exact HEAD/dependencies, then the next independent eligible scope may begin. A successor
uses only the last fully qualified unlanded HEAD or explicit clean main, never a failed head.
In Phase B, after seven days in an unresolved waiting set `waiting: expired <id>; restart?`.
A main KG change invalidating frozen dossiers also expires that batch. Return expired candidates
to the pool as unapproved attention; keep all files/verdicts unchanged. Fresh M3–M6 is required for
reuse, but never re-run those steps unprompted. The loop never merges or rebases a task branch.

## Need map, mining and game floors

The need map replaces the theme backlog. Derive eligible boards per game/category/difficulty
against exact main blobs, reserve, tombstones and ranking; target four per cell. Publish total,
approved, held, eligible and starter shelves separately. A no-candidate cell is a shortfall, not
permission for weak vocabulary or generic links. Read-only helper CLIs under
`~/work/_temp/content-loop/miner/`:

- `python3 need_map.py --root <task> --out <evidence>/need-map.json`
- `python3 compat_index.py --root <task> --out <evidence>/compat-index@<sha>.json`
- `python3 mine.py --root <task> --compat <index> --cell <game>:<category>:<difficulty> --per-cell 3 --budget <bounded-count> --out <evidence>/mining.json`
- `python3 critic_blind.py build --root <task> --input <candidate> --public-out <evidence>/critic-public.json --key-out <evidence>/critic-key.json`
- `python3 critic_blind.py compare --key <private-key> --response <critic-answer> --out <evidence>/critic-comparison.json`
- `python3 sha256_manifest.py create --base <evidence> --out <evidence>/manifest.json`; verify with `verify --manifest <manifest>`.
- `python3 review_independence.py --author-seal <sealed-urls> --reviews <factual-envelope> <quality-envelope> --artifacts <M1-M5-index> --out <evidence>/independence.json`

Run these by absolute helper path; they read repo bytes, never import/execute source modules, and
write only inside content-loop scratch. Outputs are hypotheses/measurements; they do not stage,
reserve, promote or certify a board. Bounded miner shortfalls and unresolved static expressions
are surfaced. The private critic key and sealed author source set never enter the critic/reviewer
input; the critic needs visible tile text/captions to play, but no group/predicate/solution labels.

| Game | Existing floors and blind critic |
| --- | --- |
| Conexiuni | Four typed 4-member hubs; validate-pack and strict FAIL-clean critique: tile fairness, red-herring budget, duplicates against full inventory/tombstones, reskins, member overuse >8. Critic solves 16 shuffled tiles without group labels, rejects a second valid partition, supplies “each tile …” predicates and recognizes ≥3/4 per group. |
| Cald | ≥5 actual direct non-distractor predecessors, reachable ≥120, responsive ≥40, salience reviewed. Critic supplies five openers before distances; ≥1 within two hops and one dominant sense. Main-served predecessors, not pending-wave totals, decide the floor. |
| Lanț | Normal shortest path 3–4 hops, greu 4–6; BFS-optimal, ≥2 first hops, layers ≥2, captions on every optimal edge. Critic plays only exposed captions, explains each transition and reaches the target within par+2. |
| Alchimie | Closure mining, greu gaps first: 5–7 seeds, exact action par, ≥2 openings and live audit-projections. Critic plays audited openings, infers target and rejects free pairs. No new discovery-world concept (252/256 is historical headroom). |
| Intrusul | Same-type hub trio plus sibling-hub intruder, valid quick shape; ≥2/3 member links ≥0.60, intruder has no member link. Blind critic names one honest predicate and odd tile; another natural odd-one-out reading fails. Rubric I (below). |
| Perechi | Four edges ≥0.60, unique maximum-weight perfect matching among 105, all 24 cross-links <0.60; starter has zero real cross-links. Critic pairs eight tiles blind and rejects alternative pairings or ambiguous tiles. Rubric J (below). |

WARN only for first three landings B1/C1/B2: Perechi matching margin ≥0.15, Alchimie productive-pair
cap ~40%, Lanț typed-edge share ≥50%, Conexiuni cross-link bands usor 0–1/normal-greu 1–3, and the
Cald gastronomie-target freeze (table in the unbound I/J section below). Record metrics/denominators and seek ratification after B2; these
proposals never override existing hard FAIL floors. The JS critique mapping stays unchanged:
I/J (unbound section below) require explicit critic/reviewer briefs until a separately authorized
code task maps them.
The derived catalog's 123-source freeze/336-board payload stays frozen. Repairing the 83 historical
FAIL-lint Conexiuni boards is a separate task; do not widen scope to make a batch pass.

## Wave steps — M0–M9

- **M0 Need map and baseline.** Create from exact clean main; record HEAD, status, relevant blobs,
  bundle/policy/rubric/procedure digests and current authored source K. No merge. Run the prior
  step-0 checks: cat-content validate, export --check, cat-content-ops check --root .. --check,
  cat-content-rail all --root .. --check, and
  `go -C go-backend test -count=1 ./internal/contentrails/ ./internal/contentbuild/ ./internal/httpgolden/`
  (`-count=1`: the rubric is read from outside the module root, so a cached `ok` hides drift).
  Verify the helpers with `python3 ~/work/_temp/content-loop/miner/sha256_manifest.py verify
  --manifest ~/work/_temp/content-loop/miner/phase-a-helpers-manifest.json`; a mismatch is BLOCKED.
  Any supplemental helper also needs its own exact versioned pin, parent baseline reference,
  fresh independent APP code review and meaningful real-output regression evidence. A helper
  review is reusable only for identical code/input contracts; every content baseline still runs.
  Red unchanged validate/export/ops is BLOCKED. Red rail/contentrails disables install, reports the
  first error and grants no waiver. Build the need map and main-bound compat index; historical
  PASS entries and retired feat/gui-cat-m3 bindings do not substitute for this baseline.
- **M1 Mining.** Select thinnest eligible cells; 503 cells first (historically Perechi gastronomie/
  meme_net and ten empty Conexiuni cells). Three prospects per slot, max two mining ticks; shrink
  the batch rather than loop. Vocab-gap requires a named board_ref and minimum truthful KG change;
  if a lemma is in accepted stock it becomes integrate, not new research. Never mix KG and boards
  in one landing. Board batches cap at 24, B1 at four; this retires V1's 40–60/minimum20 board rule.
- **M2 Compatibility.** Screen every planned/observed form and selected sense against normalization_map,
  normalized_index, labels, aliases, discovery_world, Cald projections, current accepted/held stock,
  exact accent-preserving ReviewedUnresolved and v72 DEFERRED_AMBIGUOUS_TERMS. Other-sense owners
  remain owned; never steal aliases. Screen BLOCKED_ALIAS_FORMS, collision pairs, fuzzy deny and all
  DEFERRED_* in scripts/{contexto_common_words_v44,basic_words_v30,basic_words_v32,basic_words_v33}_data.py,
  tests/ and every docs/reviews/*/graph-candidates.json, including pre-V1.8. Cite each hit as
  `held: recorded exclusion <file:line>`; unknown dynamic expressions fail closed. Also screen board
  signatures (Conexiuni quads/reskins, Lanț endpoint pairs, Cald targets, Intrusul/Perechi sets),
  reserve/tombstones, demotions and owner holds. No observation is an approval/reservation.
- **M3 Lint pre-screen.** Use validate-pack and critique --strict on an evidence-directory pack copy,
  using validate-pack --root <task> --kg <kg-copy> --pack <pack-copy>. For critique there is no
  pack override: prepare a bounded separate scratch source-readset root with matching fixture
  mirrors, runtime/rubric/ledger binding files and temporary pending IDs; run critique --root
  <scratch-readset> --ids <exact-temporary-ids> --strict without --write. Record every copied byte
  and before/after repo hashes; no workspace, dependencies or build caches are copied. No importer,
  import-candidates dry run or repo mutation. Unknown parser/CLI support is BLOCKED, not invented.
- **M4 Gameplay critic.** Independent critic blind-solves the game per the floors above. Use sanitized
  input and a separately sealed private key; compare its submitted solution mechanically, then
  adjudicate ambiguity/predicate/recognition in the critic's own words. One line per failure.
  The critic is a pre-review filter, never a signer; its sanitized log joins the freeze bundle.
  For Cald, the public challenge includes only the exact native player-visible `difficulty` and
  `board_category` read from the bound board; never add a target/board/source/graph field, neighbour,
  clue, example or authored guess. The critic commits exactly five ordinary normalized-distinct
  guesses before feedback using opening response schema 2 (`schema`, `challenge_id`, `openers`);
  pre-feedback target knowledge is unassessed, while final target/sense ambiguity must be false.
  Preserve opener bytes/hashes/sequence/receipts and diagnose each property independently. Persist
  the exact full comparator return exclusively before local assertions. One of those same five
  openers must have raw distance ≤2; adaptive guesses never satisfy the floor and cap 8 is unchanged.
- **M5 Freeze.** One landing module/board unit, candidates.json per category, canonical manifest of
  every binding/capture and frozen critic log. Refuse missing/hash-mismatched captures, unresolved
  compat or a missing live mechanic. Seal author sources/URLs separately. Never mutate signed bytes.
- **M6 Review round 1.** Fixed factual and quality reviewers each judge the whole frozen batch once,
  adversarial fresh web sources, signed before seeing each other. Give reviewer-visible hashes/candidate/dossiers/critic log, withholding author URLs/captures
  in a separate sealed bundle until both sign. Author sources stay sealed; each new or changed item needs ≥1 reviewer-chosen normalized URL outside the author's set. Reject a report with
  >20% repeated normalized rationale strings, >20% identical rationale rows across the pair, or a
  reviewer name appearing anywhere in an M1–M5 artifact. Record each per-item capture binding.
  Run the sidecar independence guard before accepting the M6 pair. Record the go/drop table
  ≤24 rows under the standing owner delegation and continue M7. An explicit item hold or
  separately required owner row remains a hold; delegation is not a new item-specific approval.
- **M7 Stage plus review round 2.** Only after go/drop and fresh gates. Pack: run PACK_ONLY steps 2–4:
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
- **M8 Landing packet.** Execute the applicable P/G cascade below, separate pins commit and corpus
  report. Require green gates outright, record each API playthrough, bind exact HEAD and all files.
  Finish step5 prelanding record and queue the fully qualified UNLANDED packet with pins/gates.
  Continue eligible work autonomously. Claude performs only the consolidated final review when
  Paul stops the run or explicitly requests it. Landing, push and cleanup remain external owner
  operations; this loop never merges, pushes or deletes.
- **M9 Record.** After externally verified landing, record actual player-visible per-game cell changes,
  source concepts/inputs/claims separately, rejects as tombstones via existing tooling, and the
  ≤10-line retrospective/≤3 proposals. Never auto-demote approved content or rewrite a signed verdict.

## Fixed roles and mechanical independence

Each landing fixes author, factual-v2-<id>, quality-v2-<id>, critic-v2-<id> and the landing reviewer.
The first four are distinct. Each working helper, reviewer and critic runs in a separate fresh
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
whole sealed author set; every reviewer-chosen capture is independently retained and hash-bound.
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
     scripts/everyday_graph_v1_3_data.py for nodes and edges). Class G only, after owner `go`;
     no automatic removal from any deferred or blocked list. Run `apply_common_words_v24.py --data-module <module>
     --dry-run` (expect preflight GREEN), then without `--dry-run`.
   - 4b `cat-content-ops rank --write`, `derive --write`, `check --check`; `cat-mobile-pack --check`
     (4a refreshed the contract for G; P changes no KG, so retain it; never write it with the Go tool).
   - 4c Copy authored-v<K>.json to authored-v<K+1>.json: version K+1, `parent_source_sha256` =
     sha256 of authored-v<K>, `base_commit` = the full 40-hex wave_base, and repoint the world
     archives to the last installed wave's native/world files listed in installed-authorities.json:
     world_candidate and world_previous → candidate.json, world_factual → factual-review.json,
     world_quality → quality-review.json, each with its sha256. K is derived at M0 (currently 12;
     B1 is expected v13, C1 v14, B2 v15 if no intervening landing). For B-quick append only the
     frozen, go-accepted quick records to authored-v<K+1>.quick.boards before candidate generation;
     retain category/difficulty/game/id/payload/rationale/source_id/sources and exact per-record
     hashes, no new IDs or semantic edits outside the reviewed payload. A mere copy would add no
     boards. Pack-only B1 changes no authored quick payload, but still regenerates bindings.
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
     `reviewedPins` value is stale. Each rail is its own tick and commit (4e-quick, 4e-world,
     4e-extensions).
   - 4f Pins (edited in 4e, before the extensions proposal): the derived_catalog_v38 and
     quick_games_v92 values in `reviewedPins` (go-backend/internal/contentbuild/build.go),
     `CATALOG_SHA256` in cat_de_roman_esti/wordgames/quick_catalog.py and
     `DEFAULT_DERIVED_CATALOG_SHA256` in cat_de_roman_esti/wordgames/derived_catalog.py. Then
     `cat-content export --root ..` and `export --root .. --check`.
   - 4g HTTP corpus: first `df -h /`; below 12 GB free set `waiting: disk`. Build `cat-server` into scratch; copy
     docs/reviews/go-native-toolchain/archived-reference/capture_reference.py.txt to scratch, changing
     exactly three lines: ROOT (archived line 21), the reference label (line 393) and output path
     (line 394); attach `diff -u` against the archived reference to the corpus report and refuse any
     other change. Match assignments by content if line numbers move. Run it with the repo venv,
     `CAT_ACCOUNTS_ENABLED=0` and `--binary <cat-server> --runtime go` (expect the case count of the
     previous reviewed corpus block, 1206 since V1.13; any other count is `NEEDS-OWNER` with a
     case-list diff). Record the actual count, never edit it to fit and never bypass an HTTP case.
     Move the .json.gz to go-backend/internal/httpgolden/testdata/ and, in golden.go, add only a
     renamed copy of the previous reviewed block as `reviewedV2<ID>()` (e.g. `reviewedV2B1()`), its SHA
     constant, embed line and ForSources call/slice entry. Corpus: `python-http-parity-v2-<id>.json.gz`;
     selection test: `v2<id>_selection_test.go` (e.g. `v2b1_selection_test.go`). V1 names stay historical.
   - 4h Bind the installed authorities. Per rail run `cat-content-rail <r> --source <abs> --candidate C
     --factual-review F --quality-review Q --proposal P --live-audit A --final-factual-review FF
     --final-quality-review FQ --expected-sha256 <sha256 of P> --installed-authority-out
     <scratch>/rail/<r>/entry.json` with the 4e documents; the command re-runs the native audit under
     the current binary and refuses with "final live audit incomplete/stale/unaccepted" if the installed
     behaviour no longer equals A (after 4f this happens only when the export changed what the
     quick/world replays observe). On that refusal only: rerun `--audit-catalog P --audit-out A`, have
     both reviewers re-sign FF and FQ to the new A, retry once (a second refusal sets `waiting`). Then
     assemble
     go-backend/internal/contentrails/sources/installed-authorities.json (append authored-v<K+1> to
     source_chain; replace all three rail entries for both P and G) and
     swap the sha in installed_authorities_pin.go via the metadata template (the file must equal
     PinBytesForInstalledAuthorities exactly). No second installed audit, no second reviewer round and
     no runtime freeze.
   - 4i Gates: run after the separate `pins` commit exists (moved count and selection
     expectations are red until then). First `df -h /`; below 12 GB free set `waiting: disk`. `cat-content-rail all --check`, `cat-content validate`, `export --check`,
     `cat-content-ops check --check`, `cat-mobile-pack --check`, `go -C go-backend test -count=1 -race
     -timeout 60m ./...`,
     `go -C go-backend vet ./...`, `go -C shared-go/authcore test -count=1 -race ./...`, `cat-doc-check
     --root ..`,
     `git diff --check` — no new red versus step 0. Known pre-existing reds on main: httpapi
     TestManagedSPA* (frontend not built) are historical examples, not a standing waiver. Any other red without a step-0 record counts as
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
   update only the expectations the landing moves — the new `v2<id>_selection_test.go` block in
   go-backend/internal/httpgolden with its predecessor's "did not move past" edit, the board and
   approved counts in internal/contentops (`check_test.go`, `contentops_test.go`) and the Cald
   inbound maps in internal/contexto — list each old -> new value in the README, and land only
   after the owner approves that packet.
   The separate `pins` commit touches only `go-backend/internal/httpgolden/v2<id>_selection_test.go`
   and its predecessor's selection test,
   `go-backend/internal/contentops/{check_test.go,contentops_test.go}`, and
   `go-backend/internal/contexto/content_v1_3_test.go`. List each old → new value and `git show --stat`;
   class P changes no KG/Cald map. No unrelated test logic changes. New/edited Python tests,
   `tests/current_content.py`, rules_unicode15.json, runtime and GUI remain outside scope.
   If the task worktree is dirty or a merge is unfinished on waking, preserve every byte and stop at
   `waiting: unfinished task worktree`; inspect/recover only the owned sub-step with the owner.
   Never reset/clean, delete a packet, merge main or touch another task's work.


## Cascade classes and prelanding record

**Class P (pack/quick):** no KG change; M7 pack/quick review as appropriate, then full 4b–4i.
Quick, world and extensions all receive the new authored source, initial reviews, proposal,
current audit, fresh final acceptance and replacement authority entries. Exact unchanged item
semantics may use the inherited-item rule in 4d; the world audit/finals themselves are fresh.
Pack/ranking bytes are world audit inputs, so unchanged world gameplay does not permit stale
signed bindings. Default all --check, corpus, pins, gates and per-board HTTP play remain mandatory.
**Class G (curation/vocab-gap):** full 4a–4i including world. No KG and board additions co-land;
Alchimie has its own review/audit batch even within a multi-game P landing.

Step5 prepares pool dispositions/reasons and docs/reviews/v2-<id>-<slug>/README.md (≤80 plain lines):
player gain, table summary, actual owner decisions, retrospective, ≤3 proposals and every BLOCKED/
NEEDS-OWNER, plus every comparison task worktree the landing created (the landing session removes
them). Keep the exact installed-authority rail files plus ≤10 small text files (README,
graph reviews, playthrough log, reference/capture_v2_<id>.py.txt). Raw captures, role transcripts,
build output and failed attempts stay under evidence, never in repo docs. Preserve all bytes;
retention cleanup belongs to the later Claude landing session after verified NAS copy.
Only after the prelanding checks update STATUS counts/Last verified within its 120-line budget;
if doing so requires an out-of-scope history-file edit, report NEEDS-OWNER. Run cat-doc-check
--root .. --inventory docs/tracked-markdown.json and git diff --check; commit, queue UNLANDED.
If main moved, the loop does not merge: Claude's landing session merges main into the task branch
and reruns 4i (and 4g when httpapi or content packages changed). If main moves again, repeat once
only after explicit direction, then wait `main keeps moving`.

## Curation wave (class G; ADR-0210)

Curation steps **0–3** replace M1–M4; M2 compatibility still applies fully. Step 0 runs M0 gates on
current main. Step 1 chooses ≥20 accepted existing-owner morphology families from final module
payloads (never planned/observed lists), recording original wave/id/closure and every exclusion.
The canonical stock is `docs/content-consolidation/v1-8-through-v1-32/current-stock.json` on its
branch; V1.38–V1.42 payloads are read from their preserved content/v1-* branches with `git show`,
never executed. Step 2 rebinds retained own-head DEX/DOOM3/table and second-source evidence; missing captures are
ineligible. Step 3 consolidates one module and obtains fresh whole-batch dual review with the V2
independence sidecars and guard, then records go/drop under the standing delegation, retaining
item-specific owner holds. Step 4 is full 4a–4i and test pins; step 5 queues the qualified packet. These source items are not counted as 24 boards.

C1 starts with V1.38–V1.42 final payloads, including Avion, Cinematograf and Interfon; lane labels
alone do not prove morphology eligibility (Interfon's historical lane differs). Hold any family
with a key hit in the exact M2 exclusion sources as `held: recorded exclusion <file:line>`. Mănăstire and Sucitor (without bare sucitoare)
get separate go/drop rows, each `snapshot rebuild: <files>`; Paul's go on a row accepts it.
Bare sucitoare always stays excluded; Ie never gets ii/iei. Do not override earlier exclusions,
clip a required family or reopen a hold automatically. Fresh verification is required for weaker
review tiers; V1.33 specifically needs new source research, never missing /tmp captures. V1.14
items are re-applied through this cascade; never merge its partial branch or ask its declined
HTTP exception. Preserve all content/v1-* refs (NAS bundle ac0a2b63… under
branch-archive/cat_de_roman_esti/2026-10-22-content-loop-branches/).
While stock remains, at least one in each three landings is curation. Order by evidence tier,
then documented board yield; any read-only yield simulation uses in-memory data, never source
module execution or import dry-runs. Board candidates are re-screened after each class G landing,
including Lanț optimal routes and Alchimie par. Stock matches turn vocab-gap into integrate.
Keep corrected stock measures: 4,968 single-token +766 multiword inputs (three display-only
labels separate); 3 nodes cross incoming 5 using main-served predecessors, 45 only when complete
pending waves co-land. Holds are records, may overlap later accepted lemmas, and never leak.

## First three landings and improvement loop

1. **B1 / P:** up to four Lanț chains in gastronomie normal, limba normal, personalitati normal,
   societate greu. If a cell yields none after two mining ticks, select the next-thinnest normal/
   greu Lanț cell from the actual need map and name the substitution. Land fewer than four rather
   than wait for filler. Measure actual 4c–4h cascade cost, corpus time/count and pin packet.
2. **C1 / G:** at least 20 alias-only morphology families as above, then re-screen the B2 queue.
3. **B2 / P:** at most 20 boards: eight Perechi (gastronomie/meme_net, four each), eight Conexiuni
   (arta_cultura usor/greu, societate usor/greu, sport usor/normal, film_tv usor, geografie normal),
   four Cald greu (literatura/personalitati). These are priorities, not prequalified boards.
Then use measured cell deficits, maintaining the curation ratio. Every landed or expired wave
records a retrospective ≤10 plain lines: proposed/accepted/installed, actual delta, top three hold/
rejection reasons, step ticks, failures and player gain. Record ≤3 evidence-based old→new proposals;
never apply procedure changes. New concepts still need a named game, 4–8 truthful links to
separate endpoints: ≥2 main-served, ≤2 batch peers, ≥2 same-category; check peer closure. No quota
filler, category repair, hidden target approval or fabricated links. Cold vocabulary is parked
vocabulary-only, not repeatedly researched. Owner-decision-first items wait.

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

## Rubric I/J and V2 review protocol (unbound trial text)

This section is not digest-bound. `docs/CRITIQUE_RUBRIC.md` is bound into rankings, the derived
catalog, all three rails and the installed authorities (`contentbuild.RubricSHA256`), so folding
this text into it changes that digest. That fold is a separate owner-authorized class-G rubric
transition (rubric constant and Python pin, rank/derive, re-audit of all three rails, authorities,
corpus), never part of a class-P landing. Rubric section A applies to all six games.

The proposed rules below are **WARN only for the first three V2 landings (B1, C1, B2)**; record the
observed metric and the reviewers' reasoning, then seek ratification after those landings.
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

**V2 judge-fleet protocol.** M4's gameplay critic is a label/solution-blind pre-review filter, never
a signer; its log joins the frozen bundle. The fixed `factual-v2-<id>` and `quality-v2-<id>`
reviewers sign round 1 independently against the frozen candidates, then sign round 2 as verifier
and analyst against the native dossiers (and Alchimie audit). In each round, both `signed_at`
timestamps must exist before either reads the other's verdict. Author sources stay sealed until
both sign; each reviewer chooses at least one URL per new or changed item outside the author's
normalized URL set. Reject a review with more than 20% identical rationale strings or whose reviewer
name appears in an M1–M5 artifact. Preserve the rubric's two-signature contract. For V2 this
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
  their margin. The proposed margin ≥0.15 is WARN for B1, C1 and B2 under the trial above;
  uniqueness and the existing hard floors remain required.
- **J3 Blind pairing.** Shuffle the eight displayed tiles and withhold labels, intended
  pairs and the solution. The gameplay critic pairs them, then compare unordered pairs
  mechanically with the authored matching. A different pairing or an ambiguous tile fails
  the pre-review filter, even when the numeric matching is unique.
- **J4 Explainable links.** Each intended pair passes A1/A2/A7 and has a short, factual,
  nameable relation. A strong KG edge alone cannot justify an association a Romanian
  player would not recognize or distinguish from another plausible partner.


## Heartbeat prompt (new cat-content-v2 only, after approval)

```text
Continue in this existing chat under the latest explicit owner override and state.json.
Read state first. Inspect saved canonical APP jobs once; running unchanged work returns quietly.
Never duplicate a job. PID/starttime checks apply only to saved OS subprocesses.
For productive work read the current plan/exact step; reread full instructions only on a changed
recorded digest or missing context. Immutable evidence is referenced, not recopied or reapproved.
During the specifically authorized repair r1: max8 productive ticks/6local commits, separate
from all preserved content budgets and carried planning5. Use existing designs for concrete
code, fresh independent APP review, meaningful real regressions and a separate exact version pin.
Original helpers/manifests and signed evidence stay unchanged; no generic review-of-review stage.
Gameplay-protocol GP1 plus rejected GP2 are two carried successor checkpoints, not an r1 reset;
`gameplay-protocol-v3` is rejected because it admitted caller-selected limits 1–100. GP3 uses the
separate `gameplay-protocol-v3-cap8` bytes and requires exact integer cap 8 in the builder, direct
oracle, sealed key and public comparator checks. Preserve opening schema2, exact native Cald
category/difficulty, independent diagnostics, pre-assertion result capture, and every five-opener
warmth/final-target/final-sense floor; fresh independent qualification and a pin remain mandatory.
Then continue the dataset loop autonomously: one checkpoint/tick, interactive bursts<=4,
content limits24ticks/20commits, research<=12items/300seconds each, dictionary spacing>=2seconds.
Fresh fixed factual/quality/critic APP contexts, both whole-batch reviews, seals, URL novelty,
signatures before peer access/unseal, full actors/captures and native schemas remain mandatory.
All M0-M8, source/rail/corpus1206/HTTP/fuzzy/exactSHA/pin gates and special holds remain binding.
ClassP skips only4a; P and G both rebuild/review/audit/re-sign world plus quick/extensions.
Shared blockers stop dependent lanes. Failed budgets are never reset and failed heads never used.
Queue fully qualified UNLANDED packets with exact dependencies, then the next eligible scope.
Only exact qualified predecessor HEAD or cleanmain may be a base; fresh actual-byte checks apply.
No land/merge/push/fetch/pull/remote-ref/deploy/delete/prune or runtime/GUI/deps/toolchain/CI changes.
No weakened gate or model/cache changes. Local worktrees use git worktree add --no-track exactSHA.
Claude is only the final consolidated review when Paul stops or explicitly requests it.
Notify qualified increments, material failures or genuine new owner rulings once; stay quiet otherwise.
```
