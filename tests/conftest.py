"""Pytest configuration and fixtures for integration tests."""

import httpx
import pytest

BASE_URL = "http://localhost:8000/v1"
HEADERS = {
    "x-vondr-auth-type": "api_key",
    "x-vondr-api-key-id": "00000000-0000-0000-0000-000000000001",
    "x-vondr-organization-id": "00000000-0000-0000-0000-000000000001",
    "Content-Type": "application/json",
}


@pytest.fixture
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def headers() -> dict[str, str]:
    return HEADERS.copy()


@pytest.fixture
def client(base_url: str, headers: dict[str, str]) -> httpx.Client:
    """Synchronous httpx client for integration tests."""
    return httpx.Client(base_url=base_url, headers=headers, timeout=60.0)


@pytest.fixture
async def async_client(base_url: str, headers: dict[str, str]) -> httpx.AsyncClient:
    """Async httpx client for integration tests."""
    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=60.0) as client:
        yield client
