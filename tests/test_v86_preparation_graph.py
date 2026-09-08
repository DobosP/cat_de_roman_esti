"""Preparation words preserve identities and provide real, directed playable feedback."""

from __future__ import annotations

import ast
import hashlib
import json
import random
import unicodedata
from dataclasses import asdict
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import contexto_projection as P
from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import WordGameService, get_service
from tests.content_scenarios import contexto_seed

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v86-preparation-and-route-quality"
FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
GRAPH_SHA256 = "01069c928a5bd4087a2716575b928ad281d461036b2e0213ab4c090a8b32656f"
MODULE_SHA256 = "1f2afac7903fd529245ed326e2bd229ba3d50a80c57f263633d8b741486c5950"
BASELINE_SHA256 = "b7d28b990d37164d8e41a93965a5824162ded56b2907ac03388fee717eb144b2"
FORMS = {
    "n_v86_food_frisca": ("Frișcă", (
        "frișcă bătută", "frișcă naturală", "frișcă de smântână",
    )),
    "n_v86_food_albus": ("Albuș", ("albușul", "albușului", "albușuri", "albușurile")),
    "n_v86_food_galbenus": ("Gălbenuș", (
        "gălbenușul", "gălbenușului", "gălbenușuri", "gălbenușurile",
    )),
    "n_v86_food_zahar_pudra": ("Zahăr pudră", (
        "zahărul pudră", "zahărului pudră", "zahăr pudră fin",
    )),
    "n_v86_food_lapte_praf": ("Lapte praf", (
        "laptele praf", "laptelui praf", "lapte praf integral",
    )),
    "n_v86_food_amidon": ("Amidon alimentar", (
        "amidonul alimentar", "amidonului alimentar", "amidon de porumb",
    )),
    "n_v86_food_crema_vanilie": ("Cremă de vanilie", (
        "cremei de vanilie", "creme de vanilie", "cremele de vanilie",
    )),
    "n_v86_kitchen_congelator": ("Congelator", (
        "congelatorul", "congelatorului", "congelatoare", "congelatoarele",
    )),
    "n_v86_kitchen_mixer": ("Mixer de bucătărie", (
        "mixerul de bucătărie", "mixerului de bucătărie", "mixere de bucătărie",
    )),
}
PREDECESSORS = {
    "n_v86_food_frisca": "n_v20gas_smantana",
    "n_v86_food_albus": "n_v4gas_ou",
    "n_v86_food_galbenus": "n_v4gas_ou",
    "n_v86_food_zahar_pudra": "n_v24_food_pantry_zahar",
    "n_v86_food_lapte_praf": "n_v4gas_lapte",
    "n_v86_food_amidon": "n_v2lim_porumb",
    "n_v86_food_crema_vanilie": "n_v85_food_vanilie",
    "n_v86_kitchen_congelator": "n_v24_home_appliances_frigider",
}


def _json(path):
    return json.loads(path.read_bytes())


def _post(client, url, **payload):
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200, response.content
    return response.json()


def _hidden(body, target):
    encoded = json.dumps(body, ensure_ascii=False)
    assert "target" not in body and "solution" not in body
    assert target not in encoded and get_service().label(target) not in encoded
    assert "anchor_id" not in encoded


def _context_game(target):
    gid = C.store.create(C._build_session(target, "usor", None))
    return Client(), gid, f"/api/wordgames/contexto/games/{gid}"


def _assigned(tree, name):
    return ast.literal_eval(next(
        statement.value for statement in tree.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    ))


def test_served_graph_is_the_exact_independently_reviewed_preparation_batch():
    candidate_bytes = (REVIEW / "graph-candidates.json").read_bytes()
    assert hashlib.sha256(candidate_bytes).hexdigest() == GRAPH_SHA256
    candidate = json.loads(candidate_bytes)
    review = _json(REVIEW / "graph-review.json")
    assert review["verdict"] == "accept"
    assert review["candidate_sha256"] == GRAPH_SHA256
    assert review["module_sha256"] == MODULE_SHA256
    assert review["coverage"]["edge_indices"] == list(range(41))
    assert len(review["coverage"]["forms"]) == 30
    module = (ROOT / "scripts/preparation_graph_v86_data.py").read_bytes()
    assert hashlib.sha256(module).hexdigest() == MODULE_SHA256
    tree = ast.parse(module)
    assert list(_assigned(tree, "NODES")) == candidate["nodes"]
    assert list(_assigned(tree, "EDGES")) == candidate["edges"]
    assert candidate["remove_edges"] == []
    nodes = {node["id"]: node for node in _json(FIXTURE)["kg_nodes"]}
    assert {node for node in nodes if node.startswith("n_v86_")} == set(FORMS)
    assert len(FORMS) == 9 and sum(len(forms) for _, forms in FORMS.values()) == 30
    for expected in candidate["nodes"]:
        actual = nodes[expected["id"]]
        assert {key: actual[key] for key in expected} == expected
        assert (actual["label_ro"], tuple(actual["aliases"])) == FORMS[expected["id"]]
    svc = get_service()
    for expected in candidate["edges"]:
        edge = svc.link(expected["src"], expected["dst"])
        assert edge is not None and not edge.is_distractor
        assert (edge.src_id, edge.dst_id, edge.relation, edge.label_ro,
                edge.strength, edge.bidirectional) == (
            expected["src"], expected["dst"], expected["relation"], expected["label_ro"],
            expected["strength"], False,
        )


