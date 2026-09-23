"""V1 recipe refresh preserves reviewed identities and rejects stale snapshots."""
from __future__ import annotations

import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import Client

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import alchimie as A
from cat_de_roman_esti.wordgames import packs as P
from cat_de_roman_esti.wordgames import recipe_extensions as R
from cat_de_roman_esti.wordgames.service import SessionStore, WordGameService
from scripts import build_alchimie_recipe_extensions as B

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "docs/reviews/v1-testing-release/content"
REVIEW = CONTENT / "recipes"
CATALOG = REVIEW / "catalog.json"
AFFECTED = {"al_arta_cultura_016": 1, "al_film_tv_020": 3, "al_sport_083": 3}
WITHDRAWN = "al_istorie_034"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def write(path: Path, value: dict) -> None:
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def identities(catalog: dict) -> dict:
    return {
        addition["candidate_id"]: {
            "board_id": board["id"], "pair": addition["pair"],
            "result": addition["result"], "edge_ids": addition["edge_ids"],
        }
        for board in catalog["boards"] for addition in board["additions"]
    }


def canonical_book(record: dict, projection) -> bytes:
    return R.canonical_bytes(R.core_record(
        record["seeds"], record["target"], record["category"],
        projection.recipes, projection.routes, projection.par,
    ))


def prepare_comparison(directory: Path, catalog_path: Path = CATALOG):
    baseline_blob = gzip.decompress((CONTENT / "kg-before-v1.json.gz").read_bytes())
    assert sha(baseline_blob) == "d4774bb73d38500eada2d8f3c3a4b0829c660a2241d96f3e6826dd0ee862e109"
    old_catalog_blob = gzip.decompress((REVIEW / "before-v1-catalog.json.gz").read_bytes())
    assert sha(old_catalog_blob) == (
        "ab58dbf9a36561503032508f58338352fd634d054ae99629ab68fd18b42ea301"
    )
    old_path = directory / "before-v1-catalog.json"
    old_path.write_bytes(old_catalog_blob)
    kg_blob = (ROOT / "cat_de_roman_esti/fixtures/kg_sample.json").read_bytes()
    old_kg, kg = json.loads(baseline_blob), json.loads(kg_blob)
    services = [WordGameService(Graph.from_records(raw["kg_nodes"], raw["kg_edges"]))
                for raw in (old_kg, kg)]
    old_pack = json.loads(gzip.decompress((CONTENT / "games_pack.json.before-v1.gz").read_bytes()))
    old_records = {r["id"]: r for r in old_pack["alchimie"] if r["status"] == "approved"}
    current_pack = read(ROOT / "cat_de_roman_esti/fixtures/games_pack.json")
    records = {r["id"]: r for r in current_pack["alchimie"]}
    loaded = P.load_pack()
    items = {item.id: item for item in loaded.pool("alchimie")
             if not loaded.ranked or item._pilot_eligible}
    assert len(items) == 68
    assert all(records[bid] == old_records[bid] for bid in items)
    reserve = read(CONTENT / "alchimie-reserve-proposal.json")
    reserved = {r["id"] for r in reserve["items"]}
    assert set(old_records) - set(items) == reserved and len(reserved) == 12
    books = []
    for svc, path in zip(services, (old_path, catalog_path), strict=True):
        by_id = {}
        with patch.object(A, "get_service", new=lambda svc=svc: svc), \
                patch.object(R, "CATALOG_PATH", path):
            for bid in sorted(items):
                rec = records[bid]
                core = A._build_recipe_projection(rec["seeds"], rec["target"], rec["category"])
                live = A._build_playable_recipe_projection(
                    rec["seeds"], rec["target"], rec["category"],
                )
                assert core is not None and live is not None
                by_id[bid] = {"core": core, "live": live, "bytes": canonical_book(rec, live)}
        books.append(by_id)
    return SimpleNamespace(
        services=services, baseline_kg_sha=sha(baseline_blob), kg_sha=sha(kg_blob),
        old_catalog=json.loads(old_catalog_blob), catalog=read(catalog_path),
        old_path=old_path, catalog_path=catalog_path, records=records, items=items,
        reserved=reserved, before=books[0], after=books[1],
    )


