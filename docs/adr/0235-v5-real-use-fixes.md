# ADR-0235: V5 real-use fixes — one disturbed definition, paired re-blind, full frequency list, pilot 3

Date: 2026-11-16
Status: accepted (Paul, 2026-11-16).
Decider: Paul Dobos.
Amends [ADR-0230](0230-content-loop-v5.md) and [ADR-0231](0231-v5-dumps-words-and-model-candidates.md).
Every other rule, gate, hold and boundary of both stands. Where they differ, this ADR governs from
campaign `v5-pilot-3` on.

## Context

Campaign `v5-pilot-2` ran 2026-11-13 21:17Z to 2026-11-14 06:48Z, then marked its goal blocked and
did not resume. It landed 7 forms (Robinet 2, Pătrunjel 5) and no words, links or boards. It also
reached, without landing: 5 reviewed new words with 20 sourced links (Sparanghel, Oază, Cactus,
Trăsnet, Dig), 12 frozen forms awaiting judgments plus 14 kept dump forms never authored, and 3
reviewed boards (Baschet, Laborator, Orez → Varză). Weekly quota went from 50% to 81%; about a
third of the usage in that window came from other ChatGPT sessions. A read-only review of the root
session and the records (`~/work/_temp/adhoc-content-loop-v5-real-use-20261116/proposal.md`)
found, in order of cost:

1. **The words gate could not be passed.** `cat-board-view-diff` counted a Cald board as disturbed
   in S7 when anything in its view changed, including the reachable-word count, but in the dry run
   only its top-100 ids. One new word changes the reachable count on every Cald board, so
   Sparanghel disturbed all 257 Cald boards in S7 and 3 in the dry run. `close_landing.py` then
   required a blind-critic win on each, and the blind critic wins existing Cald boards about 2 times
   in 18, unchanged or not.
2. **The frequency check parked real words.** The word screen used the 50,000-word FrequencyWords
   list with exact comma-diacritic matching. Of 291 single-word backlog labels, 135 got no
   frequency (for example Olar, Nuc, Zimbru, Arțar, Șopârlă, Păpădie). With the full list and
   cedilla/comma folding, 288 have a positive count.
3. **Root overhead.** The pilot-1 chat was continued, so context was 588k at re-arm. The root made
   3,137 calls at a median 422k context (65% of all cached tokens), spent about a quarter of its
   input polling running gates, and posted 20 full reports, 11 of them in the last 42 empty minutes.
4. **The quota band.** Intake closed at 70%, and the loop then also refused judgments for frozen
   forms while it ran board rehearsals.
5. **Boards.** The three reviewed boards waited for a 96-hour timer, and a forms landing voided two
   of their judgments because the loop bound them to a whole-bundle digest instead of the board's
   own view.
6. **A Lanț near-duplicate was found late.** Transilvania → Munții Apuseni reproduced a branch of
   the served `lt_geografie_239` and was caught only at quality review, after four jobs.

## Decision

1. **One definition of disturbed.** A Cald board is disturbed when its target or the set or order
   of its top-100 words changes. A Lanț board is disturbed when its endpoints, declared optimal,
   shortest distance or shortest-route topology changes. For Cald and Lanț, every other part of a
   board's view (top-100 scores, reachable count, target display, route captions, labels and menus)
   is a diagnostic; category, category label and difficulty still count for every game, and the
   other games keep their current parts. Dry run, S7 and closeout use this same definition (`cat-board-view-diff` schema
   `cat-board-view-diff-2`). Every board whose full view changed, disturbed or diagnostic only, is
   still played over local HTTP; only disturbed boards are blind-played again. Closeness and
   temperature shifts, inside or beyond the top 100 while its set and order hold, therefore change
   without a re-blind.
2. **Paired no-worse re-blind for existing Cald boards.** For each disturbed existing Cald board the
   blind critic plays the candidate, and `cat-board-view-diff --reblind-compare` replays the same
   guesses on the baseline and the candidate. The verdict is win when the candidate is won; worse
   when the same guesses win the baseline but not the candidate; no-worse when the candidate's best
   rank is at most the baseline's best rank plus the number of new concepts ranked above it; worse
   otherwise. A worse board refuses the landing. Both judges (factual and quality, neither the author
   nor a critic) sign every disturbed existing Cald board's top-100 change. A no-worse board that
   neither build wins is flagged `stock_quality` in the landing receipt and listed for Paul; the
   flag itself does not block.
   New boards keep the absolute win rule, and Lanț and the other games keep their current rules.
   ADR-0231 decision 8's "every disturbed board is re-blinded and replayed" reads under this
   decision.
3. **Quota band.** Intake means S1–S3 (screening, sourcing, authoring and freezing). Between 70% and
   90% of the weekly meter no new item enters S1–S3, but frozen items may finish S4–S10 (blind play,
   both judgments, train, gates and landing). At 90% the campaign stops as before. `resume.py`'s
   `finish-judged-only` mode means exactly this.
