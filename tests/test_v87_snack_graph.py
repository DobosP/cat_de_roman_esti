"""Reviewed snack words, senses and graph direction survive real typed play."""

from __future__ import annotations

import ast
import hashlib
import json
import unicodedata
from copy import deepcopy
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
REVIEW = ROOT / "docs/reviews/v87-snack-and-action-quality"
FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
GRAPH_SHA256 = "6840ba5930e75e94c0d605e9428bec59b6ebda6fb640881d8ff41de2df8c707e"
MODULE_SHA256 = "f781e6b9152dbcfe3019d7cbe8a3f684d5575b221ce67753b8e060e29ddf80f6"
BASELINE_SHA256 = "b612eda1fb8712fb57f1e16ca2a4fed3e5f6cec847c977ab45ee420c575ffa1a"
FORMS = {
    "n_v87_food_chec": ("Chec", ("checul", "checului", "checuri", "chec de casă")),
    "n_v87_food_pandispan": ("Pandișpan", (
        "pandișpanul", "pandișpanului", "pandișpanuri",
    )),
    "n_v87_food_cremsnit": ("Cremșnit", (
        "cremșnitul", "cremșnitului", "cremșnituri", "cremeș",
    )),
    "n_v87_food_tort_diplomat": ("Tort Diplomat", (
        "tortul Diplomat", "tortului Diplomat", "torturi Diplomat",
    )),
    "n_v87_food_piscot": ("Pișcot", ("pișcotul", "pișcotului", "pișcoturi", "pișcoturile")),
    "n_v87_food_briosa": ("Brioșă", ("brioșei", "brioșe", "brioșele", "brioșelor")),
    "n_v87_food_praf_copt": ("Praf de copt", (
        "praful de copt", "prafului de copt", "praf de copt pentru prăjituri",
    )),
    "n_v87_food_bicarbonat": ("Bicarbonat de sodiu alimentar", (
        "bicarbonatul de sodiu alimentar", "bicarbonat alimentar",
        "bicarbonat de sodiu pentru copt",
    )),
    "n_v87_food_gelatina": ("Gelatină alimentară", (
        "gelatinei alimentare", "gelatină pentru prăjituri", "gelatină alimentară pudră",
    )),
}
PREDECESSORS = {
    "n_v87_food_chec": "n_v24_food_pantry_faina",
    "n_v87_food_pandispan": "n_v24_food_pantry_faina",
    "n_v87_food_cremsnit": "n_v86_food_crema_vanilie",
    "n_v87_food_tort_diplomat": "n_v87_food_piscot",
    "n_v87_food_piscot": "n_v24_food_pantry_faina",
    "n_v87_food_briosa": "n_v24_food_pantry_faina",
    "n_v87_food_praf_copt": "n_v87_food_bicarbonat",
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


def test_served_snack_graph_matches_the_complete_independent_review():
    candidate_bytes = (REVIEW / "graph-candidates.json").read_bytes()
    assert hashlib.sha256(candidate_bytes).hexdigest() == GRAPH_SHA256
    candidate = json.loads(candidate_bytes)
    review = _json(REVIEW / "graph-review.json")
    assert review["verdict"] == "accept" and review["current_blockers"] == []
    assert review["candidate_sha256"] == GRAPH_SHA256
    assert review["module_sha256"] == MODULE_SHA256
    assert [edge["edge_index"] for edge in review["edges"]] == list(range(50))
    assert all(edge["verdict"] == "accept" for edge in review["edges"])
    assert (review["counts"]["nodes"], review["counts"]["forms"],
            review["counts"]["edges"], review["counts"]["removals"]) == (9, 31, 50, 0)
    module = (ROOT / "scripts/snack_graph_v87_data.py").read_bytes()
    assert hashlib.sha256(module).hexdigest() == MODULE_SHA256
    tree = ast.parse(module)
    assert list(_assigned(tree, "NODES")) == candidate["nodes"]
    assert list(_assigned(tree, "EDGES")) == candidate["edges"]
    assert candidate["remove_edges"] == []
    nodes = {node["id"]: node for node in _json(FIXTURE)["kg_nodes"]}
    assert {node for node in nodes if node.startswith("n_v87_")} == set(FORMS)
    assert len(FORMS) == 9 and sum(len(forms) for _, forms in FORMS.values()) == 31
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


def test_complete_v86_graph_and_all_old_native_owners_reconstruct_exactly():
    from tests.content_history import before_v87_fixture, before_v88_fixture

    current = before_v88_fixture(_json(FIXTURE))
    baseline = before_v87_fixture(_json(FIXTURE))
    encoded = (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == BASELINE_SHA256
    assert FIXTURE.read_bytes() == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    assert len(current["kg_nodes"]) - len(baseline["kg_nodes"]) == 9
    assert len(current["kg_edges"]) - len(baseline["kg_edges"]) == 50
    assert current["kg_puzzles"] == baseline["kg_puzzles"]
    old_edges = {edge["id"]: edge for edge in baseline["kg_edges"]}
    current_edges = {edge["id"]: edge for edge in current["kg_edges"]}
    assert all(current_edges[key] == edge for key, edge in old_edges.items())
    old_nodes = {node["id"]: node for node in baseline["kg_nodes"]}
    new_nodes = {node["id"]: node for node in current["kg_nodes"]}
    for node_id, old in old_nodes.items():
        assert {k: v for k, v in old.items() if k != "degree"} == {
            k: v for k, v in new_nodes[node_id].items() if k != "degree"
        }
    previous = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    svc = get_service()
    for node in baseline["kg_nodes"]:
        for surface in (node["id"], node["label_ro"], *node.get("aliases", [])):
            assert svc.resolve(surface) == previous.resolve(surface), surface


@pytest.mark.parametrize("owner", FORMS)
def test_all_snack_forms_keep_exact_identity_under_unicode_repeat_and_self_win(owner):
    label, forms = FORMS[owner]
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        for form in (label, *forms):
            assert get_service().resolve(form) == owner
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
        assert client.get(url).json()["guesses"] == body["guesses"]
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("owner", PREDECESSORS)
def test_every_reachable_snack_form_is_a_real_typed_lant_destination(owner):
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


def test_all_50_reviewed_directions_work_and_their_unreviewed_reverses_do_not():
    edges = _json(REVIEW / "graph-candidates.json")["edges"]
    assert len(edges) == 50 and all(not edge["bidirectional"] for edge in edges)
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


def test_cremes_is_the_single_reviewed_equivalent_and_not_plain_cream():
    candidate = _json(REVIEW / "graph-candidates.json")
    assert [(row["node_id"], row["surface"]) for row in candidate["lexical_equivalents"]] == [
        ("n_v87_food_cremsnit", "cremeș"),
    ]
    review = _json(REVIEW / "graph-review.json")
    equivalents = [(node["id"], form["surface"]) for node in review["nodes"]
                   for form in node["forms"] if form["kind"] == "documented_regional_equivalent"]
    assert equivalents == [("n_v87_food_cremsnit", "cremeș")]
    assert get_service().resolve("cremeș") == "n_v87_food_cremsnit"
    client, gid, url = _context_game("n_v86_food_crema_vanilie")
    try:
        body = _post(client, url + "/guess", text="cremeș")
        assert body["ok"] and not body["won"]
        assert body["guess"]["id"] == "n_v87_food_cremsnit"
        _hidden(body, "n_v86_food_crema_vanilie")
        won = _post(client, url + "/guess", text="cremă de vanilie")
        assert won["won"] and won["guess"]["id"] == "n_v86_food_crema_vanilie"
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("surface", "owner", "target"), [
    ("făină", "n_v24_food_pantry_faina", "n_v24_food_snack_biscuit"),
    ("unt", "n_v24_food_breakfast_unt", "n_v24_food_snack_biscuit"),
    ("zahăr", "n_v24_food_pantry_zahar", "n_v24_food_snack_biscuit"),
    ("cuptor de bucătărie", "n_v84_food_cuptor", "n_v24_food_snack_biscuit"),
    ("praf de copt", "n_v87_food_praf_copt", "n_v24_food_snack_biscuit"),
    ("bicarbonat alimentar", "n_v87_food_bicarbonat", "n_v24_food_snack_biscuit"),
    ("lapte", "n_v4gas_lapte", "n_v85_food_ciocolata"),
    ("zahăr", "n_v24_food_pantry_zahar", "n_v85_food_ciocolata"),
    ("cremă de vanilie", "n_v86_food_crema_vanilie", "n_v87_food_cremsnit"),
    ("frișcă", "n_v86_food_frisca", "n_v87_food_tort_diplomat"),
    ("zahăr pudră", "n_v86_food_zahar_pudra", "n_v87_food_piscot"),
    ("cacao", "n_v85_food_cacao", "n_v87_food_chec"),
])
def test_defining_snack_inputs_are_hot_nonwinning_private_and_resumable(surface, owner, target):
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        guess = body["guess"]
        assert guess["id"] == owner and guess["distance"] == 1
        assert guess["temperature"] == "Fierbinte" and 2 <= guess["rank"] <= 12
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


@pytest.mark.parametrize(("surface", "owner", "target"), [
    ("chec", "n_v87_food_chec", "n_v4gas_lapte"),
    ("brioșă", "n_v87_food_briosa", "n_gas_cozonac"),
    ("pandișpan", "n_v87_food_pandispan", "n_v18gas_amandina"),
])
def test_new_finished_foods_are_usable_native_guesses_with_real_outgoing_associations(
    surface, owner, target,
):
    assert P.resolve_projection(surface) is None
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"]
        assert body["guess"]["id"] == owner
        assert body["guess"]["distance"] == 1 and body["guess"]["temperature"] == "Fierbinte"
        assert get_service().link(owner, target) is not None
        _hidden(body, target)
    finally:
        C.store.delete(gid)


def test_only_chec_and_briosa_projections_retire_without_scoring_from_audit_metadata():
    from tests.content_history import before_v87_projection_rows, before_v88_projection_rows

    live = [(term.surface, term.anchor_id, term.domain, term.rank_penalty,
             term.mapping_kind, term.public_id) for term in P.PROJECTION_TERMS]
    before = before_v87_projection_rows(live)
    live = before_v88_projection_rows(live)
    assert len(before) == 468 and len(live) == 467
    assert [row for row in before if row[0] not in {"chec", "brioșă"}] == [
        row for row in live if row[0] != "tort"
    ]
    assert len([row for row in live if row[0] == "tort"]) == 1
    assert P.resolve_projection("chec") is None and P.resolve_projection("brioșă") is None
    terms = [asdict(term) for term in P.PROJECTION_TERMS]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(P, "NATIVE_PROJECTION_REPLACEMENTS", ())
        assert [asdict(term) for term in P._build_terms()] == terms


def test_qualified_chemical_food_inputs_do_not_capture_generic_or_unrelated_senses():
    svc = get_service()
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        for word in ("gelatină", "bicarbonat", "bicarbonat de sodiu", "bicarbonat de amoniu",
                     "cremă", "muffin", "rece"):
            assert svc.resolve(word) is None and svc.resolve_fuzzy(word) is None
            body = _post(client, url + "/guess", text=word)
            assert body["ok"] is False and body["attempts"] == 0
            assert not body.get("needs_confirmation")
            _hidden(body, "n_mihai_eminescu")
        assert svc.resolve("drojdie") == "n_v84_food_drojdie"
        assert len({svc.resolve(word) for word in (
            "drojdie", "praf de copt", "bicarbonat alimentar", "gelatină alimentară",
        )}) == 4
    finally:
        C.store.delete(gid)


def test_hot_chocolate_stays_a_separate_nonwinning_drink_for_the_solid_food_target():
    target = "n_v85_food_ciocolata"
    term = P.resolve_projection("ciocolată caldă")
    assert term is not None and term.public_id == "ctxp_cb75bc0c21d2e2940911"
    assert get_service().resolve("ciocolată caldă") is None
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text="ciocolată caldă")
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        assert body["guess"]["id"] == term.public_id and body["guess"]["rank"] == 2
        assert body["guess"]["distance"] == 1
        assert body["guess"]["temperature"] == "Fierbinte"
        assert body["guess"]["closeness"] < 100
        # The player's compound legitimately contains the target's word; custody is
        # about the hidden answer/anchor fields, not removing their own typed label.
        assert "target" not in body and "solution" not in body
        assert target not in json.dumps(body) and "anchor_id" not in json.dumps(body)
        repeated = _post(client, url + "/guess", text="CIOCOLATA CALDA")
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text="ciocolată")
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("left", "right", "target"), [
    ("n_v24_food_pantry_faina", "n_v24_food_breakfast_unt", "n_v24_food_snack_biscuit"),
    ("n_v87_food_piscot", "n_v87_food_gelatina", "n_v87_food_tort_diplomat"),
])
def test_real_snack_recipe_outputs_explain_their_earned_oriented_links(left, right, target):
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
        assert target not in json.dumps(client.get(url).json())
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
    ("n_v87_food_pandispan", "n_v87_food_chec"),
    ("n_v24_food_snack_biscuit", "n_v87_food_piscot"),
    ("n_v4gas_prajitura", "n_v87_food_cremsnit"),
])
def test_reviewed_native_near_guesses_are_hot_but_keep_identity_and_exact_answer_custody(
    source, target,
):
    svc = get_service()
    assert svc.link(source, target) is None
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


