"""Regression contract for the reviewed V51 typed-vocabulary wave."""

from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.data import (  # noqa: E402
    load_fixture,
    mobile_app_pack_snapshot,
)
from cat_de_roman_esti.wordgames.contexto import (  # noqa: E402
    _build_session,
)
from cat_de_roman_esti.wordgames.contexto import (  # noqa: E402
    store as contexto_store,
)
from cat_de_roman_esti.wordgames.contexto_projection import (  # noqa: E402
    PROJECTION_TERMS,
    normalize_projection_surface,
    resolve_projection,
)
from cat_de_roman_esti.wordgames.derived_catalog import (  # noqa: E402
    DEFAULT_DERIVED_CATALOG_SHA256,
)
from cat_de_roman_esti.wordgames.lant import (  # noqa: E402
    LantSession,
)
from cat_de_roman_esti.wordgames.lant import (  # noqa: E402
    store as lant_store,
)
from cat_de_roman_esti.wordgames.service import (  # noqa: E402
    WordGameService,
    get_service,
)

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import apply_rereview  # noqa: E402
import audit_alchimie_projections  # noqa: E402
import contexto_common_words_v51_data as DATA  # noqa: E402
import critique_pack  # noqa: E402

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
_REVIEW = _ROOT / "docs/reviews/v51-typed-vocabulary-funnel/vocabulary.json"
_V48_REVIEW = _ROOT / "docs/reviews/v48-alchimie-pending-gate"

_KG_SHA256 = "1a5bd5ad9f6ce4b453f1b5463f335c7a006624d3cafbf6664a2e45d5b220edbc"
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_RANKINGS_SHA256 = "606937c391008c838fd0a78b06bc8ca03352f31c643cec500f7c7974cbb72366"
_DERIVED_SHA256 = "b4cb91c671191fcd2e6aa627d97cff8f7be4552c99af747701a8e1ce4a941287"
_CANDIDATE_FUNNEL_SHA256 = (
    "36eb871f07de3dde7169a896585031598791367af2c184b6dd6d15262933e416"
)
_RANKING_ROWS_SHA256 = "46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_NODES_WITHOUT_ALIASES_SHA256 = (
    "c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0"
)
_EDGES_SHA256 = "f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0"
_PUZZLES_SHA256 = "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
_V49_LEDGER_SHA256 = "e3d8166aa5c59c2ff1e7cba06be4fcd505d02a8c98224ab2fe6126d6c826cc29"
_V48_KG_SHA256 = "f2a4229c05072028fef1d8e68e97a6fe2e7c74c535bcca0fca0a0708acf5ed12"

