"""Walking backwards must never reverse the meaning of an unrevised graph verb."""

from dataclasses import replace
from types import SimpleNamespace

from django.test import Client

from cat_de_roman_esti.wordgames import lant as L
from cat_de_roman_esti.wordgames.lant_relations import REVIEWED_CAPTIONS, caption
from cat_de_roman_esti.wordgames.recipe_extensions import digest, record_snapshot
from cat_de_roman_esti.wordgames.service import get_service


def test_every_reviewed_caption_is_short_and_binds_an_actual_edge_snapshot():
    service = get_service()
    for (a, b), (expected, label) in REVIEWED_CAPTIONS.items():
        assert 0 < len(label) <= 34
        edges = [e for e in (service.link(a, b), service.link(b, a)) if e]
        assert any(digest(record_snapshot(e)) == expected for e in edges)
        for left, right in ((a, b), (b, a)):
            edge = service.link(left, right)
            if edge and digest(record_snapshot(edge)) == expected:
                assert caption(service, left, right) == label


def test_changed_edges_get_neutral_fallback_and_missing_edges_get_no_claim():
    service = get_service()
    (a, b), _value = next(iter(REVIEWED_CAPTIONS.items()))
    edge = service.link(a, b) or service.link(b, a)
    changed = replace(edge, label_ro="arbitrary directional assertion", relation="related_to")
    fake = SimpleNamespace(link=lambda _a, _b: changed)
    assert caption(fake, a, b) == "legătură directă"
    fake.link = lambda _a, _b: None
    assert caption(fake, a, b) == ""


def test_reverse_geographic_route_has_correct_captions_in_move_and_get():
    session = L.LantSession(start="n_marea_neagra", target="n_dunarea", optimal=2,
                            difficulty="usor", chain=["n_marea_neagra"])
    gid = L.store.create(session)
    client = Client()
    try:
        response = client.post(f"/api/wordgames/lant/games/{gid}/move",
                               {"text": "Delta Dunării"}, content_type="application/json")
        assert response.status_code == 200
        state = response.json()
        assert state["ok"] and state["relation"] == "mare și deltă"
        assert state["path"][-1]["relation"] == "mare și deltă"
        response = client.post(f"/api/wordgames/lant/games/{gid}/move",
                               {"text": "Dunărea"}, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["relation"] == "fluviu și deltă"
        fetched = client.get(f"/api/wordgames/lant/games/{gid}").json()
        assert fetched["won"]
        assert [step.get("relation") for step in fetched["path"]] == [
            None, "mare și deltă", "fluviu și deltă",
        ]
    finally:
        L.store.delete(gid)