@pytest.fixture(scope="module")
def comparison(tmp_path_factory):
    result = prepare_comparison(tmp_path_factory.mktemp("v1-recipe-refresh"))
    yield result
    R._load_catalog.cache_clear()


def assert_private(state: dict) -> None:
    assert not {"recipes", "routes", "pack_id", "candidate_id"} & state.keys()
    if not state["won"]:
        assert state["target"]["id"] is None


def api_win(comparison, bid: str, *, required_addition: dict | None = None) -> dict:
    item, record = comparison.items[bid], comparison.records[bid]
    expected = comparison.after[bid]["live"]
    selector = SimpleNamespace(pick_seeded=lambda *args, **kwargs: item)
    client = Client(HTTP_HOST="localhost")
    with patch.object(A, "get_pack", new=lambda: selector):
        response = client.post("/api/wordgames/alchimie/games?seed=1", data={},
                               content_type="application/json")
    assert response.status_code == 200, response.content
    state = response.json()
    assert_private(state)
    game_id = state["game_id"]
    owned = set(record["seeds"])
    calls = 0

    def craft(pair):
        nonlocal calls, state
        response = client.post(f"/api/wordgames/alchimie/games/{game_id}/combine",
                               data={"a": pair[0], "b": pair[1]}, content_type="application/json")
        assert response.status_code == 200, response.content
        state = response.json()
        assert_private(state)
        fresh = set(expected.recipes.get(tuple(pair), ())) - owned
        assert {node["id"] for node in state["discovered"]} == fresh
        owned.update(fresh)
        calls += 1
        assert state["moves"] == calls

    if required_addition:
        pair = tuple(required_addition["pair"])
        for ingredient in pair:
            plan = A._minimum_projected_plan(owned, ingredient, expected.recipes)
            assert plan is not None
            for step in plan:
                craft(step)
        assert required_addition["result"] not in owned
        craft(pair)
        assert required_addition["result"] in owned
    plan = A._minimum_projected_plan(owned, record["target"], expected.recipes)
    assert plan is not None
    for pair in plan:
        craft(pair)
    assert state["won"] and state["target"]["id"] == record["target"]
    assert state["score"] >= 100
    if required_addition is None:
        assert calls == expected.par
    return {"id": bid, "moves": calls, "par": expected.par, "won": True,
            "target_hidden_until_win": True, "recipes_private": True,
            "restored_candidate_id": (required_addition["candidate_id"]
                                      if required_addition else None)}


def test_all_68_retained_books_are_byte_equivalent_to_baseline(comparison):
    assert set(comparison.before) == set(comparison.after)
    for bid in comparison.before:
        assert comparison.before[bid]["bytes"] == comparison.after[bid]["bytes"], bid
        live = comparison.after[bid]["live"]
        seeds = set(comparison.records[bid]["seeds"])
        assert sum(set(pair) <= seeds and bool(set(outputs) - seeds)
                   for pair, outputs in live.recipes.items()) >= A.MIN_OPENING_PAIRS


def test_retained_identities_bind_current_sources_and_document_one_withdrawal(comparison):
    old, new = identities(comparison.old_catalog), identities(comparison.catalog)
    removed = {cid: row for cid, row in old.items() if cid not in new}
    assert len(old) == 50 and len(new) == 49  # Historical and live counts are different.
    assert len(comparison.old_catalog["boards"]) == 28
    assert len(comparison.catalog["boards"]) == 27
    assert len(removed) == 1 and {row["board_id"] for row in removed.values()} == {WITHDRAWN}
    assert WITHDRAWN in comparison.reserved and WITHDRAWN not in comparison.items
    assert all(old[cid] == row for cid, row in new.items())
    assert not comparison.catalog["diagnostics"]
    for binding in comparison.catalog["bindings"].values():
        assert sha((ROOT / binding["path"]).read_bytes()) == binding["sha256"]
    assert comparison.catalog["candidate_sha256"] == sha((REVIEW / "candidates.json").read_bytes())
    for review in comparison.catalog["semantic_reviews"]:
        assert review["sha256"] == sha((REVIEW / f"{review['role']}-review.json").read_bytes())
    assert len({r["reviewer"] for r in comparison.catalog["semantic_reviews"]}) == 2