4. **Pilot 3.** After the weekly reset (18 November 22:01 Bucharest), Paul starts a fresh ChatGPT
   chat. At re-arm the loop:
   - appends `campaign-stop {reason: "superseded-by-adr-0235"}` to the pilot-2 ledger (skipped
     when the ledger already holds a `campaign-stop`) and moves `contract.json`, `ledger.jsonl` and
     `state.json` into `~/work/_temp/content__v5/v5-pilot-2/`;
   - merges local main into `content/v5`, then rereads the procedure, ADR-0230, ADR-0231 and this
     ADR;
   - writes the `v5-pilot-3` contract below byte for byte except `base_sha`, which is the local main
     commit that carries this ADR;
   - appends the `owner-override` row: `owner`, `decision_date` and `quote` copied verbatim from the
     contract's `quota_override` `by`, `date` and `quote`; `contract_sha256` of the new contract;
     `previous_start_quota_pct_max` 90; the current `quota_pct`; and the limits from the contract;
   - appends `campaign-start` with `goal_meter_tokens` = the meter value at re-arm, `kit_sha` = the
     `content/v5` commit after the merge, the current `quota_pct` and `ordinary_usage`. The 7-day
     clock starts there;
   - records the retirement of the Transilvania → Munții Apuseni prospect in the registry
     (decision 6).
   Every reviewed and frozen item carries over in the registry. A board's 96-hour train timer counts
   from its own `reviewed` time. Cooldowns recorded in pilot 2 lift at `campaign-start`, because
   this ADR changes their recorded inputs.
5. **Frequency.** "Positive frequency" means a positive `exact` count from
   `scripts/content_v5/frequency.py` over FrequencyWords 2018 `ro_full.txt` (SHA-256
   `a0d0993701e251e91b9047753b6032be751217a5aaba36ed879163e020e33ded`, 15,199,764 bytes), where
   cedilla and comma spellings count as one. The pinned copy is
   `~/work/_temp/content__v5/frequency/ro_full.txt`; if it is missing, the loop fetches it once from
   `raw.githubusercontent.com` and checks the SHA-256. A multi-word label has no count and is judged
   by its words' own entries. `undiacritised_only` and `minority_spelling` are
   flagged for the reviewers, and `absent` may mean only that the lemma is missing, so a reviewer
   checks the inflected forms before parking a real word. Rows parked on frequency in pilot 2 are
   rescreened.
6. **Lanț overlap at S1.** `cat-lant-overlap` runs at S1 for every Lanț prospect; a
   `near_duplicate` prospect is parked before authoring. Transilvania → Munții Apuseni is retired
   (Paul, 2026-11-16).
7. **A board's derived view.** A board judgment binds to the item payload hash plus the board's own
   view SHA-256 from `cat-board-view-diff` under decision 1. A whole-bundle digest is not a derived
   view. A landing that leaves a board's derived view unchanged keeps its blind play and judgments.
   For boards judged before this ADR, the loop recomputes the schema-2 view at the base they were
   reviewed on and at the current base, and keeps their judgments only if the two are equal.
   Any train that adds answer keys (forms or new words) runs `resolver_diff.py` over every Cald
   target, so a typed guess that would resolve differently is caught even when the top 100 does not
   change.
8. **Null test.** Every new or changed gate runs first on the unchanged baseline. A gate that the
   unchanged baseline fails is reported to Paul. Until he rules, the items it covers wait; it rejects
   nothing, and nothing lands past it.
9. **Root operating rules.**
   - One fresh chat per campaign.
   - A gate-operator job runs the S7–S9 scripts and returns one receipt; the root never polls a
     running gate and waits with one blocking wait.
   - No rehearsal or preflight for a train that cannot open yet.
   - One line per turn; a full report only when something lands, a train qualifies, a lane is
     blocked or a decision is Paul's.
   - A turn with no eligible work spends at most 3 calls, then marks the goal blocked and states the
     exact wake time. Running jobs or a pending gate receipt are not "no eligible work"; then the
     single blocking wait applies. A blocked goal resumes only on Paul's message, so the line gives
     him the wake time.
   - Quota is read at the start and end of every turn. A rise that the campaign's own tokens do not
     explain is reported as shared usage.
10. **Budgets.** Tokens per landed unit (uncached input plus output, root included): a form 0.8 M, a
    new word with its links 3 M, a board 3 M. After a lane's second landed train, if its cost per
    landed unit exceeds twice its budget for two trains in a row, the lane cools down and the loop
    reports. When 8 M tokens are spent since the last landing with nothing landed, the loop stops and
    reports.
11. **Tools landed with this ADR.** `cat-board-view-diff` (one definition and `--reblind-compare`),
    `close_landing.py` (paired re-blind and board-change reviews), `scripts/content_v5/frequency.py`
    and `cat-lant-overlap`. Each was built with tests and portable builds and checked by an
    independent review before landing.
