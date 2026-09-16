"""Unknown ordinary words stay free without unrelated advisory suggestions."""
import pytest
from django.test import Client

from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames.service import SessionStore


@pytest.mark.parametrize("text", ["fier", "reparație", "unealtă", "scule", "rechizite"])
def test_unsupported_word_preserves_a_played_round_and_explains_no_attempt(text, monkeypatch):
    monkeypatch.setattr(C, "store", SessionStore())
    target = "n_v32_workshop_hand_cleste"
    game_id = C.store.create(C._build_session(target, "usor", None))
    client = Client()
    url = f"/api/wordgames/contexto/games/{game_id}"
    played = client.post(url + "/guess", {"text": "metal"}, content_type="application/json")
    assert played.status_code == 200 and played.json()["ok"]
    before = client.get(url).json()
    assert before["attempts"] == 1
    for _ in range(2):
        response = client.post(url + "/guess", {"text": text}, content_type="application/json")
        body = response.json()
        assert response.status_code == 200 and not body["ok"]
        assert "Nu ai pierdut nicio încercare" in body["message"]
        assert "vocabularul jocului" in body["message"]
        assert body["attempts"] == 1 and body["guesses"] == before["guesses"]
        assert "fluier" not in body["suggestions"] and "pârâu" not in body["suggestions"]
        assert target not in str(body) and "anchor_id" not in str(body)
        assert client.get(url).json() == before
    won = client.post(url + "/guess", {"text": "clești"}, content_type="application/json").json()
    assert won["won"] and won["attempts"] == 2


@pytest.mark.parametrize(("text", "expected"), [
    ("nuci", "Nucă"), ("prafzz", "Praf"), ("burttă", "Burtă"),
])
def test_useful_advisory_spellings_still_help_without_charging(text, expected, monkeypatch):
    monkeypatch.setattr(C, "store", SessionStore())
    game_id = C.store.create(C._build_session("n_v32_workshop_hand_cleste", "usor", None))
    client = Client()
    url = f"/api/wordgames/contexto/games/{game_id}"
    before = client.get(url).json()
    result = client.post(url + "/guess", {"text": text}, content_type="application/json").json()
    assert not result["ok"] and result["attempts"] == 0
    assert expected in result["suggestions"]
    assert client.get(url).json() == before
