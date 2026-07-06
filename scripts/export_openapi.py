"""Export the BFF's OpenAPI schema for mobile TypeScript client generation.

The schema is the contract a generated client (``openapi-typescript`` / ``orval`` /
``openapi-generator``) consumes. Operation method names come straight from the stable
``operationId``s (``<game>_<action>`` — e.g. ``contexto_guess``, ``alchimie_combine``),
which the views pin via ``@extend_schema(operation_id=...)`` so a route refactor never
churns the generated client surface.

Deterministic and offline (no server, no live data): it only sets up Django and runs
drf-spectacular's generator. Keys are sorted so re-exports diff cleanly in version
control.

Usage::

    python scripts/export_openapi.py                 # print to stdout
    python scripts/export_openapi.py openapi.json     # write to a file
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def export_openapi() -> dict:
    """Return the app's OpenAPI schema as a plain dict (no I/O)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")
    import django

    django.setup()
    from drf_spectacular.generators import SchemaGenerator

    return SchemaGenerator().get_schema(request=None, public=True)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    schema = export_openapi()
    text = json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True)
    if argv:
        out = Path(argv[0])
        out.write_text(text + "\n", encoding="utf-8")
        ops = sorted(
            op["operationId"]
            for methods in schema["paths"].values()
            for op in methods.values()
            if isinstance(op, dict) and "operationId" in op
        )
        print(f"wrote {out} ({len(schema['paths'])} paths, {len(ops)} operations)")
        for op in ops:
            print(f"  - {op}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
