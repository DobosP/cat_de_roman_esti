"""Reviewed V84 kitchen identities, directed routes and real player outcomes."""

from __future__ import annotations

import ast
import hashlib
import json
import random
import unicodedata
from pathlib import Path

import pytest

pytest.importorskip("django")

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import alchimie as A  # noqa: E402
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.contexto_projection import resolve_projection  # noqa: E402
from cat_de_roman_esti.wordgames.packs import get_pack  # noqa: E402
from cat_de_roman_esti.wordgames.service import get_service  # noqa: E402
from tests.content_history import before_v84_fixture, before_v85_fixture  # noqa: E402
from tests.content_scenarios import contexto_seed  # noqa: E402
from tests.current_content import CURRENT_CONTENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "docs/reviews/v84-six-game-graph-quality"
FIXTURE = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
PREFIX = "n_v84_food_"
# Independent expected identities/forms; the frozen review binds the remaining fields.
FORMS = {
    "drojdie": ("Drojdie", ("drojdia", "drojdie de panificație", "drojdia de panificație")),
    "aluat": ("Aluat", ("aluatul", "aluatului", "aluaturi", "aluaturile")),
    "cuptor": ("Cuptor de bucătărie", (
        "cuptorul de bucătărie", "cuptorului de bucătărie",
        "cuptoare de bucătărie", "cuptoarele de bucătărie",
    )),
    "zer": ("Zer", ("zerul", "zerului")),
    "saramura": ("Saramură", ("saramurii", "saramură alimentară")),
    "grau": ("Grâu", ("grâul", "grâului", "boabe de grâu")),
    "orz": ("Orz", ("orzul", "orzului", "boabe de orz")),
    "ovaz": ("Ovăz", ("ovăzul", "ovăzului", "boabe de ovăz")),
    "secara": ("Secară", ("secarei", "boabe de secară")),
    "malai": ("Mălai", ("mălaiul", "mălaiului", "făină de porumb")),
    "gris": ("Griș", ("grișul", "grișului")),
    "arpacas": ("Arpacaș", ("arpacașul", "arpacașului")),
    "cheag": ("Cheag alimentar", ("cheagul alimentar", "cheag pentru brânză")),
    "tava_copt": ("Tavă de copt", ("tăvi de copt", "tăvile de copt", "tavă pentru cuptor")),
    "sucitor": ("Sucitor", (
        "sucitorul", "sucitorului", "sucitoare de bucătărie", "sucitor de bucătărie",
    )),
}
PREDECESSORS = {
    "aluat": "n_v24_food_pantry_faina", "cuptor": PREFIX + "tava_copt",
    "zer": "n_v4gas_lapte", "saramura": "n_v4gas_sare",
    "grau": PREFIX + "orz", "orz": PREFIX + "grau", "ovaz": PREFIX + "grau",
    "secara": PREFIX + "grau", "malai": "n_v2lim_porumb",
    "gris": PREFIX + "grau", "arpacas": PREFIX + "grau",
}
SOURCE_ONLY = {
    "drojdie": PREFIX + "aluat", "cheag": "n_v4gas_lapte",
    "tava_copt": PREFIX + "cuptor", "sucitor": PREFIX + "aluat",
}
EXCLUDED = (
    "grâne", "făcăleț", "vergea", "cheag", "tavă", "cocă", "sucitoare",
    "cuptor", "cuptorul", "cuptorului", "cuptoare", "cuptoarele",
)
CONTEXT_ROUNDS = (
    ("ct_gastronomie_334", "n_v42gas_placinta_mere", "măr", "plăcintă cu mere"),
    ("ct_gastronomie_335", "n_v18gas_salam_de_biscuiti", "biscuit", "salam de biscuiți"),
    ("ct_gastronomie_336", "n_v4gas_paine", "aluat", "pâine"),
)


def _json(path):
    return json.loads(path.read_bytes())


def _assigned(tree, name):
    return ast.literal_eval(next(
        statement.value for statement in tree.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    ))


def _post(client, url, **payload):
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 200
    return response.json()


def _hidden(body, target):
    assert "target" not in body and "solution" not in body
    assert target not in json.dumps(body)
    assert "anchor_id" not in json.dumps(body)


