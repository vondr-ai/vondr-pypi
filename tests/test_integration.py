"""Integration tests for Vondr API model parsing.

These tests validate that API responses are correctly parsed into the dataclass models.
Requires the local API server to be running on localhost:8000.
"""

import json

import httpx
import pytest

from vondr.models import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    EmbeddingResponse,
    RerankResponse,
)


class TestEmbedModelParsing:
    """Test that embed API responses parse correctly into EmbeddingResponse."""

    def test_embed_model_parsing(self, client: httpx.Client) -> None:
        """Test vondr-embed response parses into EmbeddingResponse."""
        response = client.post(
            "/embed",
            json={"model": "vondr-embed", "input": ["Hello world"]},
        )
        assert response.status_code == 200

        data = response.json()
        embedding_response = EmbeddingResponse.from_dict(data)

        assert embedding_response.object == "list"
        assert len(embedding_response.data) == 1
        assert embedding_response.data[0].object == "embedding"
        assert isinstance(embedding_response.data[0].embedding, list)
        assert len(embedding_response.data[0].embedding) > 0
        assert all(isinstance(x, float) for x in embedding_response.data[0].embedding)
        assert embedding_response.data[0].index == 0

    def test_embed_multiple_inputs(self, client: httpx.Client) -> None:
        """Test embedding multiple inputs."""
        response = client.post(
            "/embed",
            json={"model": "vondr-embed", "input": ["Hello", "World"]},
        )
        assert response.status_code == 200

        data = response.json()
        embedding_response = EmbeddingResponse.from_dict(data)

        assert len(embedding_response.data) == 2
        assert embedding_response.data[0].index == 0
        assert embedding_response.data[1].index == 1


class TestRerankModelParsing:
    """Test that rerank API responses parse correctly into RerankResponse."""

    def test_rerank_model_parsing(self, client: httpx.Client) -> None:
        """Test vondr-rerank response parses into RerankResponse."""
        response = client.post(
            "/rerank",
            json={
                "model": "vondr-rerank",
                "query": "hoofdstad van Frankrijk",
                "documents": [
                    "Parijs ligt in Frankrijk",
                    "Berlijn ligt in Duitsland",
                ],
            },
        )
        assert response.status_code == 200

        data = response.json()
        rerank_response = RerankResponse.from_dict(data)

        assert rerank_response.model is not None
        assert len(rerank_response.results) == 2

        for result in rerank_response.results:
            assert isinstance(result.index, int)
            assert isinstance(result.relevance_score, float)
            assert 0.0 <= result.relevance_score <= 1.0

        # The document about Paris should rank higher
        scores_by_index = {r.index: r.relevance_score for r in rerank_response.results}
        assert scores_by_index[0] > scores_by_index[1]


class TestChatModelParsing:
    """Test that chat API responses parse correctly into ChatCompletionResponse."""

    def test_chat_non_streaming_model_parsing(self, client: httpx.Client) -> None:
        """Test non-streaming chat response parses into ChatCompletionResponse."""
        response = client.post(
            "/chat/completions",
            json={
                "model": "vondr-fast",
                "messages": [{"role": "user", "content": "Zeg alleen: hallo"}],
            },
        )
        assert response.status_code == 200

        data = response.json()
        chat_response = ChatCompletionResponse.from_dict(data)

        assert chat_response.object == "chat.completion"
        assert chat_response.model is not None
        assert len(chat_response.choices) >= 1

        choice = chat_response.choices[0]
        assert choice.index == 0
        assert choice.message.role == "assistant"
        assert choice.message.content is not None
        assert len(choice.message.content) > 0


class TestStreamingModelParsing:
    """Test that streaming chat responses parse correctly into ChatCompletionChunk."""

    def test_streaming_chat_model_parsing(self, client: httpx.Client) -> None:
        """Test streaming chat response parses into ChatCompletionChunk."""
        chunks: list[ChatCompletionChunk] = []

        with client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": "vondr-fast",
                "messages": [{"role": "user", "content": "Tel van 1 tot 3"}],
                "stream": True,
            },
        ) as response:
            assert response.status_code == 200

            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]  # Remove "data: " prefix
                if data_str == "[DONE]":
                    break

                data = json.loads(data_str)
                chunk = ChatCompletionChunk.from_dict(data)
                chunks.append(chunk)

        assert len(chunks) > 0

        # First chunk should have role
        first_chunk = chunks[0]
        assert first_chunk.object == "chat.completion.chunk"
        assert len(first_chunk.choices) >= 1

        # Collect content from all chunks
        content_parts = []
        for chunk in chunks:
            if chunk.choices and chunk.choices[0].delta.content:
                content_parts.append(chunk.choices[0].delta.content)

        full_content = "".join(content_parts)
        assert len(full_content) > 0


class TestVisionModelParsing:
    """Test that vision/image API responses parse correctly."""

    # 1x1 red pixel PNG (minimal valid PNG)
    RED_PIXEL_PNG_BASE64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )

    def test_chat_with_image_model_parsing(self, client: httpx.Client) -> None:
        """Test chat with image parses into ChatCompletionResponse."""
        data_uri = f"data:image/png;base64,{self.RED_PIXEL_PNG_BASE64}"

        response = client.post(
            "/chat/completions",
            json={
                "model": "vondr-fast",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What color is this image? Answer in one word."},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
            },
        )
        assert response.status_code == 200

        data = response.json()
        chat_response = ChatCompletionResponse.from_dict(data)

        assert chat_response.object == "chat.completion"
        assert len(chat_response.choices) >= 1

        choice = chat_response.choices[0]
        assert choice.message.role == "assistant"
        assert choice.message.content is not None
        assert len(choice.message.content) > 0
