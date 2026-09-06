"""V81 additions cannot silently rewrite the pre-wave content baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.content_history import (
    before_v81_derived,
    before_v81_fixture,
    before_v81_rankings,
    before_v82_pack,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "cat_de_roman_esti/fixtures"


@pytest.mark.parametrize(
    ("filename", "restore", "indent", "expected"),
    [
        ("kg_sample.json", before_v81_fixture, 2,
         "c158262f7216c3b7ec2381f9fbe5ffc5d2ac987ad6a1d56de61e58ec276eb370"),
        ("board_rankings_v37.json", before_v81_rankings, 1,
         "823c5f302bd36c833283038affb1125dc434a1d34fba635e71c06b721cda4cec"),
        ("derived_catalog_v38.json", before_v81_derived, 1,
         "0787a4325c84753c739e7900f174cc99f46e9a4d3fbd8ce1e035cdf84c9b6ae2"),
    ],
)
def test_complete_pre_v81_artifacts_reconstruct_exactly(filename, restore, indent, expected):
    blob = (FIXTURES / filename).read_bytes()
    assert blob == (ROOT / "tests/fixtures" / filename).read_bytes()
    restored = restore(json.loads(blob))
    encoded = (json.dumps(restored, ensure_ascii=False, indent=indent) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == expected


def test_pack_and_every_existing_puzzle_are_unchanged():
    blob = (FIXTURES / "games_pack.json").read_bytes()
    assert blob == (ROOT / "tests/fixtures/games_pack.json").read_bytes()
    baseline_pack = before_v82_pack(json.loads(blob))
    restored = (json.dumps(baseline_pack, ensure_ascii=False, indent=1) + "\n").encode()
    assert hashlib.sha256(restored).hexdigest() == (
        "27ce95294b7a8ea39aedc3f22e125650d0f06d9ecbcf0fb7af4bc6966d59cb29"
    )
    current = json.loads((FIXTURES / "kg_sample.json").read_bytes())
    assert current["kg_puzzles"] == before_v81_fixture(current)["kg_puzzles"]
    assert len(current["kg_puzzles"]) == 180
