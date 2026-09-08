"""V85's reviewed ingredients improve actual typed play and directed associations."""

from __future__ import annotations

import ast
import hashlib
import json
import random
import unicodedata
from dataclasses import asdict
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.graph import Graph  # noqa: E402
from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames import contexto as C  # noqa: E402
from cat_de_roman_esti.wordgames import contexto_projection as P  # noqa: E402
from cat_de_roman_esti.wordgames import lant as L  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import WordGameService, get_service  # noqa: E402
from tests.content_history import (  # noqa: E402
    before_v85_fixture,
    before_v85_projection_rows,
    before_v86_fixture,
    before_v86_projection_rows,
)
from tests.content_scenarios import contexto_seed  # noqa: E402
from tests.current_content import CURRENT_CONTENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v85-ingredient-feedback-and-board-clarity"
FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
PREFIX = "n_v85_food_"
FORMS = {
    "scortisoara": ("Scorțișoară", (
        "scorțișoarei", "scorțișoară măcinată", "batoane de scorțișoară",
    )),
    "cacao": ("Cacao", ("cacaua", "cacauei", "pudră de cacao")),
    "vanilie": ("Vanilie", ("vanilia", "vaniliei", "păstaie de vanilie")),
    "ciocolata": ("Ciocolată", ("ciocolate", "ciocolatei", "ciocolată de menaj")),
    "stafide": ("Stafide", ("stafidă", "stafidele", "stafidelor")),
    "migdale": ("Migdale", ("migdală", "migdalele", "migdalelor", "migdale dulci")),
    "alune_padure": ("Alune de pădure", (
        "alună de pădure", "alunele de pădure", "alunelor de pădure",
    )),
    "seminte_floarea_soarelui": ("Semințe de floarea-soarelui", (
        "semințele de floarea-soarelui", "semințelor de floarea-soarelui",
        "sămânță de floarea-soarelui",
    )),
}
SOURCE_ONLY = {
    "scortisoara": "n_v42gas_placinta_mere",
    "cacao": "n_v18gas_salam_de_biscuiti",
    "vanilie": "n_v21gas_ecler",
    "seminte_floarea_soarelui": "n_v21gas_halva",
}
PREDECESSORS = {
    "ciocolata": PREFIX + "cacao", "stafide": "n_v24_food_small_fruit_strugure",
    "migdale": "n_v18gas_fistic", "alune_padure": PREFIX + "migdale",
}
CANDIDATE_SHA256 = "be8e06af36b6b0e389ef1cc879ba8be6fb2a27b6ed0c960a78f0a2dde4fddd2b"
ORIGINAL_MODULE_SHA256 = "cee50de77b278879dadf083a69a8381a2d864c61092c19d330c43d2051e2cf53"
MODULE_SHA256 = "efdbffe1ec142c42ebdd602346819ea49e6b344a1000040f57390ec659fe9c25"
CORRECTION_SHA256 = "8066e18d5585ad0e9158817e77668276ae2c2bb0569ef57d7825cdd2a699140d"


def _json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _assigned(tree, name):
    return ast.literal_eval(next(
        statement.value for statement in tree.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    ))


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
    gid = C.store.create(C._build_session(target, "normal", None))
    return Client(), gid, f"/api/wordgames/contexto/games/{gid}"