def test_complete_v85_graph_and_every_old_native_owner_reconstruct_exactly():
    from tests.content_history import before_v86_fixture

    current = _json(FIXTURE)
    baseline = before_v86_fixture(current)
    encoded = (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == BASELINE_SHA256
    assert FIXTURE.read_bytes() == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    assert len(current["kg_nodes"]) - len(baseline["kg_nodes"]) == 9
    assert len(current["kg_edges"]) - len(baseline["kg_edges"]) == 41
    assert current["kg_puzzles"] == baseline["kg_puzzles"]
    assert all(edge in current["kg_edges"] for edge in baseline["kg_edges"])
    old_nodes = {node["id"]: node for node in baseline["kg_nodes"]}
    new_nodes = {node["id"]: node for node in current["kg_nodes"]}
    for node_id, old in old_nodes.items():
        assert {k: v for k, v in old.items() if k != "degree"} == {
            k: v for k, v in new_nodes[node_id].items() if k != "degree"
        }
    previous = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    current_service = get_service()
    surfaces = [surface for node in baseline["kg_nodes"]
                for surface in (node["id"], node["label_ro"], *node.get("aliases", []))]
    assert len(surfaces) == 13318
    for surface in surfaces:
        assert current_service.resolve(surface) == previous.resolve(surface), surface


@pytest.mark.parametrize("owner", FORMS)
def test_all_new_forms_and_unicode_spellings_repeat_one_identity_and_win_only_it(owner):
    label, forms = FORMS[owner]
    svc = get_service()
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        for form in (label, *forms):
            assert svc.resolve(form) == owner
            for spelling in (
                form, f" {form.upper()} ",
                unicodedata.normalize("NFD", form.replace("ș", "ş").replace("ț", "ţ")),
            ):
                body = _post(client, url + "/guess", text=spelling)
                assert body["ok"] and not body["won"] and body["attempts"] == 1
                assert not body.get("needs_confirmation")
                assert (body["guess"]["id"], body["guess"]["label"]) == (owner, label)
                assert body["guess"]["closeness"] < 100
                _hidden(body, "n_mihai_eminescu")
            winner, won_gid, won_url = _context_game(owner)
            try:
                won = _post(winner, won_url + "/guess", text=form)
                assert won["won"] and won["attempts"] == 1 and won["score"] == 1000
                assert won["guess"]["id"] == owner and won["guess"]["rank"] == 1
            finally:
                C.store.delete(won_gid)
        assert body["feedback"]["kind"] == "repeat"
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["attempts"] == 1
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("owner", PREDECESSORS)
def test_all_reachable_preparation_forms_are_valid_typed_lant_destinations(owner):
    start = PREDECESSORS[owner]
    client = Client()
    for form in (FORMS[owner][0], *FORMS[owner][1]):
        gid = L.store.create(L.LantSession(
            start=start, target=owner, optimal=1, difficulty="usor", chain=[start],
        ))
        try:
            body = _post(client, f"/api/wordgames/lant/games/{gid}/move", text=form)
            assert body["ok"] and body["won"] and body["moves"] == 1
            assert body["path"][-1]["id"] == owner
        finally:
            L.store.delete(gid)


def test_all_41_new_links_work_forward_and_refuse_the_unreviewed_reverse_move():
    edges = _json(REVIEW / "graph-candidates.json")["edges"]
    assert len(edges) == 41 and all(not edge["bidirectional"] for edge in edges)
    svc, client = get_service(), Client()
    for edge in edges:
        start, target = edge["src"], edge["dst"]
        assert svc.link(start, target) is not None and svc.link(target, start) is None
        for source, destination, valid in ((start, target, True), (target, start, False)):
            gid = L.store.create(L.LantSession(
                start=source, target=destination, optimal=1, difficulty="usor", chain=[source],
            ))
            url = f"/api/wordgames/lant/games/{gid}"
            try:
                body = _post(client, url + "/move", text=svc.label(destination))
                assert body["ok"] is valid, (source, destination)
                state = client.get(url).json()
                assert state["won"] is valid and state["moves"] == int(valid)
                assert [step["id"] for step in state["path"]] == (
                    [source, destination] if valid else [source]
                )
                if valid:
                    assert body["relation"] == edge["label_ro"]
                else:
                    assert body["last_error"] == "Nu exista o legatura directa"
            finally:
                L.store.delete(gid)


@pytest.mark.parametrize(("surface", "owner", "target"), [
    ("congelator", "n_v86_kitchen_congelator", "n_v3gas_inghetata"),
    ("frișcă", "n_v86_food_frisca", "n_v21gas_savarina"),
    ("smântână", "n_v20gas_smantana", "n_v86_food_frisca"),
    ("vanilie", "n_v85_food_vanilie", "n_v86_food_frisca"),
    ("mixer de bucătărie", "n_v86_kitchen_mixer", "n_v86_food_frisca"),
    ("zahăr pudră", "n_v86_food_zahar_pudra", "n_v86_food_frisca"),
    ("lapte", "n_v4gas_lapte", "n_v86_food_crema_vanilie"),
    ("amidon alimentar", "n_v86_food_amidon", "n_v86_food_crema_vanilie"),
    ("gălbenuș", "n_v86_food_galbenus", "n_v86_food_crema_vanilie"),
    ("lapte praf", "n_v86_food_lapte_praf", "n_v85_food_ciocolata"),
])
def test_defining_preparation_inputs_are_direct_hot_private_and_resumable(surface, owner, target):
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        guess = body["guess"]
        assert guess["id"] == owner and guess["distance"] == 1
        assert guess["temperature"] == "Fierbinte" and 2 <= guess["rank"] <= 10
        assert guess["closeness"] < 100
        _hidden(body, target)
        repeated = _post(client, url + "/guess", text=surface.upper())
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        assert repeated["guess"] == guess
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text=get_service().label(target))
        assert won["won"] and won["attempts"] == 2 and won["guess"]["id"] == target
    finally:
        C.store.delete(gid)