def test_three_native_near_guess_overrides_are_closed_to_the_reviewed_target_scopes():
    svc = get_service()
    for source, target in (
        ("n_v87_food_pandispan", "n_v87_food_chec"),
        ("n_v24_food_snack_biscuit", "n_v87_food_piscot"),
        ("n_v4gas_prajitura", "n_v87_food_cremsnit"),
    ):
        for other in svc.graph.nodes:
            assert C._feedback_anchor_id(svc, source, other) == (
                target if other == target else source
            ), (source, other)
        assert C._feedback_anchor_id(svc, source, "missing_target") == source
        assert C._feedback_anchor_id(svc, "missing_source", target) == "missing_source"
        incomplete = WordGameService(Graph.from_records([
            {"id": source, "label_ro": svc.label(source), "category": "gastronomie",
             "node_type": "concept", "description": "Custom source", "salience": 0.8},
        ], []))
        assert C._feedback_anchor_id(incomplete, source, target) == source


def test_projected_tort_is_a_hot_nonwinning_class_cue_and_never_a_native_alias():
    term = P.resolve_projection("tort")
    assert term is not None
    assert (term.public_id, term.anchor_id) == (
        "ctxp_7de7b40dd74b4b0f44bf", "n_v4gas_prajitura",
    )
    assert get_service().resolve("tort") is None
    target = "n_v87_food_tort_diplomat"
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text="tort")
        assert body["ok"] and not body["won"] and body["attempts"] == 1
        assert (body["guess"]["id"], body["guess"]["label"], body["guess"]["rank"]) == (
            term.public_id, "Tort", 2,
        )
        assert body["guess"]["temperature"] == "Fierbinte"
        assert body["guess"]["distance"] == 1 and body["guess"]["closeness"] < 100
        _hidden(body, target)
        repeated = _post(client, url + "/guess", text="TORT")
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text="tortul Diplomat")
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("surface", "target", "fallback"), [
    ("tort", "n_v87_food_tort_diplomat", "n_v4gas_prajitura"),
    ("ciocolată caldă", "n_v85_food_ciocolata", "n_v24_food_snack_ceai"),
])
def test_projected_neighborhood_selection_is_exact_and_requires_its_real_anchor(
    surface, target, fallback,
):
    svc = get_service()
    term = P.resolve_projection(surface)
    assert term is not None and term.anchor_id == fallback
    policy = P.PROJECTION_NEIGHBORHOODS[term.key]
    assert policy.exact_target_ids == frozenset({target})
    assert policy.include_direct_neighbors is False
    for other in svc.graph.nodes:
        assert C._projection_anchor_id(svc, term, other) == (
            target if other == target else fallback
        ), (surface, other)
    for missing in (target, fallback):
        kept = fallback if missing == target else target
        incomplete = WordGameService(Graph.from_records([
            {"id": kept, "label_ro": svc.label(kept), "category": "gastronomie",
             "node_type": "concept", "description": "Custom node", "salience": 0.8},
        ], []))
        assert C._projection_anchor_id(incomplete, term, target) == fallback


