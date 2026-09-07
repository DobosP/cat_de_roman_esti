"""Regression contract for the reviewed V72 Romanian dishes-and-pastries wave."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from tests.current_content import CURRENT_CONTENT

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.data import (  # noqa: E402
    load_fixture,
    mobile_app_pack_content_hash,
    mobile_app_pack_snapshot,
)
from cat_de_roman_esti.graph import Graph  # noqa: E402
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
    REVIEWED_FUZZY_DENY_SURFACES,
    WordGameService,
    get_service,
    normalize,
)
from tests.content_history import before_v84_fixture  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import contexto_common_words_v72_data as DATA  # noqa: E402

# V69 changes selection/ranking but has no vocabulary data module. V70–V72
# continue the alias ledger after the historical V51–V68 modules.
_HISTORICAL_ALIAS_MODULES = tuple(
    importlib.import_module(f"contexto_common_words_v{version}_data") for version in range(51, 69)
) + (
    importlib.import_module("contexto_common_words_v70_data"),
    importlib.import_module("contexto_common_words_v71_data"),
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
_REVIEW = _ROOT / "docs/reviews/v72-romanian-dishes-and-pastries-morphology/vocabulary.json"

# Exact V71 baselines. The V72 transaction must move alias-bearing artifacts only.
_V71_KG_SHA256 = "9134f057be13538cf9c4f48b50d41e06a1e6bfb36f26a5cb59cd925f9b900640"
_V71_RANKINGS_SHA256 = "f9c114570006938ec6602e9318e49a145bedd378be16120cacb4b6c9a2107a51"
_V71_DERIVED_SHA256 = "37ddf1a45ad04eeaf115589112269bc6cf3a2e19e61576a15c0acc426d168662"
_V71_MOBILE_SHA256 = "a627e1234e88ccd174369ec19e58d912faaf526025c3955305c6c6c79ae2595e"

# Current shared whole-artifact pins; the V72 alias-transaction evidence below is immutable.
_CURRENT_BUILD_VERSION = CURRENT_CONTENT.build_version
_KG_SHA256 = CURRENT_CONTENT.kg_sha256
_RANKINGS_SHA256 = CURRENT_CONTENT.rankings_sha256
_DERIVED_SHA256 = CURRENT_CONTENT.derived_sha256
_MOBILE_SHA256 = CURRENT_CONTENT.mobile_sha256

# V75 advances the served pack; V72's payload and review-evidence pins below stay immutable.
_PACK_SHA256 = CURRENT_CONTENT.pack_sha256
_CANDIDATE_FUNNEL_SHA256 = "78924a29cb235e55f0dae0f0a047ab26e8e20234eab794c6e051cc9496294e6b"
_ACCEPTED_MAP_SHA256 = "afcf6ea8956ce157f3245064415aa64183bda6bc8ce4504eaf807bfe4215ed61"
_ACCEPTED_WRAPPED_SHA256 = "61301d077cc9ac123642c519773fe5a322d32be1f89ce44ab64465c52b39475c"
_RANKING_ROWS_SHA256 = CURRENT_CONTENT.ranking_rows_sha256
_FROZEN_BOARDS_SHA256 = CURRENT_CONTENT.frozen_boards_sha256
_NODES_WITHOUT_ALIASES_SHA256 = CURRENT_CONTENT.nodes_without_aliases_sha256
_EDGES_SHA256 = CURRENT_CONTENT.edges_sha256
_PUZZLES_SHA256 = CURRENT_CONTENT.puzzles_sha256
_RESERVE_SHA256 = "4c41d092c895c61aaccfbda3cb9522c4d5767a88d9af9343efccc182f71e7612"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_INHERITED_FUZZY_DENY = {"intrigii", "intrigilor"}


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
    assert len(bindings) == 940
    assert len({alias for alias, _node_id in bindings}) == 940
    return dict(bindings)


def _post_contexto_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v72_review_funnel_is_exact_complete_and_unanimous() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    candidate_aliases = candidates["aliases"]
    final = review["final"]
    accepted = _accepted_aliases()

    assert review["schema"] == "v72-romanian-dishes-and-pastries-morphology-review-v1"
    assert review["baseline"] == {
        "build_version": "fixture-v71-literature-and-storytelling-morphology",
        "kg_nodes": 2364,
        "kg_edges": 9217,
        "kg_puzzles": 180,
        "kg_aliases": 8400,
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

    assert final["accepted_aliases"] == accepted == candidate_aliases
    assert final["accepted_aliases_sha256"] == _ACCEPTED_MAP_SHA256
    assert _canonical_sha256(accepted) == _ACCEPTED_MAP_SHA256
    assert final["accepted_aliases_wrapped_sha256"] == _ACCEPTED_WRAPPED_SHA256
    assert _canonical_sha256({"accepted_aliases": accepted}) == _ACCEPTED_WRAPPED_SHA256
    assert len(accepted) == 50
    assert len(set(accepted.values())) == 25
    assert all(count == 2 for count in Counter(accepted.values()).values())
    assert final["accepted_projections"] == {}
    assert final["deferred"] == []
    assert final["rejected"] == []

    for reviewer in review["reviews"].values():
        assert reviewer["status"] == "complete"
        assert reviewer["accepted_aliases_sha256"] == _ACCEPTED_MAP_SHA256
        assert set(reviewer["alias_accept"]) == set(accepted)
        assert reviewer["alias_reject"] == []
        assert reviewer["projection_accept"] == []
        assert reviewer["defer"] == []
        assert reviewer["reject"] == []


def test_v72_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = _accepted_aliases()
    historical_aliases = _historical_accepted_aliases()
    historical_owners = {
        node_id for module in _HISTORICAL_ALIAS_MODULES for node_id in module.ALIAS_ADDITIONS
    }

    assert DATA.BUILD_VERSION == "fixture-v72-romanian-dishes-and-pastries-morphology"
    assert len(DATA.ALIAS_ADDITIONS) == 25
    assert all(len(forms) == 2 for forms in DATA.ALIAS_ADDITIONS.values())
    assert len(aliases) == 50
    assert set(aliases).isdisjoint(historical_aliases)
    assert set(DATA.ALIAS_ADDITIONS).isdisjoint(historical_owners)
    assert DATA.BLOCKED_ALIAS_FORMS == ()
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    assert all(svc.resolve_fuzzy(surface) == node_id for surface, node_id in aliases.items())
    assert all(svc.resolve(surface) == node_id for surface, node_id in historical_aliases.items())
    owners = set(aliases.values())
    assert all(svc.node(node_id).node_type == "concept" for node_id in owners)
    assert all(svc.node(node_id).category == "gastronomie" for node_id in owners)
    historical = before_v84_fixture(fixture)
    historical_svc = WordGameService(Graph.from_records(
        historical["kg_nodes"], historical["kg_edges"],
    ))
    reviewed_additions = {
        "n_v17gas_coliva": {"n_v84_food_arpacas"},
        "n_gas_cozonac": {
            "n_v84_food_cuptor", "n_v84_food_drojdie", "n_v84_food_tava_copt",
        },
        "n_v17gas_gogosi": {"n_v84_food_aluat", "n_v84_food_drojdie"},
        "n_gas_mamaliga": {"n_v84_food_malai"},
        "n_v2gas_placinte": {"n_v84_food_sucitor"},
        "n_v18gas_salam_de_biscuiti": {
            "n_v24_food_breakfast_unt", "n_v24_food_snack_biscuit",
        },
    }
    assert set(reviewed_additions) <= owners
    for node_id in owners:
        before = set(historical_svc.predecessor_ids(node_id))
        assert 4 <= len(before) <= 24
        assert all(historical_svc.link(parent, node_id) is not None for parent in before)
        # Preserve the original bound and require exactly the reviewed new inputs;
        # a blanket higher ceiling would also permit unrelated graph drift.
        assert set(svc.predecessor_ids(node_id)) == before | reviewed_additions.get(node_id, set())
    assert svc.resolve("bulzurilor cu brânză") == "n_gas_bulz"
    assert svc.resolve("gogoșilor prăjite") == "n_v17gas_gogosi"
    assert svc.resolve("cârnaților de Pleșcoi") == "n_v17gas_carnati_plescoi"
    assert svc.resolve("salamurilor de biscuiți") == "n_v18gas_salam_de_biscuiti"
    assert svc.resolve("tochiturilor moldovenești") == "n_v11gas_tochitura_moldoveneasca"
    assert all(resolve_projection(surface) is None for surface in aliases)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == _CURRENT_BUILD_VERSION
    assert fixture["meta"]["counts"]["nodes"] == CURRENT_CONTENT.kg_counts["nodes"]
    assert fixture["meta"]["counts"]["edges"] == CURRENT_CONTENT.kg_counts["edges"]
    assert fixture["meta"]["counts"]["puzzles"] == CURRENT_CONTENT.kg_counts["puzzles"]
    assert (
        sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"])
        == CURRENT_CONTENT.kg_counts["aliases"]
    )


def test_v72_aliases_play_in_contexto_and_only_on_existing_legal_lant_hops() -> None:
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


def test_v72_preserves_v71_fuzzy_deny_and_nonaccepted_ledger_exactly() -> None:
    svc = get_service()
    assert {normalize(surface) for surface in REVIEWED_FUZZY_DENY_SURFACES} == (
        _INHERITED_FUZZY_DENY
    )
    assert DATA.BLOCKED_ALIAS_FORMS == ()
    assert DATA.DEFERRED_AMBIGUOUS_TERMS == DATA.BASE_DEFERRED_AMBIGUOUS_TERMS
    assert len(DATA.DEFERRED_AMBIGUOUS_TERMS) == 70
    assert len(set(DATA.DEFERRED_AMBIGUOUS_TERMS)) == 70

    for surface in ("intrigii", " INTRÍGII ", "intrigilor", " INTRIGILOR "):
        assert svc.resolve(surface) is None
        assert resolve_projection(surface) is None
        assert svc.resolve_fuzzy(surface) is None

    for exact in ("intrigă", "intrigi", "intrigile"):
        assert svc.resolve(exact) == "n_v4lit_intriga"
        assert svc.resolve_fuzzy(exact) == "n_v4lit_intriga"
    assert all(svc.suggest(surface) == ["intrigă"] for surface in _INHERITED_FUZZY_DENY)
    assert svc.resolve("strugur") is None
    assert svc.resolve_fuzzy("strugur") == "n_v24_food_small_fruit_strugure"


def test_v72_preserves_v71_selection_projection_topology_and_frozen_payloads() -> None:
    fixture = _json(_PACKAGE_KG)
    rankings = _json(_PACKAGE_RANKINGS)
    derived = _json(_PACKAGE_DERIVED)
    reserve = _json(_PACKAGE_RESERVE)
    nodes_without_aliases = [
        {key: value for key, value in node.items() if key != "aliases"}
        for node in fixture["kg_nodes"]
    ]

    assert len(PROJECTION_TERMS) == CURRENT_CONTENT.projection_terms
    assert len({term.domain for term in PROJECTION_TERMS}) == CURRENT_CONTENT.projection_domains
    assert _sha256(_PACKAGE_KG) == _KG_SHA256
    assert _KG_SHA256 != _V71_KG_SHA256
    assert _sha256(_PACKAGE_PACK) == _PACK_SHA256
    assert _sha256(_PACKAGE_RANKINGS) == _RANKINGS_SHA256
    assert _RANKINGS_SHA256 != _V71_RANKINGS_SHA256
    assert _sha256(_PACKAGE_DERIVED) == _DERIVED_SHA256
    assert _DERIVED_SHA256 != _V71_DERIVED_SHA256
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


def test_v72_mobile_contract_and_v49_ledger_persist_exactly() -> None:
    checked_in = _json(_MOBILE_CONTRACT)
    ledger = _json(_LEDGER)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _sha256(_MOBILE_CONTRACT) == _MOBILE_SHA256
    assert _MOBILE_SHA256 != _V71_MOBILE_SHA256
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == _CURRENT_BUILD_VERSION
    assert checked_in["manifest"]["counts"] == CURRENT_CONTENT.mobile_counts
    assert checked_in["manifest"]["content_hash"] == (
        "sha256:" + CURRENT_CONTENT.payload_sha256["mobile_content"]
    )
    historical = before_v84_fixture(_json(_PACKAGE_KG))
    assert mobile_app_pack_content_hash(
        historical["kg_nodes"], historical["kg_edges"], historical["kg_puzzles"],
    ) == (
        "sha256:5ea700a00708cf799a4cad8dcc99c54cb6595f0e99c217b5d890b9a829195918"
    )

    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert ledger["meta"]["count"] == len(ledger["items"]) == 104
