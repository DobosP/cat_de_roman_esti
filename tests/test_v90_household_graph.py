"""Reviewed dust, crumbs and lint support typed discovery through seventeen real directions."""

from __future__ import annotations

import ast
import hashlib
import json
import unicodedata
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import WordGameService, get_service
from tests import content_history as history
from tests.content_scenarios import contexto_seed
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"
REVIEW = ROOT / "docs/reviews/v90-household-discovery-and-critique-gates"
GRAPH_SHA = "672ea9f249ec9f18dbc51c24427580b61e98abbaef2b7b3a6d0fd5c557d395ba"
FORMS = {
    "n_v90_household_praf": ("Praf", ("praful", "prafului")),
    "n_v90_food_firimitura": (
        "Firimitură", ("firimituri", "firimiturile", "firimiturii", "firimiturilor"),
    ),
    "n_v90_textile_scama": ("Scamă", ("scame", "scamele", "scamei", "scamelor")),
}
DEGREE_CHANGES = {
    "n_v3sti_electricitate": (11, 12), "n_v4gas_apa": (29, 30),
    "n_v4gas_paine": (20, 21), "n_v24_food_snack_biscuit": (14, 15),
    "n_v24_home_textiles_patura": (6, 7), "n_v24_home_textiles_covor": (6, 9),
    "n_v29_clothing_everyday_haina": (8, 9), "n_v30_kitchen_table_farfurie": (5, 6),
    "n_v31_cleaning_floor_mop": (7, 8), "n_v31_cleaning_floor_aspirator": (5, 10),
    "n_v31_cleaning_floor_faras": (6, 8), "n_v31_cleaning_dishes_burete_vase": (6, 8),
    "n_v88_cleaning_matura": (5, 6),
}
BASELINE = {
    "kg_sample.json": "2964951e3f68be7b49abb7f727b97d700a42d7e3527b117ef8b6c2830103f9fc",
    "games_pack.json": "c8b310f56f3983dc8f4e6a523a85a9af79a3cf244d770474f6db6ac8266e0f04",
    "board_rankings_v37.json": "ea207d65a1846d2f9bb2945ca9320a8e5e7bdc5e9fe8c31113aaf4f749fdc3d6",
    "derived_catalog_v38.json": "4bd3cd515d21627fe42d07149bdf78951164ebfaa30df52fd1259ce26b8470d9",
    "cat_mobile_app_pack_contract.json": (
        "d2fbb9f550a05b6b128431ee55787b2b156846887f0bc8ce1908f09e6683b951"
    ),
}
# Final reviewed target IDs will be installed only after promotion and artifact freeze.
PUBLIC = {
    "ct_viata_de_roman_355": ("n_v31_cleaning_floor_faras", "Făraș", "firimituri"),
    "ct_viata_de_roman_356": ("n_v31_cleaning_floor_aspirator", "Aspirator", "scame"),
}


def _read(path):
    return json.loads(path.read_bytes())


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


def _private(body, target):
    encoded = json.dumps(body, ensure_ascii=False)
    assert "target" not in body and "solution" not in body and "anchor_id" not in encoded
    assert target not in encoded and get_service().label(target) not in encoded


def _post(client, url, **payload):
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200, response.content
    return response.json()


def test_three_concepts_and_seventeen_oriented_edges_match_both_bound_independent_reviews():
    proposal_blob = (REVIEW / "author-candidates/graph-proposal.json").read_bytes()
    assert _sha(proposal_blob) == GRAPH_SHA
    proposal = json.loads(proposal_blob)
    source = (ROOT / "scripts/household_graph_v90_data.py").read_bytes()
    tree = ast.parse(source)
    for name, expected in (("NODES", proposal["nodes"]), ("EDGES", proposal["edges"])):
        value = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == name for t in node.targets))
        assert list(ast.literal_eval(value)) == expected
    factual = _read(REVIEW / "graph-factual-review.json")
    quality = _read(REVIEW / "graph-quality-review.json")
    assert factual["decision"] == "accept_facts_for_integration_review"
    assert quality["decision"] == "accept_graph_proposal_for_integration"
    assert factual["graph_sha256"] == quality["graph_proposal_sha256"] == GRAPH_SHA
    assert [edge["index"] for edge in factual["edges"]] == list(range(17))
    assert all(edge["decision"] == "accept_as_authored" for edge in factual["edges"])
    assert [edge["ref"] for edge in quality["edge_judgments"]] == [f"edge:{i}" for i in range(17)]
    assert all(edge["decision"] == "accept" for edge in quality["edge_judgments"])
    assert len(proposal["nodes"]) == 3 and len(proposal["edges"]) == 17
    assert sum(len(forms) for _, forms in FORMS.values()) == 10
    nodes = {node["id"]: node for node in _read(FIXTURES / "kg_sample.json")["kg_nodes"]}
    assert {node for node in nodes if node.startswith("n_v90_")} == set(FORMS)
    for expected in proposal["nodes"]:
        assert {key: nodes[expected["id"]][key] for key in expected} == expected
        assert (expected["label_ro"], tuple(expected["aliases"])) == FORMS[expected["id"]]
    for expected in proposal["edges"]:
        edge = get_service().link(expected["src"], expected["dst"])
        assert edge is not None and not edge.bidirectional and not edge.is_distractor
        assert (edge.relation, edge.label_ro, edge.strength) == (
            expected["relation"], expected["label_ro"], expected["strength"],
        )


