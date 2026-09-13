#!/usr/bin/env python3
"""Verify exact quick-game additions through natural selection and real API play."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cat_de_roman_esti.web.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import intrusul as I  # noqa: E402
from cat_de_roman_esti.wordgames import perechi as P  # noqa: E402
from cat_de_roman_esti.wordgames import quick_catalog as Q  # noqa: E402
from cat_de_roman_esti.wordgames.derived_catalog import (  # noqa: E402
    DerivedCatalog,
    load_derived_catalog,
)
from scripts.build_quick_content_v92 import file_sha, runtime_source_hashes  # noqa: E402


def all_strings(value) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(all_strings(v) for v in value.values())) if value else set()
    if isinstance(value, (list, tuple)):
        return set().union(*(all_strings(v) for v in value)) if value else set()
    return set()


def audit(path: Path) -> dict:
    raw = json.loads(path.read_bytes())
    base = load_derived_catalog()
    additions = Q.validate_catalog(raw, base)
    combined = DerivedCatalog([*base._boards, *additions])
    seeds: dict[str, int] = {}
    for game, category in sorted({(b.game, b.category) for b in additions}):
        needed = {b._catalog_id for b in additions if b.game == game and b.category == category}
        for seed in range(5000):
            selected = combined.pick_seeded(game, random.Random(seed), category=category)
            if selected and selected._catalog_id in needed:
                seeds[selected._catalog_id] = seed
                needed.remove(selected._catalog_id)
            if not needed:
                break
        assert not needed, (game, category, needed)
    results = []
    for board in additions:
        game = board.game
        module = I if game == "intrusul" else P
        url = f"/api/wordgames/{game}/games"
        client = Client()
        gid = None
        with patch.object(module, "_catalog_or_503", return_value=combined):
            try:
                response = client.post(
                    f"{url}?seed={seeds[board._catalog_id]}&category={board.category}",
                )
                assert response.status_code == 200, response.content
                state = response.json()
                gid = state["game_id"]
                session = module.store.get(gid)
                assert session.catalog_id == board._catalog_id
                secrets = {board._source_id, board._catalog_id}
                assert not secrets & all_strings(state)
                assert "solution" not in state and "score" not in state
                assert client.get(f"{url}/{gid}").status_code == 200
                if game == "intrusul":
                    assert board.payload["group_label"] not in all_strings(state)
                    result = client.post(f"{url}/{gid}/guess", {"id": board.payload["intruder"]},
                                         content_type="application/json")
                    assert result.status_code == 200
                    state = result.json()
                else:
                    hidden = {p["group_label"] for p in board.payload["pairs"]}
                    assert not hidden & all_strings(state)
                    for pair in board.payload["pairs"]:
                        result = client.post(f"{url}/{gid}/match", {"ids": list(pair["members"])},
                                             content_type="application/json")
                        assert result.status_code == 200
                        state = result.json()
                        hidden.discard(pair["group_label"])
                        assert not hidden & all_strings(state)
                assert state["won"] and state["score"] == 1000
                assert not secrets & all_strings(state)
                fetched = client.get(f"{url}/{gid}").json()
                assert fetched["won"] and fetched["score"] == 1000
                results.append({"id": board._catalog_id, "game": game,
                                "source_id": board._source_id, "category": board.category,
                                "public_seed": seeds[board._catalog_id],
                                "score": state["score"], "hidden_answers_preserved": True,
                                "terminal_get_preserved": True})
            finally:
                if gid:
                    module.store.delete(gid)
    return {"kind": "quick-content-live-audit-v1", "passed": True,
            "catalog_sha256": file_sha(path), "candidate_sha256": raw["candidate_sha256"],
            "bindings": Q.bindings(live=True), "runtime_sources": runtime_source_hashes(),
            "base_counts": base.counts(), "added_counts": DerivedCatalog(additions).counts(),
            "combined_counts": combined.counts(), "replays": results,
            "core_boards_preserved": all(b in combined._boards for b in base._boards)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(Q.json_bytes(result))
    print(json.dumps({"added": result["added_counts"], "total": result["combined_counts"],
                      "replayed": len(result["replays"])}))


if __name__ == "__main__":
    main()
