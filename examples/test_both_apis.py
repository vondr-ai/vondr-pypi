"""Test script to verify calls to both Vondr APIs."""

import os
from dotenv import load_dotenv

load_dotenv()

from vondr import VondrClient


def test_app_api():
    """Test app-api.vondr.ai with VONDR_API_KEY."""
    print("Testing app-api.vondr.ai...")

    client = VondrClient(
        api_key=os.environ["VONDR_API_KEY"],
        base_url="https://app-api.vondr.ai/v1",
    )

    response = client.chat(
        messages=[{"role": "user", "content": "Say hello in one word"}],
        model="vondr-fast",
    )
    print(f"  Response: {response.choices[0].message.content}")
    print("  app-api.vondr.ai works!")


def test_witteveenbos_api():
    """Test witteveenbos-api.vondr.ai with WITTEVEEN_BOS_API_KEY."""
    print("\nTesting witteveenbos-api.vondr.ai...")

    client = VondrClient(
        api_key=os.environ["WITTEVEEN_BOS_API_KEY"],
        base_url="https://witteveenbos-api.vondr.ai/v1",
    )

    response = client.chat(
        messages=[{"role": "user", "content": "Say hello in one word"}],
        model="vondr-fast",
    )
    print(f"  Response: {response.choices[0].message.content}")
    print("  witteveenbos-api.vondr.ai works!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing both Vondr APIs")
    print("=" * 50)

    try:
        test_app_api()
        test_witteveenbos_api()

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\nError: {e}")
        raise
