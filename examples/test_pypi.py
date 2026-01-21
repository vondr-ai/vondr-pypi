"""Test script to verify the vondr package from PyPI works correctly.

Run this after installing from PyPI:
    pip install vondr==0.2.0
    python test_pypi.py
"""

import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Set the local API URL for testing
os.environ.setdefault("VONDR_BASE_URL", "https://app-api.vondr.ai/v1")

from vondr import VondrClient

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
    """Test vision with small image."""
    print("\nTesting vision (small image)...")
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
        print("  ✓ Vision (small) works!")

def test_vision_screenshot():
    """Test vision with screenshot.png file."""
    print("\nTesting vision (screenshot.png)...")

    try:
        from vondr import encode_image
    except ImportError:
        print("  ⚠ Skipping: Pillow not installed. Run: pip install vondr[images]")
        return

    import os
    screenshot_path = os.path.join(os.path.dirname(__file__), "screenshot.png")

    if not os.path.exists(screenshot_path):
        print(f"  ⚠ Skipping: screenshot.png not found at {screenshot_path}")
        return

    # Get file size
    file_size = os.path.getsize(screenshot_path)
    print(f"  Original file size: {file_size / 1024:.1f} KB")

    # Encode the image (will resize if > 20MB)
    data_uri = encode_image(screenshot_path)

    # Calculate encoded size
    encoded_size = len(data_uri.split(",")[1]) * 3 / 4
    print(f"  Encoded size: {encoded_size / 1024:.1f} KB")

    with VondrClient() as client:
        response = client.chat(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this screenshot in one sentence."},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            model="vondr-fast",
        )
        print(f"  Response: {response.choices[0].message.content}")
        print("  ✓ Vision (screenshot) works!")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing vondr package from PyPI")
    print("=" * 50)

    try:
        test_chat()
        test_embed()
        test_rerank()
        test_vision()
        test_vision_screenshot()

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