def test_exact_reviewed_concepts_forms_and_graph_records_are_served():
    candidate_bytes = (REVIEW / "graph-candidates.json").read_bytes()
    assert hashlib.sha256(candidate_bytes).hexdigest() == CANDIDATE_SHA256
    candidate = json.loads(candidate_bytes)
    review = _json(REVIEW / "graph-review.json")
    assert review["verdict"] == "accept"
    assert (review["candidate_sha256"], review["module_sha256"]) == (
        CANDIDATE_SHA256, ORIGINAL_MODULE_SHA256,
    )
    assert review["coverage"]["edge_indices"] == list(range(40))
    assert len(review["forms"]) == 25
    module_bytes = (ROOT / "scripts/ingredient_graph_v85_data.py").read_bytes()
    assert hashlib.sha256(module_bytes).hexdigest() == MODULE_SHA256
    tree = ast.parse(module_bytes)
    assert list(_assigned(tree, "NODES")) == candidate["nodes"]
    authored_edges = list(_assigned(tree, "EDGES"))
    assert authored_edges[:40] == candidate["edges"] and len(authored_edges) == 41
    assert candidate["remove_edges"] == []
    correction_bytes = (REVIEW / "mucenici-link-correction.json").read_bytes()
    assert hashlib.sha256(correction_bytes).hexdigest() == CORRECTION_SHA256
    correction = json.loads(correction_bytes)
    addendum = _json(REVIEW / "graph-review-addendum.json")
    assert addendum["verdict"] == "accept" and addendum["module_sha256"] == MODULE_SHA256
    assert addendum["correction_sha256"] == CORRECTION_SHA256
    assert authored_edges[-1] == correction["replacement"]
    assert list(_assigned(tree, "REMOVE_EDGES")) == [correction["before"]]
    assert (len(candidate["nodes"]), len(candidate["edges"])) == (8, 40)
    assert sum(len(forms) for _, forms in FORMS.values()) == 25
    raw = _json(FIXTURE)
    nodes = {node["id"]: node for node in raw["kg_nodes"]}
    assert {node for node in nodes if node.startswith(PREFIX)} == {
        PREFIX + slug for slug in FORMS
    }
    for expected in candidate["nodes"]:
        actual = nodes[expected["id"]]
        assert {key: actual[key] for key in expected} == expected
        assert (actual["label_ro"], tuple(actual["aliases"])) == FORMS[
            expected["id"].removeprefix(PREFIX)
        ]
    svc = get_service()
    for expected in authored_edges:
        edge = svc.link(expected["src"], expected["dst"])
        assert edge is not None and not edge.is_distractor
        assert (edge.src_id, edge.dst_id, edge.relation, edge.label_ro,
                edge.strength, edge.bidirectional) == (
            expected["src"], expected["dst"], expected["relation"], expected["label_ro"],
            expected["strength"], bool(expected["bidirectional"]),
        )
    assert sum(1 + edge["bidirectional"] for edge in candidate["edges"]) == 45


def test_full_v84_graph_reconstructs_and_every_old_exact_owner_is_preserved():
    current = _json(FIXTURE)
    v85 = before_v86_fixture(current)
    baseline = before_v85_fixture(current)
    encoded = (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "3fb0f97c5b4c813eb72d8fd3589c4ce92f724d0565db840c1bc3909458a60ab0"
    )
    assert FIXTURE.read_bytes() == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    # Preserve this wave's exact delta on its reconstructed graph; later native
    # concepts have separate full-artifact and old-owner preservation contracts.
    assert len(v85["kg_nodes"]) - len(baseline["kg_nodes"]) == 8
    assert len(v85["kg_edges"]) - len(baseline["kg_edges"]) == 40
    assert current["kg_puzzles"] == baseline["kg_puzzles"]
    assert not any(edge["id"] == "de5559" for edge in current["kg_edges"])
    assert all(edge in current["kg_edges"] for edge in baseline["kg_edges"]
               if edge["id"] != "de5559")
    before_edge = next(edge for edge in baseline["kg_edges"] if edge["id"] == "de5559")
    after_edge = next(edge for edge in current["kg_edges"] if (
        edge["src_id"], edge["dst_id"], edge["relation"]
    ) == ("n_v17gas_mucenici", "n_moldova_reg", "related_to"))
    assert before_edge["label_ro"] == "varianta fiartă, moldovenească"
    assert after_edge["label_ro"] == "varianta coaptă, moldovenească"
    assert {key: value for key, value in before_edge.items() if key not in {"id", "label_ro"}} == {
        key: value for key, value in after_edge.items() if key not in {"id", "label_ro"}
    }
    previous = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    current_service = get_service()
    surfaces = [surface for node in baseline["kg_nodes"]
                for surface in (node["label_ro"], *node.get("aliases", []))]
    assert len(surfaces) == 10897
    for surface in surfaces:
        assert current_service.resolve(surface) == previous.resolve(surface), surface


