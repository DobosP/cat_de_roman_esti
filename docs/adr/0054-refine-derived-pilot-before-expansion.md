# ADR-0054: Refine the two derived games before expanding the arcade

Date: 2026-07-23
Status: accepted

## Decision

Keep the V39 arcade at six games. Do not add a seventh mechanic until larger-player evidence
exists for Intrusul and Perechi. Preserve their strict, generated V38 catalog and all
pack/KG/rubric/ranking digest gates; never mine, enumerate, or widen derived content during a
request.

After category, difficulty, repeat, and starter filters, prefer derived boards whose private
standard score is at least 55. If that preferred shelf is empty, fall back only to the full
strict shelf produced by the same filters. For an unscoped beginner start, choose category,
then source, then variant, including the standard reserve when necessary. Preserve an
explicit category. Keep daily selection deterministic on its preferred shelf and leave all
four V37 schedules and hash namespaces unchanged.

Keep a player on a derived game's starter shelf until the first non-daily positive-score win
or three non-daily completions. Daily play must not advance mastery. Bound the local mastery
counter at three and merge imported copies monotonically by maximum count and logical OR for
the win flag.

For anonymous free replay, store exactly one opaque completed non-daily session ID for each
derived game in a separate versioned browser document. Validate it at 128 characters with no
controls, never store catalog/source/rank/answer data, and never read or update it for daily
play. An expired ID must be harmless. The server's existing previous-session reference still
retains at most four private source IDs.

Keep the interface tap-first and short. Remove Intrusul's inherited source-difficulty badge,
remove solved Perechi tiles from the active grid while retaining the solved-pair stack and
keyboard focus, and label a daily result's next action as free play.

## Context / why

V38 proved a bounded launch inventory, but its strict starter subset could dominate repeated
anonymous starts and a single completion graduated a beginner even after a zero-score loss.
Free play also forgot its previous source after returning home or reloading, making immediate
repeats more likely. Flat source-first selection reduced source duplication but still let a
few source-heavy categories dominate the first impression.

A seventh game was rejected because it would fragment the first pilot before the two newest
mechanics have real-player calibration. Making score 55 a hard eligibility gate was rejected
because a narrow category could become unplayable. Persisting source IDs or board metadata in
the browser was rejected because opaque session continuity already supplies bounded repeat
avoidance. Letting daily play graduate the starter was rejected because a shared daily is not
a deliberate free-play mastery sample.

## Consequences

The catalog remains 183 Intrusul and 153 Perechi boards. The preferred standard inventories
are 144 boards from 57 sources across 14 categories and 113 boards from 42 sources across 10
categories respectively; strict filtered fallback preserves playability without broadening
content. Starter exposure is category-balanced before source and variant.

Replay continuity survives home navigation and reload without revealing private content.
One or two beginner losses retain the starter shelf; three completions or one win graduate
it. Explicit category play and daily identity remain stable. Calibration still needs an
anonymous six-game pilot; these editorial scores are selection estimates, not measured fun
or Romanian-knowledge ratings.
