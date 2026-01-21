# vondr

Python client for the Vondr AI Platform.

## Installation

```bash
pip install vondr
```

For image support (vision):

```bash
pip install vondr[images]
```

## Quick Start

```python
from vondr import VondrClient

# Set environment variables or pass directly
# VONDR_API_KEY=your-api-key
# VONDR_BASE_URL=https://{HOSTNAME}-api.vondr.ai/v1

with VondrClient() as client:
    response = client.chat([
        {"role": "user", "content": "Hello!"}
    ])
    print(response.choices[0].message.content)
```

## Chat Completion

```python
response = client.chat(
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    model="vondr-fast",  # or vondr-code, vondr-think
    temperature=0.7,
    max_tokens=4096,
)
print(response.choices[0].message.content)
```

## Embeddings

```python
response = client.embed(
    input=["Hello world", "Goodbye world"],
    model="vondr-embed-dense",  # or vondr-embed-sparse
)
for item in response.data:
    print(f"Embedding {item.index}: {len(item.embedding)} dimensions")
```

## Rerank

```python
response = client.rerank(
    query="capital of France",
    documents=["Paris is in France", "Berlin is in Germany"],
    model="vondr-rerank",
)
for result in response.results:
    print(f"Document {result.index}: score {result.relevance_score:.3f}")
```

## Vision (Images)

```python
from vondr import VondrClient, encode_image

with VondrClient() as client:
    # Encode image from file path
    image_uri = encode_image("/path/to/image.jpg")

    response = client.chat([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": image_uri}}
            ]
        }
    ])
    print(response.choices[0].message.content)
```

## Async Client

```python
from vondr import AsyncVondrClient

async with AsyncVondrClient() as client:
    response = await client.chat([
        {"role": "user", "content": "Hello!"}
    ])
    print(response.choices[0].message.content)
```

## Available Models

| Model | Description |
|-------|-------------|
| `vondr-fast` | Fast general-purpose model |
| `vondr-code` | Optimized for code generation |
| `vondr-think` | Reasoning model with thinking budget |
| `vondr-embed-dense` | Dense embeddings |
| `vondr-embed-sparse` | Sparse embeddings |
| `vondr-rerank` | Document reranking |

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `VONDR_API_KEY` | Your API key |
| `VONDR_BASE_URL` | API base URL (e.g., `https://{HOSTNAME}-api.vondr.ai/v1`) |

## Development

```bash
poetry install
poetry run pytest
```
