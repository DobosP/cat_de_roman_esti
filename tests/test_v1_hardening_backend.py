"""V1 review hardening: reserve fail-closed shape, builder EOLs, health."""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path

import pytest
from django.test import Client

from cat_de_roman_esti import __version__
from cat_de_roman_esti.web import meta
from cat_de_roman_esti.wordgames import release_reserve as reserve
from cat_de_roman_esti.wordgames.derived_catalog import get_derived_catalog
from scripts import build_release_reserve_v1 as builder


def _clear_caches() -> None:
    reserve.get_reserve.cache_clear()
    get_derived_catalog.cache_clear()


@pytest.fixture(params=["missing", "tampered"])
def broken_reserve(request, monkeypatch, tmp_path: Path):
    target = tmp_path / "release_reserve_v1.json"
    if request.param == "tampered":
        target.write_bytes(reserve.RESERVE_PATH.read_bytes() + b" ")
    monkeypatch.setattr(reserve, "load_reserve", partial(reserve.load_reserve, target))
    _clear_caches()
    yield request.param
    monkeypatch.undo()
    _clear_caches()


@pytest.mark.parametrize(("game", "label"), [("intrusul", "Intrusul"), ("perechi", "Perechi")])
@pytest.mark.parametrize("query", ["seed=2", "daily=2026-07-19"])
def test_broken_reserve_is_the_games_json_503(broken_reserve, game, label, query) -> None:
    response = Client(raise_request_exception=False).post(
        f"/api/wordgames/{game}/games?{query}"
    )
    assert response.status_code == 503
    assert response["Content-Type"].startswith("application/json")
    assert response.json() == {"detail": f"Catalogul {label} este invalid."}


def test_broken_reserve_fails_startup_warmup(broken_reserve) -> None:
    with pytest.raises(ValueError, match="release reserve"):
        meta.warm()


def test_builder_check_accepts_crlf_checkouts(monkeypatch, tmp_path: Path, capsys) -> None:
    copies = []
    for index, source in enumerate(builder.COPIES):
        target = tmp_path / f"copy{index}.json"
        target.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))
        copies.append(target)
    monkeypatch.setattr(builder, "COPIES", tuple(copies))
    monkeypatch.setattr(sys, "argv", ["build_release_reserve_v1.py"])
    builder.main()
    assert "release reserve GREEN" in capsys.readouterr().out


def test_api_health_reports_the_package_version() -> None:
    body = Client().get("/api/health").json()
    assert body["version"] == __version__
