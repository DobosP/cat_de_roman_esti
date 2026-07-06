# syntax=docker/dockerfile:1
#
# cat_de_roman_esti — offline-first deploy image.
#
# Multi-stage:
#   stage 1 (node)   : npm ci/install + `npm run build` -> cat_de_roman_esti/web/static
#   stage 2 (python) : pip install the package with its [web] extra, copy in the package
#                      (fixtures + the built SPA from stage 1), run uvicorn as non-root.
#
# The runtime image needs ONLY: python 3.11 + the cat_de_roman_esti package + its
# [web] extra (django + DRF + uvicorn) + the bundled fixtures + the built SPA static.
# roedu_client is stdlib-only; romania_scraper is NOT needed at runtime.

# ---------------------------------------------------------------------------
# Stage 1: build the React/Vite SPA into cat_de_roman_esti/web/static
# ---------------------------------------------------------------------------
FROM node:18-slim AS frontend

WORKDIR /build

# Copy ONLY the manifests first so `npm ci` is cached unless deps change.
# The vendored @roedu/ui tarball is a file: dependency, so it must exist before
# `npm ci` (it rides with the manifests; bumping it busts this cache layer, correctly).
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY frontend/vendor/ ./frontend/vendor/
WORKDIR /build/frontend
# Prefer the reproducible `npm ci` (needs package-lock.json); fall back to install.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Now bring in the frontend source. vite.config.ts emits into
# ../cat_de_roman_esti/web/static, so the package dir must exist relative to frontend/.
WORKDIR /build
COPY frontend/ ./frontend/
# Needed by vite.config.ts outDir ("../cat_de_roman_esti/web/static") and by the
# package metadata read for the index.html; copying the package keeps paths identical
# to the source tree layout.
COPY cat_de_roman_esti/ ./cat_de_roman_esti/

WORKDIR /build/frontend
# `npm run build` = tsc --noEmit && vite build -> /build/cat_de_roman_esti/web/static
RUN npm run build \
    && test -f /build/cat_de_roman_esti/web/static/index.html \
    && ls /build/cat_de_roman_esti/web/static/assets/*.js >/dev/null

# ---------------------------------------------------------------------------
# Stage 2: slim python runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# - PYTHONDONTWRITEBYTECODE: no .pyc clutter in the image
# - PYTHONUNBUFFERED: logs flush immediately (good for `docker logs`)
# - PORT: default bind port (compose/launcher may override)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# Copy packaging metadata + the python package (with bundled fixtures).
# constraints.txt pins the exact `[web]` install closure for reproducible builds.
COPY pyproject.toml README.md constraints.txt ./
COPY cat_de_roman_esti/ ./cat_de_roman_esti/

# Bring in the SPA built in stage 1 (overwrites any copy that rode along in the package
# dir so the image always ships a fresh build).
COPY --from=frontend /build/cat_de_roman_esti/web/static/ ./cat_de_roman_esti/web/static/

# Install the package WITH its web extra (django + DRF + uvicorn), PINNED via constraints.txt
# for a reproducible build. Package-data in pyproject.toml ships fixtures/*.json and
# web/static/** into site-packages, so the installed copy is self-contained.
RUN pip install -c constraints.txt ".[web]" \
    && python -c "import cat_de_roman_esti.web, django, rest_framework, uvicorn; print('install OK')"

# Drop privileges: create a non-root user and own /app.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container-internal healthcheck hits the BFF's own /api/health (stdlib urllib, no curl
# needed). Uses ${PORT} so it tracks a runtime port override.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
url='http://127.0.0.1:%s/api/health' % os.environ.get('PORT','8000'); \
sys.exit(0 if urllib.request.urlopen(url, timeout=3).status==200 else 1)" || exit 1

# Bind 0.0.0.0 so the port is reachable from the host. Honor $PORT (the app's CLI takes
# --port, so we expand it here). ROEDU_API_URL / ROEDU_API_KEY are read from the env by
# the app itself (app.py -> os.environ); unset => offline fixture.
CMD ["sh", "-c", "exec python -m cat_de_roman_esti.web --host 0.0.0.0 --port \"${PORT:-8000}\""]
