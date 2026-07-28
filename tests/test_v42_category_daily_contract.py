"""V42 category-daily integration contract across the four curated games."""

import pytest

pytest.importorskip("django")

from django.test import Client  # noqa: E402

from cat_de_roman_esti.wordgames import alchimie, conexiuni, contexto, lant  # noqa: E402
from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    CURATED_CATEGORY_DAILY_MIN_POOL,
    get_pack,
)


@pytest.mark.parametrize(
    ("game", "path", "module"),
    [
        ("alchimie", "/api/wordgames/alchimie/games", alchimie),
        ("conexiuni", "/api/wordgames/conexiuni/games", conexiuni),
        ("contexto", "/api/wordgames/contexto/games", contexto),
        ("lant", "/api/wordgames/lant/games", lant),
    ],
)
def test_thin_category_daily_mines_in_theme_or_returns_unavailable(
    game: str,
    path: str,
    module,
) -> None:
    """A thin curated shelf must never borrow a board and relabel its category."""
    pack = get_pack()
    chosen: tuple[str, str] | None = None
    for difficulty in ("usor", "normal", "greu"):
        categories = sorted(
            {item.category for item in pack.pool(game, difficulty=difficulty)}
        )
        for category in categories:
            count = pack.selectable_count(
                game,
                category=category,
                difficulty=difficulty,
            )
            if 0 < count < CURATED_CATEGORY_DAILY_MIN_POOL:
                chosen = category, difficulty
                break
        if chosen is not None:
            break
    if chosen is None:
        pytest.skip(f"{game} has no thin category shelf")

    category, difficulty = chosen
    day = "2099-01-02"
    assert (
        pack.pick_daily(
            game,
            day,
            category=category,
            difficulty=difficulty,
        )
        is None
    )

    response = Client().post(
        f"{path}?daily={day}&category={category}&difficulty={difficulty}"
    )
    assert response.status_code in {200, 503}
    if response.status_code == 503:
        return

    body = response.json()
    assert body["board_category"] == category
    session = module.store.get(body["game_id"])
    assert session is not None
    if session.pack_id is not None:
        item = next(item for item in pack.pool(game) if item.id == session.pack_id)
        assert item.category == category
