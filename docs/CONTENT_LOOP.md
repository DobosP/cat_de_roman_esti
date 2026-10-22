# Content loop — V2 operating procedure

Valid until: a later owner-approved procedure supersedes this file.
Decisions: [ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md),
[ADR-0210](adr/0210-curation-waves-and-staged-stock-landing.md), and the proposed
[V2 procedure packet](adr/0211-content-loop-v2-all-boards.md).

Phase A draft: stop at `waiting: V2 procedure review`. Phase B starts only after ADR-0211 exists
on main and Paul explicitly says to start. The retired `romanian-content-discovery-improved-loop`
automation stays paused permanently. Do not start B1, install content or create a replacement
schedule while drafting this procedure. The I/J rubric edit changes a compiled reviewed hash:
Phase A records actual check results, but cannot update runtime pins, catalogs or authorities.
Native content gates remain BLOCKED until a separately authorized rubric-pin/authority transition
is reviewed and landed; this draft grants no Phase B qualification.

## Product and authority

Playable boards and targets across all six games are the product: Alchimie, Intrusul, Perechi,
Conexiuni, Cald sau Rece and Lanțul Cuvintelor. Mine the current KG for named board needs; vocabulary
is added only for a documented `board_ref` gap or through an ADR-0210 curation wave. Report added,
approved, eligible, actually selected and played boards separately from concepts, aliases, graph
claims and tooling. `cat-content-ops delta` is a count/identity report, not a playability certificate.

Read this whole file on main at cycle start and whenever its last commit differs from state
`procedure_rev`; re-read the exact current sub-step before acting. Read AGENTS.md, STATUS counts,
applicable CRITIQUE_RUBRIC sections, PACK_ONLY_CONTENT_WAVES, ADR-0210 and ADR-0211. The approved
V2 design and read-only review (2026-10-22) explain decisions; their old line numbers and snapshot
counts are not current authority. Preserve fixed-name reviewers, the hash-bound chain, dictionary
spacing, source fidelity, holds, tick/commit discipline and the Python-suite-not-a-gate rule.
Do not open SKILL.md, TASK_BRIEF.md, WORKLOG.md or unrelated older ADRs/review trees; the archived
4g reference and recorded exclusion searches below are explicit exceptions. User messages win.
After Phase A, never edit this procedure or ADRs under the content loop; propose changes instead.

Owner words are context-specific: `go` or `drop <ids>` answers only `waiting: review`; `land` answers
only `waiting: land?`; `continue` starts the next interactive burst. Other messages are questions,
not approvals. A landing instruction never authorizes the loop to merge/push/delete: Paul's
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
Create each task from the approved exact main SHA with
`python3 ~/work/agent-ops/scripts/create_task_worktree.py --repo ~/work/cat_de_roman_esti --branch content/v2-<id>-<slug> --task "<player outcome>" --write`.
Move its generated TASK_BRIEF.md into that landing's scratch; never overwrite a prior brief.
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
Do not perform this V2 migration during Phase A.
Never run bare cat-content or cat-mobile-pack without --check. Only 4f exports content; 4a's
approved importer is the only KG apply path, with explicit importable --data-module. No importer
dry-run outside approved 4a: import-candidates requires both review artifacts before any preflight.

## Cadence, waiting and expiry

One scheduled run is one tick/one sub-step (4e-quick, 4e-world and 4e-extensions are separate).
An interactive burst has at most four sub-steps; post one status line and stop until `continue`.
Each productive sub-step commits/checkpoints separately and updates the next saved step; limits
are 24 working ticks and 20 commits per landing. Research stays ≤12 items/tick and ≤300 seconds
per item; all dictionary requests across workers are ≥2 seconds apart, with author/reviewer phases
serialized. Frequency is positive-only evidence. A sub-step failing twice sets waiting with its
first error; two no-progress research ticks, budget, unresolved BLOCKED/NEEDS-OWNER, or disk <12 GB
free also set waiting. Before corpus capture or full tests run `df -h /`.
Persist waiting_since as UTC when waiting is first set or changes; never reset it on an unchanged tick.
Post each new waiting value once with a summary ≤10 lines, then stay silent until it changes.
Never issue empty keepalive requests, promise cache retention, or alter model/cache settings.