def test_freezer_core_outweighs_indirect_oven_and_yeast_without_equating_refrigeration():
    svc = get_service()
    observed = {}
    for word in ("congelator", "frigider", "cuptor de bucătărie", "drojdie"):
        client, gid, url = _context_game("n_v3gas_inghetata")
        try:
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] and not body["won"]
            observed[word] = body["guess"]
        finally:
            C.store.delete(gid)
    assert observed["congelator"]["temperature"] == "Fierbinte"
    assert observed["congelator"]["distance"] == 1
    assert observed["frigider"]["distance"] == 2
    assert observed["frigider"]["temperature"] == "Cald"
    assert observed["congelator"]["rank"] < observed["frigider"]["rank"]
    for word in ("cuptor de bucătărie", "drojdie"):
        assert observed[word]["distance"] >= 3
        assert observed[word]["temperature"] != "Fierbinte"
        assert observed[word]["rank"] > observed["frigider"]["rank"]
    assert svc.link("n_v24_home_appliances_frigider", "n_v3gas_inghetata") is None


def test_only_freezer_projection_retires_and_audit_metadata_cannot_score():
    from tests.content_history import before_v86_projection_rows

    live = [(term.surface, term.anchor_id, term.domain, term.rank_penalty,
             term.mapping_kind, term.public_id) for term in P.PROJECTION_TERMS]
    before = before_v86_projection_rows(live)
    assert len(before) == 469 and len(live) == 468
    assert [row for row in before if row[0] != "congelator"] == live
    assert P.resolve_projection("congelator") is None
    assert get_service().resolve("congelator") == "n_v86_kitchen_congelator"
    terms = [asdict(term) for term in P.PROJECTION_TERMS]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(P, "NATIVE_PROJECTION_REPLACEMENTS", ())
        assert [asdict(term) for term in P._build_terms()] == terms


