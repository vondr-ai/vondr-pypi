"""Synchronous client for Vondr AI Platform API."""

from __future__ import annotations

import asyncio
from typing import Any

from vondr._client import AsyncVondrClient, DEFAULT_TIMEOUT, MAX_RETRIES
from vondr.models import (
    ChatCompletionResponse,
    EmbeddingResponse,
    RerankResponse,
)


class VondrClient:
    """Synchronous client for Vondr AI Platform.

    This is a synchronous wrapper around AsyncVondrClient.

    Args:
        api_key: API key for authentication. If not provided, reads from
            VONDR_API_KEY environment variable.
        base_url: Base URL for the API. If not provided, reads from
            VONDR_BASE_URL environment variable. Required.
        timeout: Request timeout in seconds. Defaults to 230.
        max_retries: Maximum number of retries for failed requests. Defaults to 3.

    Example:
        client = VondrClient(base_url="https://api.example.com/v1")
        response = client.chat([
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
        self._async_client = AsyncVondrClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    def _run(self, coro: Any) -> Any:
        """Run a coroutine synchronously."""
        loop = self._get_loop()
        try:
            return loop.run_until_complete(coro)
        except RuntimeError:
            # If we're in an existing event loop, create a new one
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

    def close(self) -> None:
        """Close the client."""
        self._run(self._async_client.close())
        if self._loop is not None and not self._loop.is_closed():
            self._loop.close()
            self._loop = None

    def __enter__(self) -> VondrClient:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()

    def chat(
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
            response = client.chat([
                {"role": "user", "content": "Hello!"}
            ])
        """
        return self._run(
            self._async_client.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                response_format=response_format,
                thinking_budget=thinking_budget,
                **kwargs,
            )
        )

    def embed(
        self,
        input: str | list[str],
        model: str = "vondr-embed",
    ) -> EmbeddingResponse:
        """Create embeddings for text.

        Args:
            input: Text or list of texts to embed.
            model: Model to use. Defaults to vondr-embed.

        Returns:
            EmbeddingResponse with the embeddings.

        Example:
            response = client.embed(["Hello world", "Goodbye world"])
            print(response.data[0].embedding[:5])
        """
        return self._run(
            self._async_client.embed(
                input=input,
                model=model,
            )
        )

    def rerank(
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
            response = client.rerank(
                query="What is Python?",
                documents=["Python is a snake", "Python is a programming language"],
            )
            print(response.results[0].document)
        """
        return self._run(
            self._async_client.rerank(
                query=query,
                documents=documents,
                model=model,
                top_n=top_n,
            )
        )
