"""Quick test for Google Vertex AI with credentials from AWS Secrets Manager."""

import asyncio
import sys

sys.path.insert(0, ".")


async def test_gemini():
    from src.core.config_multitenant import get_google_vertex_credentials, get_settings
    from src.domain.ports.llm_provider_port import LLMMessage
    from src.infrastructure.llm.google_vertex_provider import GoogleVertexLLMProvider

    print("=== Testing Google Vertex AI ===")

    # Get credentials from Secrets Manager
    settings = get_settings()
    creds = get_google_vertex_credentials()

    if creds:
        print("✅ Credentials loaded from Secrets Manager")
        print(f"   Project ID: {creds.get('project_id')}")
        print(f"   Client Email: {creds.get('client_email')}")
    else:
        print("❌ No credentials found")
        return

    project_id = creds.get("project_id")
    location = settings.google_vertex_location

    print(f"\nInitializing provider (location: {location})...")
    provider = GoogleVertexLLMProvider(project_id=project_id, location=location)

    print("\nTesting gemini-2.5-flash...")
    messages = [LLMMessage(role="user", content="What is 2+2? Reply with just the number.")]

    response = await provider.generate(
        messages=messages,
        model="gemini-2.5-flash",
        temperature=0.5,
        max_tokens=50,
    )

    print("✅ SUCCESS!")
    print(f"   Response: {response.content.strip()}")
    print(f"   Model: {response.model}")
    print(f"   Tokens: {response.usage}")


if __name__ == "__main__":
    asyncio.run(test_gemini())