@pytest.mark.parametrize(("filename", "inverse"), [
    ("kg_sample.json", history.before_v90_fixture),
    ("games_pack.json", history.before_v90_pack),
    ("board_rankings_v37.json", history.before_v90_rankings),
    ("derived_catalog_v38.json", history.before_v90_derived),
    ("cat_mobile_app_pack_contract.json", history.before_v90_mobile),
])
def test_five_exact_v89_artifacts_reconstruct_without_accepting_unreviewed_rows(filename, inverse):
    path = (ROOT / "tests/fixtures" if filename.startswith("cat_mobile") else FIXTURES) / filename
    blob = path.read_bytes()
    current = json.loads(blob)
    before = inverse(current)
    indent = 2 if filename == "kg_sample.json" else 1
    assert _sha((json.dumps(before, ensure_ascii=False, indent=indent) + "\n").encode()) == (
        BASELINE[filename]
    )
    assert current == json.loads(blob)
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    assert _sha(blob) == CURRENT_CONTENT.artifact_sha256[str(path.relative_to(ROOT))]
    receipt = _read(REVIEW / "artifact-delta.json")
    assert receipt["baseline_commit"] == "190d7fdb86487c641d8a781ef7a5ce21f2b98031"
    assert receipt["files"][filename]["baseline_sha256"] == BASELINE[filename]
    for location in ("header", "old_row"):
        modified = deepcopy(current)
        if location == "header":
            header = "manifest" if filename.startswith("cat_mobile") else "meta"
            modified[header]["unreviewed"] = True
        else:
            table = next(key for key, value in modified.items() if isinstance(value, list))
            modified[table][0]["unreviewed"] = True
        with pytest.raises(AssertionError):
            inverse(modified)


def test_old659_pack_records_83_alchimie_100_lant_and_336_derived_rows_remain_exact():
    current_pack = _read(FIXTURES / "games_pack.json")
    live = history.before_v91_artifact(current_pack, "games_pack.json")
    old = history.before_v90_pack(current_pack)
    games = ("conexiuni", "contexto", "lant", "alchimie")
    assert sum(len(old[game]) for game in games) == 659
    for game in games:
        previous = {row["id"]: row for row in old[game]}
        current = {row["id"]: row for row in live[game]}
        assert {key: current[key] for key in previous} == previous
        assert set(current) - set(previous) == (set(PUBLIC) if game == "contexto" else set())
    assert live["alchimie"] == old["alchimie"] and len(live["alchimie"]) == 83
    assert live["lant"] == old["lant"] and len(live["lant"]) == 100
    derived = _read(FIXTURES / "derived_catalog_v38.json")
    assert derived["boards"] == history.before_v90_derived(derived)["boards"]
    assert len(derived["boards"]) == 336


def test_all_old_native_owners_forms_edges_and_puzzles_survive():
    current = _read(FIXTURES / "kg_sample.json")
    baseline = history.before_v90_fixture(current)
    assert len(current["kg_nodes"]) - len(baseline["kg_nodes"]) == 3
    assert len(current["kg_edges"]) - len(baseline["kg_edges"]) == 17
    assert current["kg_puzzles"] == baseline["kg_puzzles"]
    new_nodes = {node["id"]: node for node in current["kg_nodes"]}
    new_edges = {edge["id"]: edge for edge in current["kg_edges"]}
    old_service = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    for row in baseline["kg_edges"]:
        assert new_edges[row["id"]] == row
    actual_degree_changes = {
        old["id"]: (old["degree"], new_nodes[old["id"]]["degree"])
        for old in baseline["kg_nodes"] if old["degree"] != new_nodes[old["id"]]["degree"]
    }
    assert actual_degree_changes == DEGREE_CHANGES and len(DEGREE_CHANGES) == 13
    for old in baseline["kg_nodes"]:
        expected = dict(old)
        if old["id"] in DEGREE_CHANGES:
            expected["degree"] = DEGREE_CHANGES[old["id"]][1]
        assert new_nodes[old["id"]] == expected
        for word in (old["id"], old["label_ro"], *old.get("aliases", [])):
            assert get_service().resolve(word) == old_service.resolve(word), word


