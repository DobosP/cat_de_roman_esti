"""End-to-end tests for the FastAPI BFF over the OFFLINE fixture.

Uses fastapi's TestClient against ``create_app()`` with ROEDU_API_URL unset, so every
test runs server-authoritatively over the bundled ``kg_sample.json`` — no live server,
no network. The engine is reused verbatim; these tests assert the HTTP contract and the
mode-view rules, not the engine internals (those are covered by test_engine).
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from cat_de_roman_esti.web import app as app_module  # noqa: E402
from cat_de_roman_esti.web import create_app  # noqa: E402


@pytest.fixture
def client(monkeypatch) -> TestClient:
    # Force OFFLINE: no live server probe regardless of the host environment.
    monkeypatch.delenv("ROEDU_API_URL", raising=False)
    return TestClient(create_app())


# --------------------------------------------------------------------- health
def test_health_reports_offline_source(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["source"] == "offline"
    assert body["server_url"] is None
    # categories == the number of distinct puzzle categories the catalog lists, so health
    # and catalog agree. The assembled fixture spans every game category plus 'mixed'.
    catalog = client.get("/api/catalog").json()["categories"]
    assert body["categories"] == len(catalog)
    assert len(catalog) >= 3
    cat_names = {c["category"] for c in catalog}
    assert {"istorie", "literatura", "mixed"} <= cat_names


# --------------------------------------------------------------------- catalog
def test_catalog_lists_categories_with_counts(client: TestClient):
    resp = client.get("/api/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "offline"
    cats = {c["category"]: c for c in body["categories"]}
    assert "istorie" in cats
    assert "literatura" in cats
    assert "mixed" in cats
    # STRICT counts: a puzzle belongs to exactly its own .category. The cross-category
    # "mixed" puzzle is NOT double-counted into istorie/literatura — it only appears in
    # the "mixed" row.
    # Expected per-category counts are derived from the bundled fixture, so the catalog
    # contract is asserted against the assembled data, not a hard-coded snapshot.
    from cat_de_roman_esti.data import load_fixture

    bundle = load_fixture()
    for cat, row in cats.items():
        assert row["easy"] == len(bundle.puzzles_for(category=cat, difficulty="easy"))
        assert row["hard"] == len(bundle.puzzles_for(category=cat, difficulty="hard"))
    # The cross-category mixed puzzle is counted only in the "mixed" row (no double-count).
    assert cats["mixed"]["easy"] >= 1
    # human labels present
    assert cats["istorie"]["label"] == "Istorie"
    assert cats["mixed"]["label"] == "Mixt"


# ----------------------------------------------------------------- game create
def test_create_game_returns_201_game_state(client: TestClient):
    resp = client.post("/api/games", json={"category": "istorie", "difficulty": "easy"})
    assert resp.status_code == 201
    state = resp.json()
    assert state["game_id"]
    assert state["mode"] == "easy"
    assert state["category"] == "istorie"
    assert state["current_id"] == state["start_id"] == "n_stefan_cel_mare"
    assert state["target_id"] == "n_unirea_1600"
    assert state["hops"] == 0
    assert state["won"] is False
    assert state["score"] == 0
    assert state["path"] == ["n_stefan_cel_mare"]
    assert state["last_error"] is None
    # Every solution-path node is present in the node view (the map is navigable).
    node_ids = {n["id"] for n in state["nodes"]}
    for nid in ("n_stefan_cel_mare", "n_moldova", "n_unirea_1600"):
        assert nid in node_ids
    # PuzzleView shape
    assert state["puzzle"]["par"] == 2
    assert state["puzzle"]["optimal_hops"] == 2


def test_create_game_unknown_category_404(client: TestClient):
    # An unknown category has 0 strict candidates -> 404.
    resp = client.post("/api/games", json={"category": "nonsense", "difficulty": "hard"})
    assert resp.status_code == 404


# ------------------------------------------------------------ mixed (cross-cat)
def test_create_mixed_easy_returns_genuine_mixed_puzzle(client: TestClient):
    # POST {category:"mixed", difficulty:"easy"} reaches the real cross-category puzzle
    # pz_mixed_lit_ist (no longer mislabelled / unreachable). PuzzleView.category=="mixed".
    resp = client.post("/api/games", json={"category": "mixed", "difficulty": "easy"})
    assert resp.status_code == 201
    state = resp.json()
    assert state["category"] == "mixed"
    assert state["puzzle"]["id"] == "pz_mixed_lit_ist"
    assert state["puzzle"]["category"] == "mixed"
    assert state["start_id"] == "n_luceafarul"
    assert state["target_id"] == "n_putna"
    assert state["puzzle"]["par"] == 3


def test_mixed_easy_is_winnable_at_par(client: TestClient):
    # The mixed puzzle is fully playable server-authoritatively over the widened map:
    # n_luceafarul -> n_mihai_eminescu -> n_moldova -> n_putna (par 3, score 1000).
    state = client.post(
        "/api/games", json={"category": "mixed", "difficulty": "easy"}
    ).json()
    game_id = state["game_id"]
    for nid in ("n_mihai_eminescu", "n_moldova", "n_putna"):
        assert nid in state["neighbors"]
        state = client.post(f"/api/games/{game_id}/hop", json={"to": nid}).json()
        assert state["last_error"] is None
        assert state["current_id"] == nid
    assert state["won"] is True
    assert state["hops"] == 3
    assert state["score"] == 1000
    assert state["path"] == ["n_luceafarul", "n_mihai_eminescu", "n_moldova", "n_putna"]


def test_create_mixed_hard_returns_genuine_cross_category_puzzle(client: TestClient):
    # The assembled fixture provides genuine mixed HARD puzzles whose solution crosses
    # >=2 categories. Creating one returns 201 and a hard (4-7 hop) cross-category puzzle.
    resp = client.post("/api/games", json={"category": "mixed", "difficulty": "hard"})
    assert resp.status_code == 201
    state = resp.json()
    assert state["category"] == "mixed"
    assert state["puzzle"]["category"] == "mixed"
    assert state["mode"] == "hard"
    assert 4 <= state["puzzle"]["par"] <= 7
    # the solution endpoints live in different categories (a genuine cross-category hop)
    node_cat = {n["id"]: n["category"] for n in state["nodes"]}
    start_cat = node_cat.get(state["start_id"])
    target_cat = node_cat.get(state["target_id"])
    assert start_cat and target_cat and start_cat != target_cat


# ----------------------------------------------------------- next-puzzle exclude
def test_exclude_param_advances_to_different_puzzle(monkeypatch):
    # With >1 candidate for a category+difficulty, passing exclude=<finished id> picks a
    # DIFFERENT puzzle (so "Urmatoarea"/Next advances). We synthesize a second easy
    # istorie puzzle in the bundle so the combo has two candidates.
    monkeypatch.delenv("ROEDU_API_URL", raising=False)
    from cat_de_roman_esti.data import load_fixture  # noqa: E402
    from cat_de_roman_esti.engine import Puzzle  # noqa: E402

    extra = Puzzle.from_record(
        {
            "id": "pz_easy_ist_2",
            "start_id": "n_stefan_cel_mare",
            "target_id": "n_unirea_1600",
            "category": "istorie",
            "difficulty": "easy",
            "optimal_hops": 2,
            "par": 2,
            "solution_path": ["n_stefan_cel_mare", "n_moldova", "n_unirea_1600"],
            "hint_neighbors": ["n_moldova", "n_unirea_1600"],
        }
    )

    # Patch the loader so create_app picks up a bundle with the extra puzzle appended.
    base = load_fixture()
    base.puzzles.append(extra)
    monkeypatch.setattr(
        app_module, "_load_bundle", lambda: (base, "offline", None)
    )
    with TestClient(create_app()) as c:
        first = c.post(
            "/api/games", json={"category": "istorie", "difficulty": "easy"}
        ).json()
        first_id = first["puzzle"]["id"]
        # Now ask for the next, excluding the just-finished puzzle: must differ.
        nxt = c.post(
            "/api/games",
            json={
                "category": "istorie",
                "difficulty": "easy",
                "exclude": first_id,
            },
        ).json()
        assert nxt["puzzle"]["id"] != first_id


def test_exclude_param_replays_when_single_candidate(monkeypatch):
    # When a category+difficulty has exactly ONE candidate, passing exclude=<that id>
    # gracefully replays candidates[0] rather than 404-ing (backward-compatible Next).
    # We build a single-candidate bundle deterministically so the replay path is exercised
    # regardless of how many puzzles the assembled fixture has per bucket.
    monkeypatch.delenv("ROEDU_API_URL", raising=False)
    from cat_de_roman_esti.data import load_fixture  # noqa: E402

    base = load_fixture()
    only = next(p for p in base.puzzles if p.id == "pz_easy_ist")
    base.puzzles = [only]  # exactly one candidate for istorie/easy
    monkeypatch.setattr(app_module, "_load_bundle", lambda: (base, "offline", None))
    with TestClient(create_app()) as c:
        state = c.post(
            "/api/games",
            json={"category": "istorie", "difficulty": "easy", "exclude": "pz_easy_ist"},
        ).json()
        assert state["puzzle"]["id"] == "pz_easy_ist"


def test_create_game_bad_difficulty_400(client: TestClient):
    resp = client.post("/api/games", json={"category": "istorie", "difficulty": "wat"})
    assert resp.status_code == 400


# --------------------------------------------------- full server-authoritative win
def test_full_playthrough_wins_at_par_score_1000(client: TestClient):
    create = client.post("/api/games", json={"category": "istorie", "difficulty": "easy"})
    state = create.json()
    game_id = state["game_id"]

    # Solution: n_stefan_cel_mare -> n_moldova -> n_unirea_1600 (par 2).
    for nid in ("n_moldova", "n_unirea_1600"):
        # The next solution node is a real reachable neighbour each turn.
        assert nid in state["neighbors"]
        resp = client.post(f"/api/games/{game_id}/hop", json={"to": nid})
        assert resp.status_code == 200
        state = resp.json()
        assert state["last_error"] is None
        assert state["current_id"] == nid

    assert state["won"] is True
    assert state["hops"] == 2
    assert state["score"] == 1000
    assert state["path"] == ["n_stefan_cel_mare", "n_moldova", "n_unirea_1600"]


# ----------------------------------------------------------------- invalid hop
def test_invalid_hop_sets_last_error_and_does_not_advance(client: TestClient):
    state = client.post(
        "/api/games", json={"category": "istorie", "difficulty": "easy"}
    ).json()
    game_id = state["game_id"]

    # n_alba_iulia is not a neighbour of the start node -> rejected.
    resp = client.post(f"/api/games/{game_id}/hop", json={"to": "n_alba_iulia"})
    assert resp.status_code == 200
    rejected = resp.json()
    assert rejected["last_error"]  # a non-empty rejection reason
    assert rejected["current_id"] == "n_stefan_cel_mare"  # unchanged
    assert rejected["hops"] == 0
    assert rejected["path"] == ["n_stefan_cel_mare"]

    # The rejection did not persist: a fresh GET shows no last_error and no advance.
    resumed = client.get(f"/api/games/{game_id}").json()
    assert resumed["last_error"] is None
    assert resumed["current_id"] == "n_stefan_cel_mare"
    assert resumed["hops"] == 0


# ----------------------------------------------------------------- reset
def test_reset_restarts_same_puzzle(client: TestClient):
    state = client.post(
        "/api/games", json={"category": "istorie", "difficulty": "easy"}
    ).json()
    game_id = state["game_id"]
    client.post(f"/api/games/{game_id}/hop", json={"to": "n_moldova"})

    reset = client.post(f"/api/games/{game_id}/reset")
    assert reset.status_code == 200
    rstate = reset.json()
    assert rstate["current_id"] == "n_stefan_cel_mare"
    assert rstate["hops"] == 0
    assert rstate["path"] == ["n_stefan_cel_mare"]
    assert rstate["puzzle"]["id"] == state["puzzle"]["id"]


# ----------------------------------------------------------- mode view rules
def test_easy_view_excludes_distractors_and_exposes_hint(client: TestClient):
    state = client.post(
        "/api/games", json={"category": "istorie", "difficulty": "easy"}
    ).json()

    # Easy: the start-node distractor edge (hd1: n_stefan_cel_mare -> n_transilvania)
    # is filtered out of the edge view, and is not a neighbour of the start.
    edge_pairs = {(e["source"], e["target"]) for e in state["edges"]}
    assert ("n_stefan_cel_mare", "n_transilvania") not in edge_pairs
    assert "n_transilvania" not in state["neighbors"]

    # Easy: edge labels are present (label_ro), and a hint points at the next solution hop.
    assert any(e["label"] for e in state["edges"])
    assert state["hint"] == "n_moldova"


def test_hard_view_includes_distractors_and_hides_hint_and_labels(client: TestClient):
    # societate/hard[0] is pz_hard_soc_1, whose start n_consiliul_local has a
    # NON-solution distractor edge to n_nato (the hard-mode density lever).
    state = client.post(
        "/api/games", json={"category": "societate", "difficulty": "hard"}
    ).json()

    # Hard: the distractor edge IS present in the view and IS a reachable neighbour.
    edge_pairs = {(e["source"], e["target"]) for e in state["edges"]}
    assert ("n_nato", "n_consiliul_local") in edge_pairs
    assert "n_nato" in state["neighbors"]

    # Hard: labels blanked, hint hidden, and the is_distractor flag is never exposed.
    assert all(e["label"] == "" for e in state["edges"])
    assert state["hint"] is None
    assert all("is_distractor" not in e for e in state["edges"])


# ----------------------------------------------------------------- 404s
def test_get_unknown_game_404(client: TestClient):
    assert client.get("/api/games/does-not-exist").status_code == 404


def test_hop_unknown_game_404(client: TestClient):
    resp = client.post("/api/games/does-not-exist/hop", json={"to": "n_moldova"})
    assert resp.status_code == 404


def test_reset_unknown_game_404(client: TestClient):
    assert client.post("/api/games/does-not-exist/reset").status_code == 404


# ----------------------------------------------------------------- static
def test_placeholder_served_when_no_static_build(monkeypatch, tmp_path):
    # When no built SPA is present, / must serve the placeholder (never 500). We point
    # STATIC_DIR at an empty temp dir so this exercises the placeholder branch regardless
    # of whether a real `npm run build` has populated the package static dir.
    monkeypatch.delenv("ROEDU_API_URL", raising=False)
    monkeypatch.setattr(app_module, "STATIC_DIR", tmp_path / "empty_static")
    with TestClient(create_app()) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert "npm run build" in resp.text


def test_placeholder_when_static_dir_absent(monkeypatch, tmp_path):
    # Guard: even if STATIC_DIR doesn't exist at all, the app builds and serves the
    # placeholder rather than 500-ing.
    monkeypatch.delenv("ROEDU_API_URL", raising=False)
    missing = tmp_path / "does_not_exist"
    monkeypatch.setattr(app_module, "STATIC_DIR", missing)
    assert not (missing / "index.html").exists()
    app = create_app()
    with TestClient(app) as c:
        assert c.get("/").status_code == 200
        assert "npm run build" in c.get("/").text


def test_built_spa_served_when_present():
    # When a build IS present (the required deliverable), / serves the real SPA shell,
    # not the placeholder. Skipped if no build has been produced.
    if not (app_module.STATIC_DIR / "index.html").exists():
        pytest.skip("no SPA build present (run: cd frontend && npm run build)")
    with TestClient(create_app()) as c:
        resp = c.get("/")
        assert resp.status_code == 200
        assert 'id="root"' in resp.text
        assert "npm run build" not in resp.text
