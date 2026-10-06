# ADR-0176: Preserve frozen CRLF bytes during source transport

Date: 2026-10-06
Status: accepted for this finite source-only Linux handoff

## Context

Paul requested prepared source work on local main and unfinished work pushed for Linux.
ADR-0175 preserved the first aggregate default-whitespace failure and its blocked landing.
That failure includes immutable i04 CRLF research receipts. Altering their raw bytes would
invalidate preserved exact reviews; the source transport has no runtime or generated changes.

## Decision

For this one source-only transport, preserve the default-check failure as a separate fact.
Also check the complete exact source pin with standard trailing-blank, EOF and space-before-tab
rules and explicit CR-at-EOL recognition using a single command:

`git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check <main-base>..<exact-source-pin>`

No repository/global setting is changed. Every newly owned handoff commit must pass the ordinary
default whitespace check. Independent exact-pin source isolation, unchanged runtime/generated/
asset/test trees, clean main/base ancestry and origin relationship precede main update.
This partially supersedes ADR-0175's CRLF-only source-landing blocker; preserve that original
failure, decision text and every frozen byte. A real whitespace defect remains a blocker.

## Consequences

A passing line-ending-aware source check is transport evidence only. It is not a passing default
aggregate check or runtime/native/gameplay/history/source5/export/authority/assembled acceptance.
V1.5 remains NOT_QUALIFIED with zero installed content and no version increment. Windows discovery
and loops stay stopped; no new workspace, research, deployment, force push or deletion follows.
Actual local/remote landing SHAs and both check outcomes are recorded separately in the worker
source-transport receipt; failed or unexecuted qualification gates remain explicit.