@pytest.mark.parametrize("slug", FORMS)
def test_all_forms_and_unicode_variants_keep_exact_identity_and_one_private_attempt(slug):
    owner = PREFIX + slug
    label, forms = FORMS[slug]
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
        assert body["feedback"]["kind"] == "repeat"
        resumed = client.get(url).json()
        assert resumed["guesses"] == body["guesses"] and resumed["attempts"] == 1
        _hidden(resumed, "n_mihai_eminescu")
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("slug", FORMS)
def test_every_authored_form_wins_only_its_own_identity(slug):
    owner = PREFIX + slug
    for form in FORMS[slug][1]:
        client, gid, url = _context_game(owner)
        try:
            body = _post(client, url + "/guess", text=form)
            assert body["ok"] and body["won"] and body["attempts"] == 1
            assert (body["guess"]["id"], body["guess"]["rank"]) == (owner, 1)
            assert body["score"] == 1000
        finally:
            C.store.delete(gid)


@pytest.mark.parametrize(("surface", "owner", "target"), [
    ("scorțișoară", PREFIX + "scortisoara", "n_v42gas_placinta_mere"),
    ("cacao", PREFIX + "cacao", "n_v18gas_salam_de_biscuiti"),
    ("cacao", PREFIX + "cacao", "n_v18gas_amandina"),
    ("unt", "n_v24_food_breakfast_unt", "n_v42gas_placinta_mere"),
    ("vanilie", PREFIX + "vanilie", "n_v21gas_ecler"),
    ("stafide", PREFIX + "stafide", "n_v17gas_pasca"),
    ("migdale", PREFIX + "migdale", "n_v24_food_snack_biscuit"),
    ("alune de pădure", PREFIX + "alune_padure", PREFIX + "ciocolata"),
    ("semințe de floarea-soarelui", PREFIX + "seminte_floarea_soarelui", "n_v21gas_halva"),
])
def test_specific_ingredient_openers_are_direct_hot_nonwinning_and_resumable(
    surface, owner, target,
):
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"]
        guess = body["guess"]
        assert guess["id"] == owner and guess["distance"] == 1
        assert guess["temperature"] == "Fierbinte" and 2 <= guess["rank"] <= 10
        assert guess["closeness"] < 100
        _hidden(body, target)
        repeat = _post(client, url + "/guess", text=surface.upper())
        assert repeat["attempts"] == 1 and repeat["feedback"]["kind"] == "repeat"
        assert repeat["guess"] == guess
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text=get_service().label(target))
        assert won["won"] and won["attempts"] == 2 and won["guess"]["id"] == target
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("surface", "slug", "target", "temperature", "minimum_hops"), [
    ("scorțișoară", "scortisoara", "n_v4gas_paine", "Rece", 3),
    ("scorțișoară", "scortisoara", "n_gas_sarmale", "Rece", 3),
    ("cacao", "cacao", "n_gas_sarmale", "Rece", 3),
    ("cacao", "cacao", "n_v3gas_cafea", "Cald", 2),
])
def test_native_spices_do_not_inherit_food_or_coffee_proxy_hotness(
    surface, slug, target, temperature, minimum_hops,
):
    assert P.resolve_projection(surface) is None
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"]
        assert body["guess"]["id"] == PREFIX + slug
        assert body["guess"]["temperature"] == temperature
        assert body["guess"]["distance"] >= minimum_hops
        assert body["guess"]["rank"] > 10
        _hidden(body, target)
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("slug", "typo"), [("cacao", "cacaou"), ("scortisoara", "scortiisoara")])
def test_confident_native_typos_win_the_target_but_require_confirmation_elsewhere(slug, typo):
    target = PREFIX + slug
    assert get_service().resolve(typo) is None
    assert get_service().resolve_fuzzy(typo) == target
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=typo)
        # ADR-0022: a confidently corrected answer is an earned win, not a hint.
        assert body["ok"] and body["won"] and body["attempts"] == 1
        assert not body.get("needs_confirmation") and "resolved_label" not in body
        assert body["guess"]["id"] == target and body["guess"]["rank"] == 1
        assert body["target"]["id"] == target and body["score"] == 1000
    finally:
        C.store.delete(gid)
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        asked = _post(client, url + "/guess", text=typo)
        assert asked["ok"] is False and asked["needs_confirmation"]
        assert asked["attempts"] == 0 and asked["guesses"] == []
        assert asked["resolved_label"] == get_service().label(target)
        _hidden(asked, "n_mihai_eminescu")
        accepted = _post(client, url + "/guess", text=typo, confirm=asked["resolved_token"])
        assert accepted["ok"] and not accepted["won"] and accepted["attempts"] == 1
        assert accepted["guess"]["id"] == target
        _hidden(accepted, "n_mihai_eminescu")
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("slug", "typo"), [
    ("cacao", "cacaozz"), ("scortisoara", "scorțișoarăzzzz"),
])
def test_advisory_spelling_suggestions_do_not_reveal_hidden_native_targets(slug, typo):
    target = PREFIX + slug
    svc = get_service()
    assert svc.resolve(typo) is None and svc.resolve_fuzzy(typo) is None
    assert svc.label(target) in svc.suggest(typo)
    client, gid, url = _context_game(target)
    try:
        body = _post(client, url + "/guess", text=typo)
        assert body["ok"] is False and body["attempts"] == 0
        assert not body.get("needs_confirmation") and "resolved_label" not in body
        assert svc.label(target) not in body["suggestions"]
        _hidden(body, target)
        assert client.get(url).json()["guesses"] == []
    finally:
        C.store.delete(gid)


