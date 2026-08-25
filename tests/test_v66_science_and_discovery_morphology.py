"""Regression contract for the reviewed V66 science-and-discovery wave."""

from __future__ import annotations

import hashlib
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

import contexto_common_words_v66_data as DATA  # noqa: E402

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
_REVIEW = _ROOT / "docs/reviews/v66-science-and-discovery-morphology/vocabulary.json"

# Current V68 whole-artifact pins; the immutable payload pins below must not move.
_KG_SHA256 = "ed247c0fbb426781c05dd81a6d38de3e3a8d5b702b558f6fd6ff9a4e565a4128"
_RANKINGS_SHA256 = "b521d5d698a036aa81589ba059d7c04d731dbd69a2bf1a2f6b627e881a19bfe6"
_DERIVED_SHA256 = "e7acd141a357409559a93f68514b977dbd697e19a97939afa9bb200d9d70dc97"
_MOBILE_SHA256 = "1a9f0c5182630a1cc6fe89c28546884d5f61d6781ff374da8fc003691df70cae"

# Immutable payload pins must not move during this alias-only wave.
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_CANDIDATE_FUNNEL_SHA256 = (
    "9604f43ea173fac3051b5114e464c91b0acde4a9b3fefddb760f6ca5430c4100"
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
    "curentului": "n_v3sti_electricitate",
    "curenților": "n_v3sti_electricitate",
}
_REJECTED = set(_REJECTED_TARGETS)
_V51_DEFERRED = {
    "amicii",
    "arborele",
    "arbori",
    "arborii",
    "arborelui",
    "arborilor",
    "cuptor",
}
_V51_REJECTED = {"fișă", "elan", "priză multiplă"}
_V51_UNAUTHORED = {"Wi-Fi", "wifi", "email"}
_HISTORICAL_WAVE_BLOCKS = {
    # V52 through V65 rejected polysemes.
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
    "cărții",
    "cărților",
    "creierului",
    "creierelor",
    "fileului",
    "fileurilor",
    "cheii",
    "cheilor",
    "portului",
    "porturilor",
    "rolului",
    "rolurilor",
    "frontului",
    "fronturilor",
    "notei",
    "notelor",
}
_HISTORICAL_NONACCEPTED = (
    _V51_DEFERRED
    | _V51_REJECTED
    | _V51_UNAUTHORED
    | _HISTORICAL_WAVE_BLOCKS
)


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


def test_v66_review_funnel_is_exact_complete_and_collision_aware() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    candidate_aliases = candidates["aliases"]
    final = review["final"]
    accepted = _accepted_aliases()

    assert review["schema"] == "v66-science-and-discovery-morphology-review-v1"
    assert review["baseline"] == {
        "kg_nodes": 2364,
        "kg_edges": 9217,
        "kg_puzzles": 180,
        "kg_aliases": 8162,
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
    assert len(accepted) == 48
    assert len(set(accepted.values())) == 24
    assert all(count == 2 for count in Counter(accepted.values()).values())
    assert final["accepted_projections"] == {}
    assert final["deferred"] == []
    assert set(final["rejected"]) == _REJECTED
    assert set(accepted) | _REJECTED == set(candidate_aliases)
    collision_evidence = [
        "moving current or draft of air",
        "flowing current of water, including a marine or ocean current",
        "electric current in a circuit",
    ]
    assert review["sense_collision_evidence"] == {
        "curentului": collision_evidence,
        "curenților": collision_evidence,
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


def test_v66_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = _accepted_aliases()

    assert DATA.BUILD_VERSION == "fixture-v66-science-and-discovery-morphology"
    assert len(DATA.ALIAS_ADDITIONS) == 24
    assert all(len(forms) == 2 for forms in DATA.ALIAS_ADDITIONS.values())
    assert len(aliases) == 48
    assert set(DATA.BLOCKED_ALIAS_FORMS) == _REJECTED
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    assert all(
        svc.resolve_fuzzy(surface) == node_id for surface, node_id in aliases.items()
    )
    owners = set(aliases.values())
    assert all(svc.node(node_id).node_type == "concept" for node_id in owners)
    assert all(svc.node(node_id).category == "stiinta" for node_id in owners)
    assert all(
        4
        <= sum(
            svc.link(predecessor_id, node_id) is not None
            for predecessor_id in svc.predecessor_ids(node_id)
        )
        <= 33
        for node_id in owners
    )
    assert svc.resolve("științelor moderne") == "n_v2sti_stiinta"
    assert svc.resolve("microscoapelor optice") == "n_v3sti_microscop"
    assert svc.resolve("virusurilor biologice") == "n_v4sti_virus"
    assert svc.resolve("rachetelor spațiale") == "n_rachete"
    assert all(svc.resolve(surface) is None for surface in _REJECTED)
    assert all(resolve_projection(surface) is None for surface in set(aliases) | _REJECTED)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == (
        "fixture-v68-romanian-language-and-grammar-morphology"
    )
    assert fixture["meta"]["counts"]["nodes"] == 2364
    assert fixture["meta"]["counts"]["edges"] == 9217
    assert fixture["meta"]["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 8306


def test_v66_aliases_play_in_contexto_and_only_on_existing_legal_lant_hops() -> None:
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


def test_v66_nonaccepted_surfaces_stay_out_of_typed_games() -> None:
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

    assert len(_V51_DEFERRED) == 7
    assert len(_V51_REJECTED) == 3
    assert len(_V51_UNAUTHORED) == 3
    assert len(_HISTORICAL_WAVE_BLOCKS) == 30
    assert len(_HISTORICAL_NONACCEPTED) == 43
    assert len(_HISTORICAL_NONACCEPTED | _REJECTED) == 45
    for surface in _HISTORICAL_NONACCEPTED:
        assert svc.resolve(surface) is None
        assert resolve_projection(surface) is None
        assert svc.resolve_fuzzy(surface) is None


def test_v66_preserves_projection_topology_pack_and_frozen_board_payloads() -> None:
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


def test_v66_mobile_contract_and_v49_ledger_persist_exactly() -> None:
    checked_in = _json(_MOBILE_CONTRACT)
    ledger = _json(_LEDGER)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _sha256(_MOBILE_CONTRACT) == _MOBILE_SHA256
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == (
        "fixture-v68-romanian-language-and-grammar-morphology"
    )
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2364,
        "edges": 9217,
        "puzzles": 180,
    }

    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert ledger["meta"]["count"] == len(ledger["items"]) == 104
