"""V85 graph and label corrections preserve complete, reconstructible V84 artifacts."""

import hashlib
import json
from pathlib import Path

import pytest

from tests.content_history import (
    before_v85_derived,
    before_v85_fixture,
    before_v85_pack,
    before_v85_rankings,
)

FIXTURES = Path(__file__).resolve().parents[1] / "cat_de_roman_esti/fixtures"


@pytest.mark.parametrize(("filename", "restore", "indent", "expected"), (
    ("kg_sample.json", before_v85_fixture, 2,
     "3fb0f97c5b4c813eb72d8fd3589c4ce92f724d0565db840c1bc3909458a60ab0"),
    ("games_pack.json", before_v85_pack, 1,
     "c843705d565770d6916567be8b7c627c16bfdcf9dd8368e6a333f0f222484b57"),
    ("board_rankings_v37.json", before_v85_rankings, 1,
     "67a7a3274f24485d45ab75191a9701482c0959be4029e29e47c7c576360a6075"),
    ("derived_catalog_v38.json", before_v85_derived, 1,
     "579128d90d34a57a093202e54babe76b1ceb6840a36e332c9ecc540a8fb5251a"),
))
def test_complete_v84_artifacts_reconstruct(filename, restore, indent, expected):
    blob = (FIXTURES / filename).read_bytes()
    current = json.loads(blob)
    previous = restore(current)
    encoded = (json.dumps(previous, ensure_ascii=False, indent=indent) + "\n").encode()
    assert hashlib.sha256(encoded).hexdigest() == expected
    assert current == json.loads(blob), "reconstructing history must not mutate live records"
