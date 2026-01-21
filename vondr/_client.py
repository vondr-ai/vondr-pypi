"""Async client for Vondr AI Platform API."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from vondr.exceptions import (
    VondrAPIError,
    VondrAuthError,
    VondrConfigError,
    VondrRateLimitError,
)
from vondr.models import (
    ChatCompletionResponse,
    EmbeddingResponse,
    RerankResponse,
)

DEFAULT_TIMEOUT = 230.0
MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

SUPPORTED_CHAT_MODELS = {
    "vondr-fast",
    "vondr-code",
    "vondr-think",
}

SUPPORTED_EMBED_MODELS = {
    "vondr-embed-sparse",
    "vondr-embed-dense",
}

SUPPORTED_RERANK_MODELS = {
    "vondr-rerank",
}

SUPPORTED_MODELS = SUPPORTED_CHAT_MODELS | SUPPORTED_EMBED_MODELS | SUPPORTED_RERANK_MODELS


class AsyncVondrClient:
    """Async client for Vondr AI Platform.

    Args:
        api_key: API key for authentication. If not provided, reads from
            VONDR_API_KEY environment variable.
        base_url: Base URL for the API. If not provided, reads from
            VONDR_BASE_URL environment variable. Required.
        timeout: Request timeout in seconds. Defaults to 230.
        max_retries: Maximum number of retries for failed requests. Defaults to 3.

    Example:
        async with AsyncVondrClient(base_url="https://api.example.com/v1") as client:
            response = await client.chat([
                {"role": "user", "content": "Hello!"}
            ])
            print(response.choices[0].message.content)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        self.api_key = api_key or os.environ.get("VONDR_API_KEY")
        if not self.api_key:
            raise VondrConfigError(
                "API key is required. Provide it via api_key parameter "
                "or set the VONDR_API_KEY environment variable."
            )

        self.base_url = base_url or os.environ.get("VONDR_BASE_URL")
        if not self.base_url:
            raise VondrConfigError(
                "Base URL is required. Provide it via base_url parameter "
                "or set the VONDR_BASE_URL environment variable."
            )

        self.base_url = self.base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> AsyncVondrClient:
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic."""
        client = await self._get_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, url, json=json)

                if response.status_code == 401:
                    raise VondrAuthError(
                        "Invalid API key",
                        status_code=401,
                        response_body=response.json() if response.content else None,
                    )

                if response.status_code == 429:
                    raise VondrRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        response_body=response.json() if response.content else None,
                    )

                if response.status_code >= 400:
                    body = response.json() if response.content else {}
                    detail = body.get("detail", "Unknown error")
                    raise VondrAPIError(
                        detail,
                        status_code=response.status_code,
                        response_body=body,
                    )

                return response.json()

            except (VondrAuthError, VondrConfigError):
                # Don't retry auth errors
                raise

            except (VondrRateLimitError, VondrAPIError) as e:
                last_exception = e
                if (
                    isinstance(e, VondrAPIError)
                    and e.status_code not in RETRY_STATUS_CODES
                ):
                    raise

                if attempt + 1 < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    await asyncio.sleep(wait_time)
                else:
                    raise

            except httpx.RequestError as e:
                last_exception = e
                if attempt + 1 < self.max_retries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise VondrAPIError(f"Request failed: {e}") from e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise VondrAPIError("Request failed after all retry attempts")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str = "vondr-code",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 1.0,
        response_format: dict[str, Any] | None = None,
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """Create a chat completion.

        Args:
            messages: List of messages in the conversation. Each message should
                have 'role' and 'content' keys. Content can be a string or a list
                of content parts for multimodal input.
            model: Model to use. One of: vondr-fast, vondr-code, vondr-think.
            temperature: Sampling temperature (0-2). Defaults to 0.7.
            max_tokens: Maximum tokens to generate. Defaults to 4096.
            top_p: Nucleus sampling parameter. Defaults to 1.0.
            response_format: Optional response format (e.g., {"type": "json_object"}).
            thinking_budget: Optional thinking budget for reasoning models.
            **kwargs: Additional parameters passed to the API.

        Returns:
            ChatCompletionResponse with the model's response.

        Example:
            # Simple text message
            response = await client.chat([
                {"role": "user", "content": "Hello!"}
            ])

            # With image (data URI)
            response = await client.chat([
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                    ]
                }
            ])
        """
        if model not in SUPPORTED_CHAT_MODELS:
            raise ValueError(f"Unsupported model: {model}. Must be one of {SUPPORTED_CHAT_MODELS}")

        data: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            **kwargs,
        }

        if response_format is not None:
            data["response_format"] = response_format

        if thinking_budget is not None:
            data["thinking_budget"] = thinking_budget

        response = await self._request("POST", "/chat/completions", json=data)
        return ChatCompletionResponse.from_dict(response)

    async def embed(
        self,
        input: str | list[str],
        model: str = "vondr-embed-dense",
    ) -> EmbeddingResponse:
        """Create embeddings for text.

        Args:
            input: Text or list of texts to embed.
            model: Model to use. One of: vondr-embed-dense, vondr-embed-sparse.

        Returns:
            EmbeddingResponse with the embeddings.

        Example:
            response = await client.embed(["Hello world", "Goodbye world"])
            print(response.data[0].embedding[:5])
        """
        if model not in SUPPORTED_EMBED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Must be one of {SUPPORTED_EMBED_MODELS}")

        # Normalize input to list
        if isinstance(input, str):
            input = [input]

        data = {
            "input": input,
            "model": model,
        }

        response = await self._request("POST", "/embed", json=data)
        return EmbeddingResponse.from_dict(response)

    async def rerank(
        self,
        query: str,
        documents: list[str],
        model: str = "vondr-rerank",
        top_n: int | None = None,
    ) -> RerankResponse:
        """Rerank documents by relevance to a query.

        Args:
            query: The query to rank documents against.
            documents: List of documents to rerank.
            model: Model to use. Defaults to vondr-rerank.
            top_n: Number of top results to return. If not set, returns all.

        Returns:
            RerankResponse with ranked documents.

        Example:
            response = await client.rerank(
                query="What is Python?",
                documents=["Python is a snake", "Python is a programming language"],
            )
            print(response.results[0].document)
        """
        if model not in SUPPORTED_RERANK_MODELS:
            raise ValueError(f"Unsupported model: {model}. Must be one of {SUPPORTED_RERANK_MODELS}")

        data: dict[str, Any] = {
            "query": query,
            "documents": documents,
            "model": model,
        }

        if top_n is not None:
            data["top_n"] = top_n

        response = await self._request("POST", "/rerank", json=data)
        return RerankResponse.from_dict(response)