def test_qualified_ingredients_preserve_bare_projections_and_do_not_accept_ambiguous_aliases():
    svc = get_service()
    client, gid, url = _context_game("n_mihai_eminescu")
    try:
        for surface in ("alune", "semințe", "păstaie"):
            assert svc.resolve(surface) is None and svc.resolve_fuzzy(surface) is None
            body = _post(client, url + "/guess", text=surface)
            assert body["ok"] is False and body["attempts"] == 0
        for surface, owner in (("vanilină", PREFIX + "vanilie"), ("cacaoa", PREFIX + "cacao")):
            assert svc.resolve(surface) is None
            body = _post(client, url + "/guess", text=surface)
            assert body["ok"] is False and body["attempts"] == 0
            assert body["needs_confirmation"] and body["resolved_label"] == svc.label(owner)
        for attempt, (surface, public_id) in enumerate((
            ("alună", "ctxp_8a009af67b895df75bd1"),
            ("floarea-soarelui", "ctxp_d391e6ad77711ce2ed78"),
            ("cappuccino", "ctxp_ee8942a099ca0328f6e2"),
            ("ciocolată caldă", "ctxp_cb75bc0c21d2e2940911"),
        ), 1):
            assert svc.resolve(surface) is None
            assert P.resolve_projection(surface).public_id == public_id
            body = _post(client, url + "/guess", text=surface)
            assert body["ok"] and body["attempts"] == attempt
            assert body["guess"]["id"] == public_id
            _hidden(body, "n_mihai_eminescu")
    finally:
        C.store.delete(gid)


def test_all_45_reviewed_directions_work_as_real_lant_moves():
    candidate = _json(REVIEW / "graph-candidates.json")
    directions = [(edge["src"], edge["dst"]) for edge in candidate["edges"]]
    directions += [(edge["dst"], edge["src"]) for edge in candidate["edges"]
                   if edge["bidirectional"]]
    assert len(directions) == len(set(directions)) == 45
    client, svc = Client(), get_service()
    for start, target in directions:
        gid = L.store.create(L.LantSession(
            start=start, target=target, optimal=1, difficulty="usor", chain=[start],
        ))
        url = f"/api/wordgames/lant/games/{gid}"
        try:
            body = _post(client, url + "/move", text=svc.label(target))
            assert body["ok"] and body["won"] and body["moves"] == 1, (start, target)
            assert [step["id"] for step in body["path"]] == [start, target]
            assert client.get(url).json()["path"] == body["path"]
        finally:
            L.store.delete(gid)


@pytest.mark.parametrize(("start", "target"), [
    ("n_v17gas_mucenici", "n_moldova_reg"), ("n_moldova_reg", "n_v17gas_mucenici"),
])
def test_relabelled_mucenici_relation_keeps_both_moves_and_explains_baked_variant(start, target):
    svc, client = get_service(), Client()
    gid = L.store.create(L.LantSession(
        start=start, target=target, optimal=1, difficulty="usor", chain=[start],
    ))
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        body = _post(client, url + "/move", text=svc.label(target))
        assert body["ok"] and body["won"] and body["moves"] == 1
        assert body["relation"] == "varianta coaptă, moldovenească"
        assert "varianta fiartă" not in json.dumps(body, ensure_ascii=False)
        assert client.get(url).json()["path"] == body["path"]
    finally:
        L.store.delete(gid)


