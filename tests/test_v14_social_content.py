"""Regression guards for the v14 broad-audience Romanian content pass (ADR-0019)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PACK_PATH = _ROOT / "tests" / "fixtures" / "games_pack.json"
_KG_PATH = _ROOT / "tests" / "fixtures" / "kg_sample.json"

# v16 (2026-07-12): KG-enrichment re-derivation retired one approved greu Lanț board, a
# judge fleet promoted 70 pending items / rejected 3, and the ADR-0019 quarantine below
# was reasserted (editorial pending status, regardless of factual quality).
# v18 (2026-07-13): the pop-culture enrichment retired one more approved normal Lanț board
# (lt_viata_de_roman_164 — new shortcuts pulled its optimal below its band).
# v20 (2026-07-13): the duplicate-concept cleanup retired al_sport_082 (approved usor
# Alchimie — its target became one-action craftable after the sports-final merge), and the
# v20 content import retired lt_istorie_115 + lt_stiinta_162 (optimal below band).
# 2026-07-15 (ADR-0023/0024): the first owner-approved critique-gate demotion batch moved
# 18 conexiuni boards + 2 contexto targets from approved to pending (player-reported
# fairness/relevance failures + A7 non-distinctive region associations); nothing deleted.
# 2026-07-16 (ADR-0030): the v23 childhood wave staged seven more items as pending;
# approved inventory and serving remain unchanged.
_EXPECTED_INVENTORY = {
    "conexiuni": (284, 209, 75),
    "contexto": (199, 192, 7),
    "lant": (193, 94, 99),
    "alchimie": (92, 77, 15),
}

_NEW_CONTEXTO_TARGETS = {
    "ct_societate_290": "n_v11soc_diaspora",
    "ct_societate_291": "n_minoritati_nationale",
    "ct_societate_292": "n_avocatul_poporului",
    "ct_societate_293": "n_v3soc_protest",
    "ct_societate_294": "n_v3soc_mass_media",
    "ct_stiinta_295": "n_v3sti_vaccin",
    "ct_societate_296": "n_v3soc_scoala",
    "ct_meme_net_297": "n_v4mem_internet",
}

_QUARANTINED_CONEXIUNI = {
    "cx_sport_281",
    "cx_muzica_274",
    "cx_film_tv_010",
    "cx_film_tv_246",
    "cx_film_tv_098",
    "cx_geografie_001",
    "cx_literatura_129",
    "cx_muzica_056",
    "cx_sport_071",
    "cx_film_tv_015",
    "cx_film_tv_164",
    "cx_meme_net_268",
    "cx_gastronomie_172",
    "cx_stiinta_230",
    "cx_istorie_185",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _by_id(records: list[dict]) -> dict[str, dict]:
    return {record["id"]: record for record in records}


def test_v14_pack_inventory_and_review_split():
    pack = _load(_PACK_PATH)

    assert pack["meta"]["counts"] == {
        game: expected[0] for game, expected in _EXPECTED_INVENTORY.items()
    }
    for game, (total, approved, pending) in _EXPECTED_INVENTORY.items():
        records = pack[game]
        assert len(records) == total
        assert Counter(record["status"] for record in records) == {
            "approved": approved,
            "pending": pending,
        }

    # v16: 769 − 3 judge-rejected − 1 retired greu Lanț = 765; v18: − 1 retired normal Lanț.
    # 2026-07-15: 592 − 20 critique-gate demotions (ADR-0023/0024) = 572 approved.
    assert sum(expected[0] for expected in _EXPECTED_INVENTORY.values()) == 768
    assert sum(expected[1] for expected in _EXPECTED_INVENTORY.values()) == 572
    assert sum(expected[2] for expected in _EXPECTED_INVENTORY.values()) == 196


def test_v14_adds_contemporary_civic_education_science_and_digital_play():
    pack = _load(_PACK_PATH)
    conexiuni = _by_id(pack["conexiuni"])
    contexto = _by_id(pack["contexto"])

    board = conexiuni["cx_societate_290"]
    assert board["status"] == "approved"
    assert board["category"] == "societate"
    assert board["groups"] == {
        "g1": ["n_v2soc_alegeri", "n_v3soc_protest", "n_societatea_civila", "n_vot"],
        "g2": ["n_v4soc_elev", "n_v4soc_student", "n_v3soc_scoala", "n_v2soc_universitate"],
        "g3": [
            "n_stix_ion_cantacuzino",
            "n_microbiologie",
            "n_v3sti_vaccin",
            "n_v2sti_bacterie",
        ],
        "g4": [
            "n_v2mem_feed_online",
            "n_v3mem_hashtag",
            "n_v3mem_repost",
            "n_v3mem_scroll_infinit",
        ],
    }
    assert board["group_labels"] == {
        "g1": "Participare civică",
        "g2": "De la școală la facultate",
        "g3": "Sănătate publică și microbiologie",
        "g4": "În feed, la nesfârșit",
    }
    assert len(board["order"]) == len(set(board["order"])) == 16
    assert set(board["order"]) == {
        node_id for group in board["groups"].values() for node_id in group
    }

    for item_id, target in _NEW_CONTEXTO_TARGETS.items():
        assert contexto[item_id]["target"] == target
        assert contexto[item_id]["status"] == "approved"


def test_v14_quarantined_content_is_not_in_approved_pools():
    pack = _load(_PACK_PATH)
    conexiuni = _by_id(pack["conexiuni"])
    contexto = _by_id(pack["contexto"])

    quarantined = {
        item_id
        for item_id in _QUARANTINED_CONEXIUNI
        if conexiuni[item_id]["status"] == "pending"
    }
    assert quarantined == _QUARANTINED_CONEXIUNI
    assert contexto["ct_meme_net_238"]["status"] == "pending"

    approved_conexiuni = {
        record["id"] for record in pack["conexiuni"] if record["status"] == "approved"
    }
    approved_contexto = {
        record["id"] for record in pack["contexto"] if record["status"] == "approved"
    }
    assert _QUARANTINED_CONEXIUNI.isdisjoint(approved_conexiuni)
    assert "ct_meme_net_238" not in approved_contexto


def test_v14_uses_neutral_everyday_labels_and_descriptions():
    nodes = _by_id(_load(_KG_PATH)["kg_nodes"])

    everyday = nodes["n_vdr_viata_de_roman"]
    assert everyday["label_ro"] == "Viața în România"
    assert everyday["description"] == (
        "Umbrela de obiceiuri, reflexe și amintiri cotidiene recognoscibile în România."
    )
    assert "Viața de român" in everyday["aliases"]

    resourcefulness = nodes["n_vdr_descurcare_romaneasca"]
    assert resourcefulness["label_ro"] == "Descurcăreala de zi cu zi"
    assert resourcefulness["description"] == (
        "Capacitatea de a găsi soluții practice și improvizate când timpul sau "
        "resursele sunt limitate."
    )
    assert "Descurcăreala românească" in resourcefulness["aliases"]
