"""Regression contract for the reviewed V70 social-and-civic-life wave."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from collections import Counter
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

import contexto_common_words_v70_data as DATA  # noqa: E402

# V69 changes selection/ranking but has no vocabulary data module.
_HISTORICAL_ALIAS_MODULES = tuple(
    importlib.import_module(f"contexto_common_words_v{version}_data") for version in range(51, 69)
)

_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"
_PACKAGE_RESERVE = _ROOT / "cat_de_roman_esti/fixtures/contexto_impact_reserve_v69.json"
_TEST_RESERVE = _ROOT / "tests/fixtures/contexto_impact_reserve_v69.json"
_LEDGER = _ROOT / "cat_de_roman_esti/fixtures/lant_rejection_tombstones.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"
_REVIEW = _ROOT / "docs/reviews/v70-social-and-civic-life-morphology/vocabulary.json"

# Exact V69 baselines. The V70 transaction must move the alias-bearing artifacts only.
_V69_KG_SHA256 = "ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128"
_V69_RANKINGS_SHA256 = "c32b648885cf9d0aad718bda9c1dcbd86f49ddda6819ceb14a7c372e32ddb424"
_V69_DERIVED_SHA256 = "9199f60c41d334f620403ca68926790b57292d71761175a470ba7385af52da91"
_V69_MOBILE_SHA256 = "1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae"

# Exact V70 historical pins remain fixed after the V71 transaction.
_V70_KG_SHA256 = "76fc1f933000f56c0c0d46588f61eeb9c9e03af5608c950a3884550e5a3108b0"
_V70_RANKINGS_SHA256 = "3f90dc5162a2931967eef7a63c50707eb9e9a0f060684337f5638cfc4fe287fc"
_V70_DERIVED_SHA256 = "7aa1596ca6dd55451c5e8da6b99a5852e319742f1893dd630c0c22795255b5a1"
_V70_MOBILE_SHA256 = "c0f49ed6c084ecff0a76d24fb4153a25cd3b32e333ab4794a8a11140a343ee6d"

# Current V71 wrapper pins; V70's review and source assertions remain historical.
_CURRENT_BUILD_VERSION = "fixture-v71-literature-and-storytelling-morphology"
_KG_SHA256 = "9134f057be13538cf9c4f48b50d41e06a1e6bfb36f26a5cb59cd925f9b900640"
_RANKINGS_SHA256 = "f9c114570006938ec6602e9318e49a145bedd378be16120cacb4b6c9a2107a51"
_DERIVED_SHA256 = "37ddf1a45ad04eeaf115589112269bc6cf3a2e19e61576a15c0acc426d168662"
_MOBILE_SHA256 = "a627e1234e88ccd174369ec19e58d912faaf526025c3955305c6c6c79ae2595e"

# Immutable payload pins must not move during this alias-only wave.
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_CANDIDATE_FUNNEL_SHA256 = "254b4a6f9211f1f7f43e4dc3e44d36ce5c01d9d07e4aca3a7702705574408793"
_ACCEPTED_MAP_SHA256 = "4b4c1bac2346eafd084f0305dd02d10c5fe9d8afd4f5bc8a2a8ff3ba6c59b9b6"
_RANKING_ROWS_SHA256 = "faf7b1a5224b082619641de3565f2131e2ca425b41258cdd4df0b57e9cda7031"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_NODES_WITHOUT_ALIASES_SHA256 = "c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0"
_EDGES_SHA256 = "f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0"
_PUZZLES_SHA256 = "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
_RESERVE_SHA256 = "4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_REJECTED_TARGETS = {
    "legii": "n_v3soc_lege",
    "legilor": "n_v3soc_lege",
    "băncii": "n_v4soc_banca",
    "băncilor": "n_v4soc_banca",
}
_REJECTED = set(_REJECTED_TARGETS)


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
        alias: node_id for node_id, aliases in DATA.ALIAS_ADDITIONS.items() for alias in aliases
    }


def _historical_accepted_aliases() -> dict[str, str]:
    bindings = [
        (alias, node_id)
        for module in _HISTORICAL_ALIAS_MODULES
        for node_id, aliases in module.ALIAS_ADDITIONS.items()
        for alias in aliases
    ]
    assert len(bindings) == 846
    assert len({alias for alias, _node_id in bindings}) == 846
    return dict(bindings)


def _post_contexto_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v70_review_funnel_is_exact_complete_and_unanimous() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    candidate_aliases = candidates["aliases"]
    final = review["final"]
    accepted = _accepted_aliases()

    assert review["schema"] == "v70-social-and-civic-life-morphology-review-v1"
    assert review["baseline"] == {
        "kg_nodes": 2364,
        "kg_edges": 9217,
        "kg_puzzles": 180,
        "kg_aliases": 8306,
        "contexto_projection_terms": 473,
        "contexto_projection_domains": 26,
        "beginner_benchmark_total": 324,
        "beginner_benchmark_eligible": 322,
        "beginner_benchmark_eligible_resolved": 322,
    }
    assert review["candidate_funnel_sha256"] == _CANDIDATE_FUNNEL_SHA256
    assert review["candidate_funnel_sha256"] == _canonical_sha256(candidates)
    assert len(candidate_aliases) == 50
    keys = [normalize_projection_surface(surface) for surface in candidate_aliases]
    assert len(keys) == len(set(keys)) == 50
    assert Counter(candidate_aliases.values()) == Counter(
        {node_id: 2 for node_id in set(candidate_aliases.values())}
    )
    assert len(set(candidate_aliases.values())) == 25

    assert final["accepted_aliases"] == accepted
    assert _canonical_sha256(accepted) == _ACCEPTED_MAP_SHA256
    assert len(accepted) == 46
    assert len(set(accepted.values())) == 23
    assert all(count == 2 for count in Counter(accepted.values()).values())
    assert final["accepted_projections"] == {}
    assert final["deferred"] == []
    assert set(final["rejected"]) == _REJECTED
    assert set(accepted) | _REJECTED == set(candidate_aliases)

    for reviewer in review["reviews"].values():
        assert reviewer["status"] == "complete"
        assert reviewer["accepted_aliases_sha256"] == _ACCEPTED_MAP_SHA256
        assert set(reviewer["alias_accept"]) == set(accepted)
        assert set(reviewer["alias_reject"]) == _REJECTED
        assert reviewer["projection_accept"] == []
        assert reviewer["defer"] == []
        assert reviewer["reject"] == []


def test_v70_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = _accepted_aliases()
    historical_aliases = _historical_accepted_aliases()

    assert DATA.BUILD_VERSION == "fixture-v70-social-and-civic-life-morphology"
    assert len(DATA.ALIAS_ADDITIONS) == 23
    assert all(len(forms) == 2 for forms in DATA.ALIAS_ADDITIONS.values())
    assert len(aliases) == 46
    assert set(aliases).isdisjoint(historical_aliases)
    assert set(DATA.BLOCKED_ALIAS_FORMS) == _REJECTED
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    assert all(svc.resolve_fuzzy(surface) == node_id for surface, node_id in aliases.items())
    assert all(svc.resolve(surface) == node_id for surface, node_id in historical_aliases.items())
    owners = set(aliases.values())
    assert all(svc.node(node_id).node_type == "concept" for node_id in owners)
    assert all(svc.node(node_id).category == "societate" for node_id in owners)
    assert all(
        4
        <= sum(
            svc.link(predecessor_id, node_id) is not None
            for predecessor_id in svc.predecessor_ids(node_id)
        )
        <= 28
        for node_id in owners
    )
    assert svc.resolve("apartamentelor") == "n_v4soc_apartament"
    assert svc.resolve("bucuriilor") == "n_v24_feeling_joy_bucurie"
    assert svc.resolve("partidelor politice") == "n_v3soc_partid_politic"
    assert svc.resolve("prefecților") == "n_v20soc_prefect"
    assert svc.resolve("diasporelor") == "n_v11soc_diaspora"
    assert all(svc.resolve(surface) is None for surface in _REJECTED)
    assert all(resolve_projection(surface) is None for surface in set(aliases) | _REJECTED)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == _CURRENT_BUILD_VERSION
    assert fixture["meta"]["counts"]["nodes"] == 2364
    assert fixture["meta"]["counts"]["edges"] == 9217
    assert fixture["meta"]["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 8400


def test_v70_aliases_play_in_contexto_and_only_on_existing_legal_lant_hops() -> None:
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
        if target in lant_targets:
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


def test_v70_nonaccepted_surfaces_stay_out_of_typed_games() -> None:
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

    assert len(DATA.BASE_DEFERRED_AMBIGUOUS_TERMS) == 64
    assert len(DATA.DEFERRED_AMBIGUOUS_TERMS) == 68
    assert len(set(DATA.DEFERRED_AMBIGUOUS_TERMS)) == 68


def test_v70_preserves_v69_selection_projection_topology_and_frozen_payloads() -> None:
    fixture = _json(_PACKAGE_KG)
    rankings = _json(_PACKAGE_RANKINGS)
    derived = _json(_PACKAGE_DERIVED)
    reserve = _json(_PACKAGE_RESERVE)
    nodes_without_aliases = [
        {key: value for key, value in node.items() if key != "aliases"}
        for node in fixture["kg_nodes"]
    ]

    assert len(PROJECTION_TERMS) == 473
    assert len({term.domain for term in PROJECTION_TERMS}) == 26
    assert _sha256(_PACKAGE_KG) == _KG_SHA256
    assert _KG_SHA256 != _V70_KG_SHA256 != _V69_KG_SHA256
    assert _sha256(_PACKAGE_PACK) == _PACK_SHA256
    assert _sha256(_PACKAGE_RANKINGS) == _RANKINGS_SHA256
    assert _RANKINGS_SHA256 != _V70_RANKINGS_SHA256 != _V69_RANKINGS_SHA256
    assert _sha256(_PACKAGE_DERIVED) == _DERIVED_SHA256
    assert _DERIVED_SHA256 != _V70_DERIVED_SHA256 != _V69_DERIVED_SHA256
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
    assert _PACKAGE_RESERVE.read_bytes() == _TEST_RESERVE.read_bytes()
    assert _sha256(_PACKAGE_RESERVE) == _RESERVE_SHA256
    assert reserve["meta"]["count"] == len(reserve["ids"]) == 1
    assert reserve["ids"] == ["ct_muzica_163"]
    assert contexto_store._ttl == lant_store._ttl == 7200
    assert contexto_store._max == lant_store._max == 1000


def test_v70_mobile_contract_and_v49_ledger_persist_exactly() -> None:
    checked_in = _json(_MOBILE_CONTRACT)
    ledger = _json(_LEDGER)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _sha256(_MOBILE_CONTRACT) == _MOBILE_SHA256
    assert _MOBILE_SHA256 != _V70_MOBILE_SHA256 != _V69_MOBILE_SHA256
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == _CURRENT_BUILD_VERSION
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2364,
        "edges": 9217,
        "puzzles": 180,
    }

    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert ledger["meta"]["count"] == len(ledger["items"]) == 104
