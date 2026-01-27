"""Integration tests for Vondr API model parsing.

These tests validate that API responses are correctly parsed into the dataclass models.
Requires the local API server to be running on localhost:8000.
"""

import json
import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()

from vondr.models import (
    ChatCompletionChunk,
    ChatCompletionResponse,
    EmbeddingResponse,
    RerankResponse,
)


pytestmark = pytest.mark.skipif(
    not os.environ.get("VONDR_API_KEY"),
    reason="VONDR_API_KEY environment variable not set",
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


class TestToolCallingModelParsing:
    """Test that tool calling API responses parse correctly."""

    # Sample tool definition in OpenAI format
    WEATHER_TOOL = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country, e.g. Paris, France",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                    },
                },
                "required": ["location"],
            },
        },
    }

    CALCULATOR_TOOL = {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate",
                    },
                },
                "required": ["expression"],
            },
        },
    }

    def test_tool_call_response_parsing(self, client: httpx.Client) -> None:
        """Test that a tool call response parses correctly into ChatCompletionResponse."""
        response = client.post(
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "What's the weather like in Paris right now?"}
                ],
                "tools": [self.WEATHER_TOOL],
                "tool_choice": "auto",
            },
        )
        assert response.status_code == 200

        data = response.json()
        chat_response = ChatCompletionResponse.from_dict(data)

        assert chat_response.object == "chat.completion"
        assert len(chat_response.choices) >= 1

        choice = chat_response.choices[0]
        assert choice.message.role == "assistant"

        # Model should return a tool call for get_weather
        assert choice.message.tool_calls is not None
        assert len(choice.message.tool_calls) >= 1

        tool_call = choice.message.tool_calls[0]
        assert tool_call.id is not None
        assert tool_call.type == "function"
        assert tool_call.function.name == "get_weather"
        assert tool_call.function.arguments is not None

        # Arguments should be valid JSON containing location
        args = json.loads(tool_call.function.arguments)
        assert "location" in args
        assert "paris" in args["location"].lower()

        # finish_reason should be "tool_calls"
        assert choice.finish_reason == "tool_calls"

    def test_tool_response_flow(self, client: httpx.Client) -> None:
        """Test complete tool calling flow: request -> tool_call -> tool_response -> final answer."""
        # Step 1: Initial request that should trigger a tool call
        response1 = client.post(
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "What is 25 * 4?"}
                ],
                "tools": [self.CALCULATOR_TOOL],
            },
        )
        assert response1.status_code == 200

        data1 = response1.json()
        chat_response1 = ChatCompletionResponse.from_dict(data1)
        choice1 = chat_response1.choices[0]

        # Should have a tool call
        assert choice1.message.tool_calls is not None
        tool_call = choice1.message.tool_calls[0]
        assert tool_call.function.name == "calculate"

        # Step 2: Send tool response back
        response2 = client.post(
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "What is 25 * 4?"},
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "100",
                    },
                ],
                "tools": [self.CALCULATOR_TOOL],
            },
        )
        assert response2.status_code == 200

        data2 = response2.json()
        chat_response2 = ChatCompletionResponse.from_dict(data2)
        choice2 = chat_response2.choices[0]

        # Final response should be text, not another tool call
        assert choice2.message.content is not None
        assert "100" in choice2.message.content
        assert choice2.finish_reason == "stop"

    def test_multiple_tools(self, client: httpx.Client) -> None:
        """Test that model can choose from multiple tools."""
        response = client.post(
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "What's the weather in London?"}
                ],
                "tools": [self.WEATHER_TOOL, self.CALCULATOR_TOOL],
            },
        )
        assert response.status_code == 200

        data = response.json()
        chat_response = ChatCompletionResponse.from_dict(data)
        choice = chat_response.choices[0]

        # Should choose weather tool, not calculator
        assert choice.message.tool_calls is not None
        tool_call = choice.message.tool_calls[0]
        assert tool_call.function.name == "get_weather"

    def test_no_tool_call_when_not_needed(self, client: httpx.Client) -> None:
        """Test that model doesn't call tools when not needed (tool_choice=auto)."""
        response = client.post(
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "Say hello in French."}
                ],
                "tools": [self.WEATHER_TOOL],
                "tool_choice": "auto",
            },
        )
        assert response.status_code == 200

        data = response.json()
        chat_response = ChatCompletionResponse.from_dict(data)
        choice = chat_response.choices[0]

        # Should respond with text, not a tool call
        assert choice.message.content is not None
        assert "bonjour" in choice.message.content.lower()
        assert choice.message.tool_calls is None or len(choice.message.tool_calls) == 0
        assert choice.finish_reason == "stop"


class TestToolCallingStreaming:
    """Test that streaming tool calls parse correctly."""

    WEATHER_TOOL = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        },
    }

    def test_streaming_tool_call(self, client: httpx.Client) -> None:
        """Test that streaming responses with tool calls parse correctly."""
        chunks: list[ChatCompletionChunk] = []

        with client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": "vondr-code",
                "messages": [
                    {"role": "user", "content": "What's the weather in Tokyo?"}
                ],
                "tools": [self.WEATHER_TOOL],
                "stream": True,
            },
        ) as response:
            assert response.status_code == 200

            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break

                data = json.loads(data_str)
                chunk = ChatCompletionChunk.from_dict(data)
                chunks.append(chunk)

        assert len(chunks) > 0

        # Find the final chunk with finish_reason
        final_chunks = [c for c in chunks if c.choices and c.choices[0].finish_reason]
        assert len(final_chunks) >= 1

        final_chunk = final_chunks[-1]
        # Should have finish_reason "tool_calls"
        assert final_chunk.choices[0].finish_reason == "tool_calls"

        # Collect tool call data from chunks
        tool_call_chunks = [
            c for c in chunks
            if c.choices and c.choices[0].delta.tool_calls
        ]
        assert len(tool_call_chunks) > 0
