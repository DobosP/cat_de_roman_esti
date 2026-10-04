# Go backend migration

The initial Intrusul experiment is recorded in
[ADR-0160](adr/0160-start-go-backend-with-native-intrusul.md). The owner subsequently
requested both complete anonymous implementations; the resulting scope is
[ADR-0161](adr/0161-complete-anonymous-native-backends.md).

Go now serves all six games, native fallback generation, Alchimie exploration and
historical restores, metadata/OpenAPI, legal pages and the existing SPA/static
bundle. Go also implements optional native PostgreSQL accounts and bounded private pending
proposals ([ADR-0163](adr/0163-complete-native-go-accounts.md)). Those activation flags stay
off publicly; the frontend remains React/TypeScript/JavaScript. Rust retains the anonymous
research boundary. Neither native serving implementation needs Python; current rollout
state is recorded in [STATUS](STATUS.md).

Build/run, Docker, CI and browser instructions are in
[Native backends](NATIVE_BACKENDS.md). Current qualification and performance evidence
are in [STATUS](STATUS.md) and [the native verification record](reviews/native-backends/README.md).
The original narrower experiment's [receipt](reviews/go-backend-pilot/verification.json)
is history: its 16 MiB Go footprint used only Intrusul data and cannot describe this
complete port.

The initial loopback gateway in ADR-0160 is historical. The selected Go server has
no Python upstream flag or reverse proxy; unknown API paths return native 404s.

The production selection and user-authorized deployment are now
[ADR-0162](adr/0162-select-go-production-backend.md). Go is the canonical runtime;
the guarded Python gateway described above is historical and has been removed.
Python remains a build/reference tool, and Rust remains comparative research.
