"""The private native artifact must remain tied to reviewed Python content."""

from __future__ import annotations

import hashlib
import json
import unicodedata

import pytest

from scripts import export_go_content


@pytest.mark.skipif(
    unicodedata.unidata_version != "15.0.0",
    reason="export targets deployed Python 3.12 / Unicode 15",
)
def test_go_export_is_current_and_private() -> None:
    data = export_go_content.export_bytes()
    assert export_go_content.OUTPUT.read_bytes() == data
    assert hashlib.sha256(data).hexdigest() in export_go_content.PIN.read_text()
    assert "web/static" not in str(export_go_content.OUTPUT)
    payload = json.loads(data)
    assert sum(board["game"] == "intrusul" for board in payload["boards"]) == 226
    assert sum(board["game"] == "perechi" for board in payload["boards"]) == 192
    assert payload["manifest"]["counts"]["nodes"] == len(payload["labels"])
    assert len(payload["nodes"]) == len(payload["labels"])


def test_export_refuses_unbound_source_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAT_KG_FIXTURE", "not-the-reviewed-bundle.json")
    with pytest.raises(ValueError, match="without source overrides"):
        export_go_content.export_bytes()
