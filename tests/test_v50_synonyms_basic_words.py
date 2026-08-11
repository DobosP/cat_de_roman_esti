"""Regression contract for the reviewed V50 synonym/basic-word wave."""

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
import contexto_common_words_v50_data as DATA  # noqa: E402
import critique_pack  # noqa: E402

_PACKAGE_KG = _ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
_TEST_KG = _ROOT / "tests/fixtures/kg_sample.json"
_PACKAGE_PACK = _ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
_TEST_PACK = _ROOT / "tests/fixtures/games_pack.json"
_PACKAGE_RANKINGS = _ROOT / "cat_de_roman_esti/fixtures/board_rankings_v37.json"
_TEST_RANKINGS = _ROOT / "tests/fixtures/board_rankings_v37.json"
_PACKAGE_DERIVED = _ROOT / "cat_de_roman_esti/fixtures/derived_catalog_v38.json"
_TEST_DERIVED = _ROOT / "tests/fixtures/derived_catalog_v38.json"
_MOBILE_CONTRACT = _ROOT / "tests/fixtures/cat_mobile_app_pack_contract.json"
_REVIEW = _ROOT / "docs/reviews/v50-synonym-basic-word-funnel/vocabulary.json"
_V48_REVIEW = _ROOT / "docs/reviews/v48-alchimie-pending-gate"

_KG_SHA256 = "56b861ae4f6d611e70e87e27086a3a617ccfc8b6d69d51b100677df3dff4be7e"
_PACK_SHA256 = "05e80ab2ffb8ec185ad445305a728c784a93e683474d5ec645c10aa1247184ed"
_RANKINGS_SHA256 = "12c0971c60b6e93f5c4443776f46570b5f9ae29d10f7254d3a222e7a38eafd4e"
_DERIVED_SHA256 = "e987229417aea266e12f3223cb696f13aa740225aaab56cb2d55b084a4fad1ea"
_RANKING_ROWS_SHA256 = "46aabcea827c3eed9d64dd7249ea1514d4b211a5b95c4bbea2d8a825e29d86e0"
_FROZEN_BOARDS_SHA256 = "71a2acefb7e0ec62da32ad2645238d73d5e83375808160c0bd1800febd3a73b6"
_NODES_WITHOUT_ALIASES_SHA256 = (
    "c1ca327243b25415e1d7158436d00e36a3f1b53c15bc77590c9d6677d04678f0"
)
_EDGES_SHA256 = "f62f0730a3e79c1498776049d86e1013e877bc74433360b2fcfaf3f1253a89b0"
_PUZZLES_SHA256 = "3f66da71a5677ee56dbd96a46568a61f4494ac51fc41b47ec70bb54a126f27fc"
_V48_KG_SHA256 = "f2a4229c05072028fef1d8e68e97a6fe2e7c74c535bcca0fca0a0708acf5ed12"


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


def _post_contexto_guess(client: Client, game_id: str, text: str) -> dict:
    return client.post(
        f"/api/wordgames/contexto/games/{game_id}/guess",
        {"text": text},
        content_type="application/json",
    ).json()