_EXPECTED_ALIASES = {
    "odaia": "n_v24_home_rooms_camera",
    "odăi": "n_v24_home_rooms_camera",
    "odăile": "n_v24_home_rooms_camera",
    "odăii": "n_v24_home_rooms_camera",
    "odăilor": "n_v24_home_rooms_camera",
    "mămici": "n_v24_people_parents_mama",
    "mămicile": "n_v24_people_parents_mama",
    "mămicii": "n_v24_people_parents_mama",
    "mămicilor": "n_v24_people_parents_mama",
    "tăticul": "n_v24_people_parents_tata",
    "tătici": "n_v24_people_parents_tata",
    "tăticii": "n_v24_people_parents_tata",
    "tăticului": "n_v24_people_parents_tata",
    "tăticilor": "n_v24_people_parents_tata",
    "pite": "n_v4gas_paine",
    "pitele": "n_v4gas_paine",
    "pitei": "n_v4gas_paine",
    "pitelor": "n_v4gas_paine",
    "automobilul": "n_v24_transport_personal_masina",
    "automobile": "n_v24_transport_personal_masina",
    "automobilele": "n_v24_transport_personal_masina",
    "automobilului": "n_v24_transport_personal_masina",
    "automobilelor": "n_v24_transport_personal_masina",
    "autoturismul": "n_v24_transport_personal_masina",
    "autoturisme": "n_v24_transport_personal_masina",
    "autoturismele": "n_v24_transport_personal_masina",
    "autoturismului": "n_v24_transport_personal_masina",
    "autoturismelor": "n_v24_transport_personal_masina",
    "amicul": "n_v24_people_relationships_prieten",
    "amici": "n_v24_people_relationships_prieten",
    "amicului": "n_v24_people_relationships_prieten",
    "amicilor": "n_v24_people_relationships_prieten",
}
_EXPECTED_PROJECTIONS = {
    "smartphone": {
        "anchor_id": "n_v4mem_telefon",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "Wi Fi": {
        "anchor_id": "n_v4mem_internet",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "e-mail": {
        "anchor_id": "n_v4mem_internet",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "site web": {
        "anchor_id": "n_v4mem_internet",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "browser": {
        "anchor_id": "n_v4mem_internet",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "rețea socială": {
        "anchor_id": "n_v4mem_internet",
        "domain": "tehnologie",
        "rank_penalty": 1,
    },
    "sertar": {
        "anchor_id": "n_v24_home_storage_comoda_sertare",
        "domain": "mobilier și casă",
        "rank_penalty": 1,
    },
    "stație de autobuz": {
        "anchor_id": "n_v24_transport_terminals_statie",
        "domain": "transport rutier",
        "rank_penalty": 1,
    },
}
_EXPECTED_DEFERRED = {
    "amicii",
    "arborele",
    "arbori",
    "arborii",
    "arborelui",
    "arborilor",
    "cuptor",
}
_EXPECTED_REJECTED = {"fișă", "elan", "priză multiplă"}
_UNAUTHORED_SPELLING_VARIANTS = {"Wi-Fi", "wifi", "email"}
_EXPECTED_LEXICAL_SOURCES = {
    "https://dexonline.ro/definitie/odaie",
    "https://dexonline.ro/definitie/m%C4%83mic%C4%83",
    "https://dexonline.ro/definitie/t%C4%83tic",
    "https://dexonline.ro/definitie/pit%C4%83",
    "https://dexonline.ro/definitie/automobil",
    "https://dexonline.ro/definitie/autoturism",
    "https://dexonline.ro/definitie/amic",
    "https://dexonline.ro/definitie/arbore",
    "https://dexonline.ro/definitie/smartphone",
    "https://dexonline.ro/definitie/wi%20fi/1260813",
    "https://dexonline.ro/definitie/e-mail",
    "https://dexonline.ro/definitie/browser",
    "https://dexonline.ro/definitie/website",
    "https://dexonline.ro/definitie/sertar",
    "https://dexonline.ro/definitie/autosta%C8%9Bie",
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


def _candidate_surfaces(candidates: dict) -> set[str]:
    surfaces: set[str] = set()
    for values in candidates.values():
        surfaces.update(values)
    return surfaces


def _post_contexto_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v51_review_funnel_is_exact_complete_and_records_disagreement() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    surfaces = _candidate_surfaces(candidates)
    final = review["final"]
    final_partition = [
        set(final["accepted_aliases"]),
        set(final["accepted_projections"]),
        set(final["deferred"]),
        set(final["rejected"]),
    ]

    assert review["schema"] == "v51-typed-vocabulary-review-v1"
    assert review["candidate_funnel_sha256"] == _CANDIDATE_FUNNEL_SHA256
    assert review["candidate_funnel_sha256"] == _canonical_sha256(candidates)
    assert len(surfaces) == 50
    assert sum(len(values) for values in candidates.values()) == 50
    normalized = [normalize_projection_surface(surface) for surface in surfaces]
    assert len(normalized) == len(set(normalized)) == 50
    assert set().union(*final_partition) == surfaces
    assert sum(map(len, final_partition)) == 50

    assert final["accepted_aliases"] == _EXPECTED_ALIASES
    assert final["accepted_projections"] == _EXPECTED_PROJECTIONS
    assert set(final["deferred"]) == _EXPECTED_DEFERRED
    assert set(final["rejected"]) == _EXPECTED_REJECTED
    assert review["result"] == {
        "accepted_alias_surfaces": 32,
        "accepted_projection_surfaces": 8,
        "deferred_surfaces": 7,
        "rejected_surfaces": 3,
        "new_nodes": 0,
        "new_edges": 0,
        "new_game_records": 0,
    }

    reviewers = review["reviews"]
    reviewer_a = reviewers["reviewer_a"]
    reviewer_b = reviewers["reviewer_b"]
    assert set(reviewer_a["alias_accept"]) == set(_EXPECTED_ALIASES)
    assert set(reviewer_b["alias_accept"]) == set(_EXPECTED_ALIASES) | {"amicii"}
    assert set(reviewer_a["alias_reject"]) == {"amicii"}
    assert reviewer_b["alias_reject"] == []
    assert "amicii" in final["deferred"]
    reviewer_deferred = _EXPECTED_DEFERRED - {"amicii"}
    for reviewer in (reviewer_a, reviewer_b):
        dispositions = [
            set(reviewer["alias_accept"]),
            set(reviewer["alias_reject"]),
            set(reviewer["projection_accept"]),
            set(reviewer["defer"]),
            set(reviewer["reject"]),
        ]
        assert set(reviewer["projection_accept"]) == set(_EXPECTED_PROJECTIONS)
        assert set(reviewer["defer"]) == reviewer_deferred
        assert set(reviewer["reject"]) == _EXPECTED_REJECTED
        assert set().union(*dispositions) == surfaces
        assert sum(map(len, dispositions)) == 50

    projection_binding = {
        "schema": "v51-projection-binding-v1",
        "items": _EXPECTED_PROJECTIONS,
    }
    for reviewer in (reviewer_a, reviewer_b):
        assert reviewer["projection_binding_schema"] == projection_binding["schema"]
        assert reviewer["projection_binding_sha256"] == _canonical_sha256(
            projection_binding
        )
    lexical_sources = review["lexical_sources"]
    assert set(lexical_sources) == _EXPECTED_LEXICAL_SOURCES
    assert len(lexical_sources) == len(set(lexical_sources))


def test_v51_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = {
        alias: node_id
        for node_id, surfaces in DATA.ALIAS_ADDITIONS.items()
        for alias in surfaces
    }

    assert DATA.BUILD_VERSION == "fixture-v51-typed-vocabulary"
    assert aliases == _EXPECTED_ALIASES
    assert len(DATA.ALIAS_ADDITIONS) == 6
    assert len(aliases) == 32
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    blocked = _EXPECTED_DEFERRED | _EXPECTED_REJECTED | set(_EXPECTED_PROJECTIONS)
    assert all(svc.resolve(surface) is None for surface in blocked)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == "fixture-v53-food-morphology"
    assert fixture["meta"]["counts"]["nodes"] == 2364
    assert fixture["meta"]["counts"]["edges"] == 9217
    assert fixture["meta"]["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 7588


def test_v51_basic_words_are_exactly_the_reviewed_nonwinning_projection() -> None:
    svc = get_service()

    assert len(PROJECTION_TERMS) == 473
    assert len({term.domain for term in PROJECTION_TERMS}) == 26
    for surface, expected in _EXPECTED_PROJECTIONS.items():
        term = resolve_projection(surface)
        assert term is not None
        assert term.anchor_id == expected["anchor_id"]
        assert term.domain == expected["domain"]
        assert term.rank_penalty == expected["rank_penalty"] == 1
        assert svc.resolve(surface) is None

    excluded = set(_EXPECTED_ALIASES) | _EXPECTED_DEFERRED | _EXPECTED_REJECTED
    assert all(resolve_projection(surface) is None for surface in excluded)


def test_v51_aliases_play_in_contexto_and_only_on_existing_legal_lant_hops() -> None:
    client = Client()
    svc = get_service()
    lant_targets: set[str] = set()

    for alias, target in _EXPECTED_ALIASES.items():
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
        if not starts:
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

    assert lant_targets == set(_EXPECTED_ALIASES.values())


def test_v51_projections_play_only_in_contexto_and_never_win() -> None:
    client = Client()
    svc = get_service()

    for surface, expected in _EXPECTED_PROJECTIONS.items():
        target = expected["anchor_id"]
        game_id = contexto_store.create(_build_session(target, "normal", None))
        body = _post_contexto_guess(client, game_id, surface)
        assert body["ok"] is True
        assert body["won"] is False
        assert body["guess"]["id"].startswith("ctxp_")
        assert body["guess"]["rank"] >= 2
        assert svc.resolve(surface) is None

    start = "n_v4soc_casa"
    target = next(
        node_id
        for node_id in svc.neighbor_ids(start)
        if svc.link(start, node_id) is not None
    )
    session = LantSession(start=start, target=target, optimal=1, chain=[start])
    game_id = lant_store.create(session)
    for surface in _EXPECTED_PROJECTIONS:
        body = client.post(
            f"/api/wordgames/lant/games/{game_id}/move",
            {"text": surface},
            content_type="application/json",
        ).json()
        assert body["ok"] is False
        assert session.moves == 0


def test_v51_blocked_and_unauthored_spellings_stay_out_of_typed_games() -> None:
    client = Client()
    svc = get_service()
    blocked = (
        _EXPECTED_DEFERRED
        | _EXPECTED_REJECTED
        | _UNAUTHORED_SPELLING_VARIANTS
    )
    target = "n_v4mem_internet"

    for surface in blocked:
        assert svc.resolve(surface) is None
        assert resolve_projection(surface) is None
        game_id = contexto_store.create(_build_session(target, "normal", None))
        body = _post_contexto_guess(client, game_id, surface)
        assert body["ok"] is False
        assert body["attempts"] == 0
        assert "target" not in body


def test_v51_preserves_topology_pack_rows_and_frozen_derived_boards() -> None:
    fixture = _json(_PACKAGE_KG)
    rankings = _json(_PACKAGE_RANKINGS)
    derived = _json(_PACKAGE_DERIVED)
    nodes_without_aliases = [
        {key: value for key, value in node.items() if key != "aliases"}
        for node in fixture["kg_nodes"]
    ]

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


def test_v51_mobile_contract_and_v49_ledger_persist_exactly() -> None:
    checked_in = _json(_MOBILE_CONTRACT)
    ledger = _json(_LEDGER)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == "fixture-v53-food-morphology"
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2364,
        "edges": 9217,
        "puzzles": 180,
    }

    assert _sha256(_LEDGER) == _V49_LEDGER_SHA256
    assert ledger["meta"]["count"] == len(ledger["items"]) == 104
    pack = _json(_PACKAGE_PACK)
    runtime_ids = {
        row["id"]
        for game in ("conexiuni", "contexto", "lant", "alchimie")
        for row in pack[game]
    }
    rejected_ids = set(ledger["items"])
    rejected_pairs = {
        (row["start"], row["target"]) for row in ledger["items"].values()
    }
    assert rejected_ids.isdisjoint(runtime_ids)
    assert rejected_pairs.isdisjoint(
        (row["start"], row["target"]) for row in pack["lant"]
    )


def test_v51_replays_v48_projection_evidence_without_rebinding_history() -> None:
    audit_path = _V48_REVIEW / "projection-audit.json"
    audit = _json(audit_path)
    dossiers = _V48_REVIEW / "dossiers"

    assert audit["kg_sha256"] == _V48_KG_SHA256
    assert audit["kg_sha256"] != critique_pack.kg_sha256() == _KG_SHA256
    assert audit_alchimie_projections.rebuild_archived_artifact(audit, dossiers) == audit

    artifact_path = _V48_REVIEW / "alchimie_verdicts.json"
    artifact = _json(artifact_path)
    verdicts, batch, _ = apply_rereview.validated_artifact(
        artifact,
        "alchimie",
        artifact_path,
    )
    assert len(verdicts) == len(batch["input_ids"]) == 21

    tampered = deepcopy(audit)
    tampered["kg_sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="stale or invalid dossier"):
        audit_alchimie_projections.rebuild_archived_artifact(tampered, dossiers)


def test_v51_live_alchimie_gate_still_binds_the_current_kg(tmp_path: Path) -> None:
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK,
        critique_pack.PACKAGE_KG,
    )
    pending = next(row for row in pack["alchimie"] if row["status"] == "pending")
    item_id = pending["id"]
    _items, _pack_findings, selected = critique_pack.run(
        pack,
        svc,
        strong,
        regions,
        ["alchimie"],
        {"pending"},
        {item_id},
    )
    game, record, findings = selected[0]
    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    dossier = critique_pack.build_dossier(
        record,
        game,
        svc,
        strong,
        findings,
        regions,
    )
    (dossier_dir / f"{item_id}.json").write_text(
        json.dumps(dossier, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    audit = audit_alchimie_projections.build_artifact([item_id], dossier_dir)
    audit_path = tmp_path / apply_rereview.ALCHIMIE_PROJECTION_AUDIT
    verdict_path = tmp_path / "alchimie_verdicts.json"
    batch = {"input_ids": [item_id]}
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    assert audit["kg_sha256"] == _KG_SHA256
    apply_rereview.validate_live_alchimie_projection_source(batch, verdict_path)

    stale = deepcopy(audit)
    stale["kg_sha256"] = _V48_KG_SHA256
    audit_path.write_text(
        json.dumps(stale, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="stale Alchimie live-projection source"):
        apply_rereview.validate_live_alchimie_projection_source(batch, verdict_path)
