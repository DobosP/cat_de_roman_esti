"""Reviewed household tools and the corrected whipping-cream sense work in typed play."""
from __future__ import annotations

import ast
import hashlib
import json
import random
import unicodedata
from copy import deepcopy
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames import conexiuni as X
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import contexto_projection as P
from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.packs import get_pack
from cat_de_roman_esti.wordgames.service import WordGameService, get_service
from tests import content_history as history

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v88-cross-game-quality"
FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
MODULE_SHA256 = "5fa229dd7332b489f509ba9b4f6b7b1e13f71954a6ce86999cc31d69d528a249"
GRAPH_SHA256 = "da00759c270adbdf2b5b37639b7772398172b491489c8eefc95c87a8993b7aad"
BASELINE = {
    "kg_sample.json": "96d50f8b724b9d1d1ff5d02b5a9a206445d7d9edead778d6db173f00ac094bfa",
    "games_pack.json": "536036f6d030be4e8750fb104325b67a9363535506d453ef8a0e0a824a3b63ab",
    "board_rankings_v37.json": "53defb36ab442aee1135ae3dd0522559abe27234048f9accdfbd5c9fe75eccc3",
    "derived_catalog_v38.json": "f4e16944845311eeba231f866c5578a4f1de9ee40e08857cca575930a2bf1278",
}
FORMS = {
    "n_v88_school_compas": ("Compas", ("compasul", "compasului", "compasuri", "compasurile")),
    "n_v88_school_echer": ("Echer", ("echerul", "echerului", "echere", "echerele")),
    "n_v88_school_raportor": (
        "Raportor", ("raportorul", "raportorului", "raportoare", "raportoarele"),
    ),
    "n_v88_cleaning_matura": ("Mătură", ("mături", "măturile", "măturii", "măturilor")),
    "n_v88_home_taburet": ("Taburet", ("taburetul", "taburetului", "taburete", "taburetele")),
    "n_v88_kitchen_cratita": ("Cratiță", ("cratițe", "cratițele", "cratiței", "cratițelor")),
    "n_v88_food_smantana_dulce": ("Smântână dulce pentru frișcă", (
        "smântânii dulci pentru frișcă", "smântână pentru frișcă",
        "smântână lichidă pentru frișcă", "smântână dulce lichidă pentru frișcă",
    )),
}
PREDECESSORS = {
    "n_v88_school_compas": "n_v2sti_matematica",
    "n_v88_school_echer": "n_v2sti_matematica",
    "n_v88_school_raportor": "n_v2sti_matematica",
    "n_v88_cleaning_matura": "n_v31_cleaning_floor_faras",
    "n_v88_home_taburet": "n_v3muz_pian",
    "n_v88_kitchen_cratita": "n_v24_home_appliances_aragaz",
    "n_v88_food_smantana_dulce": "n_v4gas_lapte",
}
SOUR = "n_v20gas_smantana"
SWEET = "n_v88_food_smantana_dulce"
WHIPPED = "n_v86_food_frisca"


def _json(path):
    return json.loads(path.read_bytes())


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


def _post(client, url, **payload):
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200, response.content
    return response.json()


def _private_target(target):
    gid = C.store.create(C._build_session(target, "usor", None))
    return gid, f"/api/wordgames/contexto/games/{gid}"


def _no_hidden_answer(body, target):
    assert "target" not in body and "solution" not in body
    assert target not in json.dumps(body) and "anchor_id" not in json.dumps(body)


def _assigned(tree, name):
    return ast.literal_eval(next(
        statement.value for statement in tree.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    ))