@pytest.mark.parametrize("slug", PREDECESSORS)
def test_all_forms_of_reachable_new_nodes_are_exact_lant_destinations(slug):
    start, target = PREDECESSORS[slug], PREFIX + slug
    client = Client()
    for form in FORMS[slug][1]:
        gid = L.store.create(L.LantSession(
            start=start, target=target, optimal=1, difficulty="usor", chain=[start],
        ))
        try:
            body = _post(client, f"/api/wordgames/lant/games/{gid}/move", text=form)
            assert body["ok"] and body["won"] and body["moves"] == 1
            assert body["path"][-1]["id"] == target
        finally:
            L.store.delete(gid)


@pytest.mark.parametrize("slug", SOURCE_ONLY)
def test_source_only_ingredient_forms_cannot_reverse_an_authored_link(slug):
    ingredient, product = PREFIX + slug, SOURCE_ONLY[slug]
    svc, client = get_service(), Client()
    assert svc.predecessor_ids(ingredient) == []
    assert svc.link(ingredient, product) is not None and svc.link(product, ingredient) is None
    gid = L.store.create(L.LantSession(
        start=product, target=ingredient, optimal=1, difficulty="usor", chain=[product],
    ))
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        for form in (FORMS[slug][0], *FORMS[slug][1]):
            body = _post(client, url + "/move", text=form)
            assert body["ok"] is False
            assert body["last_error"] == "Nu exista o legatura directa"
            state = client.get(url).json()
            assert state["moves"] == 0 and len(state["path"]) == 1 and not state["won"]
    finally:
        L.store.delete(gid)


@pytest.mark.parametrize(("left", "right", "target"), [
    (PREFIX + "cacao", "n_v24_food_snack_biscuit", "n_v18gas_salam_de_biscuiti"),
    (PREFIX + "scortisoara", "n_v24_food_orchard_mar", "n_v42gas_placinta_mere"),
    (PREFIX + "cacao", PREFIX + "seminte_floarea_soarelui", "n_v21gas_halva"),
])
def test_actual_recipe_projection_combines_reviewed_ingredients_and_explains_earned_links(
    left, right, target,
):
    svc = get_service()
    assert svc.common_neighbors(left, right, category="gastronomie") == [target]
    projection = A._build_recipe_projection([left, right], target, "gastronomie")
    assert projection is not None and projection.par == 1
    assert projection.recipes[tuple(sorted((left, right)))] == (target,)
    session = A.AlchimieSession(
        seeds=[left, right], target=target, target_depth=projection.par,
        category="gastronomie", recipes=projection.recipes, routes=projection.routes,
    )
    for seed in session.seeds:
        session.add(seed, None)
    gid = A.store.create(session)
    client, url = Client(), f"/api/wordgames/alchimie/games/{gid}"
    try:
        initial = client.get(url).json()
        assert target not in json.dumps(initial)
        assert all(item["links"] == [] for item in initial["inventory"])
        body = _post(client, url + "/combine", a=left, b=right)
        assert body["won"] and body["moves"] == 1 and body["score"] == 1000
        assert [item["id"] for item in body["discovered"]] == [target]
        result = next(item for item in body["inventory"] if item["id"] == target)
        assert {link["source"]["id"]: link["label"] for link in result["links"]} == {
            source: svc.link(source, target).label_ro for source in (left, right)
        }
        assert all(link["target"]["id"] == target for link in result["links"])
        assert "recipes" not in body and "routes" not in body
        assert client.get(url).json()["inventory"] == body["inventory"]
    finally:
        A.store.delete(gid)


