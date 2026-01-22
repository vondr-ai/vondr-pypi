"""Response models for Vondr AI Platform API.

These models are OpenAI-compatible, following the Chat Completions API format.
See: https://platform.openai.com/docs/api-reference/chat
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# =============================================================================
# Chat Completions Models (OpenAI-compatible)
# =============================================================================


@dataclass
class FunctionCall:
    """Function call in a message (legacy, use tool_calls instead)."""

    name: str
    arguments: str  # JSON string


@dataclass
class ToolCallFunction:
    """Function details within a tool call."""

    name: str
    arguments: str  # JSON string


@dataclass
class ToolCall:
    """Tool call requested by the model."""

    id: str
    type: Literal["function"]
    function: ToolCallFunction


@dataclass
class Message:
    """Chat message in OpenAI format."""

    role: Literal["system", "user", "assistant", "tool", "function"]
    content: str | None
    tool_calls: list[ToolCall] | None = None
    function_call: FunctionCall | None = None  # Legacy, deprecated
    name: str | None = None  # For tool/function messages
    tool_call_id: str | None = None  # For tool response messages


@dataclass
class TopLogprob:
    """Token with log probability."""

    token: str
    logprob: float
    bytes: list[int] | None = None


@dataclass
class LogprobContent:
    """Logprob information for a single token."""

    token: str
    logprob: float
    bytes: list[int] | None = None
    top_logprobs: list[TopLogprob] | None = None


@dataclass
class ChoiceLogprobs:
    """Log probability information for a choice."""

    content: list[LogprobContent] | None = None


@dataclass
class Choice:
    """Chat completion choice."""

    index: int
    message: Message
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"] | None
    logprobs: ChoiceLogprobs | None = None


@dataclass
class PromptTokensDetails:
    """Details about prompt tokens."""

    cached_tokens: int = 0
    audio_tokens: int | None = None


@dataclass
class CompletionTokensDetails:
    """Details about completion tokens."""

    reasoning_tokens: int = 0
    audio_tokens: int | None = None
    accepted_prediction_tokens: int | None = None
    rejected_prediction_tokens: int | None = None


@dataclass
class Usage:
    """Token usage statistics (OpenAI-compatible)."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: PromptTokensDetails | None = None
    completion_tokens_details: CompletionTokensDetails | None = None
    # LiteLLM extensions for caching
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class ChatCompletionResponse:
    """Response from the /chat/completions endpoint (OpenAI-compatible).

    This matches the OpenAI Chat Completion response format exactly.
    See: https://platform.openai.com/docs/api-reference/chat/object
    """

    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: list[Choice]
    usage: Usage | None = None
    system_fingerprint: str | None = None
    service_tier: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletionResponse:
        """Create from API response dict."""
        choices = []
        for c in data.get("choices", []):
            # Parse message
            msg_data = c.get("message", {})

            # Parse tool_calls if present
            tool_calls = None
            if msg_data.get("tool_calls"):
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        type=tc["type"],
                        function=ToolCallFunction(
                            name=tc["function"]["name"],
                            arguments=tc["function"]["arguments"],
                        ),
                    )
                    for tc in msg_data["tool_calls"]
                ]

            # Parse function_call if present (legacy)
            function_call = None
            if msg_data.get("function_call"):
                fc = msg_data["function_call"]
                function_call = FunctionCall(name=fc["name"], arguments=fc["arguments"])

            message = Message(
                role=msg_data.get("role", "assistant"),
                content=msg_data.get("content"),
                tool_calls=tool_calls,
                function_call=function_call,
                name=msg_data.get("name"),
                tool_call_id=msg_data.get("tool_call_id"),
            )

            # Parse logprobs if present
            logprobs = None
            if c.get("logprobs"):
                lp = c["logprobs"]
                content_logprobs = None
                if lp.get("content"):
                    content_logprobs = [
                        LogprobContent(
                            token=item["token"],
                            logprob=item["logprob"],
                            bytes=item.get("bytes"),
                            top_logprobs=[
                                TopLogprob(
                                    token=tp["token"],
                                    logprob=tp["logprob"],
                                    bytes=tp.get("bytes"),
                                )
                                for tp in item.get("top_logprobs", [])
                            ] if item.get("top_logprobs") else None,
                        )
                        for item in lp["content"]
                    ]
                logprobs = ChoiceLogprobs(content=content_logprobs)

            choices.append(
                Choice(
                    index=c.get("index", 0),
                    message=message,
                    finish_reason=c.get("finish_reason"),
                    logprobs=logprobs,
                )
            )

        # Parse usage
        usage = None
        if data.get("usage"):
            u = data["usage"]

            # Parse prompt_tokens_details
            prompt_details = None
            if u.get("prompt_tokens_details"):
                pd = u["prompt_tokens_details"]
                prompt_details = PromptTokensDetails(
                    cached_tokens=pd.get("cached_tokens", 0),
                    audio_tokens=pd.get("audio_tokens"),
                )

            # Parse completion_tokens_details
            completion_details = None
            if u.get("completion_tokens_details"):
                cd = u["completion_tokens_details"]
                completion_details = CompletionTokensDetails(
                    reasoning_tokens=cd.get("reasoning_tokens", 0),
                    audio_tokens=cd.get("audio_tokens"),
                    accepted_prediction_tokens=cd.get("accepted_prediction_tokens"),
                    rejected_prediction_tokens=cd.get("rejected_prediction_tokens"),
                )

            usage = Usage(
                prompt_tokens=u.get("prompt_tokens", 0),
                completion_tokens=u.get("completion_tokens", 0),
                total_tokens=u.get("total_tokens", 0),
                prompt_tokens_details=prompt_details,
                completion_tokens_details=completion_details,
                cache_creation_input_tokens=u.get("cache_creation_input_tokens", 0),
                cache_read_input_tokens=u.get("cache_read_input_tokens", 0),
            )

        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
            system_fingerprint=data.get("system_fingerprint"),
            service_tier=data.get("service_tier"),
        )


