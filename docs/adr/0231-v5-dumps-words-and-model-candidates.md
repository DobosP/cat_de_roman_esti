# ADR-0231: V5 amendment — Wiktionary dump evidence, full paradigms, words lane, model candidates

Date: 2026-11-13
Status: accepted (Paul, 2026-11-13).
Decider: Paul Dobos.
Amends [ADR-0230](0230-content-loop-v5.md) decisions 1–7: the campaign and its meter, targets,
trains, word evidence (including the first-fetcher rule for dump evidence), sources, lanes and
tools. Every other ADR-0230 rule, gate, hold and boundary stands. Where the two differ, this ADR
governs from campaign `v5-pilot-2` on.

## Context

The V5 pilot `v5-pilot-1` started its clock 2026-11-13 12:27Z. By 14:05Z it had landed one forms
train with two forms (`usturoii`, `usturoilor`; `48c92469`, closeout `7e9105de`) and then went
idle. A read-only review of its records (`~/work/_temp/adhoc-content-sources-20261113/proposal.md`)
and three independent reviews of this ADR found:

1. **Forms die on look-alike collisions, not on evidence.** Of 13 word families tried, one landed.
   The factual judge accepted all nine it saw. Most of the others were dropped whole because one
   new form made the fuzzy answer matching resolve a different real word to them (`frunzos`,
   `cecurile`, `musturilor`, `piscaturilor`), because of an unnatural vocative, or because the
   word's own diminutive newly resolved to it (`ciocolățele`, `biscuițelor`). A reviewer's replay
   of the 14 cached tables with per-form drops found 14 clean non-vocative missing forms where 2
   landed.
2. **Existing words hold few of their forms.** The 1,164 single-word concepts carry 5,045 aliases,
   3,837 of them single words (about 3.3 per concept); `Biscuit` lacks `biscuitului` and
   `biscuiților`.
3. **The weekly forms train was spent at pilot hour 1.6**, so 60 forms could not be reached.
4. **New words cannot land**: the contract targets 0 words and 0 links, and the words-lane tools
   (link install, all-boards view diff) are not built. About 840 new-word candidates are queued and
   unproven, many parked for lack of an allowed source (for example Bucium, Toacă, Șezătoare).
5. **Page-by-page evidence caps growth** at 20 reads a day per Wikimedia host, while the same
   ro.wiktionary content is published as one official dump (26.9 MB, dated 2026-11-01, CC BY-SA 4.0
   and GFDL).
6. **The app's goal meter reads 0**, so the 40 M-token stop cannot fire. The root used about 300 M
   cached tokens against 42 M for all 22 jobs.
7. **A live contract cannot be amended**: `scripts/content_v5/resume.py` binds the owner-override
   ledger row to the exact contract bytes.

One research agent sent a single HEAD request (headers only) to dexonline's export URL to learn its
size. Nothing was downloaded; dexonline stays untouched (decision 12).

## Decision

1. **A new campaign.** `v5-pilot-1` closes as amended. At re-arm the loop, in order:
   - appends `campaign-stop {reason: "amended-by-adr-0231"}` to the old ledger;
   - moves `contract.json`, `ledger.jsonl` and `state.json` into `~/work/_temp/content__v5/v5-pilot-1/`;
   - merges local main into `content/v5`, then rereads `docs/CONTENT_LOOP.md` and this ADR;
   - writes the `v5-pilot-2` contract below, byte for byte except `base_sha`, which is the local
     main commit that carries this ADR;
   - appends the `owner-override` row, copying `owner`, `decision_date` and `quote` verbatim from the
     contract's `quota_override` (2026-11-13), with `previous_start_quota_pct_max` 90; Paul's re-arm
     message goes in the campaign README, not the ledger;
   - appends `campaign-start` with `goal_meter_tokens` = the meter value at re-arm (so pilot 1's
     tokens are not charged) and `kit_sha` = the `content/v5` commit after the merge. The 7-day
     clock starts there.
   A live campaign's contract is never edited again; an amendment closes it and starts the next.
   Whenever main gains a V5 amendment ADR, the loop merges local main into `content/v5` at the next
   turn start, before any dispatch, and rereads the procedure and the ADR.
2. **Token stop.** The value passed to `resume.py --goal-meter-tokens` is the cumulative uncached
   input plus output of the root and all jobs, summed from the ledgers of this campaign and its
   predecessors (the V4 goal-meter definition).
