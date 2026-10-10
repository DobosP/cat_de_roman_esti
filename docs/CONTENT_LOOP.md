# Content loop — operating procedure

Valid until: the owner edits or retires this file. Decision: [ADR-0188](adr/0188-park-v1-7-and-reset-content-loop.md).

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
  docs/reviews/ directory from before V1.8, except the archived capture script named in step 4g.
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

- Go 1.27.1: `export PATH=/usr/local/go/bin:$PATH GOTOOLCHAIN=local`; `go version` must report
  go1.27.1, otherwise BLOCKED. Python importer: `~/work/cat_de_roman_esti/.venv/bin/python`
  with `PYTHONPATH=scripts:.` from the worktree; never `python -I`.
- Wave V1.<N>, theme `<theme>` (say "wave", never "Source<K>"): branch `content/v1-<N>-<theme>`,
  created by `python3 ~/work/agent-ops/scripts/create_task_worktree.py --repo ~/work/cat_de_roman_esti
  --branch content/v1-<N>-<theme> --task "<theme>" --write`; scratch `~/work/_temp/content__v1-<N>-<theme>/`;
  module `scripts/<theme_underscored>_v1_<N>_data.py`; `BUILD_VERSION = "fixture-v1-<N>-<theme>"`;
  authored source `authored-v<K+1>.json` (K = highest existing, today 6); corpus
  `python-http-parity-v1-<N>.json.gz`; pool `docs/content-pool/v1-<N>-<theme>/pool.json`;
  reviews `docs/reviews/v1-<N>-<theme>/`. Loop state: `~/work/_temp/content-loop/state.json` (≤2 KB); if it is
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

1. Read state.json: wave, branch, wave_base, step, ticks_used, commits, accepted, installed,
   no_progress_ticks, waiting, baseline, procedure_rev. If `waiting` is set, reply
   `waiting since <date>: <reason>`, add one reminder line to the owner at most once per 24 h, and stop.
   Only the owner clears `waiting`.
2. Otherwise do the next sub-step, commit if files changed, update state.json.
3. Reply in at most three lines:
   `V1.<N> step <k>: <what changed> | accepted <a> | delta vs wave_base: <concepts/connections/forms>`,
   using `go -C go-backend run ./cmd/cat-content-ops delta --root .. --baseline <wave_base> --text`.
- One wave at a time: never create the next wave's branch before the current one has landed or the
  owner has closed it.
- Budgets per wave: 28 working ticks and 20 commits (a 40-item wave needs about 18: step 1, four
  research ticks, step 3, 4a–4i, step 5); research ≤12 items per tick.
- Set `waiting` and write a 10-line plain summary when: two research ticks in a row (steps 1–3)
  move no pool item to researched, held or rejected (README-only commits do not count; install
  sub-steps 4a–4i are bounded only by the budgets), a budget is reached, a BLOCKED or
  NEEDS-OWNER line stands with no research left, or the backlog is exhausted.
- Install is enabled only while, on main, `cat-content-rail all --root .. --check` is green and
  `go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/` is green (ADR-0189: the rail
  check re-runs the native audits under the current binary; a GUI/runtime commit on main no longer
  disables install). Check at step 0 and again before 4a. Otherwise run research-only: steps 0–3
  for one wave, post the step-3 table and set `waiting: install disabled` instead of `waiting: review`.
  When the owner clears it, merge main into the wave branch, redo step 0 (new wave_base) and start 4a
  only if install is now enabled. At 4i the rail check and `go test ./internal/contentrails/` must be
  green outright; "no new red" never excuses them. Missing go1.27.1 is BLOCKED.

## Wave steps (one wave = one batch of 40–60 items; one install pays the cascade once)

0. Baseline. Record `wave_base` (worktree HEAD). Record pass/fail of `cat-content validate`,
   `export --check`, `cat-content-ops check --root .. --check`, `cat-content-rail all --root .. --check`
   and `go -C go-backend test ./internal/contentrails/ ./internal/contentbuild/ ./internal/httpgolden/`.
   Record the results in state.json `baseline`. The install gate later is "no NEW red versus this
   baseline". A red `cat-content validate`, `export --check` or `cat-content-ops check` on the
   unchanged tree is BLOCKED; a red rail check or contentrails test only disables install. A red rail
   check now means content, not a runtime commit: report it as BLOCKED.