# =============================================================================
# Streaming Models (OpenAI-compatible)
# =============================================================================


@dataclass
class DeltaMessage:
    """Delta message in streaming response."""

    role: str | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    function_call: FunctionCall | None = None


@dataclass
class StreamChoice:
    """Choice in a streaming chunk."""

    index: int
    delta: DeltaMessage
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "function_call"] | None = None
    logprobs: ChoiceLogprobs | None = None


@dataclass
class ChatCompletionChunk:
    """Streaming chunk from /chat/completions (OpenAI-compatible).

    See: https://platform.openai.com/docs/api-reference/chat/streaming
    """

    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    choices: list[StreamChoice]
    system_fingerprint: str | None = None
    usage: Usage | None = None  # Only in final chunk with stream_options

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletionChunk:
        """Create from streaming response dict."""
        choices = []
        for c in data.get("choices", []):
            delta_data = c.get("delta", {})

            # Parse tool_calls in delta
            tool_calls = None
            if delta_data.get("tool_calls"):
                tool_calls = [
                    ToolCall(
                        id=tc.get("id", ""),
                        type=tc.get("type", "function"),
                        function=ToolCallFunction(
                            name=tc.get("function", {}).get("name", ""),
                            arguments=tc.get("function", {}).get("arguments", ""),
                        ),
                    )
                    for tc in delta_data["tool_calls"]
                ]

            delta = DeltaMessage(
                role=delta_data.get("role"),
                content=delta_data.get("content"),
                tool_calls=tool_calls,
                function_call=delta_data.get("function_call"),
            )

            choices.append(
                StreamChoice(
                    index=c.get("index", 0),
                    delta=delta,
                    finish_reason=c.get("finish_reason"),
                    logprobs=c.get("logprobs"),
                )
            )

        return cls(
            id=data.get("id", ""),
            object=data.get("object", "chat.completion.chunk"),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            system_fingerprint=data.get("system_fingerprint"),
            usage=data.get("usage"),
        )


# =============================================================================
# Embeddings Models (OpenAI-compatible)
# =============================================================================


@dataclass
class EmbeddingData:
    """Single embedding result."""

    object: Literal["embedding"]
    embedding: list[float]
    index: int


@dataclass
class EmbeddingResponse:
    """Response from the /embeddings endpoint (OpenAI-compatible).

    See: https://platform.openai.com/docs/api-reference/embeddings
    """

    object: Literal["list"]
    data: list[EmbeddingData]
    model: str
    usage: Usage

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingResponse:
        """Create from API response dict."""
        return cls(
            object=data.get("object", "list"),
            data=[
                EmbeddingData(
                    object=d.get("object", "embedding"),
                    embedding=d["embedding"],
                    index=d.get("index", i),
                )
                for i, d in enumerate(data.get("data", []))
            ],
            model=data.get("model", ""),
            usage=Usage(
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=0,
                total_tokens=data.get("usage", {}).get("total_tokens", 0),
            ),
        )


# =============================================================================
# Rerank Models (Vondr-specific, follows Cohere/Jina format)
# =============================================================================


@dataclass
class RerankedDocument:
    """Single reranked document result."""

    index: int
    relevance_score: float
    document: str


@dataclass
class RerankUsage:
    """Usage for rerank endpoint."""

    prompt_tokens: int
    total_tokens: int


@dataclass
class RerankResponse:
    """Response from the /rerank endpoint.

    Note: This follows the Cohere/Jina rerank format, not OpenAI
    (OpenAI doesn't have a rerank endpoint).
    """

    model: str
    results: list[RerankedDocument]
    usage: RerankUsage

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RerankResponse:
        """Create from API response dict."""
        return cls(
            model=data.get("model", ""),
            results=[
                RerankedDocument(
                    index=r["index"],
                    relevance_score=r["relevance_score"],
                    document=r.get("document", ""),
                )
                for r in data.get("results", [])
            ],
            usage=RerankUsage(
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                total_tokens=data.get("usage", {}).get("total_tokens", 0),
            ),
        )
