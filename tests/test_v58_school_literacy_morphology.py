"""Regression contract for the reviewed V58 school-literacy morphology wave."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.data import load_fixture, mobile_app_pack_snapshot  # noqa: E402
from cat_de_roman_esti.wordgames.contexto import _build_session  # noqa: E402
from cat_de_roman_esti.wordgames.contexto import store as contexto_store  # noqa: E402
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_TERMS,
    normalize_projection_surface,
    resolve_projection,
)
from cat_de_roman_esti.wordgames.derived_catalog import (  # noqa: E402
    DEFAULT_DERIVED_CATALOG_SHA256,
)
from cat_de_roman_esti.wordgames.lant import LantSession  # noqa: E402
from cat_de_roman_esti.wordgames.lant import store as lant_store  # noqa: E402
from cat_de_roman_esti.wordgames.service import (  # noqa: E402
    WordGameService,
    get_service,
)

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import contexto_common_words_v58_data as DATA  # noqa: E402

_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"
_LEDGER = _ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"
_REVIEW = _ROOT / "docs/reviews/v58-school-literacy-morphology/vocabulary.json"

# Whole-artifact digests bind the current generated fixture and wrappers.
_KG_SHA256 = "22e1f7345f9af8d67b9b5aafb769f6d42919c775ff577c3fc865f0d82215da38"
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_RANKINGS_SHA256 = "662c966c29be77e536cc73579c94b930ed3424dc99e4aa903c7a58a34d0f8773"
_DERIVED_SHA256 = "196b7a5f5fbf88c5de4e31762b238b9ce426d4d95329c38d675265e53626fa86"
_MOBILE_SHA256 = "49af5e2c9ed2a1ce00e7dfc511a8b3408bb7fad4e0a5a4a95e8cad8bac6fa22a"
_CANDIDATE_FUNNEL_SHA256 = (
    "efa98cc1f35cb5d009b87c01d38fabef5103ba62fae1f7b96df4ee9d81082716"
)
_RANKING_ROWS_SHA256 = "46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_NODES_WITHOUT_ALIASES_SHA256 = (
    "c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0"
)
_EDGES_SHA256 = "f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0"
_PUZZLES_SHA256 = "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_REJECTED_TARGETS = {
    "cărții": "n_v3lit_carte",
    "cărților": "n_v3lit_carte",
}
_REJECTED = set(_REJECTED_TARGETS)
_HISTORICAL_REJECTED = {
    "păturile",
    "păturilor",
    "mesei",
    "meselor",
    "părintelui",
    "părinților",
    "golfului",
    "golfurilor",
    "peștelui",
    "peștilor",
    "corpului",
    "corpurilor",
    "tabloului",
    "tablourilor",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _pretty_payload_sha256(value: object) -> str:
    payload = (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()
    return hashlib.sha256(payload).hexdigest()


def _accepted_aliases() -> dict[str, str]:
    return {
        alias: node_id
        for node_id, aliases in DATA.ALIAS_ADDITIONS.items()
        for alias in aliases
    }


def _post_contexto_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v58_review_funnel_is_exact_complete_and_collision_aware() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    candidate_aliases = candidates["aliases"]
    final = review["final"]
    accepted = _accepted_aliases()

    assert review["schema"] == "v58-school-literacy-morphology-review-v1"
    assert review["candidate_funnel_sha256"] == _CANDIDATE_FUNNEL_SHA256
    assert review["candidate_funnel_sha256"] == _canonical_sha256(candidates)
    assert len(candidate_aliases) == 50
    keys = [normalize_projection_surface(surface) for surface in candidate_aliases]
    assert len(keys) == len(set(keys)) == 50

    assert final["accepted_aliases"] == accepted
    assert len(accepted) == 48
    assert final["accepted_projections"] == {}
    assert final["deferred"] == []
    assert set(final["rejected"]) == _REJECTED
    assert set(accepted) | _REJECTED == set(candidate_aliases)
    assert review["sense_collision_evidence"] == {
        "cărții": [
            "book or written work",
            "playing card",
            "identity, work, or qualification document",
            "letter, message, or official writing",
        ],
        "cărților": [
            "books or written works",
            "playing cards",
            "identity, work, or qualification documents",
            "letters, messages, or official writings",
        ],
    }

    for reviewer in review["reviews"].values():
        dispositions = [
            set(reviewer["alias_accept"]),
            set(reviewer["alias_reject"]),
            set(reviewer["projection_accept"]),
            set(reviewer["defer"]),
            set(reviewer["reject"]),
        ]
        assert set(reviewer["alias_accept"]) == set(accepted)
        assert set(reviewer["alias_reject"]) == _REJECTED
        assert set().union(*dispositions) == set(candidate_aliases)
        assert sum(map(len, dispositions)) == 50

    assert len(review["lexical_sources"]) == 25
    assert len(set(review["lexical_sources"])) == 25
    assert all(
        url.startswith("https://dexonline.ro/definitie/")
        for url in review["lexical_sources"]
    )
    assert review["result"] == {
        "accepted_alias_surfaces": 48,
        "accepted_projection_surfaces": 0,
        "deferred_surfaces": 0,
        "rejected_surfaces": 2,
        "new_nodes": 0,
        "new_edges": 0,
        "new_game_records": 0,
    }


def test_v58_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = _accepted_aliases()

    assert DATA.BUILD_VERSION == "fixture-v58-school-literacy-morphology"
    assert len(DATA.ALIAS_ADDITIONS) == 24
    assert len(aliases) == 48
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    assert svc.resolve("paginilor") == "n_v4lit_pagina"
    assert all(svc.resolve(surface) is None for surface in _REJECTED)
    assert all(resolve_projection(surface) is None for surface in set(aliases) | _REJECTED)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == "fixture-v59-human-anatomy-morphology"
    assert fixture["meta"]["counts"]["nodes"] == 2364
    assert fixture["meta"]["counts"]["edges"] == 9217
    assert fixture["meta"]["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 7874


def test_v58_aliases_play_in_contexto_and_only_on_existing_legal_lant_hops() -> None:
    client = Client()
    svc = get_service()
    lant_targets: set[str] = set()

    for alias, target in _accepted_aliases().items():
        contexto_id = contexto_store.create(_build_session(target, "normal", None))
        contexto = _post_contexto_guess(client, contexto_id, alias)
        assert contexto["ok"] is True
        assert contexto["won"] is True
        assert contexto["guess"]["id"] == target

        starts = [
            node_id
            for node_id in svc.predecessor_ids(target)
            if svc.link(node_id, target) is not None
        ]
        if not starts or target in lant_targets:
            continue
        start = starts[0]
        lant_targets.add(target)
        lant_id = lant_store.create(
            LantSession(start=start, target=target, optimal=1, chain=[start])
        )
        lant = client.post(
            f"/api/wordgames/lant/games/{lant_id}/move",
            {"text": alias},
            content_type="application/json",
        ).json()
        assert lant["ok"] is True
        assert lant["won"] is True
        assert lant["current"]["id"] == target

    assert lant_targets == set(_accepted_aliases().values())


def test_v58_rejected_polysemes_stay_out_of_typed_games() -> None:
    client = Client()
    svc = get_service()
    for surface, target in sorted(_REJECTED_TARGETS.items()):
        assert svc.resolve(surface) is None
        assert resolve_projection(surface) is None
        assert svc.resolve_fuzzy(surface) is None
        game_id = contexto_store.create(_build_session(target, "normal", None))
        body = _post_contexto_guess(client, game_id, surface)
        assert body["ok"] is False
        assert body["attempts"] == 0
        assert "target" not in body

    for surface in _HISTORICAL_REJECTED:
        assert svc.resolve(surface) is None
        assert resolve_projection(surface) is None
        assert svc.resolve_fuzzy(surface) is None


def test_v58_preserves_projection_topology_pack_and_frozen_board_payloads() -> None:
    fixture = _json(_PACKAGE_KG)
    rankings = _json(_PACKAGE_RANKINGS)
    derived = _json(_PACKAGE_DERIVED)
    nodes_without_aliases = [
        {key: value for key, value in node.items() if key != "aliases"}
        for node in fixture["kg_nodes"]
    ]

    assert len(PROJECTION_TERMS) == 473
    assert len({term.domain for term in PROJECTION_TERMS}) == 26
    assert _sha256(_PACKAGE_KG) == _KG_SHA256
    assert _sha256(_PACKAGE_PACK) == _PACK_SHA256
    assert _sha256(_PACKAGE_RANKINGS) == _RANKINGS_SHA256
    assert _sha256(_PACKAGE_DERIVED) == _DERIVED_SHA256
    assert DEFAULT_DERIVED_CATALOG_SHA256 == _DERIVED_SHA256
    assert _PACKAGE_PACK.read_bytes() == _TEST_PACK.read_bytes()
    assert _PACKAGE_RANKINGS.read_bytes() == _TEST_RANKINGS.read_bytes()
    assert _PACKAGE_DERIVED.read_bytes() == _TEST_DERIVED.read_bytes()

    assert _canonical_sha256(nodes_without_aliases) == _NODES_WITHOUT_ALIASES_SHA256
    assert _canonical_sha256(fixture["kg_edges"]) == _EDGES_SHA256
    assert _canonical_sha256(fixture["kg_puzzles"]) == _PUZZLES_SHA256
    assert _pretty_payload_sha256(rankings["boards"]) == _RANKING_ROWS_SHA256
    assert _pretty_payload_sha256(derived["boards"]) == _FROZEN_BOARDS_SHA256
    assert rankings["meta"]["kg_sha256"] == _KG_SHA256
    assert derived["meta"]["kg_sha256"] == _KG_SHA256
    assert derived["meta"]["v37_rankings_sha256"] == _RANKINGS_SHA256
    assert contexto_store._ttl == lant_store._ttl == 7200
    assert contexto_store._max == lant_store._max == 1000


def test_v58_mobile_contract_and_v49_ledger_persist_exactly() -> None:
    checked_in = _json(_MOBILE_CONTRACT)
    ledger = _json(_LEDGER)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _sha256(_MOBILE_CONTRACT) == _MOBILE_SHA256
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == (
        "fixture-v59-human-anatomy-morphology"
    )
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2364,
        "edges": 9217,
        "puzzles": 180,
    }

    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert ledger["meta"]["count"] == len(ledger["items"]) == 104