@pytest.mark.parametrize("owner", FORMS)
def test_all_new_grammatical_forms_share_one_attempt_and_win_only_their_native_owner(owner):
    label, forms = FORMS[owner]
    svc, client = get_service(), Client()
    target = "n_mihai_eminescu"
    gid = C.store.create(C._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        for form in (label, *forms):
            for spelling in (form, f"  {form.upper()}  ", unicodedata.normalize(
                "NFD", form.replace("ș", "ş").replace("ț", "ţ"),
            )):
                assert svc.resolve(spelling) == owner
                body = _post(client, url + "/guess", text=spelling)
                assert body["ok"] and not body["won"] and body["attempts"] == 1
                assert body["guess"]["id"] == owner and body["guess"]["label"] == label
                assert body["guess"]["closeness"] < 100
                _private(body, target)
            win_id = C.store.create(C._build_session(owner, "usor", None))
            try:
                won = _post(client, f"/api/wordgames/contexto/games/{win_id}/guess", text=form)
                assert won["won"] and won["score"] == 1000 and won["guess"]["id"] == owner
            finally:
                C.store.delete(win_id)
        assert body["feedback"]["kind"] == "repeat"
        assert client.get(url).json()["guesses"] == body["guesses"]
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("index", range(17))
def test_all17_directed_links_are_playable_and_reverse_moves_need_their_own_real_edge(index):
    row = _read(REVIEW / "author-candidates/graph-proposal.json")["edges"][index]
    old = history.before_v90_fixture(_read(FIXTURES / "kg_sample.json"))
    old_service = WordGameService(Graph.from_records(old["kg_nodes"], old["kg_edges"]))
    client, svc = Client(), get_service()
    for start, target, valid in (
        (row["src"], row["dst"], True),
        (row["dst"], row["src"], old_service.link(row["dst"], row["src"]) is not None),
    ):
        gid = L.store.create(L.LantSession(
            start=start, target=target, optimal=1, difficulty="usor", chain=[start],
        ))
        url = f"/api/wordgames/lant/games/{gid}"
        try:
            body = _post(client, url + "/move", text=svc.label(target))
            assert body["ok"] is valid
            resumed = client.get(url).json()
            assert resumed["moves"] == int(valid) and resumed["won"] is valid
            expected_path = [start, target] if valid else [start]
            assert [step["id"] for step in resumed["path"]] == expected_path
            if valid:
                assert body["relation"] == svc.link(start, target).label_ro
        finally:
            L.store.delete(gid)


@pytest.mark.parametrize("item_id", (*PUBLIC, "ct_viata_de_roman_353"))
def test_public_tool_round_has_clear_openers_safe_clue_resume_repeat_and_exact_win(item_id):
    target, answer, opener = PUBLIC.get(item_id, ("n_v31_cleaning_floor_mop", "Mop", "praf"))
    item = next(item for item in get_pack().pool("contexto") if item.id == item_id)
    assert item._pilot_eligible and item.payload["target"] == target
    seed = contexto_seed(target, difficulty="usor", category="viata_de_roman")
    client = Client()
    initial = _post(client, f"/api/wordgames/contexto/games?seed={seed}"
                    "&category=viata_de_roman&difficulty=usor")
    gid = initial["game_id"]
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        assert C.store.get(gid).pack_id == item_id
        _private(initial, target)
        for attempt, word in enumerate(("stilou", "fotbal", "București"), 1):
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] and not body["won"] and body["attempts"] == attempt
            _private(body, target)
        clue = _post(client, url + "/clue")
        assert clue["clue_kind"] == "warmer" and clue["clues_used"] == 1
        assert clue["word"]["rank"] > 1
        _private(clue, target)
        body = _post(client, url + "/guess", text=opener)
        assert body["ok"] and not body["won"] and body["attempts"] == 4
        assert body["guess"]["distance"] == 1
        assert body["guess"]["temperature"] in {"Cald", "Fierbinte"}
        _private(body, target)
        repeat = _post(client, url + "/guess", text=opener.upper())
        assert repeat["attempts"] == 4 and repeat["feedback"]["kind"] == "repeat"
        assert repeat["guesses"] == body["guesses"]
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["clues_used"] == 1
        _private(resumed, target)
        won = _post(client, url + "/guess", text=answer)
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
        assert won["attempts"] == 5 and won["score"] == C.score_for(5, 1)
        assert client.get(url).json()["score"] == won["score"]
    finally:
        C.store.delete(gid)


