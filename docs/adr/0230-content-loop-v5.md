# ADR-0230: Content loop V5 — counted goal, trains, words first

Date: 2026-11-13
Status: accepted (Paul, 2026-11-13).
Decider: Paul Dobos.
Supersedes in part [ADR-0226](0226-content-loop-v4.md). Keeps [ADR-0227](0227-owner-qualified-test-pin-delegation.md)
and [ADR-0228](0228-policy-only-source-hosts.md). Accepts [ADR-0229](0229-native-quick-review-and-rubric-requalification.md)'s
contract for the Quick install path, to be reviewed once its real cost is measured.

## Context

V4 ran 2026-11-08 to 2026-11-12 (`1e3a04eb..0fda2bad`). It landed 19 boards: 12 Conexiuni,
2 Cald sau Rece and 5 Lanț. It added no shared words, names, links or forms. Its gates caught
real defects: second groupings, unsolvable Cald targets, a generic Lanț caption hiding a hop,
a sense mismatch and false resolver wins. Its costs were elsewhere:

1. A full qualification for every one or two boards. That was 14 cascades, each re-signing
   738 unchanged side-catalog items per reviewer.
2. Every word lane closed in the first hour. The loop dropped dexonline over its site notice,
   and the procedure required dexonline evidence for every word and form. The loop never asked Paul.
3. The goal had no number in it, so turns at "+0 words" counted as progress. The loop slept
   about 21 hours on 2026-11-09 waiting for an approval, and it had no per-job cost data.

The audit is in `~/work/_temp/adhoc-content-loop-v5-20261112/v5-proposal/01-v4-retrospective.md`.

## Decision

1. **Counted goal.** Codex keeps running the loop as a Codex goal. Each campaign names a
   contract with targets, a token budget and stop rules. Progress counts only through
   `scripts/report_content_delta.py --baseline <campaign base>`. A turn that raises no counter
   and unblocks no named queued item is no progress. Counters also rank the work queue by
   measured pass rate. A lane that keeps failing cools down until a recorded input changes.
   Targets never lower a gate. A campaign stops and reports at its end; Paul re-arms it with
   one message.
2. **Pilot campaign.** Phase 0 tools first, then 7 days or 40 M goal-meter tokens. Targets:
   60 new forms, and 6 new boards in at least 2 games. Every report's first line shows new
   words, forms, names and links separately.
3. **Trains.** Items are judged one by one into a pool. A board train assembles at 6 qualified
   items, or after 96 hours with at least 3, and holds at most 20 boards. One forms train a
   week holds at most 100 forms. Each train gets one install, one qualification, one reference
   capture, one pin commit, one exact-commit gate run and one landing review. At most one train
   is open. A judged item keeps its blind play and two judgments when another train lands first,
   while its payload hash and what the player meets are unchanged.
4. **Evidence for words.** A form on an existing word needs that word's own ro.wiktionary
   inflection table. Both reviewers read it and judge the word family. A new word needs a
   ro.wiktionary entry, a ro.wikipedia article and positive frequency. Diminutives are
   excluded in the pilot. dexonline is left untouched: no reads, and its legacy captures keep their
   labels but are not evidence for new words or forms. A synonym needs both words to share the
   selected sense in ro.wiktionary, a second Romanian source and a substitution test.
5. **Sources.** This is Paul's approved source list; a new host still needs him. The content
   hosts are `ro.wikipedia.org`, `ro.wiktionary.org`, `www.wikidata.org` (the bare `wikidata.org`
   redirects there),
   `raw.githubusercontent.com` (FrequencyWords only) and `localhost:8077`. Each Wikimedia host
   gets at most 20 new reads a day.
   - A robots `Disallow` drops only the disallowed path.
   - A terms page, `Content-Signal` or AI-crawler block drops the host for the run.
   - When two of Paul's own rules collide, the loop records it, keeps other lanes running and
     may ask Paul once.
   The plain cache-first client is enough; no operating-system role isolation is required.
6. **Lanes.** All lanes are open:
   - boards in Conexiuni, Lanț and Cald sau Rece;
   - Quick: Perechi first, with Intrusul authored in the pilot too;
   - Alchimie target rounds from existing words, with new recipe links where needed, keeping
     the 256-concept world limit;
   - forms and new words;
   - names, with ro.wikipedia plus Wikidata as sources, once the rubric has a Names section.
     Codex writes that section as its own commit and a fresh reviewer checks it;
   - edges, plus a ten-caption Lanț trial;
   - synonyms and historical-stock rescreening.
   A lane whose tool is missing waits for that tool.
