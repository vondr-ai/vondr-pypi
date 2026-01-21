"""Test script to verify the vondr package from TestPyPI works correctly.

Run this after installing from TestPyPI:
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vondr==0.2.0
    python test_testpypi.py
"""

import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Set the production API URL
os.environ.setdefault("VONDR_BASE_URL", "https://app-api.vondr.ai/v1")

from vondr import VondrClient, AsyncVondrClient

def test_chat():
    """Test chat completion."""
    print("Testing chat completion...")
    with VondrClient() as client:
        response = client.chat(
            messages=[{"role": "user", "content": "Say hello in one word"}],
            model="vondr-fast",
        )
        print(f"  Response: {response.choices[0].message.content}")
        print("  ✓ Chat works!")

def test_embed():
    """Test embeddings."""
    print("\nTesting embeddings...")
    with VondrClient() as client:
        response = client.embed(
            input=["Hello world"],
            model="vondr-embed-dense",
        )
        print(f"  Embedding dimensions: {len(response.data[0].embedding)}")
        print("  ✓ Embed works!")

def test_rerank():
    """Test reranking."""
    print("\nTesting rerank...")
    with VondrClient() as client:
        response = client.rerank(
            query="capital of France",
            documents=["Paris is in France", "Berlin is in Germany"],
            model="vondr-rerank",
        )
        print(f"  Top result: index {response.results[0].index}, score {response.results[0].relevance_score:.3f}")
        print("  ✓ Rerank works!")

def test_vision():
    """Test vision with image."""
    print("\nTesting vision...")
    # 1x1 red pixel PNG
    data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

    with VondrClient() as client:
        response = client.chat(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this image? One word."},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            model="vondr-fast",
        )
        print(f"  Response: {response.choices[0].message.content}")
        print("  ✓ Vision works!")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing vondr package from TestPyPI")
    print("=" * 50)

    try:
        test_chat()
        test_embed()
        test_rerank()
        test_vision()

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