def test_current_graph_matches_the_exact_independent_seven_concept_review():
    blob = (REVIEW / "author-graph-candidates.json").read_bytes()
    assert _sha(blob) == GRAPH_SHA256
    proposal = json.loads(blob)
    module = (ROOT / "scripts/everyday_graph_v88_data.py").read_bytes()
    assert _sha(module) == MODULE_SHA256
    tree = ast.parse(module)
    assert list(_assigned(tree, "NODES")) == proposal["nodes"]
    assert list(_assigned(tree, "EDGES")) == proposal["edges"]
    assert list(_assigned(tree, "REMOVE_EDGES")) == proposal["remove_edges"]
    review = _json(REVIEW / "graph-review.json")
    assert review["decision"] == "accept" and review["blockers"] == []
    assert review["source_module_sha256"] == MODULE_SHA256
    assert review["candidate_sha256"] == GRAPH_SHA256
    assert [row["index"] for row in review["edges"]] == list(range(33))
    assert all(row["verdict"] == "accept" for row in review["edges"])
    assert len(review["nodes"]) == 7 and len(review["forms"]) == 28
    assert len(proposal["edges"]) == 33 and len(proposal["remove_edges"]) == 1
    assert review["counts"] == {
        "concepts": 7, "forms": 28, "grammatical_forms": 25, "qualified_forms": 3,
        "directed_links": 33, "removed_directed_links": 1, "net_directed_links": 32,
        "lexical_equivalents": 0,
    }
    assert [(row["id"], row["verdict"]) for row in review["removals"]] == [
        ("de8676", "accept_removal"),
    ]
    assert review["removals"][0]["record_sha256"] == _sha(json.dumps(
        proposal["remove_edges"][0], ensure_ascii=False, sort_keys=True,
        separators=(",", ":"),
    ).encode())
    nodes = {node["id"]: node for node in _json(FIXTURE)["kg_nodes"]}
    assert {node for node in nodes if node.startswith("n_v88_")} == set(FORMS)
    for expected in proposal["nodes"]:
        assert {key: nodes[expected["id"]][key] for key in expected} == expected
        assert (expected["label_ro"], tuple(expected["aliases"])) == FORMS[expected["id"]]
    svc = get_service()
    for expected in proposal["edges"]:
        actual = svc.link(expected["src"], expected["dst"])
        assert actual is not None and not actual.bidirectional and not actual.is_distractor
        assert (actual.relation, actual.label_ro, actual.strength) == (
            expected["relation"], expected["label_ro"], expected["strength"],
        )


@pytest.mark.parametrize(("filename", "inverse"), [
    ("kg_sample.json", history.before_v88_fixture),
    ("games_pack.json", history.before_v88_pack),
    ("board_rankings_v37.json", history.before_v88_rankings),
    ("derived_catalog_v38.json", history.before_v88_derived),
])
def test_exact_v87_artifact_bytes_reconstruct_without_accepting_tampering(filename, inverse):
    path = ROOT / "cat_de_roman_esti/fixtures" / filename
    current = _json(path)
    restored = inverse(current)
    indent = 2 if filename == "kg_sample.json" else 1
    assert _sha((json.dumps(restored, ensure_ascii=False, indent=indent) + "\n").encode()) == (
        BASELINE[filename]
    )
    assert path.read_bytes() == (ROOT / "tests/fixtures" / filename).read_bytes()
    changed = deepcopy(current)
    changed["meta"]["unreviewed_probe"] = True
    with pytest.raises(AssertionError):
        inverse(changed)


def test_old_native_owners_and_graph_survive_except_the_one_explicit_cream_correction():
    current = _json(FIXTURE)
    baseline = history.before_v88_fixture(current)
    assert len(current["kg_nodes"]) - len(baseline["kg_nodes"]) == 7
    assert len(current["kg_edges"]) - len(baseline["kg_edges"]) == 32
    assert current["kg_puzzles"] == baseline["kg_puzzles"]
    prior_edges = {edge["id"]: edge for edge in baseline["kg_edges"]}
    live_edges = {edge["id"]: edge for edge in current["kg_edges"]}
    assert set(prior_edges) - set(live_edges) == {"de8676"}
    assert all(live_edges[key] == value for key, value in prior_edges.items() if key != "de8676")
    old = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    current_nodes = {node["id"]: node for node in current["kg_nodes"]}
    for node in baseline["kg_nodes"]:
        assert {k: v for k, v in node.items() if k != "degree"} == {
            k: v for k, v in current_nodes[node["id"]].items() if k != "degree"
        }
        for word in (node["id"], node["label_ro"], *node.get("aliases", [])):
            assert get_service().resolve(word) == old.resolve(word), word
    assert old.link(SOUR, WHIPPED).id == "de8676"
    assert get_service().link(SOUR, WHIPPED) is None


