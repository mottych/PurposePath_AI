#!/usr/bin/env python
"""Test script to verify Google Vertex AI configuration.

Run this script to test your Google Vertex AI setup:
    cd coaching
    uv run python scripts/test_google_vertex.py

Prerequisites:
    1. Google Cloud Project with Vertex AI API enabled
    2. Billing enabled on the project
    3. Service account with Vertex AI User role
    4. Environment variables set:
       - GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
       - GOOGLE_PROJECT_ID=your-project-id (optional if in credentials file)
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_prerequisites() -> bool:
    """Check if Google Vertex AI prerequisites are met."""
    print("=" * 60)
    print("Google Vertex AI Configuration Check")
    print("=" * 60)

    # Check for credentials file
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GOOGLE_PROJECT_ID")

    print(f"\n1. GOOGLE_APPLICATION_CREDENTIALS: {creds_path or '❌ NOT SET'}")
    if creds_path:
        if os.path.exists(creds_path):
            print("   ✅ File exists")
        else:
            print(f"   ❌ File NOT found at: {creds_path}")
            return False

    print(f"\n2. GOOGLE_PROJECT_ID: {project_id or '(will use credentials file)'}")

    # Check if google-cloud-aiplatform is installed
    try:
        import google.cloud.aiplatform  # noqa: F401

        print("\n3. google-cloud-aiplatform: ✅ Installed")
    except ImportError:
        print("\n3. google-cloud-aiplatform: ❌ NOT installed")
        print("   Run: uv pip install google-cloud-aiplatform>=1.40.0")
        return False

    if not creds_path and not project_id:
        print("\n❌ Either GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_PROJECT_ID must be set")
        print("\nTo configure:")
        print("  $env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\\path\\to\\service-account.json'")
        print("  $env:GOOGLE_PROJECT_ID = 'your-project-id'")
        return False

    return True


async def test_gemini_model() -> None:
    """Test Gemini model generation."""
    from src.domain.ports.llm_provider_port import LLMMessage
    from src.infrastructure.llm.google_vertex_provider import GoogleVertexLLMProvider

    print("\n" + "=" * 60)
    print("Testing Gemini Model")
    print("=" * 60)

    project_id = os.getenv("GOOGLE_PROJECT_ID")
    location = os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")

    print("\nInitializing GoogleVertexLLMProvider...")
    print(f"  Project ID: {project_id or '(from credentials)'}")
    print(f"  Location: {location}")

    provider = GoogleVertexLLMProvider(project_id=project_id, location=location)

    # Test with Gemini 2.5 Flash (faster and cheaper for testing)
    test_models = ["gemini-2.5-flash", "gemini-2.5-pro"]

    for model in test_models:
        print(f"\n--- Testing {model} ---")
        try:
            messages = [LLMMessage(role="user", content="What is 2+2? Reply with just the number.")]

            response = await provider.generate(
                messages=messages,
                model=model,
                temperature=0.5,
                max_tokens=50,
            )

            print(f"✅ {model} SUCCESS")
            print(f"   Response: {response.content.strip()}")
            print(f"   Tokens: {response.usage}")
            break  # Success, no need to try other models

        except Exception as e:
            print(f"❌ {model} FAILED: {e}")
            if "billing" in str(e).lower():
                print("   → Enable billing at: https://console.cloud.google.com/billing")
            elif "permission" in str(e).lower() or "403" in str(e):
                print("   → Grant 'Vertex AI User' role to your service account")
            elif "not found" in str(e).lower() or "404" in str(e):
                print(
                    "   → Enable Vertex AI API at: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com"
                )


async def main() -> None:
    """Main entry point."""
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please configure Google Vertex AI first.")
        sys.exit(1)

    try:
        await test_gemini_model()
        print("\n" + "=" * 60)
        print("✅ Google Vertex AI is configured correctly!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
