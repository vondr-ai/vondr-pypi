"""Custom exceptions for Vondr AI Platform client."""

from __future__ import annotations


class VondrError(Exception):
    """Base exception for all Vondr errors."""

    pass


class VondrAPIError(VondrError):
    """Error returned by the Vondr API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.args[0]}"
        return self.args[0]


class VondrAuthError(VondrAPIError):
    """Authentication error (401)."""

    pass


class VondrRateLimitError(VondrAPIError):
    """Rate limit exceeded (429)."""

    pass


class VondrConfigError(VondrError):
    """Configuration error (e.g., missing API key)."""

    pass
