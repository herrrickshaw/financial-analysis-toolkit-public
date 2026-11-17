"""Characterisation tests: engine outputs must match the numbers captured before the SDLC refactor, bit for bit."""
import pytest

from golden_cases import GOLDEN, build, dump

CASES = build()


@pytest.mark.parametrize("name", sorted(CASES))
def test_matches_golden(name):
    assert dump(CASES[name]) + "\n" == (GOLDEN / f"{name}.json").read_text()
