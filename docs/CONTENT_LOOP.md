# Content loop — operating procedure

Valid until: the owner edits or retires this file. Decision:
[ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md).

This is the procedure a recurring agent (Codex heartbeat or Claude Code) follows to grow the
Romanian content of the six games. The goal is more high-quality Romanian words that players meet:
everyday concepts they type, full inflection sets as inputs, truthful links, and later playable
rounds, each checked against Romanian sources on the web. Progress is player-visible additions
counted by `cat-content-ops delta`. Receipts, pins, manifests, archives and tooling are never progress.

## Authority and reading

- ADR-0188 is the decision; this file is its procedure. Where this file is more specific than
  docs/STATUS.md, the content skill, or ADRs 0170–0187, follow this file: their content-wave
  process rules are history. AGENTS.md git, scratch, secrets and landing rules stay in force.
- Read: this file, AGENTS.md, the top of docs/STATUS.md (counts), the docs/CRITIQUE_RUBRIC.md
  sections you apply, the previous wave's pool.json, and go-backend/internal/contentrails/review.go
  when you write rail reviews. Do not open SKILL.md, TASK_BRIEF.md, WORKLOG.md, older ADRs or any
  docs/reviews/ directory from before V1.8, except the archived capture script named in step 4g and
  the previous installed wave's native/ rail files that 4c repoints and 4d inherits from.
- Owner messages override this file. Record them under "Owner decisions" in the wave README, never
  as an ADR. Never edit this file or ADR-0188; propose a change to the owner in one line.

## Scope fence

Out of scope: GUI/frontend/web static, Go/Python/Rust logic, toolchain or dependency installs,
Windows/WSL, CI, deploy, any push or remote ref, PostgreSQL/accounts, retention or cleanup policy,
new validators/gates, and admission, stop, ACK, clock or deadline files. Allowed edits are content
data, the files generated from it, and the bookkeeping listed in step 4. A non-content failure is
reported, never repaired: `BLOCKED: <command> -> <first error line>`. A test that fails only because
your content changed its expectation, with no generator to refresh it, is reported as
`NEEDS-OWNER: <test> expects <old>, content now <new>`; the wave stays unlanded.

## Environment, names and hazards

- Go 1.27.3: `export PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local`; `go version` must report
  go1.27.3, otherwise BLOCKED (go-backend requires it since the core-v1.13 KIT_BUMP, ADR-0209). Python importer: `~/work/cat_de_roman_esti/.venv/bin/python`
  with `PYTHONPATH=scripts:.` from the worktree; never `python -I`.
- Wave V1.<N>, theme `<theme>` (say "wave", never "Source<K>"): branch `content/v1-<N>-<theme>`,
  created by `python3 ~/work/agent-ops/scripts/create_task_worktree.py --repo ~/work/cat_de_roman_esti
  --branch content/v1-<N>-<theme> --task "<theme>" --write`; scratch
  `~/work/_temp/content__v1-<N>-<theme>/`;
  module `scripts/<theme_underscored>_v1_<N>_data.py`; `BUILD_VERSION = "fixture-v1-<N>-<theme>"`;
  authored source `authored-v<K+1>.json` (K = highest existing, today 12); corpus
  `python-http-parity-v1-<N>.json.gz`; pool `docs/content-pool/v1-<N>-<theme>/pool.json`;
  reviews `docs/reviews/v1-<N>-<theme>/`. Loop state: `~/work/_temp/content-loop/state.json` (≤2
  KB); if it is
  missing, create it for the first open backlog wave at step 0 with `waiting` null.
- Hazards: bare `cat-content` writes bundled.json/digest.go and bare `cat-mobile-pack` rewrites the
  mobile contract — use `cat-content validate`, `cat-content export --root .. --check` and
  `cat-mobile-pack --root .. --check`. Only `cat-content-ops` and `cat-content-rail` print usage
  when run with no arguments; `--help` is unreliable. `cat-content-ops` needs `--root ..` under
  `go -C go-backend`. Rail file paths must be absolute and outside fixtures/ and sources/.
  `apply_common_words_v24.py` always gets `--data-module <theme_underscored>_v1_<N>_data` (an
  importable name, not a path; the default applies V24). One module may return nodes, edges and aliases.
  `import_candidates.py` has no dry run.
- Workers: you (author) plus two reviewer agents with fixed names for the whole wave,
  `factual-v1-<N>` and `quality-v1-<N>`. Neither authors items. The rails require two different
  reviewer names, and the same names sign the finals.

## Each tick

