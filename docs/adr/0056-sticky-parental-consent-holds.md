# ADR-0056: Keep a self-declared minor on a sticky parental-consent hold

Date: 2026-07-24
Status: accepted

## Decision

Once self-service consent identifies an account as below the Romanian self-consent age, keep
`is_minor` and `parental_consent_required` set until a future verifiable parental-consent
flow clears them. Do not let another self-service consent request replace the stored birth
year, create consent records, enable progress saving, or enable public ranking.

Serialize consent and profile-visibility mutations on the same `Profile` row inside database
transactions. Recheck the hold and current consent only after acquiring that lock. Limit
profile edits to the explicitly requested nickname/visibility fields so a stale writer cannot
overwrite age, consent-version, or hold state.

## Context / why

The first age-gate implementation correctly returned 403 for a minor, but a second request
could submit an adult birth year, clear both hold flags, create current consent records, and
enable account-linked storage. Locking only the consent endpoint was insufficient: a
concurrent full profile save could read pre-hold state, wait, then replay stale consent fields
after the hold transaction committed.

Automatically accepting a corrected adult year was rejected because the service cannot
distinguish a typo from bypassing the child-data gate. A support override was rejected
because no verified operator or parental workflow exists yet.

## Consequences

An under-age self-service account remains unable to save scores or opt into rankings after
any adult-year resubmission. No schema migration is needed. Adult consent and normal nickname
or visibility updates retain their response contracts, but the two writers now serialize on
one row and profile saves update only intended fields.

A legitimate correction or child-account launch now requires a separately specified,
auditable parental-verification flow. Accounts remain disabled in the anonymous deployment
profile.