def test_plate_sponge_direction_opens_exactly_seven_old_kitchen_nodes_and_removal_reverses_it():
    from cat_de_roman_esti.wordgames.contexto_feedback import COMMON_FEEDBACK_PROXIES

    current = _read(FIXTURES / "kg_sample.json")
    previous = history.before_v90_fixture(current)
    old_service = WordGameService(Graph.from_records(previous["kg_nodes"], previous["kg_edges"]))
    old_pack = history.before_v90_pack(_read(FIXTURES / "games_pack.json"))
    old_rankings = history.before_v90_rankings(_read(FIXTURES / "board_rankings_v37.json"))
    by_id = {row["id"]: row["target"] for row in old_pack["contexto"]}
    mature_targets = {
        by_id[row["id"]] for row in old_rankings["boards"]
        if row["game"] == "contexto" and row["pilot_eligible"]
    } - {"n_v31_cleaning_floor_mop"}
    assert len(mature_targets) == 235
    cleaning = {
        "n_v31_cleaning_dishes_burete_vase", "n_v31_cleaning_supply_detergent",
        "n_v31_cleaning_floor_aspirator", "n_v31_cleaning_floor_faras",
        "n_v31_cleaning_floor_mop", "n_v31_cleaning_water_galeata",
    }
    kitchen = {
        "n_v30_kitchen_cookware_oala", "n_v30_kitchen_cookware_tigaie",
        "n_v30_kitchen_drink_cana", "n_v30_kitchen_table_castron",
        "n_v30_kitchen_table_farfurie", "n_v30_kitchen_utensil_furculita",
        "n_v30_kitchen_utensil_lingura",
    }
    bridge = [edge for edge in current["kg_edges"] if (
        edge["src_id"], edge["dst_id"]
    ) == ("n_v30_kitchen_table_farfurie", "n_v31_cleaning_dishes_burete_vase")]
    assert len(bridge) == 1 and bridge[0]["relation"] == "cleaned_with"
    without_plate_edge = WordGameService(Graph.from_records(
        current["kg_nodes"], [edge for edge in current["kg_edges"] if edge != bridge[0]],
    ))
    for svc, expected in (
        (old_service, cleaning), (get_service(), cleaning | kitchen),
        (without_plate_edge, cleaning),
    ):
        assert {
            node_id for node_id in COMMON_FEEDBACK_PROXIES
            if not mature_targets.isdisjoint(svc.distances_from(node_id))
        } == expected
        for node_id in expected:
            assert mature_targets <= set(svc.distances_from(node_id))



def test_exact_final_judgments_promote_only_the_two_reviewed_tool_candidates():
    candidate = REVIEW / "author-candidates/viata_de_roman/candidates.json"
    assert _sha(candidate.read_bytes()) == (
        "0a7d3cb1c78f19a5bb9568765ffb5ed96dfd321eade88fb3365afa37adada769"
    )
    for name in ("verify_factual.json", "verify_quality.json"):
        assert _read(candidate.parent / name)["candidate_sha256"] == (
            "sha256:" + _sha(candidate.read_bytes())
        )
    quality = _read(candidate.parent / "verify_quality.json")
    assert [(row["ref"], row["verdict"]) for row in quality["instances"]] == [
        ("contexto[0]", "keep"), ("contexto[1]", "keep"), ("contexto[2]", "drop"),
    ]
    artifact = _read(REVIEW / "final-gate/contexto_verdicts.json")
    assert artifact["batch"] == {"version": 2, "mode": "gate", "input_ids": list(PUBLIC)}
    assert artifact["verdicts"] == dict.fromkeys(PUBLIC, "promote")
    assert artifact["coverage"] == {
        "total": 2, "verified": 2, "unverifiedClean": 0, "verifiersLost": 0, "lost": 0,
    }
    reviewers = set()
    for role in ("analyst", "verifier"):
        path = REVIEW / f"{role}.json"
        raw = _read(path)
        reviewers.add(raw["reviewer"])
        assert raw["role"] == role and raw["input_ids"] == list(PUBLIC)
        assert artifact["provenance"][role]["sha256"] == "sha256:" + _sha(path.read_bytes())
        for item, verdict in zip(raw["items"], artifact["perItem"], strict=True):
            assert item == verdict[f"{role}_review"]
            assert item["review_binding"] == verdict["review_binding"]
            assert item["verdict"] == verdict["final"] == "promote"
            dossier = _read(REVIEW / "dossiers" / (item["id"] + ".json"))
            assert dossier["review_binding"] == item["review_binding"]
    assert len(reviewers) == 2
    assert all(row.payload["target"] != "n_v31_cleaning_dishes_burete_vase"
               for row in get_pack().pool("contexto"))