@pytest.mark.parametrize("bid,number", AFFECTED.items())
def test_old_snapshots_disable_only_additions_and_refreshed_books_restore_them(
    comparison, bid, number,
):
    rec, svc = comparison.records[bid], comparison.services[1]
    core = comparison.after[bid]["core"]
    with patch.object(R, "CATALOG_PATH", comparison.old_path):
        stale = R.extend_recipes(svc, rec["seeds"], rec["target"], rec["category"],
                                 core.recipes, core.routes, core.par)
    assert stale == core.recipes
    assert len(comparison.after[bid]["live"].recipes) - len(stale) == number
    assert comparison.after[bid]["bytes"] == comparison.before[bid]["bytes"]


@pytest.mark.parametrize("bid,nid,eid,field", [
    ("al_arta_cultura_016", "n_ateneul_roman", None, "description"),
    ("al_film_tv_020", "n_ftv_operatiunea_monstrul", None, "degree"),
    ("al_sport_083", None, "de1218", "label_ro"),
])
def test_restamped_tampered_snapshot_still_fails_closed(comparison, tmp_path, bid, nid, eid, field):
    catalog = deepcopy(comparison.catalog)
    board = next(b for b in catalog["boards"] if b["id"] == bid)
    snapshot = board["nodes"][nid] if nid else board["edges"][eid]
    snapshot[field] = snapshot[field] + 1 if field == "degree" else "unreviewed text"
    board["entry_sha256"] = R.digest({k: v for k, v in board.items() if k != "entry_sha256"})
    R.validate_catalog(catalog)  # Structurally valid JSON must still match the real graph.
    path = tmp_path / "tampered.json"
    write(path, catalog)
    rec, core = comparison.records[bid], comparison.after[bid]["core"]
    with patch.object(R, "CATALOG_PATH", path):
        result = R.extend_recipes(comparison.services[1], rec["seeds"], rec["target"],
                                  rec["category"], core.recipes, core.routes, core.par)
    assert result == core.recipes


@pytest.mark.parametrize("source", ["kg", "pack", "rubric"])
def test_current_builder_rejects_stale_source_binding_even_with_restamped_reviews(tmp_path, source):
    candidate = read(REVIEW / "candidates.json")
    candidate["bindings"][source]["sha256"] = "0" * 64
    candidate_path = tmp_path / "candidates.json"
    write(candidate_path, candidate)
    reviews = []
    for role in ("factual", "quality"):
        review = read(REVIEW / f"{role}-review.json")
        review["candidate_sha256"] = sha(candidate_path.read_bytes())
        path = tmp_path / f"{role}.json"
        write(path, review)
        reviews.append(path)
    with pytest.raises(ValueError, match=f"stale or invalid {source} binding"):
        B.build_catalog(candidate_path, *reviews)


def test_all_68_public_api_wins_and_seven_restored_recipe_crafts(comparison):
    with patch.object(A, "get_service", new=lambda: comparison.services[1]), \
            patch.object(A, "store", SessionStore(ttl_seconds=7200, max_sessions=1000)), \
            patch.object(R, "CATALOG_PATH", comparison.catalog_path):
        for bid in sorted(comparison.items):
            api_win(comparison, bid)
        restored = 0
        for board in comparison.catalog["boards"]:
            if board["id"] in AFFECTED:
                for addition in board["additions"]:
                    api_win(comparison, board["id"], required_addition=addition)
                    restored += 1
        assert restored == 7


def test_served_catalog_matches_the_reviewed_v1_refresh():
    served = ROOT / "cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json"
    assert served.read_bytes() == CATALOG.read_bytes()
