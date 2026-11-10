# ADR-0228. Policy-only source-host access

Valid until: Paul revises this grant — then treat as history.

Date: 2026-11-10
Status: accepted

## Context

The accepted V4 plan requires primary-policy inspection and an independently reviewed
source-client configuration with Paul's approval of exact SOURCES.md bytes.
The Romanian Wikipedia terms page links to Wikimedia Foundation terms.
FrequencyWords distinguishes MIT software and CC BY-SA 4.0 content.
The existing host grant supports the content research in ADR-0226.

## Decision

Paul approves read-only HTTPS GETs for primary terms and licence inspection on
foundation.wikimedia.org, creativecommons.org and docs.github.com.
Use the existing fixed V4 User-Agent, canonical response cache, robots and terms checks.
Space requests by at least two seconds per host and ten seconds for Wikimedia hosts.
A 429 or 5xx invokes the existing one-hour minimum breaker. Policy refusal drops that
host for the run and adds its owner-queue entry. Redirects retain the exact host boundary.
Policy receipts identify the first fetcher as policy and support source-policy assessment.
The source-client configuration follows the separate exact-SOURCES approval in plan M2.1.

## Owner log

Paul answered the following question in this chat on 2026-11-10.

> Shared words +0, names +0. Boards +9 Conexiuni, +1 Cald (Muzeu), +3 Lanț (Aragaz → Lingură), +0 Alchimie/Intrusul/Perechi.
> The source-client review needs primary terms and licences hosted outside your standing allowlist.
> Approve policy-only, read-only GETs to foundation.wikimedia.org, creativecommons.org and docs.github.com under the same UA, caching, robots and rate controls?
> This permits policy inspection to prepare the separately required exact SOURCES.md approval packet.

> Approve policy-only access (Recommended)

## Evidence

The verbatim question and answer are retained in
`/home/dobo/work/_temp/content__v4/owner/policy-only-host-grant-20261110.json`,
SHA-256 `f23c4a09010719dbc0771186c4a043f7cf233d4620ed2bc1dd3d4bec4eef3261`.
Policy retrieval and the final SOURCES byte review have their own dated receipts.
