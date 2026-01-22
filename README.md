# vondr

Python client for the Vondr AI Platform.

## Installation

```bash
pip install vondr
```

## Quick Start

```python
from vondr import VondrClient

# Set environment variables or pass directly
# VONDR_API_KEY=your-api-key
# VONDR_BASE_URL=https://{HOSTNAME}-api.vondr.ai/v1

client = VondrClient()
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
    model="vondr-embed",
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

# Encode image from file path
image_uri = encode_image("/path/to/image.jpg")

client = VondrClient()
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

client = AsyncVondrClient()
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
| `vondr-embed` | Text embeddings |
| `vondr-rerank` | Document reranking |

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `VONDR_API_KEY` | Your API key |
| `VONDR_BASE_URL` | API base URL (e.g., `https://{HOSTNAME}-api.vondr.ai/v1`) |

## Development

Install Poetry (`pipx install poetry` recommended).

```bash
poetry install
poetry run pytest
```

## Release

Set your token before publishing: `POETRY_PYPI_TOKEN_PYPI` (or `POETRY_PYPI_TOKEN_TESTPYPI` when targeting TestPyPI).

**Using PowerShell script:**

```powershell
./scripts/release.ps1 -Version 0.2.1          # publish to PyPI
./scripts/release.ps1 -Version 0.2.1 -Repository testpypi  # publish to TestPyPI
```

The script will bump the version in `pyproject.toml`, install deps, run tests, build wheel+sdist, publish, then commit/tag/push if a git remote exists.

**Manual release:**

```bash
poetry version 0.2.1
poetry build
export POETRY_PYPI_TOKEN_TESTPYPI="your-token"
poetry publish -r testpypi

export POETRY_PYPI_TOKEN_PYPI="your-token"
poetry publish
```
