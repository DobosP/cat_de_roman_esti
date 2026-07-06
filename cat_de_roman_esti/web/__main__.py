"""uvicorn launcher for the cat_de_roman_esti BFF (Django ASGI).

    python -m cat_de_roman_esti.web --host 127.0.0.1 --port 8000

Serves the built SPA at ``/`` and the ``/api`` routes. By default it plays against
the bundled offline fixture; set ``CAT_KG_FIXTURE`` to point at another bundle.

Single process on purpose: live game sessions are in-memory (SessionStore), so
never scale by adding uvicorn workers — scale reads by putting a cache in front.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

import uvicorn


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cat_de_roman_esti.web",
        description="Run the cat_de_roman_esti web backend-for-frontend.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="bind port (default 8000)")
    parser.add_argument("--reload", action="store_true", help="enable autoreload (dev)")
    parser.add_argument(
        "--log-level", default="info", help="uvicorn log level (default info)"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    uvicorn.run(
        "cat_de_roman_esti.web.asgi:application",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