def test_tort_fallback_cannot_inherit_the_native_prajitura_to_cremsnit_override():
    target = "n_v87_food_cremsnit"
    client, gid, url = _context_game(target)
    try:
        projected = _post(client, url + "/guess", text="tort")
        assert projected["ok"] and not projected["won"]
        assert projected["guess"]["id"] == "ctxp_7de7b40dd74b4b0f44bf"
        assert projected["guess"]["distance"] > 1 and projected["guess"]["rank"] > 2
        assert projected["guess"]["temperature"] == "Rece"
        _hidden(projected, target)
        native = _post(client, url + "/guess", text="prăjitură")
        assert native["ok"] and not native["won"] and native["attempts"] == 2
        assert native["guess"]["id"] == "n_v4gas_prajitura"
        assert native["guess"]["rank"] == 2 and native["guess"]["temperature"] == "Fierbinte"
        _hidden(native, target)
    finally:
        C.store.delete(gid)


def test_projected_typo_privacy_uses_the_isolated_effective_fallback():
    client = Client()
    for typo, label, target, should_offer in (
        ("tortzz", "Tort", "n_v87_food_cremsnit", True),
        ("tortzz", "Tort", "n_v87_food_tort_diplomat", False),
        ("ciocolata caldazz", "Ciocolată caldă", "n_v85_food_ciocolata", False),
    ):
        assert get_service().resolve(typo) is None and get_service().resolve_fuzzy(typo) is None
        assert label in [term.label for term in P.suggest_projection(typo)]
        gid = C.store.create(C._build_session(target, "usor", None))
        url = f"/api/wordgames/contexto/games/{gid}"
        try:
            body = _post(client, url + "/guess", text=typo)
            assert body["ok"] is False and body["attempts"] == 0
            assert not body.get("needs_confirmation")
            assert (label in body["suggestions"]) is should_offer
            _hidden(body, target)
            assert client.get(url).json()["guesses"] == []
        finally:
            C.store.delete(gid)


