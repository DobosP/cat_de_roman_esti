# ADR-0006: Mobile App-Pack Contract Fixture

Date: 2026-07-04
Status: accepted

## Decision
Export a deterministic public mobile app-pack fixture from the bundled KG with only the
fields roedu-mobile may consume: manifest trust fields, node `id`/`label_ro`, edge
`id`/`src_id`/`dst_id`, and puzzle `id`/`start_id`/`target_id`/`difficulty`. Keep
server-side helper fields such as `solution_path` and `hint_neighbors` out of this
fixture, and pin it with cat-side generator tests plus roedu-mobile importer tests.

## Context / why
The mobile app must stay coupled to HTTP/app-pack contracts rather than Python internals
or a live cat server. The previous mobile demo fixture proved importer mechanics but did
not prove compatibility with cat-exported field names. Sharing a checked-in JSON snapshot
gives both repositories a stable contract artifact without source imports, secrets, or
runtime infrastructure.

## Consequences
Changing the mobile public app-pack fields now requires regenerating
`tests/fixtures/cat_mobile_app_pack_contract.json`, copying it to roedu-mobile, and
updating both contract test suites in the same change. The fixture is a contract-test
artifact; it does not replace the runtime mobile demo bundle by itself.
