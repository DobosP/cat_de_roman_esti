# Go backend migration

The initial Intrusul experiment is recorded in
[ADR-0160](adr/0160-start-go-backend-with-native-intrusul.md). The owner subsequently
requested both complete anonymous implementations; the resulting scope is
[ADR-0161](adr/0161-complete-anonymous-native-backends.md).

Go now serves all six games, native fallback generation, Alchimie exploration and
historical restores, metadata/OpenAPI, legal pages and the existing SPA/static
bundle. Rust implements the same boundary. Both need no Python runtime for serving
the anonymous release. Accounts and the optional submissions queue remain disabled.
The deployed Python V1.0.1 release has not changed.

Build/run, Docker, CI and browser instructions are in
[Native backends](NATIVE_BACKENDS.md). Current qualification and performance evidence
are in [STATUS](STATUS.md) and [the native verification record](reviews/native-backends/README.md).
The original narrower experiment's [receipt](reviews/go-backend-pilot/verification.json)
is history: its 16 MiB Go footprint used only Intrusul data and cannot describe this
complete port.

The optional `-python-upstream http://127.0.0.1:8000` flag retains the guarded
anonymous loopback gateway for unknown legacy routes. All known game/site paths
remain native. The gateway validates the upstream manifest and refuses accounts;
its combined heaps are outside the standalone benchmark.