def test_projection_isolation_retains_legacy_feedback_proxies_and_ingredient_policy():
    svc = get_service()
    assert C._feedback_anchor_id(
        svc, "n_v30_kitchen_cookware_oala", "n_mihai_eminescu", allow_exact_pairs=False,
    ) == "n_v4gas_bucatarie"
    assert C._feedback_anchor_id(
        svc, "n_v81_food_pantry_nuca", "n_mihai_eminescu", allow_exact_pairs=False,
    ) == "n_v24_food_breakfast_miere"
    assert C._feedback_anchor_id(
        svc, "n_v81_food_pantry_nuca", "n_gas_cozonac", allow_exact_pairs=False,
    ) == "n_v81_food_pantry_nuca"
    session = C._build_session("n_v4gas_bucatarie", "usor", None)
    score = C._score_feedback(
        svc, session, "n_v30_kitchen_cookware_oala", nonwinning=True,
    )
    assert score.anchor_id == "n_v4gas_bucatarie"
    assert score.rank == 2 and score.feedback_distance == 1


def _hidden_after_player_echo(body, target, visible_owner):
    """Mask only already submitted public labels before checking hidden-answer custody."""
    cleaned = deepcopy(body)
    expected_label = (
        next(term.label for term in P.PROJECTION_TERMS if term.public_id == visible_owner)
        if visible_owner.startswith("ctxp_") else get_service().label(visible_owner)
    )

    def strip_echo(value):
        if isinstance(value, dict):
            if value.get("id") == visible_owner and "label" in value:
                assert value["label"] == expected_label
                value["label"] = "submitted public guess"
            for child in value.values():
                strip_echo(child)
        elif isinstance(value, list):
            for child in value:
                strip_echo(child)

    strip_echo(cleaned)
    _hidden(cleaned, target)


