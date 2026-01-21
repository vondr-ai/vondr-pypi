"""
Vondr AI Platform client library.

Example:
    # Synchronous usage
    from vondr import VondrClient

    with VondrClient() as client:
        response = client.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response.choices[0].message.content)

    # Asynchronous usage
    from vondr import AsyncVondrClient

    async with AsyncVondrClient() as client:
        response = await client.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response.choices[0].message.content)
"""

from importlib import metadata as importlib_metadata

from vondr._client import AsyncVondrClient
from vondr._sync_client import VondrClient
from vondr.exceptions import (
    VondrAPIError,
    VondrAuthError,
    VondrConfigError,
    VondrError,
    VondrRateLimitError,
)
from vondr.models import (
    # Chat Completions
    ChatCompletionResponse,
    ChatCompletionChunk,
    Choice,
    StreamChoice,
    Message,
    DeltaMessage,
    FunctionCall,
    ToolCall,
    ToolCallFunction,
    ChoiceLogprobs,
    LogprobContent,
    TopLogprob,
    # Usage
    Usage,
    PromptTokensDetails,
    CompletionTokensDetails,
    # Embeddings
    EmbeddingResponse,
    EmbeddingData,
    # Rerank
    RerankResponse,
    RerankedDocument,
    RerankUsage,
)

# Image encoding is optional (requires Pillow)
try:
    from vondr._images import encode_image
except ImportError:
    encode_image = None  # type: ignore[misc, assignment]

__all__ = [
    # Clients
    "VondrClient",
    "AsyncVondrClient",
    # Chat Completions Models
    "ChatCompletionResponse",
    "ChatCompletionChunk",
    "Choice",
    "StreamChoice",
    "Message",
    "DeltaMessage",
    "FunctionCall",
    "ToolCall",
    "ToolCallFunction",
    "ChoiceLogprobs",
    "LogprobContent",
    "TopLogprob",
    # Usage Models
    "Usage",
    "PromptTokensDetails",
    "CompletionTokensDetails",
    # Embeddings Models
    "EmbeddingResponse",
    "EmbeddingData",
    # Rerank Models
    "RerankResponse",
    "RerankedDocument",
    "RerankUsage",
    # Exceptions
    "VondrError",
    "VondrAPIError",
    "VondrAuthError",
    "VondrRateLimitError",
    "VondrConfigError",
    # Utilities
    "encode_image",
]


def _load_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:
        return "0.0.0"


__version__ = _load_version()