def test_qualified_starch_mixer_and_existing_ingredients_keep_their_sense_boundaries():
    svc = get_service()
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        for word in ("amidon", "rece", "răcire", "congelare", "cremă"):
            assert svc.resolve(word) is None and svc.resolve_fuzzy(word) is None
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] is False and body["attempts"] == 0
            assert not body.get("needs_confirmation")
            _hidden(body, "n_mihai_eminescu")
        projected = P.resolve_projection("mixer")
        assert projected is not None and projected.anchor_id == "n_v4gas_bucatarie"
        assert svc.resolve("mixer") is None
        body = _post(client, url + "/guess", text="mixer")
        assert body["ok"] and body["guess"]["id"] == projected.public_id
        for word, owner in (("smântână", "n_v20gas_smantana"),
                            ("lapte", "n_v4gas_lapte"),
                            ("zahăr", "n_v24_food_pantry_zahar")):
            assert svc.resolve(word) == owner and owner not in FORMS
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("left", "right", "target"), [
    ("n_v86_food_zahar_pudra", "n_v20gas_smantana", "n_v86_food_frisca"),
    ("n_v86_food_galbenus", "n_v86_food_amidon", "n_v86_food_crema_vanilie"),
])
def test_preparation_pairs_create_earned_alchimie_explanations(left, right, target):
    svc = get_service()
    projection = A._build_recipe_projection([left, right], target, "gastronomie")
    assert projection is not None and projection.par == 1
    assert target in projection.recipes[tuple(sorted((left, right)))]
    session = A.AlchimieSession(
        seeds=[left, right], target=target, target_depth=1, category="gastronomie",
        recipes=projection.recipes, routes=projection.routes,
    )
    for seed in session.seeds:
        session.add(seed, None)
    gid = A.store.create(session)
    client, url = Client(), f"/api/wordgames/alchimie/games/{gid}"
    try:
        initial = client.get(url).json()
        assert target not in json.dumps(initial)
        body = _post(client, url + "/combine", a=left, b=right)
        assert body["won"] and body["moves"] == 1
        earned = next(row for row in body["inventory"] if row["id"] == target)
        assert {link["source"]["id"]: link["label"] for link in earned["links"]} == {
            parent: svc.link(parent, target).label_ro for parent in (left, right)
        }
        assert all(link["target"]["id"] == target for link in earned["links"])
        assert "recipes" not in body and "routes" not in body
        assert client.get(url).json()["inventory"] == body["inventory"]
    finally:
        A.store.delete(gid)


@pytest.mark.parametrize(("source", "target"), [
    ("n_v21gas_ecler", "n_v86_food_crema_vanilie"),
    ("n_v21gas_savarina", "n_v86_food_frisca"),
])
def test_reviewed_dessert_to_cream_feedback_is_hot_but_preserves_identity_and_answer_custody(
    source, target,
):
    svc = get_service()
    assert svc.link(source, target) is None
    assert svc.link(target, source) is not None
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=svc.label(source))
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        guess = body["guess"]
        assert (guess["id"], guess["label"], guess["rank"], guess["distance"]) == (
            source, svc.label(source), 2, 1,
        )
        assert guess["temperature"] == "Fierbinte" and guess["closeness"] < 100
        _hidden(body, target)
        repeated = _post(client, url + "/guess", text=svc.node(source).aliases[0])
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        assert repeated["guess"] == guess
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text=svc.label(target))
        assert won["won"] and won["attempts"] == 2
        assert won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)
    client, gid, url = _context_game(source)
    try:
        won = _post(client, url + "/guess", text=svc.label(source))
        assert won["won"] and won["guess"]["id"] == source and won["guess"]["rank"] == 1
        assert won["score"] == 1000
    finally:
        C.store.delete(gid)


def test_each_reverse_feedback_policy_is_closed_to_its_single_existing_target():
    svc = get_service()
    for source, target in (
        ("n_v21gas_ecler", "n_v86_food_crema_vanilie"),
        ("n_v21gas_savarina", "n_v86_food_frisca"),
    ):
        for other in svc.graph.nodes:
            assert C._feedback_anchor_id(svc, source, other) == (
                target if other == target else source
            ), (source, other)
        assert C._feedback_anchor_id(svc, source, "missing_target") == source
        assert C._feedback_anchor_id(svc, "missing_source", target) == "missing_source"
        # Even matching canonical IDs cannot supply a target absent from a custom KG.
        without_target = WordGameService(Graph.from_records([
            {"id": source, "label_ro": svc.label(source), "category": "gastronomie",
             "node_type": "concept", "description": "Custom source", "salience": 0.8},
        ], []))
        assert C._feedback_anchor_id(without_target, source, target) == source