def test_v50_review_funnel_is_exact_complete_and_unanimous() -> None:
    review = _json(_REVIEW)
    candidates = review["candidates"]
    alias_candidates = set(candidates["aliases"])
    projection_candidates = set(candidates["projections"])
    hold_candidates = set(candidates["holds"])
    explicit_rejects = set(candidates["explicit_rejects"])
    candidate_surfaces = (
        alias_candidates | projection_candidates | hold_candidates | explicit_rejects
    )

    assert review["schema"] == "v50-typed-vocabulary-review-v1"
    assert review["candidate_funnel_sha256"] == _canonical_sha256(candidates)
    assert len(candidate_surfaces) == 50
    assert sum(
        map(
            len,
            (alias_candidates, projection_candidates, hold_candidates, explicit_rejects),
        )
    ) == 50
    normalized = [normalize_projection_surface(surface) for surface in candidate_surfaces]
    assert len(normalized) == len(set(normalized)) == 50

    reviews = review["reviews"]
    final = review["final"]
    accepted_aliases = set(final["accepted_aliases"])
    accepted_projections = set(final["accepted_projections"])
    projection_binding = {
        "schema": "v50-projection-binding-v1",
        "items": final["accepted_projections"],
    }
    projection_binding_sha256 = _canonical_sha256(projection_binding)
    for reviewer in (reviews["reviewer_a"], reviews["reviewer_b"]):
        assert reviewer["projection_binding_schema"] == projection_binding["schema"]
        assert reviewer["projection_binding_sha256"] == projection_binding_sha256
    assert accepted_aliases == (
        set(reviews["reviewer_a"]["alias_accept"])
        & set(reviews["reviewer_b"]["alias_accept"])
    )
    assert accepted_projections == (
        set(reviews["reviewer_a"]["projection_accept"])
        & set(reviews["reviewer_b"]["projection_accept"])
    )
    assert set(final["rejected"]) == (
        set(reviews["unanimous_reject"])
        | (
            set(reviews["reviewer_a"]["alias_reject"])
            & set(reviews["reviewer_b"]["alias_reject"])
            - accepted_projections
        )
    )
    final_partition = [
        accepted_aliases,
        accepted_projections,
        set(final["deferred"]),
        set(final["rejected"]),
    ]
    assert set().union(*final_partition) == candidate_surfaces
    assert sum(map(len, final_partition)) == len(candidate_surfaces)
    assert review["result"] == {
        "accepted_alias_surfaces": 8,
        "accepted_projection_surfaces": 12,
        "deferred_surfaces": 8,
        "rejected_surfaces": 22,
        "new_nodes": 0,
        "new_edges": 0,
        "new_game_records": 0,
    }
    assert len(review["lexical_sources"]) == len(set(review["lexical_sources"])) == 13
    assert all(url.startswith("https://dexonline.ro/") for url in review["lexical_sources"])


def test_v50_alias_batch_is_exact_collision_free_and_applied_to_both_mirrors() -> None:
    fixture = _json(_PACKAGE_KG)
    review = _json(_REVIEW)
    svc = WordGameService(load_fixture(_PACKAGE_KG).graph)
    aliases = {
        alias: node_id
        for node_id, surfaces in DATA.ALIAS_ADDITIONS.items()
        for alias in surfaces
    }

    assert aliases == review["final"]["accepted_aliases"]
    assert len(DATA.ALIAS_ADDITIONS) == 6
    assert len(aliases) == 8
    assert all(svc.resolve(surface) == node_id for surface, node_id in aliases.items())
    assert all(svc.resolve(surface) is None for surface in DATA.BLOCKED_ALIAS_FORMS)
    assert _PACKAGE_KG.read_bytes() == _TEST_KG.read_bytes()
    assert fixture["meta"]["build_version"] == DATA.BUILD_VERSION
    assert fixture["meta"]["counts"]["nodes"] == 2364
    assert fixture["meta"]["counts"]["edges"] == 9217
    assert fixture["meta"]["counts"]["puzzles"] == 180
    assert sum(len(node.get("aliases", ())) for node in fixture["kg_nodes"]) == 7460


def test_v50_basic_words_are_exactly_the_reviewed_nonwinning_projection() -> None:
    review = _json(_REVIEW)
    accepted = review["final"]["accepted_projections"]
    svc = get_service()

    assert len(PROJECTION_TERMS) == 465
    assert len({term.domain for term in PROJECTION_TERMS}) == 26
    for surface, expected in accepted.items():
        term = resolve_projection(surface)
        assert term is not None
        assert term.anchor_id == expected["anchor_id"]
        assert term.domain == expected["domain"]
        assert term.rank_penalty == expected["rank_penalty"] == 1
        assert svc.resolve(surface) is None

    excluded = {
        *review["final"]["accepted_aliases"],
        *review["final"]["deferred"],
        *review["final"]["rejected"],
    }
    assert all(resolve_projection(surface) is None for surface in excluded)
    assert normalize_projection_surface("bărbie") == normalize_projection_surface("Barbie")


def test_v50_aliases_play_in_contexto_and_on_legal_lant_hops() -> None:
    client = Client()
    svc = get_service()
    lant_targets: set[str] = set()

    for alias, target in _json(_REVIEW)["final"]["accepted_aliases"].items():
        contexto_id = contexto_store.create(_build_session(target, "normal", None))
        contexto = _post_contexto_guess(client, contexto_id, alias)
        assert contexto["ok"] is True
        assert contexto["won"] is True
        assert contexto["guess"]["id"] == target

        starts = [
            node_id
            for node_id in svc.neighbor_ids(target)
            if svc.link(node_id, target) is not None
        ]
        if not starts:
            # Alias authoring must not manufacture a reverse edge solely to make a
            # currently one-way concept typeable from the other side in Lanț.
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

    assert lant_targets == {
        "n_v24_home_rooms_camera",
        "n_lbax_regionalism_barabula",
        "n_lbax_regionalism_papusoi",
        "n_v4gas_paine",
    }