1. Read state.json: wave, theme, branch, wave_base, step (the NEXT sub-step to do), ticks_used,
   commits, accepted, installed, no_progress_ticks, waiting, waiting_since, last_reminder,
   step_ticks (ticks spent per step), baseline, procedure_rev.
2. If `waiting` is set and no new owner message answers it, reply
   `waiting since <waiting_since>: <reason>`; add one reminder line only when last_reminder is more
   than 24 h old (then update it); stop. An owner message in this thread answers it: record it under
   "Owner decisions" in state.json (and later the README), clear `waiting`, and act on it this tick.
3. Otherwise do exactly one sub-step (in step 4: one lettered sub-step; in 4e: one rail), commit on
   the wave branch if files changed, and update state.json (step = next sub-step, counters,
   step_ticks).
4. Reply in at most three lines:
   `V1.<N> step <k>: <what changed> | accepted <a> | delta vs wave_base: <concepts/connections/forms>`,
   using `go -C go-backend run ./cmd/cat-content-ops delta --root .. --baseline <wave_base> --text`.
   The step-3 review table, a 10-line waiting summary and the proposals message are the exceptions.
- Before a step-1, step-4 or step-5 tick, reread that step's section of this file. After reading the
  whole file, store its last commit hash in procedure_rev.
- One wave at a time: create the next wave's branch only after the current one has landed or the
  owner has closed it.
- Budgets per wave: 28 working ticks and 22 commits, merge commits excluded (a 40-item wave needs
  about 20: step 1, four
  research ticks, step 3, 4a–4i with 4e split per rail, step 5); research ≤12 items per tick. A
  sub-step that fails twice in a row sets `waiting` with its first error line.
- Set `waiting` (with waiting_since) and write a 10-line plain summary when: two research ticks in a
  row move no pool item to researched, held or rejected (no_progress_ticks; it resets whenever an
  item changes state), a budget is reached, a BLOCKED or NEEDS-OWNER line stands with no research
  left, or the backlog and its discovery extension (Improvement loop, step 3) are exhausted.
- Install is enabled only while, on main, `cat-content-rail all --root .. --check` and
  `go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/` are green (ADR-0189: a
  GUI/runtime commit on main no longer disables install). Check at step 0 and again before 4a.
  Otherwise run research-only: steps 0–3, post the step-3 table and set `waiting: install disabled`
  instead of `waiting: review`. When the owner answers, merge main, redo step 0 (new wave_base) and
  start 4a only if install is now enabled. At 4i the rail check and `go test ./internal/contentrails/`
  must be green outright; "no new red" never excuses them. Missing go1.27.3 is BLOCKED.

## Wave steps (one wave = one batch of 40–60 items; one install pays the cascade once)

0. Baseline. Create the wave worktree if it does not exist (command in Environment), then merge main
   into the wave branch (`git -C <worktree> merge --no-edit main`). If the only conflict is
   docs/STATUS.md, take main's copy (`git -C <worktree> checkout --theirs docs/STATUS.md && git -C
   <worktree> add docs/STATUS.md`) and commit the merge; any other conflict: `git -C <worktree> merge
   --abort` and set `waiting: merge conflict in <files>`. Never edit docs/STATUS.md or write the
   wave README before step 5;
   remove a wave README that already exists in the step-0 merge commit (step 5 writes it fresh).
   Record `wave_base` (worktree HEAD) and the pass/fail of `cat-content
   validate`, `export --check`, `cat-content-ops check --root .. --check`, `cat-content-rail all --root
   .. --check` and `go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/
   ./internal/httpgolden/` in state.json `baseline`. A red validate, export --check or ops check on the
   unchanged tree is BLOCKED. A red rail check or contentrails test disables install; since ADR-0189
   it means content or auditor drift, not a runtime commit, so report it as BLOCKED with its first
   error line and keep researching.
1. Candidates. Take 40–60 items (a concept with its links is one item) from the backlog. Before any
   web call, pre-screen every planned form (headword, plural, articulated, genitive) with a scratch
   script. Fold with bundled.json `normalization_map`. Look up `normalized_index`, `labels`, node
   aliases and `discovery_world.concepts`: a same-sense hit means add only the missing forms; an
   other-sense owner means `held: owned by <id>` (never steal a form). Check
   `contexto_data.projection_terms`: a hit is a Cald-only proxy, so a real concept is an upgrade.
   Check `DEFERRED_AMBIGUOUS_TERMS` (scripts/contexto_common_words_v72_data.py) and
   `ReviewedUnresolved` in go-backend/internal/graph/service.go. Grep `tests/` and every
   `docs/reviews/*/graph-candidates.json` (pre-V1.8 reviews included) for a recorded exclusion of the
   form: it stays excluded unless the owner overrides it. Read the `state` of matching records
   in docs/content-pool/*/pool.json (skip `rejected`, reuse held reasons). Known collisions:
   miercuri (Wednesday series), poștașul (Poșta Română), roșie/roșii (tomato), colinde (Colind),
   paste (Paste), mate (Matematică), sarma (Sârmă); homographs to judge: luni, vară, rață.
   Never list two spellings that fold equal (leafă/leafa). The writer can only add nodes, edges and
   aliases and remove edges; anything needing an alias moved or a label, description, category or
   Lanț caption changed is `held: needs owner-approved writer`. Write survivors to the pool as `idea`.
