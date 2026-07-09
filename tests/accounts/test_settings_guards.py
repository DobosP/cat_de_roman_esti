"""Production settings guards fail closed (fresh-process import of settings)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _setup(env: dict) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if not k.startswith("CAT_")}
    base.update(env)
    base["DJANGO_SETTINGS_MODULE"] = "cat_de_roman_esti.web.settings"
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        env=base,
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )


def test_secret_key_required_in_prod():
    r = _setup({"CAT_ACCOUNTS_ENABLED": "1", "CAT_DEBUG": "0", "CAT_DOMAIN": "joc.example.ro"})
    assert r.returncode != 0
    assert "CAT_SECRET_KEY" in r.stderr


def test_wildcard_host_rejected_in_prod():
    r = _setup({"CAT_ACCOUNTS_ENABLED": "1", "CAT_DEBUG": "0", "CAT_SECRET_KEY": "x" * 50})
    assert r.returncode != 0
    assert "CAT_DOMAIN" in r.stderr


@pytest.mark.parametrize("hsts", ["0", "31536000"])
def test_prod_config_ok_with_secret_and_domain(hsts):
    r = _setup(
        {
            "CAT_ACCOUNTS_ENABLED": "1",
            "CAT_DEBUG": "0",
            "CAT_SECRET_KEY": "x" * 50,
            "CAT_DOMAIN": "joc.example.ro",
            "CAT_HSTS_SECONDS": hsts,
            "CAT_DATABASE_URL": "sqlite:////tmp/cat_guard_check.sqlite3",
        }
    )
    assert r.returncode == 0, r.stderr
