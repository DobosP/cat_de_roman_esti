# Content loop V4

[ADR-0226](adr/0226-content-loop-v4.md) records Paul's decisions.
[STATUS](STATUS.md) records what shipped. [CRITIQUE_RUBRIC](CRITIQUE_RUBRIC.md) sets the quality bar.

## Output and execution

Codex runs the loop in the current chat until Paul stops it. Use one local `content/v4` branch
and worktree at `~/work/_worktrees/cat_de_roman_esti/content__v4`, with scratch, cache and
evidence at `~/work/_temp/content__v4/`. V3 stays archived under ADR-0225. Use the verified seed
copy for migration. Keep the loop checkout through landings and preserve other owners' work.

The output is player-visible Romanian content for the six games. Report actual added words,
names and boards by game, with examples, then up to nine plain lines. Use
`scripts/report_content_delta.py --baseline <ref>` and include per-game exposure separately
where needed. Report only landings, qualified cohorts and owner decisions. Batch owner
questions with options and a recommendation, and continue independent work.

## Registry and queues

Use `docs/content-registry/registry.jsonl` (`cat-content-candidate-1`). The orchestrator is its
single writer. Append transitions and derive the current view. Jobs return proposed changes.
Record id, type, lane, class, state, Romanian label, identity/sense, payload, provenance
(URL/path, digest, first-fetch role, time), checks, exact review bindings, critic log,
holds, player benefit, origin, dependencies, co-landing group and retry predicate as applicable.

The main path is idea → screened → sourced → authored → reviewed → qualified → landed.
Other states are rejected, duplicate, already_served, parked(prerequisite), held_recorded,
held_owner and retracted(reason). Keep recorded exclusions traceable to file and line.
Re-screen them only when their retry predicate fires. Only Paul's own quoted ruling changes
an owner hold. Refuse partial co-landing groups and missing dependencies.

Seed from landed exclusion constants, pools, stock, V3 intake and dispositions, tombstones,
demotions, reserves and ADR-0210. Reconcile input and output counts. Legacy captures stay
labelled legacy. Keep `exclusions.json` and the owner, drawing-board, landing and lessons logs
alongside the registry. Keep the operational ledger append-only and scratch `state.json`
below 2,048 bytes with the run id, approved hashes, ranking version, active jobs, breaker
table, stop flag and last landing SHA. Recompute the need map when ranking changes.

## Lanes in cycle order

Large intake, per-item decisions, no yield quotas. The first content milestone uses class P
boards on existing nodes (L1 and L4). Park lanes whose prerequisites are missing and keep going.

| Lane | Work and floor |
|---|---|
| L1 | New Conexiuni replacement boards in the cells of the 83 approved-but-ineligible predecessors. Use the current lint baseline. Each shares fewer than eight tiles and no three-of-four quad with the predecessor or another inventory/tombstone board. Keep predecessors in place and the 79 owner-held boards untouched. Measure the first 30 cells before forecasting yield. |
| L4 | Boards from need on existing nodes for Conexiuni, Cald sau Rece, Lanțul Cuvintelor and Alchimie target rounds. Intrusul and Perechi require the I/J rubric binding, generalized game mapping and `install quick`. Alchimie world/extension work requires a separate scope ruling and install verb. |
| L3 | Names and everyday concepts. Concepts need 4–8 truthful edges, at least two to existing main nodes and two within the same category. Names follow the child-safety rule below. |
| L5 | Edges for low-degree nodes and truthful Lanț captions. Verify each relation and re-play touched boards. |
| L2 | Re-screen historical stock with current exclusions, fresh own-head C2 evidence and exact authored-byte verification. |
| L6 | Synonyms in one selected sense, with DEX agreement on both heads, a second source and a substitution test. |
| L7 | Forms on existing owners with own-head DEX/DOOM3 attribution and an alias playthrough. |

