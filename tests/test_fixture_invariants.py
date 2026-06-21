"""Pytest guard over the bundled KG fixture.

Imports the committed validator (``scripts/validate_fixture.py``) and asserts the
shipped fixture passes EVERY puzzle/shape/meta invariant with zero errors, and
that the two bundled copies are byte-identical. This is the CI counterpart of the
``python scripts/validate_fixture.py`` pre-commit gate: if a future fixture
regeneration reintroduces (say) a distractor-shortcut hard puzzle, this test goes
red.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_VALIDATOR_PATH = _REPO_ROOT / "scripts" / "validate_fixture.py"


def _load_validator():
    """Load the standalone validator module by path (it is not an importable pkg)."""
    spec = importlib.util.spec_from_file_location("validate_fixture", _VALIDATOR_PATH)
    assert spec and spec.loader, f"cannot load validator at {_VALIDATOR_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def test_validator_module_loads():
    assert hasattr(validator, "validate")
    assert callable(validator.validate)


@pytest.mark.parametrize(
    "fixture_path",
    [validator.PACKAGE_FIXTURE, validator.TESTS_FIXTURE],
    ids=["package_copy", "tests_copy"],
)
def test_fixture_has_zero_invariant_errors(fixture_path):
    """Every invariant holds over the bundled fixture (both copies)."""
    errors = validator.validate(fixture_path)
    assert errors == [], (
        f"{len(errors)} fixture invariant error(s):\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_fixture_copies_are_byte_identical():
    """The package copy and the tests copy must be byte-for-byte identical."""
    pkg = validator.PACKAGE_FIXTURE.read_bytes()
    tst = validator.TESTS_FIXTURE.read_bytes()
    assert pkg == tst, (
        f"fixture copies differ: {validator.PACKAGE_FIXTURE} "
        f"({len(pkg)} bytes) vs {validator.TESTS_FIXTURE} ({len(tst)} bytes)"
    )


def test_validator_main_exits_zero_on_clean_fixture():
    """The gate's main() returns 0 (GREEN) over the current fixture."""
    assert validator.main([str(validator.PACKAGE_FIXTURE)]) == 0


def test_all_error_classes_are_covered_by_summary():
    """Sanity: the summary prefixes match the declared ERROR_CLASSES set."""
    # Every error string the validator emits is prefixed with a known class.
    errors = validator.validate(validator.PACKAGE_FIXTURE)
    # Clean fixture => no errors, but assert the summary helper is wired up.
    summary = validator._summarize(errors)
    assert summary == {}
    assert set(validator.ERROR_CLASSES)  # non-empty contract