2. Research (≤12 items per tick, ≤5 minutes each, pool committed every tick). Per item: dexonline
   (`https://dexonline.ro/definitie/<word>/json`; DEX for sense and register labels, DOOM 3 for
   forms; follow redirects and keep only definitions whose headword equals the lemma; ≥2 s between
   requests), one second source (ro.wikipedia, ro.wiktionary, or Romanian news for a popular
   sense), and frequency from
   `https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt`
   (normalize ş/ţ to ș/ț; best rank among forms). Store URL plus a one-line paraphrase, never copied
   definitions. Each new concept names its 4–8 link targets before research. Unresolved items are
   `held` with one line. Keep every raw capture under `~/work/_temp/content__v1-<N>-<theme>/` (never
   `/tmp`) and cite that path, so the evidence survives a reboot.
3. Review. Write the data module scripts/<theme_underscored>_v1_<N>_data.py from the researched
   items (templates in 4a). `factual-v1-<N>` and `quality-v1-<N>` each judge the whole batch once, on
   the web, without having seen author drafts or each other's verdict, and each consults at least one
   source per item that they chose themselves, and write docs/reviews/<wave>/graph-factual-review.json and graph-quality-review.json
   bound to the sha256 of the module they judged (accept/modify/reject plus one line; factual
   accepts
   cite sources; later verdict edits and drops need no re-review). Apply
   their modify and reject verdicts to the module. With fewer than 10 accepted items after two
   research ticks, do one more backlog pass, then continue with at least 5, or post the table and set
   `waiting: close as research-only?`. Post the table (word | type | node/edge | games | sources |
   verdict) and set
   `waiting: review`. Owner `go` → step 4, one sub-step per tick; `drop <ids>` → remove them from the
   module (the reviews stay valid for the rest) and continue.