3. **Targets and counters.** 60 new forms on existing words, 12 new words, 48 new links, and 6 new
   boards in at least 2 games. An existing word is a concept in the `base_sha` bundle. A link counts
   only when at least one end is a new word; forms of new words and links between existing words are
   reported apart and count toward nothing. `report_content_delta.py` gains this split.
4. **Trains.** Board trains are unchanged. Forms and new words share a train. It opens when 20 forms
   or 6 new words are in the reviewed pool (S6), or after 96 hours with at least 1 reviewed item, or
   with at least 1 when quota reaches 70%, or near the end, when under 24 hours or under 4 M tokens
   remain (`resume.py` accepts no train events after its stop). It holds at most 100 forms and
   20 new words; its `train-open` kind is `forms`, or `mixed` when it carries a word. At most one
   train is open. The weekly forms train is withdrawn.
5. **Wiktionary dump as evidence.** `dumps.wikimedia.org` joins the approved hosts for the
   `rowiktionary` and `rowiki` dump files and their checksum files only.
   - One sequential GET per file, 10 s spacing, the procedure's User-Agent; each file and each
     checksum file is one read against the host's 20-a-day cap; at most one download per file and
     dump date. The file is checked against Wikimedia's published checksum and pinned by SHA-256 in a
     receipt. The ADR-0230 robots, terms and AI-crawler rules apply to the host.
   - The evidence for a form or an entry is the page's raw wikitext revision inside the verified
     file (page title, revision id, byte hash). Instead of a URL, each reviewer recomputes the file's
     SHA-256, extracts the page's raw text without the table parser and transcribes the table cells
     without seeing the proposed list; a script diffs each transcription against the proposal, and a
     difference the reviewer cannot resolve drops that form. The script-fetched file receipt meets
     the first-fetcher rule. One family in ten also gets a live ro.wiktionary spot check within the
     cap.
   - **Parser gate before first use.** For each of the 14 pages cached live in V5 whose cached
     revision equals the dump's, the parser's set of (cell label, form) pairs equals the set read from
     the rendered live table; a page whose revision differs is replaced by another sample page. Ten
     more live pages are checked the same way, at least 2 each of adjectives, invariable nouns,
     plural-only nouns and nouns with two plurals. Verbs need their own 10-page verb sample. Any
     mismatch blocks the dump route until the parser is fixed; a rerun reuses cached pages and makes
     no new reads.
   - The ro.wikipedia title and redirect lists are a pre-filter only. The article check for a new
     word stays a live ro.wikipedia read within the cap.
   - Until the dump route passes its gate, forms continue with live table reads, the existing form
     screen and the landing reviewer's manual probing.
6. **Full paradigms, per-form drops.** The forms lane aims to give every existing word every form in
   its own ro.wiktionary table that the game lacks: nouns and adjectives first, verbs after the verb
   sample passes. Vocatives only for nouns that name people or animals.
   - Forms come only from the table. Neither grammar rules nor a model creates a form; a rule check
     may only flag an odd cell for the reviewers.
   - A form that changes how a different word resolves, or that a reviewer finds unnatural, is
     dropped by itself and the rest of the family continues. A family drops whole only when its lemma
     itself collides, its table is doubtful, or the reviewers reject the family. After any drop the
     resolver diff reruns on the kept set.
   - A change that only removes an existing wrong resolution (for example `cercurile` no longer
     resolving to Cer) may be cleared by the landing reviewer.
   - No diminutive forms are authored. A family is not dropped when the only resolver change is that
     the word's own diminutive newly resolves to it, confirmed by both reviewers and the landing
     reviewer as a diminutive of the same lemma, citing the diminutive's own ro.wiktionary entry
     where one exists.
7. **Collision screen and profanity probes.** Before authoring, a script lists every real Romanian
   form near each proposed key (from the verified dump, or from live reads until the dump route
   passes) plus the profanity probe list, and feeds them to `resolver_diff.py --probes`. The list is
   a tracked file committed with the probe builder, seeded from the vulgar stems in the cached
   FrequencyWords list plus a reviewed supplement, with diacritics folded and its hash pinned in the
   train receipt; the loop reports it to Paul once and does not wait. A form whose normalised key
   equals a probe, or that makes any probe newly resolve to any word, exactly or fuzzily, is dropped,
   and no reviewer may clear it.