def test_v50_projections_play_only_in_contexto_and_never_win() -> None:
    client = Client()
    accepted = _json(_REVIEW)["final"]["accepted_projections"]
    svc = get_service()

    for surface, expected in accepted.items():
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
    for surface in accepted:
        body = client.post(
            f"/api/wordgames/lant/games/{game_id}/move",
            {"text": surface},
            content_type="application/json",
        ).json()
        assert body["ok"] is False
        assert session.moves == 0


def test_v50_projection_typo_does_not_disclose_a_proxy_of_the_secret() -> None:
    client = Client()
    game_id = contexto_store.create(_build_session("n_v24_body_face_cap", "normal", None))
    body = _post_contexto_guess(client, game_id, "barbaa")

    assert body["ok"] is False
    assert body["attempts"] == 0
    assert "Barbă" not in body["suggestions"]
    assert "target" not in body


def test_v50_preserves_topology_pack_rows_and_frozen_derived_boards() -> None:
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


def test_v50_mobile_contract_tracks_only_the_alias_release() -> None:
    checked_in = _json(_MOBILE_CONTRACT)

    assert checked_in == mobile_app_pack_snapshot(_PACKAGE_KG)
    assert _MOBILE_CONTRACT.read_bytes() == (
        json.dumps(checked_in, ensure_ascii=False, indent=1) + "\n"
    ).encode("utf-8")
    assert checked_in["manifest"]["build_version"] == DATA.BUILD_VERSION
    assert checked_in["manifest"]["counts"] == {
        "nodes": 2364,
        "edges": 9217,
        "puzzles": 180,
    }


def test_v50_replays_v48_projection_evidence_without_rebinding_history() -> None:
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


def test_v50_live_alchimie_gate_requires_every_current_provenance_input(
    tmp_path: Path,
) -> None:
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
    assert len(selected) == 1

    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    game, record, findings = selected[0]
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

    def write_audit(value: dict) -> None:
        audit_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )

    write_audit(audit)
    apply_rereview.validate_live_alchimie_projection_source(batch, verdict_path)

    mutations = []
    changed_pack = deepcopy(audit)
    changed_pack["pack_sha256"] = "0" * 64
    mutations.append(changed_pack)
    changed_kg = deepcopy(audit)
    changed_kg["kg_sha256"] = "0" * 64
    mutations.append(changed_kg)
    changed_rubric = deepcopy(audit)
    changed_rubric["rubric_sha256"] = "0" * 64
    mutations.append(changed_rubric)
    changed_runtime = deepcopy(audit)
    changed_runtime["runtime_sources"][0]["sha256"] = "0" * 64
    changed_runtime["runtime_source_manifest_sha256"] = _canonical_sha256(
        changed_runtime["runtime_sources"]
    )
    mutations.append(changed_runtime)
    changed_runtime_manifest = deepcopy(audit)
    changed_runtime_manifest["runtime_source_manifest_sha256"] = "0" * 64
    mutations.append(changed_runtime_manifest)
    changed_generator = deepcopy(audit)
    changed_generator["generator"]["sha256"] = "0" * 64
    mutations.append(changed_generator)

    for changed in mutations:
        write_audit(changed)
        with pytest.raises(SystemExit, match="stale Alchimie live-projection source"):
            apply_rereview.validate_live_alchimie_projection_source(
                batch,
                verdict_path,
            )


def test_v50_embedded_rubric_bindings_replay_but_live_dossiers_use_current() -> None:
    dossier = _json(next((_V48_REVIEW / "dossiers").glob("*.json")))

    assert critique_pack.dossier_review_binding(dossier) == dossier["review_binding"]
    changed = deepcopy(dossier)
    changed["rubric_sha256"] = "0" * 64
    assert critique_pack.dossier_review_binding(changed) != dossier["review_binding"]
    changed["rubric_sha256"] = "bad"
    with pytest.raises(ValueError, match="rubric_sha256"):
        critique_pack.dossier_review_binding(changed)
