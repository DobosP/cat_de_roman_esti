"""uvicorn launcher for the cat_de_roman_esti BFF.

    python -m cat_de_roman_esti.web --host 127.0.0.1 --port 8000

Serves the built SPA at ``/`` and the ``/api`` routes. By default it plays against the
bundled offline fixture; set ``ROEDU_API_URL`` to use the live ro_data_server.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

import uvicorn

from .app import create_app


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

    if args.reload:
        # Reload needs an import string, not an app instance.
        uvicorn.run(
            "cat_de_roman_esti.web.app:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            reload=True,
            log_level=args.log_level,
        )
    else:
        uvicorn.run(create_app(), host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