@pytest.mark.parametrize(("record_id", "target", "opener", "owner"), [
    ("ct_gastronomie_341", "n_v2gas_branza", "laptelui", "n_v4gas_lapte"),
    ("ct_gastronomie_342", "n_v4gas_lapte", "brânzeturi", "n_v2gas_branza"),
    ("ct_gastronomie_343", "n_v21gas_savarina", "frișcă naturală", "n_v86_food_frisca"),
    ("ct_gastronomie_344", "n_v86_food_frisca", "savarine", "n_v21gas_savarina"),
    ("ct_gastronomie_345", "n_v86_food_crema_vanilie", "eclere", "n_v21gas_ecler"),
])
def test_five_public_targets_keep_clues_and_hot_openers_private_until_the_exact_win(
    record_id, target, opener, owner,
):
    eligible = {item.id for item in get_pack().pool("contexto", category="gastronomie")
                if item._pilot_eligible}
    assert record_id in eligible
    seed = contexto_seed(target, difficulty="usor")
    client = Client()
    created = _post(client, (
        "/api/wordgames/contexto/games"
        f"?category=gastronomie&difficulty=usor&seed={seed}"
    ))
    gid = created["game_id"]
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        session = C.store.get(gid)
        assert session is not None and session.target == target and session.pack_id == record_id
        _hidden(created, target)
        for attempt, word in enumerate(("stilou", "fotbal", "București"), 1):
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] and not body["won"] and body["attempts"] == attempt
            _hidden(body, target)
        clue = _post(client, url + "/clue")
        assert clue["clue_kind"] == "warmer" and clue["clues_used"] == 1
        assert clue["word"]["rank"] > 1
        _hidden(clue, target)
        resumed = client.get(url).json()
        assert resumed["attempts"] == 3 and resumed["clues_used"] == 1
        assert resumed["guesses"] == body["guesses"]
        _hidden(resumed, target)
        hot = _post(client, url + "/guess", text=opener)
        assert hot["ok"] and not hot["won"] and hot["attempts"] == 4
        assert hot["guess"]["id"] == owner and hot["guess"]["distance"] == 1
        assert hot["guess"]["temperature"] == "Fierbinte"
        _hidden(hot, target)
        repeated = _post(client, url + "/guess", text=opener.upper())
        assert repeated["attempts"] == 4 and repeated["feedback"]["kind"] == "repeat"
        assert repeated["guesses"] == hot["guesses"]
        won = _post(client, url + "/guess", text=get_service().label(target))
        assert won["won"] and won["attempts"] == 5 and won["clues_used"] == 1
        assert won["guess"]["id"] == target and won["guess"]["rank"] == 1
        assert client.get(url).json()["won"]
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("intermediate", "node_id"), [
    ("frișcă bătută", "n_v86_food_frisca"),
    ("congelatorul", "n_v86_kitchen_congelator"),
])
def test_public_fridge_round_shows_both_unmarked_bridges_and_resumes_each_legal_route(
    intermediate, node_id,
):
    chosen = None
    for seed in range(1000):
        item = L._pick_curated(
            random.Random(seed), daily=None, category="gastronomie", difficulty="usor",
            exclude_ids=set(),
        )
        if item is not None and item.id == "lt_gastronomie_222":
            chosen = seed
            break
    assert chosen is not None, "reviewed Frigider→Înghețată must be publicly selectable"
    client = Client()
    created = _post(client, (
        "/api/wordgames/lant/games"
        f"?category=gastronomie&difficulty=usor&seed={chosen}"
    ))
    gid = created["game_id"]
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        assert created["start"]["id"] == "n_v24_home_appliances_frigider"
        assert created["target"]["id"] == "n_v3gas_inghetata" and created["optimal"] == 2
        choices = created["choices"]
        assert {"Frișcă", "Congelator"} <= {row["label"] for row in choices}
        assert all(set(row) == {"label", "relation"} for row in choices)
        rejected = _post(client, url + "/move", text="înghețată")
        assert rejected["ok"] is False and client.get(url).json()["moves"] == 0
        first = _post(client, url + "/move", text=intermediate)
        assert first["ok"] and not first["won"] and first["moves"] == 1
        assert first["path"][-1]["id"] == node_id
        assert client.get(url).json()["path"] == first["path"]
        won = _post(client, url + "/move", text="înghețată")
        assert won["ok"] and won["won"] and won["moves"] == 2 and won["score"] == 1000
        assert [row["id"] for row in won["path"]] == [
            "n_v24_home_appliances_frigider", node_id, "n_v3gas_inghetata",
        ]
        assert client.get(url).json()["path"] == won["path"]
    finally:
        L.store.delete(gid)