Landing mode is land-or-expire, with at most one batch from M5 freeze to landed; no next-batch M1
until it lands or expires. In Phase B only, after seven days in any waiting set `waiting: expired <id>; restart?`.
A main KG change invalidating frozen dossiers also expires that batch. Return expired candidates
to the pool as unapproved attention; keep all files/verdicts unchanged. Fresh M3–M6 is required for
reuse, but never re-run those steps unprompted. A non-KG bound input change also invalidates review:
stop for a refreshed main-bound task/review, never merge/rebase the task or transfer old PASS lanes.

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
| Intrusul | Same-type hub trio plus sibling-hub intruder, valid quick shape; ≥2/3 member links ≥0.60, intruder has no member link. Blind critic names one honest predicate and odd tile; another natural odd-one-out reading fails. Rubric I. |
| Perechi | Four edges ≥0.60, unique maximum-weight perfect matching among 105, all 24 cross-links <0.60; starter has zero real cross-links. Critic pairs eight tiles blind and rejects alternative pairings or ambiguous tiles. Rubric J. |

WARN only for first three landings B1/C1/B2: Perechi matching margin ≥0.15, Alchimie productive-pair
cap ~40%, Lanț typed-edge share ≥50%, Conexiuni cross-link bands usor0–1/normal-greu1–3, and the
Cald gastronomie-target freeze. Record metrics/denominators and seek ratification after B2; these
proposals never override existing hard FAIL floors. The JS critique mapping stays unchanged:
I/J require explicit critic/reviewer briefs until a separately authorized code task maps them.
The derived catalog's 123-source freeze/336-board payload stays frozen. Repairing the 83 historical
FAIL-lint Conexiuni boards is a separate task; do not widen scope to make a batch pass.

## Wave steps — M0–M9

- **M0 Need map and baseline.** Create from exact clean main; record HEAD, status, relevant blobs,
  bundle/policy/rubric/procedure digests and current authored source K. No merge. Run the prior
  step-0 checks: cat-content validate, export --check, cat-content-ops check --root .. --check,
  cat-content-rail all --root .. --check, and
  `go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/ ./internal/httpgolden/`.
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
- **M5 Freeze.** One landing module/board unit, candidates.json per category, canonical manifest of
  every binding/capture and frozen critic log. Refuse missing/hash-mismatched captures, unresolved
  compat or a missing live mechanic. Seal author sources/URLs separately. Never mutate signed bytes.
- **M6 Review round 1.** Fixed factual and quality reviewers each judge the whole frozen batch once,
  adversarial fresh web sources, signed before seeing each other. Give reviewer-visible hashes/candidate/dossiers/critic log, withholding author URLs/captures
  in a separate sealed bundle until both sign. Author sources stay sealed; each item needs ≥1 reviewer-chosen normalized URL outside the author's set. Reject a report with
  >20% repeated normalized rationale strings, >20% identical rationale rows across the pair, or a
  reviewer name appearing anywhere in an M1–M5 artifact. Record each per-item capture binding.
  Run the sidecar independence guard before accepting the M6 pair. Post the go/drop table ≤24 rows and set `waiting: review`. Only go/drop answers this wait.
- **M7 Stage plus review round 2.** Only after go/drop and fresh gates. Pack: run PACK_ONLY steps 2–4:
  import-candidates --pack-only --write, critique --dossier --write, live Alchimie audit for its
  separate review batch, same two fixed reviewers as verifier/analyst, build-review then
  apply-review --write. Quick boards follow 4c–4e candidates/reviews/proposal/audit/finals. G uses
  curation 0–3 then full 4a–4i. Preserve independent ordering in both rounds; native raw JSON exact
  keys stay unchanged, so signed_at, source seals and access receipts are SHA-bound sidecar
  envelopes. Run review_independence.py before build-review; native build-review does not yet
  implement V2 sidecar checks. Run the same guard before accepting every curation step3, initial
  rail-review and final-audit signature pair, including flows that never call build-review. Stop if any check cannot be established, never claim future code.
