# Consumer fills module/frontend commands in its repo-owned source; bases are locked.
FROM node:26.10.0-trixie-slim@sha256:930557a230abacbc3f4fd9b8648abf8f4bee1e17cb72195dcdfb2f709bc85b33 AS node
WORKDIR /build
RUN npm install -g npm@12.2.0
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./frontend/
COPY frontend/vendor/ ./frontend/vendor/
RUN cd frontend && npm ci
COPY frontend/ ./frontend/
RUN cd frontend && npm run build
FROM golang:1.27.1-trixie@sha256:8f58fd67ea075142d947a60e0caa4317746a55118d312f027793d382c7741734 AS golang
WORKDIR /build
ARG GATE_SHA
ARG GATE_TREE_SHA256
COPY . .
COPY --from=node /build/frontend/dist/ ./embedfs/dist/
RUN CGO_ENABLED=0 go build -trimpath -ldflags "-X main.gateSHA=${GATE_SHA} -X main.gateTree=${GATE_TREE_SHA256}" -o /app .
FROM gcr.io/distroless/static-debian13:nonroot@sha256:e2e927ec666bae08560abb3c55d0659eceabb657f56b6782ab500a9fc7f555e3 AS distroless
COPY --from=golang /app /app
ENTRYPOINT ["/app"]
# Social selects this target because its runtime needs Debian media tools.
FROM debian:13.7-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f AS debian
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ffmpeg libavif-bin util-linux perl-base && rm -rf /var/lib/apt/lists/*
COPY --from=golang /app /app
ENTRYPOINT ["/app"]
