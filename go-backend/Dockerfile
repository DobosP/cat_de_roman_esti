# syntax=docker/dockerfile:1
# Standalone Go recipe, built from repository root with actual SHA/tree build arguments.
# Fresh managed assets and identity are identical to the GUI build prerequisites.
FROM node:26.10.0-bookworm-slim@sha256:cfa005801786b8e38fa220af518e43f5654c53b36af36b4ad5b3049225ee261e AS frontend
WORKDIR /build
COPY versions.lock.json /build/versions.lock.json
RUN npm install --global npm@12.2.0
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY frontend/vendor/ ./frontend/vendor/
WORKDIR /build/frontend
RUN npm ci
WORKDIR /build
COPY frontend/ ./frontend/
COPY legacy/ ./legacy/
COPY scripts/gui-assets.mjs ./scripts/gui-assets.mjs
COPY tools/gui-bootstrap-webkit/scripts/kit-sync.mjs ./tools/gui-bootstrap-webkit/scripts/kit-sync.mjs
RUN cd frontend && npm run build
# Owning sync verifies the actual manifest/assets and exact frozen original30.
RUN node scripts/gui-assets.mjs sync

FROM golang:1.27.1-bookworm@sha256:e114385c58e7280d2f56d6cf374219dda33fef8eb77f72e9f290ccae6160bd90 AS backend
ARG GATE_SHA
ARG GATE_TREE_SHA256
ENV GOTOOLCHAIN=local
WORKDIR /build/go-backend
COPY shared-go/authcore/ /build/shared-go/authcore/
COPY go-backend/ ./
COPY versions.lock.json /build/versions.lock.json
COPY cat_de_roman_esti/fixtures/ /build/cat_de_roman_esti/fixtures/
COPY tests/fixtures/kg_sample.json tests/fixtures/games_pack.json /build/tests/fixtures/
COPY docs/CRITIQUE_RUBRIC.md /build/docs/CRITIQUE_RUBRIC.md
COPY --from=frontend /build/go-backend/embedfs/dist/ ./embedfs/dist/
COPY --from=frontend /build/go-backend/embedfs/legacy/ ./embedfs/legacy/
RUN GOMAXPROCS=2 GOFLAGS=-p=2 go run ./cmd/cat-content export --root .. --check
# No defaults or environment fallback: failure prevents the app compilation.
RUN GOMAXPROCS=2 GOFLAGS=-p=2 go run ./cmd/cat-gui-build --root .. --sha "$GATE_SHA" --tree-sha256 "$GATE_TREE_SHA256" \
    && CGO_ENABLED=0 GOMAXPROCS=2 GOFLAGS=-p=2 go build -trimpath -ldflags="-s -w" -o /out/cat-server ./cmd/cat-server

FROM debian:bookworm-slim@sha256:a4672c0cb26fbdde88e38fa2dfb6c681942306680e41e4378b28770b6e79ee91 AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libpcre2-8-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app
RUN mkdir -p /data/submissions && chown 10001:10001 /data/submissions && chmod 700 /data/submissions
WORKDIR /app
COPY --from=backend /out/cat-server /usr/local/bin/cat-server
COPY shared-go/authcore/LICENSE /usr/share/doc/cat-authcore/LICENSE
ENV CAT_ACCOUNTS_ENABLED=0
USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["curl", "--fail", "--silent", "--show-error", "--output", "/dev/null", "--max-time", "3", "http://127.0.0.1:8080/api/health"]
ENTRYPOINT ["/usr/local/bin/cat-server"]
CMD ["-listen", "0.0.0.0:8080"]
