"""SPA serving: deep-link fallback + the no-build placeholder page.

WhiteNoise serves the real files (/, /assets/*) straight from ``web/static``; only
paths that are not files reach the catch-all here, which returns ``index.html`` so
the React router can take over (/alchimie, /cald-rece, ...). Unknown /api/* paths
never get here — urls.py routes them to the JSON 404 first.
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse

from .settings import STATIC_DIR

_PLACEHOLDER_HTML = """<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>cat_de_roman_esti</title>
  <style>
    body { margin:0; min-height:100vh; display:flex; align-items:center;
      justify-content:center; font-family: system-ui, sans-serif; color:#e8e8f0;
      background: radial-gradient(1200px 800px at 30% 20%, #1b2350, #0a0d1f 70%); }
    .card { max-width: 34rem; padding: 2rem 2.5rem; border-radius: 18px;
      background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { margin:0 0 .5rem; font-size:1.6rem;
      background: linear-gradient(90deg,#ffd166,#ef476f,#118ab2);
      -webkit-background-clip:text; background-clip:text; color:transparent; }
    code { background: rgba(255,255,255,0.08); padding:.15rem .4rem; border-radius:6px; }
    a { color:#84d6ff; }
    p { line-height:1.55; }
  </style>
</head>
<body>
  <div class="card">
    <h1>cat_de_roman_esti</h1>
    <p>The API is live, but the front-end build is missing.</p>
    <p>Build the SPA to play the word-game arcade:</p>
    <p><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></p>
    <p>The API is at <a href="/api/health">/api/health</a>.</p>
  </div>
</body>
</html>
"""


def spa_index(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    index_html = STATIC_DIR / "index.html"
    if index_html.exists():
        return HttpResponse(index_html.read_bytes(), content_type="text/html; charset=utf-8")
    # No build: only the root gets the friendly placeholder (FastAPI-era behavior);
    # everything else is a plain JSON 404.
    if request.path in ("", "/"):
        return HttpResponse(_PLACEHOLDER_HTML, content_type="text/html; charset=utf-8")
    return JsonResponse({"detail": "Not Found"}, status=404)
