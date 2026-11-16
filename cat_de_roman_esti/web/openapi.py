"""Add the shared round counters to the existing operation IDs."""

from __future__ import annotations

ROUND_GAMES = ("alchimie", "conexiuni", "contexto", "intrusul", "lant", "perechi")


def document_round_counters(result, **_kwargs):
    """Document public hints without listing private board fields as response properties."""
    for path, operations in result["paths"].items():
        for game in ROUND_GAMES:
            if not path.startswith(f"/api/wordgames/{game}/games"):
                continue
            for operation in operations.values():
                response = operation.get("responses", {}).get("200")
                if response is None:
                    continue
                properties = {
                    "steps": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Cumulative steps in this round.",
                    },
                    "hints_left": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 2 if game == "intrusul" else 3,
                        "description": "Remaining available rungs.",
                    },
                    "hint_level": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 2 if game == "intrusul" else 3,
                        "description": "Highest rung used, or zero before the first hint.",
                    },
                    "score": {"type": "integer", "description": "Legacy account score."},
                }
                if game != "contexto":
                    properties["perfect"] = {
                        "type": "boolean",
                        "description": "A win with zero steps.",
                    }
                response["content"] = {
                    "application/json": {
                        "schema": {"type": "object", "properties": properties, "additionalProperties": True}
                    }
                }
            break
    return result