1. Candidates. Take 40–60 items (a concept with its links is one item) from the backlog. Before any
   web call, pre-screen every planned form (headword, plural, articulated, genitive) with a scratch
   script. Fold with bundled.json `normalization_map`. Look up `normalized_index`, `labels`, node
   aliases and `discovery_world.concepts`: a same-sense hit means add only the missing forms; an
   other-sense owner means `held: owned by <id>` (never steal a form). Check
   `contexto_data.projection_terms`: a hit is a Cald-only proxy, so a real concept is an upgrade.
   Check `DEFERRED_AMBIGUOUS_TERMS` (scripts/contexto_common_words_v72_data.py) and
   `ReviewedUnresolved` in go-backend/internal/graph/service.go. Read the `state` of matching records
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
   `held` with one line.
3. Review. `factual-v1-<N>` and `quality-v1-<N>` each judge the whole batch once, on the web, and
   write docs/reviews/<wave>/graph-factual-review.json and graph-quality-review.json over the exact
   module bytes (accept/modify/reject plus one line; factual accepts cite sources). With fewer than 10
   accepted items after two research ticks, do one more backlog pass, then install at least 5 or close
   the wave as research-only. Post the table (word | type | node/edge | games | sources | verdict) and
   set `waiting: review`. On the owner's `go`, run steps 4–5 without another wait; on `drop <ids>`,
   remove them and continue.
