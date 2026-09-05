"""Unit checks for the standalone, offline runtime measurement harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parents[1] / "scripts/measure_wordgames_runtime.py"
_SPEC = importlib.util.spec_from_file_location("measure_wordgames_runtime", _SCRIPT)
assert _SPEC and _SPEC.loader
runtime = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(runtime)


def test_offline_environment_overrides_inherited_service_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAT_ACCOUNTS_ENABLED", "1")
    monkeypatch.setenv("ROEDU_API_URL", "https://example.invalid")
    monkeypatch.setenv("ROEDU_API_KEY", "not-a-secret-test-value")
    monkeypatch.setenv("CAT_KG_FIXTURE", "/tmp/not-the-bundled-fixture.json")
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "wrong.settings")

    runtime.configure_offline_environment()

    assert runtime.os.environ["CAT_ACCOUNTS_ENABLED"] == "0"
    assert runtime.os.environ["ROEDU_API_URL"] == ""
    assert runtime.os.environ["ROEDU_API_KEY"] == ""
    assert runtime.os.environ["CAT_KG_FIXTURE"] == str(runtime.OFFLINE_FIXTURE)
    assert runtime.os.environ["DJANGO_SETTINGS_MODULE"] == "cat_de_roman_esti.web.settings"


@pytest.mark.parametrize("rounds, guesses", [(0, 1), (1, 0), (1, 11)])
def test_workload_rejects_invalid_or_repeated_contexto_terms(rounds: int, guesses: int) -> None:
    with pytest.raises(ValueError):
        runtime.validate_workload(rounds, guesses)


def test_workload_allows_all_distinct_contexto_terms() -> None:
    runtime.validate_workload(100, len(runtime.CONTEXT0_TERMS))