- **M8 Landing packet.** Execute the applicable P/G cascade below, separate pins commit and corpus
  report. Require green gates outright, record each API playthrough, bind exact HEAD and all files.
  Finish step5 prelanding record, then `waiting: land? (pins packet + gates)`. Only Paul's Claude
  Code session reviews the packet, runs merge --ff-only, pushes per ADR-0014, SHA-verifies the NAS
  evidence copy and deletes branch/worktree per ADR-0037. The loop never merges, pushes or deletes.
- **M9 Record.** After externally verified landing, record actual player-visible per-game cell changes,
  source concepts/inputs/claims separately, rejects as tombstones via existing tooling, and the
  ≤10-line retrospective/≤3 proposals. Never auto-demote approved content or rewrite a signed verdict.

## Fixed roles and mechanical independence

Each landing fixes author, factual-v2-<id>, quality-v2-<id>, critic-v2-<id> and the landing reviewer.
The first four are distinct. Reviewers and critic each run as their own
`codex exec -m <model>` subprocess using rungs from
`~/.claude/skills/agent-routing/scripts/fleet-tiers.sh`; critic and factual use different rungs.
Do not infer a model alias: retain the selected rung/model/effort, exact prompt and transcript under
`evidence/<id>/roles/<name>/` and hash each. Only the frozen role-appropriate bundle is provided.
The same factual/quality names sign round2 as verifier/analyst; roles do not change their identity.

Source seals, actor artifacts, report signatures, capture IDs and access receipts are retained by
manifest. Both signed_at timestamps must exist before either receives/reads the other's report;
first-peer-read receipts must be later than both signed_at values. A timestamp assertion is not
proof of process isolation: retain dispatch/delivery transcripts. After both sign, unseal sources
for mechanical set-difference checks; stale/missing receipts or >20% identical rationales void the
review. Native raw review JSON gets no unsupported metadata fields. The scratch preflight checks
the envelopes; the existing native build-review/apply-review binding checks still run unchanged.
For the 20% rule, normalize whitespace/case; within each report divide duplicate rationale rows
beyond their first occurrence by all item rows, and across the pair divide identical per-ID rows
by all IDs. More than20% in either comparison fails. Normalize URL scheme/host/default ports,
remove fragments and sort query pairs; preserve path/word accents. URL set difference uses the
whole sealed author set; every reviewer-chosen capture is independently retained and hash-bound.
The actor/artifact index lists every M1–M5 path and SHA; scan full bytes, not just actor fields.
Helper CLI envelope fields and smoke examples are in
`~/work/_temp/content-loop/miner/INDEPENDENCE.md`.

## Install cascade — exact substeps 4a–4i

One commit per lettered sub-step; each rail in 4e is a separate sub-step. Go tools via
   `go -C go-backend run ./cmd/<tool> ... --root ..`. Class P skips 4a and retains world; class G runs all three rails. Inherited world keeps its original
source version and is checked through default all --check, not --source authored-v<K+1>.
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
     For P keep the existing world
     entry and every bound world byte unchanged; rebuild/re-sign quick and extensions. For G use quick,
     world, extensions: `cat-content-rail <r> --source <abs> --candidate-out
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
     retained class-P world is not rebuilt and uses its original source. The `--write` and
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
     source_chain; replace quick/extensions entries for P, preserving the world entry exactly;
     replace all three rail entries for G) and
     swap the sha in installed_authorities_pin.go via the metadata template (the file must equal
     PinBytesForInstalledAuthorities exactly). No second installed audit, no second reviewer round and
     no runtime freeze.
   - 4i Gates: first `df -h /`; below 12 GB free set `waiting: disk`. `cat-content-rail all --check`, `cat-content validate`, `export --check`,
     `cat-content-ops check --check`, `cat-mobile-pack --check`, `go -C go-backend test -race
     -timeout 60m ./...`,
     `go -C go-backend vet ./...`, `go -C shared-go/authcore test -race ./...`, `cat-doc-check
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
   The separate `pins` commit touches only `go-backend/internal/httpgolden/*_selection_test.go`,
   `go-backend/internal/contentops/{check_test.go,contentops_test.go}`, and
   `go-backend/internal/contexto/content_v1_3_test.go`. List each old → new value and `git show --stat`;
   class P changes no KG/Cald map. No unrelated test logic changes. New/edited Python tests,
   `tests/current_content.py`, rules_unicode15.json, runtime and GUI remain outside scope.
   If the task worktree is dirty or a merge is unfinished on waking, preserve every byte and stop at
   `waiting: unfinished task worktree`; inspect/recover only the owned sub-step with the owner.
   Never reset/clean, delete a packet, merge main or touch another task's work.