def test_frozen_review_authoring_and_served_graph_agree_exactly():
    blob = (REVIEW / "graph-candidates.json").read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == "50dc48c4000905e5b3a1e56ed3c3c5add45c2fcd859691b74113ab072902dc60"
    review = _json(REVIEW / "graph-review.json")
    assert review["candidate_sha256"] == digest and review["verdict"] == "accept"
    candidate = json.loads(blob)
    tree = ast.parse((ROOT / "scripts/kitchen_graph_v84_data.py").read_text())
    assert list(_assigned(tree, "NODES")) == candidate["nodes"]
    assert list(_assigned(tree, "EDGES")) == candidate["edges"]
    assert list(_assigned(tree, "REMOVE_EDGES")) == candidate["remove_edges"]
    assert (len(candidate["nodes"]), len(candidate["edges"]), len(candidate["remove_edges"])) == (
        15, 57, 1,
    )
    assert sum(len(forms) for _, forms in FORMS.values()) == 42
    raw = _json(FIXTURE)
    served_nodes = {node["id"]: node for node in raw["kg_nodes"]}
    new_ids = {PREFIX + slug for slug in FORMS}
    assert {node_id for node_id in served_nodes if node_id.startswith(PREFIX)} == new_ids
    for expected in candidate["nodes"]:
        actual = served_nodes[expected["id"]]
        assert {key: actual[key] for key in expected} == expected
        slug = expected["id"].removeprefix(PREFIX)
        assert (actual["label_ro"], tuple(actual["aliases"])) == FORMS[slug]
    assert not any(edge["id"] == "de520" for edge in raw["kg_edges"])
    svc = get_service()
    assert svc.link("n_gas_telemea", "n_gas_placinte_poale_brau") is None
    for expected in candidate["edges"]:
        edge = svc.link(expected["src"], expected["dst"])
        assert edge is not None and not edge.is_distractor
        assert (edge.src_id, edge.dst_id, edge.relation, edge.label_ro, edge.strength,
                edge.bidirectional) == (
            expected["src"], expected["dst"], expected["relation"], expected["label_ro"],
            expected["strength"], bool(expected["bidirectional"]),
        )