@pytest.mark.parametrize(("record_id", "target", "opener", "owner"), [
    ("ct_gastronomie_346", "n_v24_food_snack_biscuit", "făinii", "n_v24_food_pantry_faina"),
    ("ct_gastronomie_347", "n_v87_food_chec", "pandișpan", "n_v87_food_pandispan"),
    ("ct_gastronomie_348", "n_v87_food_cremsnit", "prăjituri", "n_v4gas_prajitura"),
    ("ct_gastronomie_349", "n_v87_food_tort_diplomat", "tort", "ctxp_7de7b40dd74b4b0f44bf"),
    ("ct_gastronomie_350", "n_v87_food_piscot", "biscuiți", "n_v24_food_snack_biscuit"),
    ("ct_gastronomie_351", "n_v85_food_ciocolata", "ciocolată caldă",
     "ctxp_cb75bc0c21d2e2940911"),
])
def test_six_public_snack_rounds_keep_private_clues_and_distinct_hot_guesses_until_exact_win(
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
        # Hot chocolate includes the user's own answer-word substring; it must
        # preserve that echoed drink label without exposing the actual answer ID.
        _hidden_after_player_echo(hot, target, owner)
        repeated = _post(client, url + "/guess", text=opener.upper())
        assert repeated["attempts"] == 4 and repeated["feedback"]["kind"] == "repeat"
        assert repeated["guesses"] == hot["guesses"]
        _hidden_after_player_echo(repeated, target, owner)
        resumed = client.get(url).json()
        assert resumed["guesses"] == repeated["guesses"] and resumed["attempts"] == 4
        _hidden_after_player_echo(resumed, target, owner)
        answer = "cremeș" if target == "n_v87_food_cremsnit" else get_service().label(target)
        won = _post(client, url + "/guess", text=answer)
        assert won["won"] and won["attempts"] == 5 and won["clues_used"] == 1
        assert won["guess"]["id"] == target and won["guess"]["rank"] == 1
        assert client.get(url).json()["won"]
    finally:
        C.store.delete(gid)
