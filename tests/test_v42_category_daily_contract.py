"""Daily starts ignore free-round filters across the four curated games (ADR-0232)."""

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import alchimie, conexiuni, contexto, lant  # noqa: E402


@pytest.mark.parametrize(
    ("game", "path", "module"),
    [
        ("alchimie", "/api/wordgames/alchimie/games", alchimie),
        ("conexiuni", "/api/wordgames/conexiuni/games", conexiuni),
        ("contexto", "/api/wordgames/contexto/games", contexto),
        ("lant", "/api/wordgames/lant/games", lant),
    ],
)
def test_daily_uses_easy_and_ignores_category_and_other_difficulty(
    game: str, path: str, module
) -> None:
    day = "2099-01-02"
    client = Client()
    plain = client.post(f"{path}?daily={day}").json()
    filtered = client.post(f"{path}?daily={day}&category=gastronomie&difficulty=greu").json()
    assert plain["daily"] == filtered["daily"] == day
    assert plain["difficulty"] == filtered["difficulty"] == "usor"
    plain_session = module.store.get(plain.pop("game_id"))
    filtered_session = module.store.get(filtered.pop("game_id"))
    assert plain == filtered
    assert plain_session.pack_id == filtered_session.pack_id
    if game != "alchimie":
        assert "board_category" not in filtered