8. **Words lane.** The goal builds the link install, the all-boards view diff and the link span
   checker; ADR-0230 decision 6 already opens the lane when they land. The queued backlog goes first.
   - **Dry run.** Before the first words train, the view diff runs on the first S2-sourced backlog
     word in registry order, installed into a throwaway candidate that is never reviewed or landed.
     A Cald board counts as disturbed when its target's top 100 changes; a Lanț board when its
     shortest route changes. If one word disturbs more than 10 boards in all games together, the
     words lane waits and the loop asks Paul once. In a words train every disturbed board is
     re-blinded and replayed (S7).
   - **Evidence** is unchanged: a Romanian section in ro.wiktionary (from the dump), a live
     ro.wikipedia article, positive frequency, and 4–8 links each stated by an approved source. Each
     link cites a short quoted span that the span checker finds in the cached receipt of the source
     it cites.
   - **Child safety, for every new word whatever its origin.** The deny-list and owner holds apply;
     no person names in the W or G lanes; an entry whose ro.wiktionary section carries the label
     vulgar, argou, peiorativ, depreciativ or trivial is dropped. Funeral and folk-magic words (for
     example pomană, parastas, strigoi, descântec), alcohol, tobacco, slaughter, ethnic or religious
     group terms and insults go to Paul's queue in one batch per train (rubric A5); other lanes keep
     running. Both reviewers still sign `child_safe`.
9. **Model-proposed candidates (G lane).** The lane opens when every backlog row in state `idea` has
   passed S1 and the dump Wiktionary check (survived or parked); the live article read is not needed
   for it to open.
   - Sweeps run one cultural cell at a time (customs, folk dress, instruments, fairy tales, crafts,
     village life, food, school, play, nature), three fresh threads per cell, 10 items per thread.
     Generator threads use author slots; a cell's threads may run in sequence, and generator
     threads never take both author slots while authored items wait. Each item gives a lemma, part of speech, a one-line sense,
     its cell and 4–8 typed link proposals using the graph's relation names, each with a one-line
     reason.
   - **Model output is never evidence.** A `sourced` transition needs a source-client or dump
     receipt hash. Candidates are recorded with origin `model`. Reviewers and the blind critic never
     see generator reasons, agreement counts or scores. A generator thread never authors, judges or
     critiques its own proposals.
   - Agreement between the three threads only ranks items. Script-clean means it passes S1 and is not
     already in the registry; a cell with fewer than 10 script-clean candidates per 100 proposed cools
     down. Yield is compared with the 335 backlog rows in state `idea` that are not yet in the game.
   - Generator senses never ship. Any text shown in the game is written fresh and checked for overlap
     with source text.
   - Prompts and docs describe this as proposing candidate words. The output is never collected from
     the app by scripts and never used to train a model.
10. **Licence.** Forms and word existence are treated as language facts and may ship as answer forms.
    Before the first train that carries dump-derived content, the repo credits ro.wiktionary
    contributors (CC BY-SA 4.0, dump date, URL) in a tracked credits file, and a future app credits
    page repeats it. No source sentence ships.
11. **Tools named here.** Each may be built inside the campaign as its own commit with a threat
    model, tests, a portable build and a fresh-context review:
    - the source client's dump route (dump and checksum files for `rowiktionary` and `rowiki` only,
      streamed to disk under its own size limit, checksum verified, SHA-256 receipt), the one
      source-policy change this ADR permits;
    - the dump reader and table parser;
    - the collision probe builder with the profanity probe list;
    - the counter split in `report_content_delta.py`;
    - the registry check's requirement of a receipt hash for `sourced`, the one validator change this
      ADR permits;
    - the link install, the all-boards view diff and the link span checker.
    Other tool work stays repair only.
12. **dexonline** stays untouched, as ADR-0230 decided.

### The `v5-pilot-2` contract

