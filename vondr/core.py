from __future__ import annotations


def greet(name: str) -> str:
    """
    Return a friendly greeting for the provided name.
    """

    cleaned = name.strip() or "there"
    return f"Hello, {cleaned}!"

