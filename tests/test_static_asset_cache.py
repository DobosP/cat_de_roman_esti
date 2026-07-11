import pytest
from django.conf import settings
from django.test import Client, override_settings

from cat_de_roman_esti.web.settings import _env_positive_int, _vite_asset_is_immutable


def test_vite_hashed_assets_are_immutable() -> None:
    assert _vite_asset_is_immutable(
        "/unused/on/disk/index-Ab12_-xy.js", "/assets/index-Ab12_-xy.js"
    )
    assert _vite_asset_is_immutable(
        "/unused/on/disk/font-aB3dE7_g.woff2", "/assets/font-aB3dE7_g.woff2"
    )


def test_unversioned_or_non_asset_urls_are_not_immutable() -> None:
    assert not _vite_asset_is_immutable("/unused/index.js", "/assets/index.js")
    assert not _vite_asset_is_immutable(
        "/unused/index-Ab12_-xy.js", "/other/index-Ab12_-xy.js"
    )


def test_tracked_vite_asset_gets_immutable_response_cache() -> None:
    asset = next((settings.STATIC_DIR / "assets").glob("index-*.js"))
    response = Client().get(f"/assets/{asset.name}")
    assert response.status_code == 200
    assert "immutable" in response.headers["Cache-Control"]
    assert "max-age=315360000" in response.headers["Cache-Control"]


def test_positive_request_limit_environment(monkeypatch) -> None:
    monkeypatch.setenv("TEST_CAT_REQUEST_BYTES", "32768")
    assert _env_positive_int("TEST_CAT_REQUEST_BYTES", 1) == 32768
    for bad in ("0", "-1", "1.5", "not-a-number"):
        monkeypatch.setenv("TEST_CAT_REQUEST_BYTES", bad)
        with pytest.raises(RuntimeError, match="positive integer"):
            _env_positive_int("TEST_CAT_REQUEST_BYTES", 1)


@override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=64)
def test_oversized_api_body_is_a_bounded_json_413() -> None:
    response = Client(raise_request_exception=False).post(
        "/api/wordgames/lant/games/not-a-session/move",
        data={"text": "x" * 100},
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}
