"""Alias layer (ADR-0012): exact alternate surface forms resolving to canonical nodes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames.service import WordGameService

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _service(nodes: list[dict], edges: list[dict]) -> WordGameService:
    return WordGameService(graph=Graph.from_records(nodes, edges))


NODES = [
    {"id": "n_sarmale", "label_ro": "Sarmale", "category": "gastronomie",
     "aliases": ["sarmalele", "sarma", "sarmalute"]},
    {"id": "n_masina", "label_ro": "Mașină", "category": "societate",
     "aliases": ["automobil", "autoturism"]},
    # A node whose alias collides with another node's LABEL: the label must win.
    {"id": "n_rival", "label_ro": "Automobilul Dacia", "category": "societate",
     "aliases": ["mașină"]},
]
EDGES = [
    {"id": "e1", "src_id": "n_sarmale", "dst_id": "n_masina", "relation": "related_to",
     "label_ro": "", "strength": 0.5, "is_distractor": 0, "bidirectional": 1},
]


def test_alias_resolves_to_canonical_node():
    svc = _service(NODES, EDGES)
    assert svc.resolve("sarmalele") == "n_sarmale"
    assert svc.resolve("  SARMA ") == "n_sarmale"
    assert svc.resolve("sărmăluțe".replace("ă", "a")) == "n_sarmale"
    assert svc.resolve("automobil") == "n_masina"


def test_labels_always_win_over_aliases():
    svc = _service(NODES, EDGES)
    # "mașină" is n_masina's LABEL and n_rival's alias — the label owns the key.
    assert svc.resolve("masina") == "n_masina"
    assert svc.resolve("Mașină") == "n_masina"


def test_bundled_fixture_aliases_are_indexed():
    """Once the fixture ships aliases, every one of them must resolve."""
    from cat_de_roman_esti.wordgames.service import get_service

    svc = get_service()
    missing = [
        (node.id, alias)
        for node in svc.graph.nodes.values()
        for alias in node.aliases
        if svc.resolve(alias) is None
    ]
    assert missing == []


def test_validator_flags_alias_collisions_and_long_labels(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "validate_fixture", _REPO_ROOT / "scripts" / "validate_fixture.py"
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    base = json.loads(
        (_REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "kg_sample.json").read_text(
            encoding="utf-8"
        )
    )
    # Poison: alias colliding with another node's label; a redundant self-alias;
    # an over-long concept label; an over-long alias.
    n0, n1 = base["kg_nodes"][0], base["kg_nodes"][1]
    n0["aliases"] = [n1["label_ro"], n0["label_ro"], "unu doi trei patru cinci sase"]
    poisoned = tmp_path / "poisoned.json"
    poisoned.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")

    errors = validator.validate(poisoned)
    classes = {e.split(":", 1)[0] for e in errors}
    assert "alias_unique" in classes
    assert "label_style" in classes
