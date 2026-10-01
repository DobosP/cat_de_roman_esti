"""The private native artifact must remain tied to reviewed Python content."""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts import export_go_content


def test_go_export_is_current_and_private() -> None:
    data = export_go_content.export_bytes()
    assert export_go_content.OUTPUT.read_bytes() == data
    assert hashlib.sha256(data).hexdigest() in export_go_content.PIN.read_text()
    assert "web/static" not in str(export_go_content.OUTPUT)
    payload = json.loads(data)
    assert len(payload["boards"]) == 226
    assert all(board["game"] == "intrusul" for board in payload["boards"])
    assert payload["manifest"]["counts"]["nodes"] == len(payload["labels"])


def test_export_refuses_unbound_source_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAT_KG_FIXTURE", "not-the-reviewed-bundle.json")
    with pytest.raises(ValueError, match="without source overrides"):
        export_go_content.export_bytes()