## Cascade classes and prelanding record

**Class P (pack/quick):** no KG change; M7 pack/quick review as appropriate, then 4b rank/derive,
4c authored-v<K+1>, 4d–4e quick plus extensions, 4f pins/export, 4g independent corpus, 4h quick/
extensions authorities, 4i gates and each new board HTTP-played once. World inherits unchanged
because it has no pack binding: its KG, rubric, editorial source and previous-world bindings must
all remain exact. Check world through default all --check or its retained original source, never
pass the new authored source to the inherited world rail. Regeneration/re-signing quick and extensions is mandatory even when
only the pack changes: their pack/KG/derived bindings must equal live digests. No light path.
**Class G (curation/vocab-gap):** full 4a–4i including world. No KG and board additions co-land;
Alchimie has its own review/audit batch even within a multi-game P landing.

Step5 prepares pool dispositions/reasons and docs/reviews/v2-<id>-<slug>/README.md (≤80 plain lines):
player gain, table summary, actual owner decisions, retrospective, ≤3 proposals and every BLOCKED/
NEEDS-OWNER. Keep the exact installed-authority rail files plus ≤10 small text files (README,
graph reviews, playthrough log, reference/capture_v2_<id>.py.txt). Raw captures, role transcripts,
build output and failed attempts stay under evidence, never in repo docs. Preserve all bytes;
retention cleanup belongs to the later Claude landing session after verified NAS copy.
Only after the prelanding checks update STATUS counts/Last verified within its 120-line budget;
if doing so requires an out-of-scope history-file edit, report NEEDS-OWNER. Run cat-doc-check
--root .. --inventory docs/tracked-markdown.json and git diff --check; commit, stop at land?.
If main moved, no loop merge: have the owner refresh the task/main binding and required checks;
repeat once only after explicit direction, then wait `main keeps moving` if unresolved.

## Curation wave (class G; ADR-0210)

Curation steps **0–3** replace M1–M4; M2 compatibility still applies fully. Step0 runs M0 gates on
current main. Step1 chooses ≥20 accepted existing-owner morphology families from final module
payloads (never planned/observed lists), recording original wave/id/closure and every exclusion.
Step2 rebinds retained own-head DEX/DOOM3/table and second-source evidence; missing captures are
ineligible. Step3 consolidates one module and obtains fresh whole-batch dual review with the V2
independence sidecars and guard, then posts go/drop as waiting review. Step4 is full 4a–4i and test pins;
step5 prepares the packet and stops at land?. These source items are not counted as 24 boards.

C1 starts with V1.38–V1.42 final payloads, including Avion, Cinematograf and Interfon; lane labels
alone do not prove morphology eligibility (Interfon's historical lane differs). Reject any family
with a key hit in the exact M2 exclusion sources. Mănăstire and Sucitor (without bare sucitoare)
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
labels separate); 3 nodes cross incoming5 using main-served predecessors, 45 only when complete
pending waves co-land. Holds are records, may overlap later accepted lemmas, and never leak.

## First three landings and improvement loop

1. **B1 / P:** up to four Lanț chains in gastronomie normal, limba normal, personalitati normal,
   societate greu. If a cell yields none after two mining ticks, select the next-thinnest normal/
   greu Lanț cell from the actual need map and name the substitution. Land fewer than four rather
   than wait for filler. Measure actual 4c–4h cascade cost, corpus time/count and pin packet.
