# syntax=docker/dockerfile:1
# Build from the repository root: docker build -f go-backend/Dockerfile .
FROM golang:1.27.1-bookworm AS build
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
COPY --from=build /out/cat-server /usr/local/bin/cat-server
COPY shared-go/authcore/LICENSE /usr/share/doc/cat-authcore/LICENSE
# ADR-0020 keeps this compiled SPA in the repository beside its source.
COPY cat_de_roman_esti/web/static/ ./cat_de_roman_esti/web/static/
ENV CAT_ACCOUNTS_ENABLED=0
USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["curl", "--fail", "--silent", "--show-error", "--output", "/dev/null", "--max-time", "3", "http://127.0.0.1:8080/api/health"]
ENTRYPOINT ["/usr/local/bin/cat-server"]
CMD ["-listen", "0.0.0.0:8080"]
