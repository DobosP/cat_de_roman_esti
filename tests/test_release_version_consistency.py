"""The testing-release version is written in several files; they must never drift (ADR-0159)."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import cat_de_roman_esti

ROOT = Path(__file__).resolve().parents[1]


def _release_ts() -> dict[str, str]:
    text = (ROOT / "frontend/src/release.ts").read_text(encoding="utf-8")
    return dict(re.findall(r'export const (RELEASE_\w+) = "([^"]+)";', text))


def test_every_version_field_matches_the_python_package():
    version = cat_de_roman_esti.__version__
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    release = _release_ts()

    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert pyproject["project"]["version"] == version
    assert package["version"] == version
    assert lock["version"] == version
    assert lock["packages"][""]["version"] == version
    assert release["RELEASE_VERSION"] == version


def test_lobby_badge_names_the_exact_build():
    release = _release_ts()
    assert release["RELEASE_LABEL"] == f"V{release['RELEASE_VERSION']}"
