# syntax=docker/dockerfile:1
# Optional Rust 1.98.1 reference, built from repository root.
# Keep its locked Rust build and filesystem SPA boundary; do not activate it as default.
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
RUN cd frontend && npm run build \
    && test -f /build/frontend/dist/index.html \
    && test -f /build/frontend/dist/.vite/manifest.json \
    && ls /build/frontend/dist/assets/*.js >/dev/null

FROM rust:1.98.1-bookworm@sha256:c49256cbe5ea0188bc658a689500d70c41eb51f009a7a7be209caf60a944f3ec AS build
WORKDIR /build
# Rust embeds the same reviewed export and Unicode-decimal table as Go.
COPY go-backend/ ./go-backend/
COPY rust-backend/ ./rust-backend/
WORKDIR /build/rust-backend
RUN cargo build --locked --release --bin cat-rust-server

FROM debian:bookworm-slim@sha256:a4672c0cb26fbdde88e38fa2dfb6c681942306680e41e4378b28770b6e79ee91 AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /build/rust-backend/target/release/cat-rust-server /usr/local/bin/cat-rust-server
COPY --from=frontend /build/frontend/dist/ ./cat_de_roman_esti/web/static/
ENV CAT_ACCOUNTS_ENABLED=0
USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["curl", "--fail", "--silent", "--show-error", "--output", "/dev/null", "--max-time", "3", "http://127.0.0.1:8080/api/health"]
ENTRYPOINT ["/usr/local/bin/cat-rust-server"]
CMD ["--listen", "0.0.0.0:8080"]