@pytest.mark.parametrize("owner", FORMS)
def test_every_reviewed_form_resolves_repeats_and_wins_only_its_native_identity(owner):
    label, forms = FORMS[owner]
    client = Client()
    gid, url = _private_target("n_mihai_eminescu")
    try:
        for form in (label, *forms):
            for spelling in (form, f" {form.upper()} ", unicodedata.normalize(
                "NFD", form.replace("ș", "ş").replace("ț", "ţ"),
            )):
                assert get_service().resolve(spelling) == owner
                body = _post(client, url + "/guess", text=spelling)
                assert body["ok"] and not body["won"] and body["attempts"] == 1
                assert body["guess"]["id"] == owner and body["guess"]["label"] == label
                assert body["guess"]["closeness"] < 100 and not body.get("needs_confirmation")
                _no_hidden_answer(body, "n_mihai_eminescu")
            win_id, win_url = _private_target(owner)
            try:
                win = _post(client, win_url + "/guess", text=form)
                assert win["won"] and win["score"] == 1000 and win["guess"]["rank"] == 1
                assert win["guess"]["id"] == owner
            finally:
                C.store.delete(win_id)
        assert body["feedback"]["kind"] == "repeat"
        assert client.get(url).json()["guesses"] == body["guesses"]
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("owner", FORMS)
def test_new_word_forms_are_typed_destinations_on_real_oriented_lant_links(owner):
    start = PREDECESSORS[owner]
    for form in (FORMS[owner][0], *FORMS[owner][1]):
        gid = L.store.create(L.LantSession(
            start=start, target=owner, optimal=1, difficulty="usor", chain=[start],
        ))
        try:
            body = _post(Client(), f"/api/wordgames/lant/games/{gid}/move", text=form)
            assert body["ok"] and body["won"] and body["moves"] == 1
            assert body["path"][-1]["id"] == owner
        finally:
            L.store.delete(gid)


@pytest.mark.parametrize("index", range(33))
def test_each_new_direction_is_playable_and_reverse_moves_need_their_own_reviewed_edge(index):
    edges = _json(REVIEW / "author-graph-candidates.json")["edges"]
    row = edges[index]
    forward_pairs = {(edge["src"], edge["dst"]) for edge in edges}
    svc, client = get_service(), Client()
    start, target = row["src"], row["dst"]
    for source, destination, valid in (
        (start, target, True), (target, start, (target, start) in forward_pairs),
    ):
        gid = L.store.create(L.LantSession(
            start=source, target=destination, optimal=1, difficulty="usor", chain=[source],
        ))
        url = f"/api/wordgames/lant/games/{gid}"
        try:
            body = _post(client, url + "/move", text=svc.label(destination))
            assert body["ok"] is valid
            state = client.get(url).json()
            assert state["moves"] == int(valid) and state["won"] is valid
            assert [step["id"] for step in state["path"]] == (
                [source, destination] if valid else [source]
            )
            if valid:
                assert body["relation"] == svc.link(source, destination).label_ro
            else:
                assert body["last_error"] == "Nu exista o legatura directa"
        finally:
            L.store.delete(gid)


def test_only_the_two_reviewed_household_projections_retire():
    live = [(t.surface, t.anchor_id, t.domain, t.rank_penalty, t.mapping_kind, t.public_id)
            for t in P.PROJECTION_TERMS]
    previous = history.before_v88_projection_rows(live)
    assert len(previous) == 467 and len(live) == 465
    assert [row for row in previous if row[0] not in {"taburet", "mătură"}] == live
    for word, owner in (("taburet", "n_v88_home_taburet"), ("mătură", "n_v88_cleaning_matura")):
        assert P.resolve_projection(word) is None and get_service().resolve(word) == owner
    assert not any("smântână" in row[0] and "frișcă" in row[0] for row in previous)
    action = P.resolve_projection("a mătura")
    assert action is not None and get_service().resolve("a mătura") is None
    assert action.public_id != "ctxp_14422411a52f6dbbfe68"