4. Install (one commit per lettered sub-step; state.step = 4a..4i; Go tools via
   `go -C go-backend run ./cmd/<tool> ... --root ..`).
   - 4a Write the module from scripts/everyday_inputs_v1_6_data.py (aliases) or
     scripts/everyday_graph_v1_3_data.py (nodes and edges). For leafă, export
     `DEFERRED_AMBIGUOUS_TERMS` without "leafă". Run `apply_common_words_v24.py --data-module <module>
     --dry-run` (expect preflight GREEN), then without `--dry-run`.
   - 4b `cat-content-ops rank --write`, `derive --write`, `check --check`; `cat-mobile-pack --check`
     (apply already refreshed the contract; never write it with the Go tool).
   - 4c Copy authored-v<K>.json to authored-v<K+1>.json: version K+1, `parent_source_sha256` =
     sha256 of authored-v<K>, `base_commit` = wave_base, and repoint archives.world_candidate,
     world_previous, world_factual and world_quality to the last installed wave's native/world
     files (for V1.8: docs/reviews/v1-6-everyday-inputs/native/world/), as v5→v6 did. For quick,
     world, extensions: `cat-content-rail <r> --source <abs> --candidate-out
     <abs>/docs/reviews/<wave>/native/<r>/candidate.json`.
   - 4d The two reviewers write native/<r>/factual-review.json and quality-review.json covering every
     item (schema in review.go). Items the KG change did not touch are `inherited: true`, citing the
     previous record.
   - 4e Every rail command in 4c–4h passes `--source <absolute path of authored-v<K+1>.json>`; the
     `--write` and `--installed-authority-out` commands also repeat `--candidate C --factual-review F
     --quality-review Q`. Serially for quick, then world, then extensions: `--candidate C
     --factual-review F --quality-review Q --proposal P`; `--audit-catalog P --audit-out A`; the
     reviewers write final-factual/final-quality reviews bound to A; then `--proposal P --live-audit A
     --final-factual-review FF --final-quality-review FQ --expected-sha256 <sha256 of P> --write`.
     Write A as docs/reviews/<wave>/native/<r>/audit.json and FF/FQ as final-factual-review.json /
     final-quality-review.json in the same directory: these are the documents installed-authorities.json
     will bind in 4h. Installed-authority-entry drafts go under `~/work/_temp/content__v1-<N>-<theme>/rail/<r>/`.
   - 4f Pins: the derived_catalog_v38 and quick_games_v92 values in `reviewedPins`
     (go-backend/internal/contentbuild/build.go), `CATALOG_SHA256` in wordgames/quick_catalog.py and
     `DEFAULT_DERIVED_CATALOG_SHA256` in wordgames/derived_catalog.py. Then `cat-content export
     --root ..` and `export --root .. --check`.
   - 4g HTTP corpus: build `cat-server` into scratch; copy
     docs/reviews/go-native-toolchain/archived-reference/capture_reference.py.txt to scratch, changing
     only ROOT, the reference label and the output path; run it with the repo venv,
     `CAT_ACCOUNTS_ENABLED=0` and `--binary <cat-server> --runtime go` (expect 1207 matched responses).
     Move the .json.gz to go-backend/internal/httpgolden/testdata/ and, in golden.go, add only a
     renamed copy of the previous `reviewedV1x()` block, its SHA constant, embed line and ForSources
     entry.
   - 4h Bind the installed authorities. Per rail run `cat-content-rail <r> --source <abs> --candidate C
     --factual-review F --quality-review Q --proposal P --live-audit A --final-factual-review FF
     --final-quality-review FQ --expected-sha256 <sha256 of P> --installed-authority-out
     <scratch>/rail/<r>/entry.json` with the 4e documents; the command re-runs the native audit under
     the current binary and refuses with "final live audit incomplete/stale/unaccepted" if the installed
     behaviour no longer equals A (after 4f this happens only when the export changed what the
     quick/world replays observe). On that refusal only: rerun `--audit-catalog P --audit-out A`, have
     both reviewers re-sign FF and FQ to the new A, retry. Then assemble sources/installed-authorities.json
     (append authored-v<K+1> to source_chain; replace the three rail entries with the emitted drafts) and
     swap the sha in installed_authorities_pin.go via the metadata template (the file must equal
     PinBytesForInstalledAuthorities exactly). No second installed audit, no second reviewer round and
     no runtime freeze.
   - 4i Gates: `cat-content-rail all --check`, `cat-content validate`, `export --check`,
     `cat-content-ops check --check`, `cat-mobile-pack --check`, `go -C go-backend test -race -timeout 40m ./...`,
     `go -C go-backend vet ./...`, `go -C shared-go/authcore test -race ./...`, `cat-doc-check --root ..`,
     `git diff --check` — no new red versus step 0. Then play each new word once through a local
     cat-server API (a Cald sau Rece guess resolves; an alias shares its node's slot), keeping a log
     of at most 200 lines.
   Install may touch only: the module; the apply transaction files (both kg_sample.json, both
   games_pack.json, tests/fixtures/cat_mobile_app_pack_contract.json); board_rankings_v37 and
   derived_catalog_v38 (both fixture dirs); quick_games_v92, alchimie_discovery_world_v92 and
   alchimie_recipe_extensions_v92 (cat_de_roman_esti/fixtures only); bundled.json and digest.go via
   export; the pins in 4f; authored-v<K+1>.json, installed-authorities.json,
   installed_authorities_pin.go; the corpus and the golden.go block; the rail files under
   docs/reviews/<wave>/native/ (including audit.json, final-factual-review.json and
   final-quality-review.json under docs/reviews/<wave>/native/<r>/); Go or frontend testdata that an existing generator rewrites (name it
   in the README); count mirrors in tests/current_content.py; the pool, the wave README and
   docs/STATUS.md. Never new or edited `_test.go`, new Python tests, new repo scripts or
   rules_unicode15.json. On waking to a dirty worktree mid-step, reset the worktree only
   (`git -C <worktree> checkout -- . && git -C <worktree> clean -fd`; never in ~/work/cat_de_roman_esti) and redo the sub-step from its last commit.
5. Record and land. Pool records become integrated, held or rejected, each with one reason.
   docs/reviews/<wave>/ holds exactly the rail files installed-authorities.json binds (about 21 files,
   ~6 MiB, byte-exact, no -r2 copies) plus at most 10 small text files: README.md (≤80 lines of plain
   sentences), the graph proposal/review JSON, the playthrough log and reference/capture_v1_<N>.py.txt.
   No tarballs, raw logs, build outputs or failed-attempt packets; a failure is one README line.
   Update docs/STATUS.md counts and `Last verified`, replacing the previous wave's line; stay within
   the 120-line budget by appending the moved line to WORKLOG.md (append without reading it), never
   by removing spaces; then rerun `cat-doc-check --root ..` and `git diff --check`. No ADR unless game
   behaviour or a data schema changes. Landing: merge main into the wave branch; if the merge
   touched go-backend/** or shared-go/**, rerun 4i (the rail check re-audits under the merged binary)
   and redo 4g only if the merge changed go-backend/internal/httpapi or a content/game package,
   otherwise rerun validate, export --check and ops check; then `git -C ~/work/cat_de_roman_esti merge
   --ff-only content/v1-<N>-<theme>`. If main moved again, retry once, then set
   `waiting: main keeps moving — pause the GUI loop for one landing`. Run `cat-content-rail all
   --check` on main and record it. Never push. Then delete the wave branch, worktree and scratch.
   With LANDING_MODE=hold, stop after 4i and set `waiting: land?` instead.

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
  same-category, but it counts batch links, so it cannot catch an island. Give a closed set one honest parent (Anotimp, Punct cardinal, Crăciun) instead of
  wiring every member to every other. `label_ro` must read true from source to target. Lanț shows
  only relation captions (is_a, part_of, created_by, contemporary_of; others show "legătură
  directă"), so prefer an honest is_a or part_of.
- Never relax a validator limit, rubric floor or threshold, and never invent a link to make a puzzle pass.

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
2. V1.9 repairs: removing the false Toma Caragiu–Reconstituirea edge fits the writer (REMOVE_EDGES
   with the full prior record). Description diacritics ("roman"→"român"), the Herta Müller and Mica
   Unire 1859 labels and the Vioară/Zăpadă categories need an owner-approved writer; keep them held.
   Synonym: geamantan → Valiză once an owner exists.
3. V1.10 rounds: easy Conexiuni groups and Cald sau Rece targets on the V1.8 concepts through
   docs/PACK_ONLY_CONTENT_WAVES.md, plus repair of ineligible Conexiuni boards. games_pack.json is
   bound by the rails, so expect the same cascade; this path is untested.
Closed, do not research again: Compot, Sandviș, Mărțișor, Ouă roșii, Sarmale, Colind (concept), Poză (concept).

## Heartbeat prompt (paste into the automation)

```text
You run the Romanian content loop for ~/work/cat_de_roman_esti ("Cât de român ești").
Procedure: ~/work/cat_de_roman_esti/docs/CONTENT_LOOP.md on main. Read it at the start of a wave,
after any context compaction, and whenever `git -C ~/work/cat_de_roman_esti log -1 --format=%h --
docs/CONTENT_LOOP.md` differs from procedure_rev in ~/work/_temp/content-loop/state.json. It and
ADR-0188 override older content-loop ADRs, wave READMEs, TASK_BRIEF files and the retired
"Romanian content versions — V1.2 onward" heartbeat. V1.7 is parked; never resume it.
Every tick: follow the procedure's "Each tick" section. Do one sub-step, commit, update
state.json, and reply in at most three lines. If state.json says waiting, reply one line and stop.
Goal: more high-quality Romanian words players meet, verified on dexonline and a second source.
Progress is `cat-content-ops delta`; receipts, pins and tooling are not progress.
Never: GUI/frontend, toolchain, runtime logic, CI, deploy, push, PostgreSQL, retention policy, new
gates or admission/clock files, or edits to CONTENT_LOOP.md or ADR-0188. Report a broken
non-content gate as BLOCKED and do not fix it. Owner messages in this thread override the procedure.
LANDING_MODE=local   (local = merge to local main after green gates; hold = wait for "land")
```
