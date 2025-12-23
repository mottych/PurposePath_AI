"""E2E test for Google Vertex AI with credentials from AWS Secrets Manager."""

import os

import pytest
from coaching.src.core.config_multitenant import get_google_vertex_credentials, get_settings
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.google_vertex_provider import GoogleVertexLLMProvider


pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_VERTEX_E2E"),
    reason="Google Vertex E2E disabled by default; set RUN_VERTEX_E2E=1 to run",
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gemini_with_secrets_manager_credentials() -> None:
    """
    Test Gemini model with credentials loaded from AWS Secrets Manager.

    This test verifies:
    1. Credentials are correctly loaded from Secrets Manager
    2. GoogleVertexLLMProvider initializes with those credentials
    3. Gemini model responds correctly
    """
    # Get credentials from Secrets Manager
    settings = get_settings()
    creds = get_google_vertex_credentials()

    assert creds is not None, "Google Vertex credentials not found in Secrets Manager"
    assert "project_id" in creds, "Credentials missing project_id"
    assert "client_email" in creds, "Credentials missing client_email"

    project_id = creds.get("project_id")
    location = settings.google_vertex_location

    # Initialize provider
    provider = GoogleVertexLLMProvider(project_id=project_id, location=location)

    # Test with Gemini 2.5 Flash (faster for testing)
    messages = [LLMMessage(role="user", content="What is 2+2? Reply with just the number.")]

    response = await provider.generate(
        messages=messages,
        model="gemini-2.5-flash",
        temperature=0.5,
        max_tokens=50,
    )

    assert response.content, "Response content is empty"
    assert "4" in response.content, f"Expected '4' in response, got: {response.content}"
    assert response.model == "gemini-2.5-flash"
    assert response.provider == "google_vertex"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gemini_25_pro_with_secrets_manager() -> None:
    """Test Gemini 2.5 Pro model."""
    creds = get_google_vertex_credentials()
    assert creds is not None, "Google Vertex credentials not found"

    settings = get_settings()
    provider = GoogleVertexLLMProvider(
        project_id=creds.get("project_id"),
        location=settings.google_vertex_location,
    )

    messages = [
        LLMMessage(
            role="user",
            content="Explain quantum computing in exactly one sentence.",
        )
    ]

    response = await provider.generate(
        messages=messages,
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=100,
    )

    assert response.content
    assert len(response.content) > 20
    assert response.model == "gemini-2.5-pro"
    assert response.provider == "google_vertex"
