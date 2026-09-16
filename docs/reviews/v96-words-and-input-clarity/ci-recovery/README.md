Valid until: the bound test or browser-routing behavior changes — then repeat affected checks.

V96's first [GitHub run](https://github.com/DobosP/cat_de_roman_esti/actions/runs/35155920107)
passed both backend jobs and 539 browser cases. The final mobile recovery case timed out.
Local repetition reproduced it twice. Traces show that keyboard activation sent the craft,
the server committed with HTTP 200, and the following recovery GET remained pending.
This rules out the initially suspected scrolling/readiness issue.

The test's one-shot network handler was removed while aborting the mocked response.
Installed Playwright source and paired runs support an interception-teardown race; this
is not claimed as an upstream-confirmed bug. Keeping the handler registered through the
recovery read avoids that teardown. A manual counter aborts only the first combine;
later requests continue. The unchanged result/focus assertions now also require exactly
one craft request and one recovery GET, and check the committed response was HTTP 200.

No application, content, dependency, asset, timeout, retry or keyboard-sequence changes.
The independent reviewer observed **30 consecutive mobile passes** and **12 desktop/mobile
V96 cases passed**, plus unchanged product bytes. Native 212, lint and build pass; bundle
remains 119.23/120 KiB. Two failed traces, compact diagnosis and exact logs are preserved.

[Correction receipt](receipt.json) identifies the sole amended test input, preserving the
original integration receipt as history. All 42 other gate inputs and all ten installed
artifacts remain exact. [Independent review](independent/final-review.json) and
[archive manifest](archive-manifest.json) bind the proof. Fresh GitHub CI follows publication.