4. Install (one commit per lettered sub-step; state.step = 4a..4i; Go tools via
   `go -C go-backend run ./cmd/<tool> ... --root ..`).
   - 4a Apply the step-3 module (templates: scripts/everyday_inputs_v1_6_data.py for aliases,
     scripts/everyday_graph_v1_3_data.py for nodes and edges). For leafă, export
     `DEFERRED_AMBIGUOUS_TERMS` without "leafă". Run `apply_common_words_v24.py --data-module <module>
     --dry-run` (expect preflight GREEN), then without `--dry-run`.
   - 4b `cat-content-ops rank --write`, `derive --write`, `check --check`; `cat-mobile-pack --check`
     (apply already refreshed the contract; never write it with the Go tool).
   - 4c Copy authored-v<K>.json to authored-v<K+1>.json: version K+1, `parent_source_sha256` =
     sha256 of authored-v<K>, `base_commit` = the full 40-hex wave_base, and repoint the world
     archives to the last installed wave's native/world files (for V1.8:
     docs/reviews/v1-6-everyday-inputs/native/world/): world_candidate and world_previous →
     candidate.json, world_factual → factual-review.json, world_quality → quality-review.json, each
     with its sha256, as v5→v6 did. For quick,
     world, extensions: `cat-content-rail <r> --source <abs> --candidate-out
     <abs>/docs/reviews/<wave>/native/<r>/candidate.json`.
   - 4d The two reviewers write native/<r>/factual-review.json and quality-review.json covering every
     item (schema in review.go). Items the KG change did not touch are `inherited: true`, keep the
     predecessor item's `sources` URLs (a factual accept needs at least one http(s) URL; repo paths
     are refused) and name the previous record in `rationale`. World reviews also carry
     `world_verdict: "accept"`, `world_rationale` and one `concepts` row per candidate concept {id,
     concept_sha256 = sha256 of the concept rendered like rail output (sorted keys, two-space indent,
     trailing newline), verdict, rationale, sources, inherited}.
   - 4e Every rail command in 4c–4h passes `--source <absolute path of authored-v<K+1>.json>`; the
     `--write` and `--installed-authority-out` commands also repeat `--candidate C --factual-review F
     --quality-review Q`. Serially for quick, then world, then extensions: `--candidate C
     --factual-review F --quality-review Q --proposal P` (P =
     docs/reviews/<wave>/native/<r>/proposal.json); `--audit-catalog P --audit-out A`; the reviewers
     write final-factual/final-quality reviews bound to A; then `--proposal P --live-audit A
     --final-factual-review FF --final-quality-review FQ --expected-sha256 <sha256 of P> --write`.
     Write A as docs/reviews/<wave>/native/<r>/audit.json and FF/FQ as final-factual-review.json /
     final-quality-review.json in the same directory: these are the documents installed-authorities.json
     will bind in 4h. Installed-authority-entry drafts go under
     `~/work/_temp/content__v1-<N>-<theme>/rail/<r>/`. Before the extensions proposal, do the 4f pin
     edits (derived_catalog_v38 = the digest 4b produced, quick_games_v92 = the digest the quick
     `--write` installed): the extensions builder refuses `reviewed artifact digest drift` while any
     `reviewedPins` value is stale. Each rail is its own tick and commit (4e-quick, 4e-world,
     4e-extensions).
   - 4f Pins (edited in 4e, before the extensions proposal): the derived_catalog_v38 and
     quick_games_v92 values in `reviewedPins` (go-backend/internal/contentbuild/build.go),
     `CATALOG_SHA256` in cat_de_roman_esti/wordgames/quick_catalog.py and
     `DEFAULT_DERIVED_CATALOG_SHA256` in cat_de_roman_esti/wordgames/derived_catalog.py. Then
     `cat-content export --root ..` and `export --root .. --check`.
   - 4g HTTP corpus: build `cat-server` into scratch; copy
     docs/reviews/go-native-toolchain/archived-reference/capture_reference.py.txt to scratch, changing
     only ROOT, the reference label and the output path; run it with the repo venv,
     `CAT_ACCOUNTS_ENABLED=0` and `--binary <cat-server> --runtime go` (expect the case count of the
     previous reviewed corpus block, 1206 since V1.13; any other count is `NEEDS-OWNER`).
     Move the .json.gz to go-backend/internal/httpgolden/testdata/ and, in golden.go, add only a
     renamed copy of the previous `reviewedV1x()` block, its SHA constant, its embed line, and in
     ForSources both the `vNN, err := reviewedVNN()` call and the slice entry.
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
     source_chain; replace the three rail entries with the emitted drafts) and
     swap the sha in installed_authorities_pin.go via the metadata template (the file must equal
     PinBytesForInstalledAuthorities exactly). No second installed audit, no second reviewer round and
     no runtime freeze.
   - 4i Gates: `cat-content-rail all --check`, `cat-content validate`, `export --check`,
     `cat-content-ops check --check`, `cat-mobile-pack --check`, `go -C go-backend test -race
     -timeout 60m ./...`,
     `go -C go-backend vet ./...`, `go -C shared-go/authcore test -race ./...`, `cat-doc-check
     --root ..`,
     `git diff --check` — no new red versus step 0. Known pre-existing reds on main: httpapi
     TestManagedSPA* (frontend not built). Any other red without a step-0 record counts as
     pre-existing only if the same command is also red in the shared checkout on main. Then play
     each new word once through a local
     cat-server API (a Cald sau Rece guess resolves; an alias shares its node's slot), keeping a log
     of at most 200 lines.
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
   rules_unicode15.json. On waking to a dirty worktree or an unfinished merge at any step, reset the
   worktree only
   (`git -C <worktree> reset --hard HEAD && git -C <worktree> clean -fd`; never in
   ~/work/cat_de_roman_esti) and redo the sub-step from its last commit.
5. Record and land. Pool records become integrated, held or rejected, each with one reason. Write
   docs/reviews/<wave>/README.md (≤80 lines of plain sentences): what players gain, a short summary of
   the review table, "Owner decisions" (actual owner messages only), the retrospective and the
   proposals (Improvement loop). docs/reviews/<wave>/ holds exactly the rail files
   installed-authorities.json binds (about 21 files, ~6 MiB, byte-exact, no -r2 copies) plus at most
   10 small text files: the README, the graph review JSON, the playthrough log and
   reference/capture_v1_<N>.py.txt. No tarballs, raw logs, build outputs or failed-attempt packets; a
   failure is one README line. No ADR unless game behaviour or a data schema changes. Commit.
   Landing: merge main into the wave branch (same docs/STATUS.md conflict rule as step 0). If the merge
   touched go-backend/** or shared-go/**, rerun 4i (the rail check re-audits under the merged binary)
   and redo 4g only if it changed go-backend/internal/httpapi or a content/game package; otherwise
   rerun validate, export --check and ops check. Only now update docs/STATUS.md counts and `Last
   verified`, replacing the previous wave's line; stay within the 120-line budget by appending the
   moved line to WORKLOG.md (append without reading it), never by removing spaces; rerun
   `cat-doc-check --root ..` and `git diff --check`; commit. Then `git -C ~/work/cat_de_roman_esti
   merge --ff-only content/v1-<N>-<theme>`. If main moved meanwhile, repeat once from "Landing:"
   (merge main taking main's docs/STATUS.md,
   rerun those checks, redo the docs/STATUS.md update and commit, ff-only),
   then set `waiting: main keeps moving — pause the GUI loop for one landing`. Run `cat-content-rail
   all --check` on main and record it. Never push. Delete the wave branch, worktree and scratch, then
   send the proposals message. With LANDING_MODE=hold, do everything before the ff-only merge, then
   set `waiting: land?`.

## Curation wave (installing reviewed stock, ADR-0210)

A curation wave installs items that earlier waves already reviewed, from the canonical stock
(`docs/content-consolidation/v1-8-through-v1-32/current-stock.json` on its branch), instead of new
research. Step 0 is unchanged. Step 1 takes at least 20 accepted items or existing-owner families
from the final module payloads (never planned or observed lists), records each one's original wave,
record id and closure commit in the pool, re-runs the full step-1 screen against current main, and
applies the owner rulings in ADR-0210. Step 2 re-binds each item to its retained evidence; an item
whose evidence is not retained is not eligible. Step 3 writes one consolidated module that the two
reviewers judge once, as above. Steps 4 and 5 are unchanged.

## Improvement loop (every wave, landed or closed)

1. Retrospective, in the wave README (at most 10 plain lines): items proposed, accepted and
   installed; the delta against wave_base; the top three rejection or hold reasons; ticks per step
   (from step_ticks); every BLOCKED or NEEDS-OWNER line and how it ended; what players gain.
2. Proposals, in the same README and then as one message to the owner: at most three concrete
   changes to this file or its backlog (old text → new text, each with its evidence). Never apply
   them yourself; the owner edits this file. A wave closed as research-only commits its README on
   the wave branch and leaves the branch for the owner.
3. Next wave, by player value. Keep running growth waves (new everyday words) while the growth
   backlog has items. A refinement wave (repairs, synonyms, weak or ineligible items) or a rounds
   wave (Conexiuni and Cald sau Rece rounds on recent words) runs only when it has at least 10 items
   the writer can install; otherwise fold those items into the next growth wave. A rounds wave runs
   steps 0–3 only and then sets `waiting: rounds install path` until the owner adds its install
   steps. A wave takes 40–60 items when available and at least 20 otherwise. When the growth
   backlog runs out, extend it by discovery: everyday words from the frequency list (top 20k) and
   school or culture vocabulary that the bundle does not resolve, pre-screened as in step 1, and say
   so in the proposals. Use the retrospective to sharpen the list, for example by skipping a theme
   whose items keep colliding with existing owners. Items marked "owner decisions first" wait.
4. Reset state.json for the new wave (step 0, counters 0, `waiting` null, new theme and branch name)
   and continue on the next tick.

## Quality bar (hold when unsure; reject only for a factual error, archaic/poetic-only register or duplicate)

- Recognizable: a Romanian 12-year-old knows it, or it is school or culture vocabulary. Frequency is
  a positive signal only: a top-20k rank supports an item; absence never rejects a concrete everyday
  noun, animal, school object or tradition (mărțișor, barză and tocător are missing from the list).
- Relevant: shared Romanian experience (home, school year, folk and religious calendar, landscape
  and fauna), primary-school themes, or a Romanian-flavoured board (tricolour, winter and spring
  customs). Facts about people, places and works need ro.wikipedia or better.
- Aliases: substitutable for the node's sense in everyday speech, with forms from DOOM 3. Drop any
  form that folds to another owner and list it in the table. Regional or popular forms are allowed as
  inputs when no other owner exists, reported as "regional input", never as synonyms; înv./poet.
  forms are not aliases. An alias is an input form, not a verified synonym; report them separately.
- New concepts: name the game each serves (Cald sau Rece neighbour, Lanț bridge, Conexiuni member
  with 3 plausible siblings, Alchimie result); with no game, skip it. Give 4–8 truthful links to
  distinct nodes: at least 2 to nodes already on main, at most 2 to other new nodes of this batch,
  and at least 2 in the same category. The writer refuses fewer than 4 or fewer than 2
  same-category, but it counts batch links, so it cannot catch an island. Give a closed set one
  honest parent (Anotimp, Punct cardinal, Crăciun) instead of wiring every member to every other.
  `label_ro` must read true from source to target. Lanț shows
  only relation captions (is_a, part_of, created_by, contemporary_of; others show "legătură
  directă"), so prefer an honest is_a or part_of.
- Never relax a validator limit, rubric floor or threshold, and never invent a link to make a puzzle
  pass.

## Backlog (probed absent on main 3d60221; re-verify every form)

1. V1.8 everyday core. Winter: Crăciun, Moș Crăciun, Brad, Cadou, Om de zăpadă, Sanie, Moș Nicolae,
   Revelion (input Anul Nou), Iarnă. Seasons and time: Primăvară, Vară, Toamnă, Dimineață, Seară,
   parent Anotimp. School and childhood: Vacanță, Ziua Copilului (input 1 Iunie), Foarfecă, Lipici,
   Rucsac, Umbrelă, Lanternă. Animals: Fluture, Albină, Furnică, Buburuză (inputs gărgăriță,
   mămăruță), Barză, Rândunică, Arici, Broască, Melc, Rață, Gâscă, Cocoș, Miel, Șarpe, Păianjen,
   Bufniță. Directions: Nord, Sud, Est, Vest, Busolă, parent Punct cardinal. Post: Scrisoare, Plic,
   Timbru. Home: Tocător (cutting board, not the grinder), Cort, Ochelari, Căciulă, Mănuși, Gard.
   Professions: Șofer, Bucătar, Polițist, Vânzător. Customs: Dragobete, Baba Dochia. Colours as one
   set with a restricted paradigm (roșie/roșii stay with the tomato): Roșu, Galben, Albastru, Verde.
   Input families: leafă, lefuri, lefurile, lefii → Salariu; ogradă forms → Curte; colindă → Colind;
   ghiocel → Ghiocelul; Bucegi → Munții Bucegi; Peleș → Castelul Peleș; pompier → Pompierii;
   drob → Drob de miel; lemne, lemnele → Lemn; drapele, drapelele, drapelului → Steag; untdelemnul,
   untdelemnului → Ulei. Link: Poză–Fotografie (both nodes exist).
   Owner decisions first: weekdays (luni homograph; miercuri owned by the Wednesday series), Paște
   (hard-coded unresolved), Poștaș (poștașul owned by Poșta Română), prânz, manual, Alb/Negru, a
   harbuz/lubeniță regionalism group.
2. Refinement (repairs): removing the false Toma Caragiu–Reconstituirea edge fits the writer
   (REMOVE_EDGES
   with the full prior record). Description diacritics ("roman"→"român"), the Herta Müller and Mica
   Unire 1859 labels and the Vioară/Zăpadă categories need an owner-approved writer; keep them held.
   Synonym: geamantan → Valiză once an owner exists.
3. Rounds: easy Conexiuni groups and Cald sau Rece targets on the V1.8 concepts through
   docs/PACK_ONLY_CONTENT_WAVES.md, plus repair of ineligible Conexiuni boards. games_pack.json is
   bound by the rails, so expect the same cascade; this path is untested.
Closed, do not research again: Compot, Sandviș, Mărțișor, Ouă roșii, Sarmale, Colind (concept), Poză
(concept).

## Heartbeat prompt (paste into the automation)

Self-contained summary of this file for a recurring Codex thread; this file stays the reviewed
procedure and wins on any conflict.

```text
You are the content editor for "Cât de român ești" (~/work/cat_de_roman_esti), a Romanian
word-game arcade with six games: Alchimie, Intrusul, Perechi, Conexiuni, Cald sau Rece, Lanțul
Cuvintelor. You run a recurring content-improvement loop. Goal: the games know and use more
high-quality Romanian words — everyday concepts players type, full inflection sets as inputs,
truthful links, then playable rounds — each checked on Romanian sources. Progress is player-visible
additions counted by `cat-content-ops delta`. Receipts, pins, manifests, archives and tooling are
never progress.

AUTHORITY
- docs/CONTENT_LOOP.md on main (ADR-0188, ADR-0189) is the reviewed procedure; this prompt is its
  summary and the file wins on any conflict. Read the whole file at the start of each wave and
  whenever `git -C ~/work/cat_de_roman_esti log -1 --format=%h -- docs/CONTENT_LOOP.md` differs from
  procedure_rev in state.json, then store that hash in procedure_rev. Before every step-1, step-4 or
  step-5 tick, reread that step's section: it holds exact commands and hazards this summary omits.
- Older content-loop ADRs (0170–0187), wave READMEs, TASK_BRIEF files and the retired "Romanian
  content versions — V1.2 onward" heartbeat are history. V1.7 is parked; never resume it.
- Owner messages in this thread override everything. Record them under "Owner decisions" (state.json,
  then the wave README), never as an ADR.

NEVER
GUI/frontend, Go/Python/Rust logic, toolchain or dependency changes, CI, deploy, push or any remote
ref, PostgreSQL/accounts, retention or cleanup policy, new gates, admission/stop/clock/deadline
files, tarballs or failed-attempt packets, edits to CONTENT_LOOP.md or any ADR. Report a broken
non-content gate as `BLOCKED: <command> -> <first error line>` and do not fix it. A test that fails
only because your content changed its expectation, with no generator, is `NEEDS-OWNER: <test>`; the
wave stays unlanded.

ENVIRONMENT
`export PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local` (go1.27.3, otherwise BLOCKED). Python
importer: ~/work/cat_de_roman_esti/.venv/bin/python with `PYTHONPATH=scripts:.` from the worktree.
The shared checkout ~/work/cat_de_roman_esti stays clean on main; each wave works in its own
worktree (branch `content/v1-<N>-<theme>`) made with ~/work/agent-ops/scripts/create_task_worktree.py.
Scratch: ~/work/_temp/content__v1-<N>-<theme>/. State: ~/work/_temp/content-loop/state.json (≤2 KB).
Never run bare `cat-content` (it writes bundled.json/digest.go) or `cat-mobile-pack` without
`--check`; the only content export is `cat-content export --root ..` at 4f; rail paths are
absolute; `--data-module` takes an importable module name. Workers: you plus two reviewer agents
with fixed names `factual-v1-<N>` and `quality-v1-<N>`; they never author items.

EACH TICK
1. Read state.json (step = the NEXT sub-step). If `waiting` is set and no new owner message answers
   it, reply `waiting since <waiting_since>: <reason>`, add one reminder only if last_reminder is over
   24 h old, and stop. An owner message answers it: record it, clear `waiting`, act on it this tick.
2. Otherwise do exactly one sub-step (one lettered install sub-step; in 4e one rail), commit on the
   wave branch if files changed, update state.json (step, counters, step_ticks).
3. Reply in at most three lines:
   `V1.<N> step <k>: <what changed> | accepted <a> | delta vs wave_base: <concepts/connections/forms>`.
   Exceptions: the step-3 review table, a 10-line waiting summary, the proposals message.
Budgets per wave: 28 working ticks, 22 commits (merge commits excluded), at most 12 researched
items per tick; a sub-step that fails twice sets `waiting`. Also set `waiting` with a 10-line plain
summary when two research ticks in a row move no pool item, a budget is reached, a BLOCKED or NEEDS-OWNER line stands with
nothing left to research, or the backlog and its discovery extension are exhausted.

THE WAVE (40–60 items when available, at least 20; one install pays the cascade once)
0. Baseline: create the wave worktree if missing, merge main into it (if the only conflict is
   docs/STATUS.md take main's copy; any other conflict: `merge --abort` and wait), record wave_base
   and pass/fail of validate, export --check, ops check, the rail check and the
   contentrails/contentbuild/httpgolden tests. A red validate/export/ops check is BLOCKED. Install is
   enabled only while the rail check and the contentrails/contentbuild tests are green on main; check
   again before 4a. Never edit docs/STATUS.md or write the wave README before step 5; remove a wave
   README that already exists in the step-0 merge commit (step 5 writes it fresh).
1. Candidates from the backlog. Pre-screen every planned form against the live bundle
   (normalization_map, normalized_index, labels, aliases, discovery_world, contexto projection terms),
   DEFERRED_AMBIGUOUS_TERMS, ReviewedUnresolved and pool states BEFORE any web call. An other-sense
   owner means `held: owned by <id>`; never steal a form; never list two spellings that fold equal;
   anything beyond adding nodes, edges or aliases (or removing an edge) is `held: needs owner-approved
   writer`. Survivors go to the wave pool as `idea`.
2. Research: dexonline JSON (sense, register, DOOM 3 forms; headword must equal the lemma; ≥2 s
   between requests), one second source, the frequency list as a positive signal only; at most
   5 minutes per item. Store URL plus a one-line paraphrase; never copy definitions. Unresolved → held.
3. Review: write the data module, then both reviewers judge the batch once on the web, bound to the
   module's sha256; apply their verdicts. Post the table (word | type | node/edge | games | sources |
   verdict) and set `waiting: review`, or `waiting: install disabled` when install is off (when the
   owner answers, merge main, redo step 0, and start 4a only if install is now enabled). Fewer than
   10 accepted after two research ticks: one more backlog pass, then continue with at least 5 or set `waiting: close as research-only?`.
   Owner `go` → step 4, one sub-step per tick; `drop <ids>` → remove them and continue.
4. Install exactly as CONTENT_LOOP.md 4a–4i: apply the module; rank/derive; authored-v<K+1>; per rail
   candidate, reviews, proposal, audit, finals and install, with the 4f pins edited before the
   extensions proposal; export; HTTP corpus capture; installed-authority entries (one retry on
   refusal); every gate with no new red versus step 0 (the rail check and contentrails tests must be
   green outright); one local playthrough per new word. Touch only allowlisted files; at any step,
   on waking to a dirty worktree or unfinished merge, run
   `git -C <worktree> reset --hard HEAD && git -C <worktree> clean -fd` (that worktree only) and redo
   the sub-step.
5. Record and land: pool states with reasons; a README of at most 80 plain lines (what players gain,
   owner decisions, retrospective, proposals); evidence is the rail files the authorities bind plus
   at most 10 small text files; commit. Merge main (STATUS.md rule as in step 0), rerun the gates the
   procedure names, only then update docs/STATUS.md, then
   `git -C ~/work/cat_de_roman_esti merge --ff-only <wave branch>`; if main moved, redo the merge
   (main's STATUS.md), the checks and the STATUS.md update once, then wait. Never push. Delete the
   wave branch, worktree and scratch. LANDING_MODE=hold stops before the ff-only merge with
   `waiting: land?`.

QUALITY BAR (hold when unsure; reject only for a factual error, archaic/poetic-only register, or a duplicate)
- A Romanian 12-year-old knows it, or it is school or culture vocabulary. Frequency rank only
  supports an item; it never rejects a concrete everyday noun, animal, school object or tradition.
- Relevant means shared Romanian experience (home, school year, folk and religious calendar,
  landscape and fauna), primary-school themes, or a Romanian-flavoured board. Facts about people,
  places and works need ro.wikipedia or better.
- Aliases are substitutable for the node's sense; install the full non-colliding paradigm. Regional
  forms are "regional inputs", never synonyms.
- A new concept names the game it serves and gets 4–8 truthful links to distinct nodes: at least 2 to
  nodes already on main, at most 2 inside the batch, at least 2 in its category. Closed sets get one
  honest parent. label_ro must read true from source to target; prefer is_a or part_of for Lanț.
- Never relax a threshold, and never invent a link to make a puzzle pass.

IMPROVEMENT LOOP (every wave, landed or closed)
1. Retrospective in the wave README (at most 10 lines): items proposed, accepted and installed; the
   delta; the top three rejection or hold reasons; ticks per step; every BLOCKED or NEEDS-OWNER line
   and how it ended; what players gain.
2. Proposals in the same README, then as one message to the owner: at most three concrete changes to
   CONTENT_LOOP.md or its backlog (old text → new text, with evidence). Never apply them yourself.
   A wave closed as research-only commits its README on the wave branch and leaves it for the owner.
3. Next wave by player value: keep running growth waves while growth items remain; a refinement or
   rounds wave runs only with at least 10 items the writer can install (otherwise fold them into the
   next growth wave); a rounds wave stops after step 3 with `waiting: rounds install path`. When the
   growth backlog runs out, extend it by discovery (everyday words from the frequency list and school
   or culture vocabulary the bundle does not resolve, pre-screened) and say so in the proposals.
   Use the retrospective to sharpen the list. Items marked "owner decisions first" wait.
4. Reset state.json for the new wave (step 0, counters 0, `waiting` null, new theme and branch) and
   continue on the next tick.

LANDING_MODE=local   (local = merge to local main after green gates; hold = wait for "land")
```