7. **Tools.** Codex builds them inside the goal.
   - The core kit lands before the pilot clock starts.
   - The extra lanes open as their own tools land.
   - Each tool is its own commit with tests, a portable build and a fresh-context review.
   - Otherwise, tool work during a campaign is repair only.
8. **Catalog reuse later.** Whether a board train may skip re-reviewing untouched side-catalogs
   is decided after the pilot. Until then any impact tool runs in shadow and decides nothing.
9. **Evidence location and close-out.** Nothing goes under `/tmp`. A landing is complete when
   one receipt-only docs commit has written the registry rows and `landing.json`, and STATUS and
   the landing queue point to them.
10. **V4 leftovers.** After a byte-verified NAS archive, delete:
    - the `/tmp` originals;
    - the bulky rebuildable parts of `_temp/content__v4`, keeping the verified evidence copy and the
      inputs V5 needs;
    - the detached Codex review worktree;
    - the eight empty review folders.
    Registry and receipt paths under `/tmp/<name>` that were salvaged resolve to
    `~/work/_temp/content__v4/tmp-evidence/<name>`, whose files are byte-identical. Its `SHA256SUMS`
    and `VERIFY.json` list what was copied and what was already gone (for example
    `cat-v4-c19-lant-author`).

## Kept from ADR-0226 and earlier

- Owner holds:
  - no bare *sucitoare*;
  - Ie never gets *ii*/*iei*;
  - Mănăstire and Sucitor rows only on Paul's explicit go;
  - the 79 held Conexiuni boards stay held;
  - the 87 owner-held registry rows stay held.
- Minors are never name entries. Living persons go to Paul's queue.
- Two independent judgments with `child_safe` per new item.
- The first-fetcher rule for reviewer sources.
- Fresh blind play for every new or touched board; a critic fail drops the item.
- Exact-commit gates: the pinned build, 4i with the full Go race suite, and GUI gates when
  boards, edges, captions or e2e ids change.
- Never land red. Local-only fast-forward; no push, no pull request, no deploy.
- Never restart Docker or change host configuration.
- Generators for fixtures; no hand edits. ADRs append-only.
- The loop never changes runtime gameplay code such as the resolver.
- Errors never stop the loop: a failed item goes to the drawing board and a tool error parks it.
- The ADR-0210 held families stay held.
- A headless driver needs a separate owner-accepted agent-ops ADR.
- Message Paul only when something lands, a train qualifies, a lane is blocked or a decision is
  his. Batch questions into one message with options and a recommendation.

ADR-0226's "keep it running until I stop it", "no quotas", fixed lane order, dexonline grant,
whole-host refusal rule and "never ask me again" are replaced by decisions 1, 4, 5 and 6 above.

## Consequences

- The fixed cost of qualification is shared by every item in a train. Ranking positions still
  move, once per train.
- Forms can land in the first week. New words need the link install and the all-boards view
  check first.
- If the 20-reads-a-day cap or Wiktionary coverage starves a word lane, the pilot reports it
  as blocked in its first line.

## Rollback

Stop the goal. `docs/CONTENT_LOOP.md` at `163578f8` (V4) remains a valid fallback procedure.
Tools live on their own commits. Landed content is removed only by a local revert commit
through the full gates.

## Owner log

Paul, 2026-11-13, Claude Code session `2c6bf228` (instruction, then his selected answers, verbatim):

```text
Learn to main and ask any decision that you have to me now interactively.

Word evidence: Wiktionary tables (Recommended)
Sources: Path-level, ask once (Recommended)
Goal: Counted, ranks work (Recommended)
Open lanes: Perechi first (Recommended),Intrusul too,Alchimie recipe lane,Names and Lanț captions
Tool builder: Codex, inside the goal (Recommended)
Batch size: 6+ boards, weekly forms (Recommended)
Alchimie: Rounds first, keep cap (Recommended)
Name sources: Wikidata (Recommended)
Skip reviews: Decide after the pilot (Recommended)
V4 cleanup: Archive to NAS, then delete (Recommended)
Source list: ADR-0230 is the list (Recommended)
Names rubric: Codex + fresh review (Recommended)
Synonyms: Wiktionary + second source (Recommended)
```

The full question and option texts are kept with the proposal, in `10-owner-answers-20261113.md`.
Earlier, on 2026-11-12, Paul wrote: "i like the goal looping work design but just inprove it", and
"Yes, do both", which approved the `/tmp` evidence salvage and the C44 record (`163578f8`).