12. **Diacritics** stay outside the loop. A read-only census found 134 accented Romanian lemmas whose
    folded spelling resolves to a served concept that does not carry that spelling, 90 of them a
    different word (for example `rău` → Râu, `barcă` → FC Barcelona, `deșert` → Desert). The resolver change is runtime code and gets its own task and ADR.

### The `v5-pilot-3` contract

```json
{
  "campaign": "v5-pilot-3",
  "base_sha": "<the local main commit that carries ADR-0235>",
  "ends": {"days": 7, "goal_meter_tokens": 40000000,
           "goal_meter": "ledger uncached_in + out of root and jobs",
           "clock_starts": "campaign-start at re-arm after the weekly reset"},
  "targets": {"forms": 60, "forms_scope": "existing words in the base_sha bundle",
              "boards": {"total": 6, "min_games": 2}, "words": 12, "names": 0,
              "links": 48, "links_scope": "at least one new-word end"},
  "counters_rank_queue": true,
  "cooldown": {"empty_batches": 2, "same_reason_hits": 3},
  "train": {"max_open": 1, "assemble_at": 6, "assemble_after_h": 96, "min_after_h": 3,
            "max_boards": 20, "board_timer_from": "each board's reviewed time",
            "forms_words": {"assemble_at_forms": 20, "assemble_at_words": 6, "after_h": 96,
                            "min_items": 1, "flush_at_quota_pct": 70,
                            "flush_when_left": {"hours": 24, "tokens": 4000000},
                            "max_forms": 100, "max_words": 20}},
  "quota_band": {"intake_stages": ["S1", "S2", "S3"], "finish_frozen_between_pct": [70, 90]},
  "sources": {"hosts": ["ro.wikipedia.org", "ro.wiktionary.org", "www.wikidata.org",
                        "raw.githubusercontent.com", "localhost:8077", "dumps.wikimedia.org"],
              "dump_scope": ["rowiktionary", "rowiki"],
              "daily_cap_per_wikimedia_host": 20, "robots_scope": "path", "ask_on_collision": true},
  "frequency": {"list": "FrequencyWords 2018 ro_full.txt",
                "sha256": "a0d0993701e251e91b9047753b6032be751217a5aaba36ed879163e020e33ded",
                "tool": "scripts/content_v5/frequency.py"},
  "diminutives": {"author": false, "clear_own_confirmed_resolving": true},
  "disturbed": {"cald": "target or top-100 set or order", "lant": "endpoints, optimal or shortest route",
                "max_boards_per_word_dry_run": 10},
  "reblind": {"existing_cald": "paired no-worse, both judges sign", "new_boards": "win"},
  "generator": {"opens": "after backlog idea rows pass S1 and the dump check",
                "threads_per_cell": 3, "items_per_thread": 10,
                "cooldown_min_clean_per_100": 10},
  "budgets_per_landed_unit": {"measure": "uncached_in + out, root included",
                              "form": 800000, "word": 3000000, "board": 3000000,
                              "stop_without_landing_tokens": 8000000},
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

- A new word re-blinds only the boards whose top 100 it changes: 4 for Sparanghel, about 25 for the
  five reviewed words together, instead of all 257.
- The words lane can land again, and 132 parked backlog words come back to screening.
- Fewer root calls and reports leave more of the weekly meter for judged items.
- The paired rule cannot make an existing Cald board measurably worse for the same guesses, but it no
  longer requires the critic to solve a board it could not solve before.

## Rollback

Supersede this ADR and revert the tool commits with a local revert commit through the full gates.
Landed content is removed the same way.

## Owner log

Paul, 2026-11-16, Claude Code session `2c6bf228`. His messages, then his selected answers, verbatim:

```text
find Cat content loop V5 pilot and fix it so it finds new conet

Find the ChatGPT session and understand why it behaved and not why it did not find enough games or words and or concepts and got stuck. Improve that based on how it performed on real views.

real use

Top 100: Which words and order (Recommended)
Re-blind: Paired no-worse (Recommended)
Quota band: Frozen items finish (Recommended)
Next run: Pilot 3 after reset (Recommended)
Builder: You build them here (Recommended)
Apuseni: Retire it (Recommended)
Diacritics: Census, then a fix (Recommended)
```

The question and option texts are kept in
`~/work/_temp/adhoc-content-loop-v5-real-use-20261116/owner-answers.md`. These parts were set by the
author from the reviews rather than by a question to Paul: "worse" when the same guesses win only
the baseline, the consistency checks between a compare receipt and its transcript, the null test,
the root operating rules, the budgets and their stop rules, the derived-view binding wording, and
the `minority_spelling` flag, the `k` allowance (a candidate's best rank may trail the baseline's
by the number of new concepts ranked above it), cooldowns lifting at `campaign-start`, and applying
the Lanț route definition to S7 as well as the dry run (captions, labels and menus become
diagnostics there too).
