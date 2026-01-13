import pytest

from vondr import greet


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Vondr", "Hello, Vondr!"),
        ("  Alice  ", "Hello, Alice!"),
        ("", "Hello, there!"),
        ("   ", "Hello, there!"),
    ],
)
def test_greet(name: str, expected: str) -> None:
    assert greet(name) == expected

