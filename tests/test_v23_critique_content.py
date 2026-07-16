"""Regression guards for the critique-informed childhood wave (ADR-0030)."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PACK = json.loads((_ROOT / "tests/fixtures/games_pack.json").read_text(encoding="utf-8"))
_KG = json.loads((_ROOT / "tests/fixtures/kg_sample.json").read_text(encoding="utf-8"))

_ITEM_IDS = {
    "cx_viata_de_roman_291",
    "ct_literatura_298",
    "ct_viata_de_roman_299",
    "lt_literatura_210",
    "lt_viata_de_roman_211",
    "al_literatura_097",
    "al_viata_de_roman_098",
}

_NODE_IDS = {
    "n_v23via_elasticul",
    "n_v23via_tara_tara_vrem_ostasi",
    "n_v23via_ratele_si_vinatorii",
    "n_v23via_telefonul_fara_fir",
    "n_v23via_nu_te_supara_frate",
    "n_v23via_piticot",
    "n_v23via_moara_joc",
    "n_v23via_pacalicii",
    "n_v23via_abecedar",
    "n_v23via_ghiozdan",
    "n_v23via_penar",
    "n_v23via_tabla_scolara",
    "n_v23lit_capra_cu_trei_iezi",
    "n_v23lit_punguta_cu_doi_bani",
    "n_v23lit_ursul_pacalit_de_vulpe",
    "n_v23lit_povestea_porcului",
    "n_v23lit_praslea_cel_voinic",
    "n_v23lit_tinerete_fara_batranete",
    "n_v23lit_greuceanu",
    "n_v23lit_ileana_cosanzeana",
    "n_v23lit_zmeul",
    "n_v23lit_fat_frumos",
}


def test_v23_items_remain_pending_until_the_bound_judge_gate():
    records = {
        item["id"]: item
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for item in _PACK[game]
        if item["id"] in _ITEM_IDS
    }

    assert set(records) == _ITEM_IDS
    assert {item["status"] for item in records.values()} == {"pending"}
    assert records["lt_literatura_210"]["optimal"] == 2
    assert records["lt_viata_de_roman_211"]["optimal"] == 2
    assert records["al_literatura_097"]["target_depth"] == 2
    assert records["al_viata_de_roman_098"]["target_depth"] == 3


def test_v23_graph_wave_has_the_reviewed_size_and_no_duplicate_moara_node():
    nodes = {node["id"]: node for node in _KG["kg_nodes"]}
    edges = [
        edge
        for edge in _KG["kg_edges"]
        if edge["src_id"] in _NODE_IDS or edge["dst_id"] in _NODE_IDS
    ]

    assert _NODE_IDS <= set(nodes)
    assert len(_NODE_IDS) == 22
    assert len(edges) == 78
    assert nodes["n_v23via_moara_joc"]["aliases"] == ["Țintar", "jocul de moară", "moara"]
    assert not any(node["label_ro"] == "Țintar" for node in _KG["kg_nodes"])


def test_v23_conexiuni_groups_are_unique_and_type_coherent():
    board = next(item for item in _PACK["conexiuni"] if item["id"] == "cx_viata_de_roman_291")
    nodes = {node["id"]: node for node in _KG["kg_nodes"]}
    tiles = [node_id for group in board["groups"].values() for node_id in group]

    assert len(tiles) == len(set(tiles)) == 16
    assert all(
        len({nodes[node_id]["node_type"] for node_id in group}) == 1
        for group in board["groups"].values()
    )