def test_graph_delta_restores_the_full_v83_snapshot_and_old_surface_owners():
    from cat_de_roman_esti.graph import Graph
    from cat_de_roman_esti.wordgames.service import WordGameService

    raw = _json(FIXTURE)
    assert FIXTURE.read_bytes() == (ROOT / "tests/fixtures/kg_sample.json").read_bytes()
    assert (len(raw["kg_nodes"]), len(raw["kg_edges"]), len(raw["kg_puzzles"])) == tuple(
        CURRENT_CONTENT.kg_counts[key] for key in ("nodes", "edges", "puzzles")
    )
    assert sum(len(node.get("aliases", [])) for node in raw["kg_nodes"]) == (
        CURRENT_CONTENT.kg_counts["aliases"]
    )
    baseline = before_v84_fixture(raw)
    encoded = (json.dumps(baseline, ensure_ascii=False, indent=2) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == (
        "4ce12d15ec247ebcaba3e119caed91f8d2624b09fa5568a8d7ece728f76a8a5e"
    )
    previous = WordGameService(Graph.from_records(baseline["kg_nodes"], baseline["kg_edges"]))
    current = get_service()
    for node in baseline["kg_nodes"]:
        for surface in (node["id"], node["label_ro"], *node.get("aliases", [])):
            assert current.resolve(surface) == previous.resolve(surface), surface


@pytest.mark.parametrize("slug", FORMS)
def test_all_new_forms_are_exact_private_nonwinning_repeatable_and_resumable(slug):
    owner = PREFIX + slug
    target = "n_mihai_eminescu"
    svc, client = get_service(), Client()
    gid = C.store.create(C._build_session(target, "normal", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        for form in FORMS[slug][1]:
            assert svc.resolve(form) == owner
            for spelling in (form, f" {form.upper()} ", unicodedata.normalize(
                "NFD", form.replace("ș", "ş").replace("ț", "ţ"),
            )):
                body = _post(client, url + "/guess", text=spelling)
                assert body["ok"] and not body["won"] and body["attempts"] == 1
                assert not body.get("needs_confirmation")
                assert body["guess"]["id"] == owner
                assert body["guess"]["label"] == FORMS[slug][0]
                assert body["guess"]["closeness"] < 100
                _hidden(body, target)
        repeat = _post(client, url + "/guess", text=FORMS[slug][1][0])
        assert repeat["feedback"]["kind"] == "repeat" and repeat["attempts"] == 1
        resumed = client.get(url).json()
        assert resumed["guesses"] == repeat["guesses"] and resumed["attempts"] == 1
        _hidden(resumed, target)
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize("slug", FORMS)
def test_new_forms_can_win_their_own_identity_without_an_approximation(slug):
    owner = PREFIX + slug
    client = Client()
    for form in FORMS[slug][1]:
        gid = C.store.create(C._build_session(owner, "normal", None))
        try:
            body = _post(client, f"/api/wordgames/contexto/games/{gid}/guess", text=form)
            assert body["ok"] and body["won"] and body["attempts"] == 1
            assert body["guess"]["id"] == owner and body["guess"]["rank"] == 1
            assert body["score"] == 1000
        finally:
            C.store.delete(gid)


@pytest.mark.parametrize("slug", PREDECESSORS)
def test_every_reachable_new_form_is_a_legal_direct_typed_lant_destination(slug):
    owner, start = PREFIX + slug, PREDECESSORS[slug]
    assert get_service().link(start, owner) is not None
    client = Client()
    for form in FORMS[slug][1]:
        gid = L.store.create(L.LantSession(
            start=start, target=owner, optimal=1, difficulty="usor", chain=[start],
        ))
        url = f"/api/wordgames/lant/games/{gid}"
        try:
            result = _post(client, url + "/move", text=form)
            assert result["ok"] and result["won"] and result["moves"] == 1
            assert result["path"][-1]["id"] == owner
            assert client.get(url).json()["path"] == result["path"]
        finally:
            L.store.delete(gid)


@pytest.mark.parametrize("slug", SOURCE_ONLY)
def test_source_only_forms_cannot_reverse_an_edge_but_the_authored_direction_works(slug):
    owner, destination = PREFIX + slug, SOURCE_ONLY[slug]
    svc, client = get_service(), Client()
    assert svc.predecessor_ids(owner) == []
    assert svc.link(owner, destination) is not None
    assert svc.link(destination, owner) is None
    gid = L.store.create(L.LantSession(
        start=destination, target="n_v4gas_paine", optimal=1,
        difficulty="usor", chain=[destination],
    ))
    url = f"/api/wordgames/lant/games/{gid}"
    try:
        for form in FORMS[slug][1]:
            result = _post(client, url + "/move", text=form)
            assert result["ok"] is False
            assert result["last_error"] == "Nu exista o legatura directa"
        assert client.get(url).json()["moves"] == 0
    finally:
        L.store.delete(gid)
    gid = L.store.create(L.LantSession(
        start=owner, target=destination, optimal=1, difficulty="usor", chain=[owner],
    ))
    try:
        result = _post(client, f"/api/wordgames/lant/games/{gid}/move", text=svc.label(destination))
        assert result["ok"] and result["won"] and result["moves"] == 1
    finally:
        L.store.delete(gid)


def test_exclusions_preserve_legacy_behavior_without_stealing_new_food_identities():
    svc = get_service()
    client = Client()
    gid = C.store.create(C._build_session("n_gas_sarmale", "normal", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        for form in EXCLUDED:
            assert svc.resolve(form) is None
            expected_fuzzy = "n_v3per_sculptor" if form == "cuptorului" else None
            assert svc.resolve_fuzzy(form) == expected_fuzzy
            if form == "tavă":
                continue  # Existing projection identity is preserved below.
            body = _post(client, url + "/guess", text=form)
            assert body["ok"] is False and body["attempts"] == 0
            assert bool(body.get("needs_confirmation")) == (form == "cuptorului")
            if form == "cuptorului":
                assert body["resolved_label"] == "Sculptor"
            _hidden(body, "n_gas_sarmale")
        tray = _post(client, url + "/guess", text="tavă")
        assert tray["ok"] and tray["attempts"] == 1 and not tray["won"]
        assert tray["guess"]["id"] == "ctxp_0da09b9a45e5fe4f7eae"
        assert tray["guess"]["id"] != PREFIX + "tava_copt"
        assert resolve_projection("tavă").anchor_id == "n_v30_kitchen_cookware_oala"
        _hidden(tray, "n_gas_sarmale")
        assert resolve_projection("drojdie") is None
        assert svc.resolve("drojdie") == PREFIX + "drojdie"
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("surface", "owner", "target", "rank"), [
    ("biscuit", "n_v24_food_snack_biscuit", "n_v18gas_salam_de_biscuiti", 3),
    ("măr", "n_v24_food_orchard_mar", "n_v42gas_placinta_mere", 3),
    ("drojdie", PREFIX + "drojdie", "n_v17gas_gogosi", 3),
    ("zer", PREFIX + "zer", "n_gas_urda", 4),
    ("saramură", PREFIX + "saramura", "n_gas_telemea", 5),
])
def test_specific_food_inputs_are_hot_without_changing_identity_or_revealing_answers(
    surface, owner, target, rank,
):
    client = Client()
    gid = C.store.create(C._build_session(target, "usor", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        body = _post(client, url + "/guess", text=surface)
        assert body["ok"] and not body["won"]
        assert (body["guess"]["id"], body["guess"]["rank"], body["guess"]["distance"],
                body["guess"]["temperature"]) == (owner, rank, 1, "Fierbinte")
        _hidden(body, target)
        repeated = _post(client, url + "/guess", text=surface.upper())
        assert repeated["attempts"] == 1 and repeated["guess"] == body["guess"]
        assert client.get(url).json()["guesses"] == body["guesses"]
        won = _post(client, url + "/guess", text=get_service().label(target))
        assert won["won"] and won["guess"]["id"] == target and won["guess"]["rank"] == 1
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("target", "rank", "temperature"), [
    ("n_gas_sarmale", 246, "Rece"), ("n_gas_telemea", 203, "Caldut"),
])
@pytest.mark.parametrize("graph_epoch", ("before_v85", "current"))
def test_yeast_no_longer_inherits_generic_food_hotness(
    target, rank, temperature, graph_epoch, monkeypatch,
):
    if graph_epoch == "before_v85":
        from cat_de_roman_esti.graph import Graph
        from cat_de_roman_esti.wordgames.service import WordGameService

        previous = before_v85_fixture(_json(FIXTURE))
        svc = WordGameService(Graph.from_records(previous["kg_nodes"], previous["kg_edges"]))
        monkeypatch.setattr(C, "get_service", lambda: svc)
    client = Client()
    gid = C.store.create(C._build_session(target, "normal", None))
    try:
        body = _post(client, f"/api/wordgames/contexto/games/{gid}/guess", text="drojdie")
        assert body["guess"]["id"] == PREFIX + "drojdie"
        assert body["guess"]["temperature"] == temperature
        assert body["guess"]["distance"] == 3
        if graph_epoch == "before_v85":
            assert body["guess"]["rank"] == rank
        else:
            # More reachable concepts can move numerical rank positions without
            # reviving the retired broad-food association or a direct/hot claim.
            assert body["guess"]["rank"] > 1
        assert body["ok"] and not body["won"]
        _hidden(body, target)
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("left", "right", "result", "labels"), [
    ("n_v4gas_sare", "n_v4gas_apa", PREFIX + "saramura", {
        "n_v4gas_sare": "se dizolvă pentru", "n_v4gas_apa": "solvent pentru",
    }),
    ("n_v24_food_pantry_faina", "n_v4gas_apa", PREFIX + "aluat", {
        "n_v24_food_pantry_faina": "se amestecă pentru",
        "n_v4gas_apa": "hidratează făina pentru",
    }),
])
def test_real_recipe_projection_crafts_materials_and_explains_only_earned_links(
    left, right, result, labels,
):
    assert get_service().common_neighbors(left, right, category="gastronomie") == [result]
    projection = A._build_recipe_projection([left, right], result, "gastronomie")
    assert projection is not None and projection.par == 1
    assert projection.recipes[tuple(sorted((left, right)))] == (result,)
    session = A.AlchimieSession(
        seeds=[left, right], target=result, target_depth=projection.par,
        category="gastronomie", recipes=projection.recipes, routes=projection.routes,
    )
    for seed in session.seeds:
        session.add(seed, None)
    gid = A.store.create(session)
    client, url = Client(), f"/api/wordgames/alchimie/games/{gid}"
    try:
        initial = client.get(url).json()
        assert result not in json.dumps(initial)
        assert all(item["links"] == [] for item in initial["inventory"])
        body = _post(client, url + "/combine", a=left, b=right)
        assert body["won"] and body["moves"] == 1 and body["score"] == 1000
        assert [item["id"] for item in body["discovered"]] == [result]
        earned = next(item for item in body["inventory"] if item["id"] == result)
        assert {link["source"]["id"]: link["label"] for link in earned["links"]} == labels
        assert all(link["target"]["id"] == result for link in earned["links"])
        assert len(earned["links"]) == 2
        assert "recipes" not in body and "routes" not in body
        assert client.get(url).json()["inventory"] == body["inventory"]
    finally:
        A.store.delete(gid)


def test_larger_graph_preserves_request_and_session_bounds():
    assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == 64 * 1024
    for store in (C.store, L.store, A.store):
        assert store._ttl == 7200 and store._max == 1000
    client = Client()
    gid = C.store.create(C._build_session("n_gas_sarmale", "normal", None))
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        response = client.post(
            url + "/guess", {"text": "a" * (64 * 1024)}, content_type="application/json",
        )
        assert response.status_code == 413
        assert client.get(url).json()["attempts"] == 0
    finally:
        C.store.delete(gid)


@pytest.mark.parametrize(("record_id", "target", "opener", "answer"), CONTEXT_ROUNDS)
def test_public_contexto_rounds_have_hot_openers_resume_and_exact_wins(
    record_id, target, opener, answer,
):
    eligible = {item.id for item in get_pack().pool("contexto", category="gastronomie")
                if item._pilot_eligible}
    assert record_id in eligible
    seed = contexto_seed(target, difficulty="usor")
    client = Client()
    initial = _post(client, (
        "/api/wordgames/contexto/games"
        f"?category=gastronomie&difficulty=usor&seed={seed}"
    ))
    gid = initial["game_id"]
    url = f"/api/wordgames/contexto/games/{gid}"
    try:
        _hidden(initial, target)
        body = _post(client, url + "/guess", text=opener)
        assert body["ok"] and not body["won"] and body["guess"]["temperature"] == "Fierbinte"
        _hidden(body, target)
        assert client.get(url).json()["guesses"] == body["guesses"]
        repeated = _post(client, url + "/guess", text=opener.upper())
        assert repeated["attempts"] == 1 and repeated["feedback"]["kind"] == "repeat"
        won = _post(client, url + "/guess", text=answer)
        assert won["won"] and won["guess"]["id"] == target and won["attempts"] == 2
        assert client.get(url).json()["won"]
    finally:
        C.store.delete(gid)


def test_public_lant_flour_to_cornulete_supports_both_reviewed_branches_and_resume():
    chosen = None
    for seed in range(1000):
        item = L._pick_curated(
            random.Random(seed), daily=None, category="gastronomie", difficulty="usor",
            exclude_ids=set(),
        )
        if item is not None and item.id == "lt_gastronomie_220":
            chosen = seed
            break
    assert chosen is not None, "reviewed Lanț route must be publicly selectable"
    for intermediate in ("aluatului", "cozonac"):
        client = Client()
        initial = _post(client, (
            "/api/wordgames/lant/games"
            f"?category=gastronomie&difficulty=usor&seed={chosen}"
        ))
        gid = initial["game_id"]
        url = f"/api/wordgames/lant/games/{gid}"
        try:
            assert initial["start"]["id"] == "n_v24_food_pantry_faina"
            assert initial["target"]["id"] == "n_v21gas_cornulete"
            first = _post(client, url + "/move", text=intermediate)
            assert first["ok"] and not first["won"] and first["moves"] == 1
            assert client.get(url).json()["path"] == first["path"]
            won = _post(client, url + "/move", text="cornulețului cu gem")
            assert won["ok"] and won["won"] and won["moves"] == 2
            assert client.get(url).json()["won"]
        finally:
            L.store.delete(gid)
