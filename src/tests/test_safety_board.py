import pytest


@pytest.mark.safety
def test_add() -> None:
    assert 2 + 4 == 6, "Add Failed"


@pytest.mark.safety
def test_subtract() -> None:
    assert 6 - 4 == 2, "Subtract Failed"


@pytest.mark.safety
def test_multiply() -> None:
    assert 2 * 2 == 4, "Multiply Failed"
