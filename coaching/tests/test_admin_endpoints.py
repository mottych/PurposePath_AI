"""Tests for admin health and stats endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_admin_health_endpoint():
    """Test the admin health endpoint returns proper structure."""
    from coaching.src.api.routes.admin.health import get_admin_health
    from coaching.src.domain.entities.llm_topic import LLMTopic
    from coaching.src.repositories.topic_repository import TopicRepository

    # Mock topic repository
    mock_repo = AsyncMock(spec=TopicRepository)

    # Create mock topics
    mock_topics = [
        LLMTopic(
            topic_id="test_topic_1",
            topic_name="Test Topic 1",
            category="coaching",
            topic_type="single_shot",
            description="Test topic",
            tier_level="FREE",
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            display_order=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            prompts=[],
        )
    ]
    mock_repo.list_all = AsyncMock(return_value=mock_topics)

    # Call the endpoint
    response = await get_admin_health(topic_repo=mock_repo)

    # Verify response structure
    assert response.success is True
    assert response.data is not None
    assert hasattr(response.data, "overall_status")
    assert hasattr(response.data, "validation_status")
    assert hasattr(response.data, "service_status")
    assert response.data.overall_status in ["healthy", "warnings", "errors", "critical"]


@pytest.mark.asyncio
async def test_admin_stats_endpoint():
    """Test the admin stats endpoint returns proper structure."""
    from coaching.src.api.routes.admin.topics import get_topics_stats
    from coaching.src.domain.entities.llm_topic import LLMTopic
    from coaching.src.repositories.topic_repository import TopicRepository

    # Mock topic repository
    mock_repo = AsyncMock(spec=TopicRepository)

    # Create mock topics
    mock_topics = [
        LLMTopic(
            topic_id="test_topic_1",
            topic_name="Test Topic 1",
            category="coaching",
            topic_type="single_shot",
            description="Test topic",
            tier_level="FREE",
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            display_order=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            prompts=[],
        ),
        LLMTopic(
            topic_id="test_topic_2",
            topic_name="Test Topic 2",
            category="coaching",
            topic_type="single_shot",
            description="Inactive test topic",
            tier_level="FREE",
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            is_active=False,
            display_order=2,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            prompts=[],
        ),
    ]
    mock_repo.list_all = AsyncMock(return_value=mock_topics)

    # Mock UserContext
    from coaching.src.api.models.auth import UserContext

    mock_user = MagicMock(spec=UserContext)

    # Call the endpoint
    response = await get_topics_stats(
        start_date=None,
        end_date=None,
        tier=None,
        interaction_code=None,
        model_code=None,
        topic_repo=mock_repo,
        _user=mock_user,
    )

    # Verify response structure
    assert "data" in response
    data = response["data"]

    assert "interactions" in data
    assert "templates" in data
    assert "models" in data
    assert "system_health" in data
    assert "last_updated" in data

    # Verify template stats
    assert data["templates"]["total"] == 2
    assert data["templates"]["active"] == 1
    assert data["templates"]["inactive"] == 1


@pytest.mark.asyncio
async def test_health_check_identifies_no_active_topics():
    """Test health check identifies critical issue when no active topics."""
    from coaching.src.api.routes.admin.health import get_admin_health
    from coaching.src.domain.entities.llm_topic import LLMTopic
    from coaching.src.repositories.topic_repository import TopicRepository

    # Mock topic repository with NO active topics
    mock_repo = AsyncMock(spec=TopicRepository)

    mock_topics = [
        LLMTopic(
            topic_id="test_topic_inactive",
            topic_name="Inactive Topic",
            category="coaching",
            topic_type="single_shot",
            description="Test topic",
            tier_level="FREE",
            basic_model_code="claude-3-5-sonnet-20241022",
            premium_model_code="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            is_active=False,
            display_order=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            prompts=[],
        )
    ]
    mock_repo.list_all = AsyncMock(return_value=mock_topics)

    # Call the endpoint
    response = await get_admin_health(topic_repo=mock_repo)

    # Should identify critical issue
    assert response.data.overall_status == "critical"
    assert len(response.data.critical_issues) > 0
    assert any("NO_ACTIVE_TOPICS" in issue.code for issue in response.data.critical_issues)
