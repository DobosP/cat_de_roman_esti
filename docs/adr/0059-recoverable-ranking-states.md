# ADR-0059: Make ranking loading and failure states recoverable

Date: 2026-07-24
Status: accepted

## Decision

Render ranking loading as a centered live status with `aria-busy`. Clear stale ranking data
before each request. After loading settles, render failures as an alert with one short next
action: an accounts-off or missing-endpoint 404 says the ranking is not active and links
home; any other failure offers `Reîncearcă`, retrying the currently selected game.

Keep both recovery actions at least 44 pixels high and preserve the existing mobile selector
and desktop tabs.

## Context / why

Opening `/clasament` directly in the anonymous deployment returned a correct JSON 404, but
the UI reduced every failure to static generic text. Temporary network failures had no
retry, loading was not announced, and the nominally centered cards placed text against their
top edge at 390 pixels.

Redirecting all failures home was rejected because it hides recoverable outages. Retrying
automatically without an explicit player action was rejected because it creates an
unbounded request loop and gives no clear state transition.

## Consequences

Mobile, keyboard, and assistive-technology users receive a concise status and a useful next
step without losing the selected game or seeing stale rows. A misconfigured accounts-on
deployment whose ranking route returns 404 receives the same safe unavailable state.

Ranking rows, verified-score authorship, consent, nickname/visibility rules, public fields,
request bounds, and telemetry remain unchanged. The change is confined to the lazy ranking
screen plus shared CSS.
