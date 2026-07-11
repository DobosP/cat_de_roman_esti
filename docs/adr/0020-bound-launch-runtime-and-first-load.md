# ADR-0020: Bound the launch runtime and first load

Date: 2026-07-11
Status: accepted

## Decision

Keep the Django 5.2 BFF and React SPA, while moving the build baseline to Python 3.12,
Node 24 LTS, React 19.2, and Vite 8.1. Load each game route dynamically and use Motion's
feature-lazy DOM renderer. Enforce a recursive 120 KiB gzip ceiling on the entry's static
JS/CSS import graph from Vite's manifest; lazy route chunks are measured by the build but
are not first-load inputs. Ship only the Latin and Latin Extended variable-font subsets.
Treat Vite-hashed `/assets/` as immutable. Bound each game's in-memory sessions to a
two-hour sliding TTL and 1,000-entry LRU by default, and reject request bodies above 64 KiB at
both Caddy and the ASGI receive boundary before Django can buffer them.
Expose all three runtime limits through validated environment variables. Keep the matching
`web/static` bundle and Vite manifest as tracked release artifacts whenever frontend source
changes; backend-only changes must not regenerate them.

Use ESLint 10.7.0's flat configuration with `@eslint/js` 10.0.1,
`typescript-eslint` 8.63.0, `eslint-plugin-react-hooks` 7.1.1, and
`eslint-plugin-react-refresh` 0.5.3. Keep TypeScript at 5.9.3: the registry's TypeScript
7.0.2 release is outside typescript-eslint's supported `<6.1.0` peer range. Node 24
satisfies ESLint 10's runtime floor.

## Context / why

The launch host must also run other apps and infrastructure, while the four games need
rich client animation and server-held hidden answers. Rewriting this interaction model in
a static framework or Go would add migration risk without addressing the measured costs:
the warm anonymous Django process was about 89 MiB RSS, but the former 40,000-session
aggregate ceiling could add roughly 46 MiB even before sessions accumulated play history.
The pre-split SPA was 117.25 KiB gzip of JS, all routes loaded eagerly, WhiteNoise cached
Vite assets for only 60 seconds, and broad Fontsource entry points emitted ten subsets.
Framework replacement was therefore rejected in favor of explicit, testable budgets at
the actual memory, transfer, and cache boundaries.

## Consequences

The verified entry graph is 115.34 KiB gzip including CSS, and each game downloads only
when opened. The build fails if recursive static imports cross 120 KiB; intentional budget
changes require an explicit `INITIAL_BUNDLE_GZIP_LIMIT_KIB` override plus review of this
decision. Four Romanian-capable WOFF2 files replace ten broad subsets. Hashed assets receive
long-lived immutable caching, while HTML remains short-lived. Operators may tune
`CAT_SESSION_TTL_SECONDS`, `CAT_MAX_SESSIONS_PER_GAME`, and `CAT_MAX_REQUEST_BYTES`, but
invalid, non-positive, fractional-cap, or non-finite values fail fast. The single-process
session constraint remains; horizontal scaling still requires a shared session store. The
runtime image deletes any source-tree static directory before copying the freshly built
bundle, so Docker cannot retain obsolete hashed files even if a checkout is inconsistent.
CI runs the frontend contract tests before linting and rebuilding the budget-gated artifact.
The Caddy 2.11 edge and an ASGI receive wrapper share the request-body limit; chunked requests
stop at the crossing chunk and receive 413 without being fully spooled by Django. The view-level
`Content-Length` check remains a WSGI/defense-in-depth guard.
The final production image is 241,861,503 bytes at
`sha256:03b8288a928a2166e9a2c4d2586eedeb72f0e8c95cdfa882bcea53a15f7845ff`, runs as
`appuser`, and imports the ASGI wrapper with the default 65,536-byte ceiling.
The development-only lint migration removes the ESLint 8 legacy-config/EOL dependency
tree. ESLint 10.7 is used instead of the initially reviewed 10.6 because 10.7 became the
current registry release on 2026-07-10; a clean lockfile install and all frontend gates
pass with this baseline, and the complete npm dependency audit reports zero vulnerabilities.
The exact constrained Python closure also reports no known vulnerabilities. TypeScript 7 stays
deferred until the lint toolchain supports it.