Names, concepts, edges, synonyms and forms are class G. Source-backed lanes require the
source controls below, and class G landing requires the full graph install and pin cascade.
Keep bare *sucitoare* excluded, keep *ii*/*iei* off Ie, and hold Mănăstire/Sucitor rows
until Paul explicitly authorizes them. Keep the ADR-0210 held families. Minors are never
name entries. Put living persons in the owner queue. Prefer content a Romanian 12-year-old
would recognize.

## Roles and gates

Codex dispatches separate fresh author, blind gameplay critic, factual reviewer, quality
reviewer and landing reviewer subagents using `fork_turns=none` and distinct task names.
Give each a role-specific brief and inputs. Never show reviewers the peer verdict before
both sign. The landing reviewer neither authors nor judges any item in that cohort.
Keep the critic's input answer-stripped and the private key separate. Limit dispatch to at
most six jobs, 3 h and 25 M tokens per slice, subject to the chat's smaller concurrency cap.
A headless driver needs a separate owner-accepted agent-ops ADR and approved profiles.

**Per item**
1. Screen against the resolver, registry, exclusions and full inventory. Check owner identity,
   collisions, fuzzy neighbours, Cald inbound floor and co-landing. Use the miner helpers
   until the native screen/need/mine verbs exist.
2. Close sources as applicable. Own-head DEX/DOOM3 for forms, DEX/DOOM3 plus a second Romanian
   source and positive-only frequency for concepts, two Romanian sources for names and a source
   stating each edge. Boards need truthful predicates and gameplay floors.
3. Run `critique_pack.py --strict` joined to `cat-content-ops critique` or
   `cat-content validate-pack` as applicable. Screen rejected/tombstoned items on resubmission.

**Per cohort**
4. Run the blind gameplay critic for every new or touched board. For Lanț, give the
   critic native prospective captions. For Cald, apply the ADR-0213 eight-guess protocol.
   Keep the ADR-0210 exemption for standalone forms on existing owners. A critic fail drops
   the item even if reviewers promote it.
5. Obtain independent factual and quality judgments for each new or changed item. Require
   two accepts, `child_safe` per item and each judgment bound to the exact payload. For
   source-backed claims, each reviewer chooses at least one URL whose first fetcher was
   neither author nor legacy. Hide author URLs and entries until both sign. For KG-only boards
   reviewers independently check predicates against the game data. Check cited-URL novelty,
   reviewer-name leakage and over 20% identical rationales. Verify staged bytes equal frozen bytes.
6. Pre-check importer entry points, schemas and output paths. Apply class P through
   `cat-content-ops import-candidates --pack-only` with the existing pending, dossier, raw
   review, strict promotion and final audit rail. Use the existing reviewed graph transaction
   for class G until `install apply` exists. Keep generated input modules in scratch. Run rank,
   derive, `cat-content validate`, `export --check`, ops `check --check` and mobile check.
   Use the generators for fixtures and static assets.
7. Refresh all changed rail bindings under ADR-0189 and ADR-0212. A pack change can invalidate the
   world audit even with identical world payload. Run fresh required audits/finals and
   `cat-content-rail all --check`. Class G also regenerates the full authored snapshot and
   affected pins including Cald inbound expectations. The original 4a–4i mechanics are
   recorded in ADR-0220 and the V3 procedure at commit `1e3a04eb`.
8. Apply ADR-0186 to the source-bound HTTP corpus. Capture/replay with the asserted reviewed
   case count (1,206 at V4 start). A changed count is NEEDS-OWNER with a case-list diff.
   Self-capture is not independent expected evidence. Put moved pin expectations in a separate
   commit with an old-to-new list. [ADR-0227](adr/0227-owner-qualified-test-pin-delegation.md) delegates
   future separate test-expectation commits only after independent-oracle regeneration, every
   existing exact-SHA gate and a fresh independent landing review. Count changes still need Paul.

**Per landing**
9. Queue qualified items, with frozen bytes, two reviews, critic evidence, install and gate
   results. The fresh landing reviewer checks the go/drop table, player diff, fuzzy-neighbour
   shift and corpus/pins. Review every flagged, L1, name and synonym item and a stated sample
   of the rest. Run the pinned build and 4i on the exact candidate SHA with generated SPA assets:
   rails, validate, export, ops, mobile, full Go race suite, vet, authcore race, doc inventory
   and whitespace. No pre-existing missing-assets waiver. Play every new board to a verified
   result and every new alias through local HTTP, checking direct owner, repeat and wins where
   applicable. If boards, edges, captions or e2e ids change, also run both exact-SHA GUI gates:
   `GATE_OPERATOR=agent:codex bash scripts/gate.sh unit --sha <SHA> --parallel 4` and
   `env -u GATE_OPERATOR python3 -I scripts/gui-full-runner.py --sha <SHA> --parallel 4`.
10. Update STATUS in the series. From the clean shared `main` checkout, Codex runs
    `git merge --ff-only <reviewed SHA>` after every gate passes. If main moved, merge it into
    `content/v4`, reconcile STATUS and inventory, and rerun gates and review on the new SHA.
    Local Git only. Keep the loop branch and remove only owned review worktrees. Keep compact,
    reproducible manifests and text-first evidence. Verify retained receipts before pruning
    owned bulky outputs. Keep cohort evidence at or below 50 MB with a README up to 30 lines.

## Source controls

The only research network path is the cache-first source client. Before it exists, use existing
receipts and KG-backed boards. The allowlist is `dexonline.ro`, `ro.wikipedia.org`,
`ro.wiktionary.org`, `raw.githubusercontent.com` (FrequencyWords only) and
`localhost:8077` (the local ro_data_server). Remote requests are read-only HTTPS GETs.
Send `cat-de-roman-esti-content-research/4 (+https://github.com/DobosP/cat_de_roman_esti)`.
Space requests by host by at least 2 seconds, or 10 seconds for Wikimedia. Cache every
response and reuse it. Record exact URLs, body SHA, time and first-fetch role. Do not
let redirects add hosts. Only cite receipt metadata and a brief paraphrase in tracked docs.
dexonline legacy captures and new GETs are allowed with these controls.

Obey robots and terms, including crawler directives, `Content-Signal` and stricter crawl
delay. A 429 or 5xx parks the host for one hour (or longer if Retry-After requires it).
A policy refusal drops that host for the run and adds one owner queue entry. Keep working on
other sources and lanes. The host grant is standing. Future source-client configuration,
templates and profiles use approved byte hashes. Owner authority comes from Paul's own message,
quoted in the ADR. Jobs cannot change the procedure, rubric, ADRs, AGENTS, validators, pins,
source policy or hold fixtures.

## Recovery and tool changes

Retry a tool error three times with backoff, then park the affected item. An integrity
failure sends the item to the drawing board with its reason and retry predicate. Continue the
cohort. Recheck predicates at dispatch. Record a denied capability or required owner decision
in the owner queue while other lanes proceed. Report-only Docker preflight checks disk,
network and pinned image; leave host configuration and Docker service alone.

Each tool change is its own commit with a threat model, focused tests, a portable build
(Go on linux/darwin/windows), and a fresh-context code review by someone who did not write it.
The landing kit includes preflight, pinned build, parameterized 4i, content/fuzzy diff and
HTTP play tools. Keep bulky output in scratch and keep compact verification records.
