# V86 Lanț alternative coverage

Valid until: the bound Lanț policy or measured pack/graph changes — then treat as history.

The Stafide→Brânză round had two valid shortest branches, through Pască and Poale-n brâu.
Its three visible choices were Cozonac, Pască and Salam de biscuiți. The second shortest
branch was excluded because the final corridor sort used only local strength, salience
and the existing soft hub penalty; it discarded the preceding distance-aware ordering.

The generic correction reserves up to two of the existing three corridor slots for
distinct unvisited shortest continuations, using the existing semantic-quality order
within that set. Remaining corridor space still uses the prior quality ranking, so the
third slot can expose exploration. Existing target-reachable detour slots remain. The
public display remains alphabetical and contains only each local label and short edge
description. No route classification, distance, complete path or new identifier is sent.

The menu remains capped at six choices and three corridor hops, with no corridor backfill
beyond that quota. Visited nodes, dead ends and duplicate normalized labels stay excluded.
All other legal direct typed moves remain available. No session field, cache, request bound,
TTL, score, hint escalation, curated selection or graph edge changes in this policy edit.
Lanț's destination was already public; this change does not reveal its private route web.

## Measured selection change

Before and after captures used the same V85 graph and pack at baseline `14e8895`:

- KG SHA-256: `b7d28b990d37164d8e41a93965a5824162ded56b2907ac03388fee717eb144b2`.
- Pack SHA-256: `835937cc369918a0070a8d09a35f3982f21f74275476f061aa6c05242d270b4d`.
- **59 of 96 eligible initial menus change; 37 stay exact.**
- Total visible shortest continuations rise from **107 to 198**.
- Starts missing two available distinct shortest continuations fall from **59 to zero**.
- Stafide now shows Cozonac, Pască and Poale-n brâu; the available graph routes are unchanged.

These are suggestion selections, not new boards, new routes or 59 independently certified
editorial improvements. The graph can contain imperfect associations; reserving a shorter
continuation does not prove human fairness or enjoyment. Root's separate V86 graph/content
work can change later captures and must not be conflated with this isolated comparison.

Exact observations: [before](menus-before.json), [after](menus-after.json) and
[changed menus](menu-delta.json). The capture script remains in task scratch under
`lant/capture_menus.py` and accepts a worktree path and output path.

## Targeted verification

`PYTHONPATH=. ~/work/cat_de_roman_esti/.venv/bin/python -m pytest tests/test_wordgames_lant.py tests/test_v86_lant_choice_coverage.py -q -o addopts=''`

**65 passed in 158.80 seconds**, including nine new cases. Coverage includes one/two/four
shortest alternatives, retention of an exploratory corridor slot and safe detour, graph
insertion-order determinism, visited-shortest recovery, every eligible current start, and
actual API menus/moves for gastronomic, cultural and music rounds. Existing hint, homonym,
off-menu typing, cap, undo, score, dead-end, concurrency and deterministic-selector checks
remain green. Source/result bindings are in [verification.json](verification.json), including
the captured [policy diff](policy.diff.gz) and exact before/after menu hashes.

The initial static lint caught an unbound test-loop lambda; binding its service argument
fixed that test-only issue before the green run. No gameplay assertion failed.

The policy diff is losslessly gzipped: its original context-line spaces are retained,
and the verification receipt binds both decoded diff and archive bytes.
