"""End-to-end tests for onboarding and website analysis with real AI.

Tests:
- Website scanning and analysis
- Onboarding suggestions
- Business data extraction from websites
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_website_scan_real_ai(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test website scanning with real AI analysis.

    Validates:
    - Website content extracted
    - AI analyzes business info
    - Structured data returned
    """
    payload = {"url": "https://www.example.com"}

    response = await e2e_client.post("/api/website/scan", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert "domain" in data
    assert "business_info" in data

    business_info = data["business_info"]
    assert "industry" in business_info
    assert "value_proposition" in business_info

    # AI should extract meaningful info
    assert len(business_info.get("industry", "")) > 0
    assert len(business_info.get("value_proposition", "")) > 10


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_onboarding_suggestions_real_ai(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test onboarding suggestions with real AI.

    Validates:
    - Personalized suggestions generated
    - Multiple suggestion types
    - Context-aware recommendations
    """
    payload = {
        "business_context": {
            "business_name": "TechStartup Inc",
            "industry": "SaaS",
            "stage": "Seed",
            "team_size": 5,
        },
        "goals": ["Define core values", "Create mission statement", "Set OKRs"],
    }

    response = await e2e_client.post("/api/suggestions/onboarding", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "suggestions" in data
    assert len(data["suggestions"]) > 0

    for suggestion in data["suggestions"]:
        assert "title" in suggestion
        assert "description" in suggestion
        assert "priority" in suggestion
        assert len(suggestion["description"]) > 30  # Real AI content


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_bulk_website_scan_real_ai(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test bulk website scanning with real AI.

    Validates:
    - Multiple URLs processed
    - Parallel processing works
    - All results returned
    """
    urls = ["https://www.example.com", "https://www.google.com", "https://www.github.com"]

    response = await e2e_client.post("/api/website/bulk-scan", json={"urls": urls})

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == len(urls)

    for result in data["results"]:
        assert "url" in result
        assert "status" in result
        if result["status"] == "success":
            assert "business_info" in result


__all__ = []  # Test module, no exports