2. **C1 / G:** at least 20 alias-only morphology families as above, then re-screen the B2 queue.
3. **B2 / P:** at most20 boards: eight Perechi (gastronomie/meme_net, four each), eight Conexiuni
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
Romanian everyday/school/culture relevance and an honest readable predicate are mandatory;
people/places/works use Romanian Wikipedia or better. Frequency is positive only. DEX sense/
register, exact-head DOOM3 and that head's attributed ordinary flexion table plus one Romanian
second source are required for lexical additions. Do not borrow another head's table; qualified
compounds require component morphology and separate compound-sense evidence. Only selected-sense
substitutable inputs are synonyms; morphology, regional/diminutive/qualified inputs stay distinct.
Normalize ş/ţ to ș/ț; inspect accent-preserving spellings before trusting folded ranks. No two
fold-equal spellings are separate additions, no other-sense key theft, no threshold relaxation.
Truthful label_ro reads from source to target; prefer honest is_a/part_of for displayed Lanț steps.
Current game/critic floors above and all applicable rubric FAILs remain binding.

## Heartbeat prompt (new cat-content-v2 only, after approval)

```text
Run Cât de român ești V2 from docs/CONTENT_LOOP.md on main (ADR-0188/0210/0211).
Never resume romanian-content-discovery-improved-loop. Start only after ADR0211 is on main and
Paul says start; no schedule creation/resume is implied by Phase A approval alone.
Read state first, then whole procedure at start/procedure_rev change and exact current sub-step.
Phase B first tick appends old owner_decisions/protected_refs to decisions.jsonl; state stays ≤2KB.
Boards/targets across six games are the product; M0 need map, M1 mine, M2 compat, M3 lint, M4 blind
critic, M5 freeze, M6 independent round1, M7 stage+round2, M8 landing packet, M9 record. Curation
uses steps0–3, full M2 screen, then4a–4i/5. B1 up to4 Lanț, C1 ≥20 V1.38–42 morphology families,
B2 up to20 multi-game boards; later cap24, curation at least1in3 landings. No KG+boards co-land.
Use current main-bound task worktree, Go1.27.3 PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local.
Never checks from shared main; never source-module execution/apply except approved4a. No importer
pre-screen dryrun. P pays rank/derive, quick+extensions regeneration, pins/export, corpus,
authorities and gates with world inherited; G pays full4a–4i. No light path or skipped gate.
Read scratch-helper interfaces; outputs are unapproved. Preserve sources, original verdicts,
V1 holds/refs, all evidence and rule exclusions; sucitoare excluded, Ie never ii/iei, V1.33 fresh
research, V1.14 reapplied not merged. Raw evidence/prompts/modelIDs/transcripts/manifests under
~/work/_temp/content-loop/evidence/<id>/ only. Never /tmp, delete, reset/clean, merge, push or deploy.
Fixed author/factual-v2-id/quality-v2-id/critic-v2-id; each reviewer/critic own codex exec subprocess
from fleet-tiers rungs, critic and factual different rungs. Sealed author URLs until both sign;
≥1 reviewer-chosen URL per item, signed_at precedes peer reading, >20% identical rationales or
reviewer actor in M1–M5 voids review. SHA-bound sidecar preflight plus unchanged native checks.
One sub-step per scheduled tick; interactive burst≤4 then stop until continue. Max24ticks/20commits;
research≤12items/tick,≤300sec/item, dictionary globally≥2sec, phases serialized. Fail twice waits.
Only go/drop answers review, land answers land?, continue starts a burst. Notify each new waiting
once with≤10lines, silence unchanged waits; elapsed time never approves. Seven days waiting or
invalidating main-KG change expires; never rerun M3–M6 unprompted. df -h / before corpus/fulltests;
free<12GB waits disk. BLOCKED/NEEDS-OWNER failures are reported, not repaired outside scope.
Every landing has separate allowlisted pins commit old→new+git show --stat; independent4g script
changes exactly ROOT/reference/output lines, attached diff, count previous block1206 or NEEDS-OWNER
with case-listdiff. 4i HTTP-plays every board; every alias gets fuzzy-neighbour probe+Cald guess.
Stop waiting: review after M6 table≤24rows; then waiting: land? (pins packet + gates). Paul's Claude
Code session reviews/ff-only/pushes/NAS-verifies/cleans. The loop never lands itself. Record actual
per-game cell outcomes and ≤10line retrospective/≤3proposals after external landing. No dummy
requests, cache guarantees or model/cache setting changes.
```
