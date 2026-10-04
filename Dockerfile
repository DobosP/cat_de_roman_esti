# syntax=docker/dockerfile:1
# Canonical release: freshly compiled SPA and native Go games/accounts serving.
FROM node:24-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY frontend/vendor/ ./frontend/vendor/
WORKDIR /build/frontend
RUN npm ci
WORKDIR /build
COPY frontend/ ./frontend/
COPY cat_de_roman_esti/ ./cat_de_roman_esti/
WORKDIR /build/frontend
RUN npm run build \
    && test -f /build/cat_de_roman_esti/web/static/index.html \
    && ls /build/cat_de_roman_esti/web/static/assets/*.js >/dev/null

FROM golang:1.27.1-bookworm AS backend
WORKDIR /build/go-backend
COPY shared-go/authcore/ /build/shared-go/authcore/
COPY go-backend/ ./
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/cat-server ./cmd/cat-server

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libpcre2-8-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app
RUN mkdir -p /data/submissions && chown 10001:10001 /data/submissions && chmod 700 /data/submissions
WORKDIR /app
COPY --from=backend /out/cat-server /usr/local/bin/cat-server
COPY shared-go/authcore/LICENSE /usr/share/doc/cat-authcore/LICENSE
COPY --from=frontend /build/cat_de_roman_esti/web/static/ ./cat_de_roman_esti/web/static/
ENV CAT_ACCOUNTS_ENABLED=0 PORT=8000
USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent --show-error --output /dev/null --max-time 3 "http://127.0.0.1:${PORT:-8000}/api/health"
CMD ["sh", "-c", "exec /usr/local/bin/cat-server -listen \"0.0.0.0:${PORT:-8000}\""]