```json
{
  "campaign": "v5-pilot-2",
  "base_sha": "<the local main commit that carries ADR-0231>",
  "ends": {"days": 7, "goal_meter_tokens": 40000000,
           "goal_meter": "ledger uncached_in + out of root and jobs",
           "clock_starts": "campaign-start at re-arm"},
  "targets": {"forms": 60, "forms_scope": "existing words in the base_sha bundle",
              "boards": {"total": 6, "min_games": 2}, "words": 12, "names": 0,
              "links": 48, "links_scope": "at least one new-word end"},
  "counters_rank_queue": true,
  "cooldown": {"empty_batches": 2, "same_reason_hits": 3},
  "train": {"max_open": 1, "assemble_at": 6, "assemble_after_h": 96, "min_after_h": 3,
            "max_boards": 20,
            "forms_words": {"assemble_at_forms": 20, "assemble_at_words": 6, "after_h": 96,
                            "min_items": 1, "flush_at_quota_pct": 70,
                            "flush_when_left": {"hours": 24, "tokens": 4000000},
                            "max_forms": 100, "max_words": 20}},
  "sources": {"hosts": ["ro.wikipedia.org", "ro.wiktionary.org", "www.wikidata.org",
                        "raw.githubusercontent.com", "localhost:8077", "dumps.wikimedia.org"],
              "dump_scope": ["rowiktionary", "rowiki"],
              "daily_cap_per_wikimedia_host": 20, "robots_scope": "path", "ask_on_collision": true},
  "diminutives": {"author": false, "clear_own_confirmed_resolving": true},
  "dry_run": {"cald": "target top 100 changes", "lant": "shortest route changes", "max_boards": 10},
  "generator": {"opens": "after backlog idea rows pass S1 and the dump check",
                "threads_per_cell": 3, "items_per_thread": 10,
                "cooldown_min_clean_per_100": 10},
  "alchimie_world_max_concepts": 256,
  "tool_repair_cap": {"hours_per_item": 4, "share_of_job_tokens": 0.15, "attempts": 2},
  "threads": {"max": 6},
  "start_quota_pct_max": 90,
  "quota_override": {"by": "Paul", "date": "2026-11-13",
                     "quote": "i change the logic i am allowing it with to start till 90% is used",
                     "start_limit_exclusive": true, "stop_at_pct": 90,
                     "restrict_new_intake_at_pct": 70, "paid_credits": false},
  "reuse": "shadow"
}
```

## Consequences

- Forms throughput depends on the collision screen, not on reads; per-form drops keep a family's
  safe forms instead of losing all of them.
- Words land only after the dry run shows their board cost, so a words train cannot silently
  re-blind most boards.
- The backlog is used before any model sweep; if it proves culturally weak, the G lane becomes the
  main source.
- The pilot restarts its 7-day clock at re-arm; `v5-pilot-1`'s records stay in its archive folder.

## Rollback

Stop the G and W lanes and the dump route; the dump files live only in `_temp`. Landed content is
removed only by a local revert commit through the full gates. A later ADR supersedes this one.

## Owner log

Paul, 2026-11-13, Claude Code session `2c6bf228`. His messages, then his selected answers, verbatim
except one term he asked to keep out of prompts, shown as [word omitted]:

```text
this loop is not good enough i think different sources onlyne are needed or some new techniques to search for words with strong usage in romanian culture and concepts, i am considering asking the model to generate them similar as [word omitted at Paul's request] the information from the chatgpt model like the words he knows in romania and how they are linked and use internet for validation

Dumps: Yes, as evidence (Recommended)
New words: Backlog, then model (Recommended)
Cadence: When enough qualify (Recommended)
dexonline: Leave untouched
Diminutives: Allow same-word ones (Recommended)
Landing: I write it, you pause (Recommended)

And it may be that Codex has anti-[word omitted] rules, so don't use the [word omitted] word exactly in the prompt. Then the language different words of the same different forms of the same word. For example, biscuite and biscuit. Silor, biscuite. Like I should have these forms for every word, or is any way to grammatically find this? I know that Romania has a lot of exceptions, so I think just having all of the forms, it could be possible. There are not so many words in total.

Campaign: New campaign, fresh clock (Recommended)
Token stop: Uncached in + output (Recommended)
Dry run: Top 100 or route (Recommended)
Credit: Ship, credit in repo (Recommended)
Leftovers: Flush at 96 h or end (Recommended)
Sensitive: Your queue, one batch (Recommended)
```

The question and option texts are kept in
`~/work/_temp/adhoc-content-sources-20261113/owner-answers.md`. Decision 6's full-paradigm aim and
per-form drops follow Paul's message about having all the forms. These numbers were set by the
author from the reviews rather than by a question to Paul: 10 items per generator thread, the
10-per-100 cool-down, 20 words per train, the 10-page live and verb samples, the one-in-ten spot
check, the five Wiktionary labels, and the end flush at 24 hours or 4 M tokens left. The author also
added, from the reviews: the predecessor-ledger sum in decision 2, the ro.wikipedia title lists in
decision 5, the vocative limit and the reviewers' confirmation of diminutives in decision 6, the
profanity rules in decision 7, and generator threads using author slots.