def test_cleaning_audit_representative_changes_only_metadata_and_preserves_the_other_domains(
    monkeypatch,
):
    audit = list(P.PROJECTION_LEGIBILITY_AUDIT)
    assert len(audit) == 26
    assert audit[6] == ("curățenie", "pămătuf", "n_v31_cleaning_floor_aspirator")
    audit[6] = ("curățenie", "mătură", "n_v31_cleaning_floor_aspirator")
    assert _sha(json.dumps(audit, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode()) == (
        "2e30115faa04d99beaec28fd0df28235c7517ef32c85fd491cf1133014895245"
    )
    assert P.NATIVE_PROJECTION_REPLACEMENTS == (
        ("nucă", "ingrediente", "n_v81_food_pantry_nuca"),
        ("drojdie", "ingrediente", "n_v84_food_drojdie"),
        ("scorțișoară", "ingrediente", "n_v85_food_scortisoara"),
        ("cacao", "băuturi", "n_v85_food_cacao"),
    )
    term = P.resolve_projection("pămătuf")
    assert term is not None and term.anchor_id == "n_v31_cleaning_floor_aspirator"
    current_terms = list(P.PROJECTION_TERMS)
    monkeypatch.setattr(P, "PROJECTION_LEGIBILITY_AUDIT", ())
    monkeypatch.setattr(P, "NATIVE_PROJECTION_REPLACEMENTS", ())
    assert list(P._build_terms()) == current_terms


def test_sour_sweet_and_whipped_cream_remain_distinct_and_the_false_step_is_rejected():
    svc, client = get_service(), Client()
    assert svc.resolve("smântână") == svc.resolve("smântână fermentată") == SOUR
    assert svc.resolve("smântână pentru frișcă") == SWEET
    assert svc.resolve("frișcă") == WHIPPED
    assert svc.resolve("smântână dulce") is None
    assert svc.link(SWEET, WHIPPED) is not None and svc.link(SOUR, WHIPPED) is None
    gid = L.store.create(L.LantSession(
        start=SOUR, target=WHIPPED, optimal=1, difficulty="usor", chain=[SOUR],
    ))
    try:
        url = f"/api/wordgames/lant/games/{gid}"
        body = _post(client, url + "/move", text="frișcă")
        assert not body["ok"]
        state = client.get(url).json()
        assert not state["won"] and state["moves"] == 0
    finally:
        L.store.delete(gid)
    gid, url = _private_target(WHIPPED)
    try:
        body = _post(client, url + "/guess", text="smântână pentru frișcă")
        assert body["ok"] and not body["won"] and body["guess"]["id"] == SWEET
        assert body["guess"]["distance"] == 1 and body["guess"]["closeness"] < 100
        _no_hidden_answer(body, WHIPPED)
        win = _post(client, url + "/guess", text="frișcă")
        assert win["won"] and win["guess"]["id"] == WHIPPED
    finally:
        C.store.delete(gid)


def _public_item(game, marker):
    candidates = []
    for item in get_pack().pool(game):
        members = {node for group in item.payload.get("groups", {}).values() for node in group}
        if (item.payload.get("target") == marker if game == "alchimie" else marker in members):
            candidates.append(item)
    assert len(candidates) == 1
    item = candidates[0]
    for seed in range(1000):
        chosen = get_pack().pick_seeded(
            game, random.Random(seed), category=item.category, difficulty=item.difficulty,
        )
        if chosen is not None and chosen.id == item.id:
            return item, seed
    raise AssertionError(f"Reviewed item {item.id} is not publicly selectable")


@pytest.mark.parametrize(("game", "marker"), [
    ("alchimie", "n_v87_food_cremsnit"),
    ("conexiuni", "n_v88_school_compas"),
    ("conexiuni", "n_v88_home_taburet"),
])
def test_new_round_is_publicly_selectable_private_until_earned_and_resumable(game, marker):
    item, seed = _public_item(game, marker)
    client = Client()
    body = _post(client, f"/api/wordgames/{game}/games?seed={seed}"
                 f"&category={item.category}&difficulty={item.difficulty}")
    gid, url = body["game_id"], f"/api/wordgames/{game}/games/{body['game_id']}"
    store = A.store if game == "alchimie" else X.store
    try:
        session = store.get(gid)
        assert session.pack_id == item.id
        if game == "alchimie":
            assert session.target_depth == 3 and body["target"]["id"] is None
            assert marker not in json.dumps(body) and "recipes" not in body and "routes" not in body
            plan = A._minimum_projected_plan(set(session.seeds), marker, session.recipes)
            assert plan is not None and len(plan) == 3
            for pair in plan:
                body = _post(client, url + "/combine", a=pair[0], b=pair[1])
                assert client.get(url).json()["inventory"] == body["inventory"]
            assert body["won"] and body["moves"] == 3 and body["target"]["id"] == marker
        else:
            labels = set(session.group_labels.values())
            assert all(label not in json.dumps(body, ensure_ascii=False) for label in labels)
            for group in session.groups.values():
                body = _post(client, url + "/guess", ids=list(group))
                resumed = client.get(url).json()
                assert resumed["won"] == body["won"]
            assert body["won"] and {row["label"] for row in body["solution"]} == labels
        assert client.get(url).json()["won"]
    finally:
        store.delete(gid)