def test_native_replacement_metadata_has_no_resolution_or_scoring_role(monkeypatch):
    terms = [asdict(term) for term in P.PROJECTION_TERMS]
    current_rows = [
        (term.surface, term.anchor_id, term.domain, term.rank_penalty,
         term.mapping_kind, term.public_id) for term in P.PROJECTION_TERMS
    ]
    v85_rows = before_v86_projection_rows(current_rows)
    restored = before_v85_projection_rows(current_rows)
    retained = {row[0]: row for row in restored if row[0] not in {"cacao", "scorțișoară"}}
    assert len(restored) == 471 and len(retained) == len(v85_rows) == 469
    assert len(P.PROJECTION_TERMS) == CURRENT_CONTENT.projection_terms
    for term in P.PROJECTION_TERMS:
        assert retained[term.surface] == (
            term.surface, term.anchor_id, term.domain, term.rank_penalty,
            term.mapping_kind, term.public_id,
        )
    monkeypatch.setattr(P, "NATIVE_PROJECTION_REPLACEMENTS", ())
    assert [asdict(term) for term in P._build_terms()] == terms
    for surface, owner in (("cacao", PREFIX + "cacao"), ("scorțișoară", PREFIX + "scortisoara")):
        assert P.resolve_projection(surface) is None
        assert get_service().resolve(surface) == owner
    client, gid, url = _context_game("n_v18gas_salam_de_biscuiti")
    try:
        body = _post(client, url + "/guess", text="cacao")
        assert body["guess"]["id"] == PREFIX + "cacao"
        assert body["guess"]["distance"] == 1 and body["guess"]["temperature"] == "Fierbinte"
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("record_id", "target", "opener", "owner"), [
    ("ct_gastronomie_337", "n_v21gas_ecler", "vaniliei", PREFIX + "vanilie"),
    ("ct_gastronomie_338", "n_v18gas_amandina", "cacauei", PREFIX + "cacao"),
    ("ct_gastronomie_339", "n_v21gas_halva", "semințelor de floarea-soarelui",
     PREFIX + "seminte_floarea_soarelui"),
    ("ct_gastronomie_340", "n_v3gas_inghetata", "vanilie", PREFIX + "vanilie"),
])
def test_four_public_rounds_offer_private_clues_hot_ingredients_resume_and_exact_wins(
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
        for attempt, cold_word in enumerate(("stilou", "fotbal", "București"), 1):
            cold = _post(client, url + "/guess", text=cold_word)
            assert cold["ok"] and not cold["won"] and cold["attempts"] == attempt
            _hidden(cold, target)
        clue = _post(client, url + "/clue")
        assert clue["clue_kind"] == "warmer" and clue["clues_used"] == 1
        assert clue["word"]["rank"] > 1
        _hidden(clue, target)
        resumed = client.get(url).json()
        assert resumed["clues_used"] == 1 and resumed["guesses"] == cold["guesses"]
        assert resumed["attempts"] == 3
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
    ("pască cu brânză", "n_v17gas_pasca"),
    ("poale-n brâu", "n_gas_placinte_poale_brau"),
])
def test_public_raisin_to_cheese_round_has_two_real_bridges_and_resumes_each_step(
    intermediate, node_id,
):
    chosen = None
    for seed in range(1000):
        item = L._pick_curated(
            random.Random(seed), daily=None, category="gastronomie", difficulty="usor",
            exclude_ids=set(),
        )
        if item is not None and item.id == "lt_gastronomie_221":
            chosen = seed
            break
    assert chosen is not None, "the reviewed Stafide→Brânză round must be publicly selectable"
    client = Client()
    created = _post(client, (
        "/api/wordgames/lant/games"
        f"?category=gastronomie&difficulty=usor&seed={chosen}"
    ))
    gid = created["game_id"]
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        assert created["start"]["id"] == PREFIX + "stafide"
        assert created["target"]["id"] == "n_v2gas_branza" and created["optimal"] == 2
        first = _post(client, url + "/move", text=intermediate)
        assert first["ok"] and not first["won"] and first["moves"] == 1
        assert first["path"][-1]["id"] == node_id
        assert client.get(url).json()["path"] == first["path"]
        won = _post(client, url + "/move", text="brânză")
        assert won["ok"] and won["won"] and won["moves"] == 2 and won["score"] == 1000
        assert [step["id"] for step in won["path"]] == [
            PREFIX + "stafide", node_id, "n_v2gas_branza",
        ]
        assert client.get(url).json()["path"] == won["path"]
    finally:
        L.store.delete(gid)
