import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.services.insights_service import BusinessDataContext, InsightsService
from coaching.src.services.llm_service import LLMService

from shared.models.schemas import PaginatedResponse


@pytest.fixture
def mock_repo():
    return MagicMock(spec=DynamoDBConversationRepository)


@pytest.fixture
def mock_business_client():
    client = MagicMock(spec=BusinessApiClient)
    # Setup default async returns
    client.get_organizational_context = AsyncMock(
        return_value={"vision": "Test Vision", "purpose": "Test Purpose"}
    )
    client.get_user_goals = AsyncMock(
        return_value=[{"id": "1", "title": "Goal 1", "status": "active", "progress": 50}]
    )
    client.get_goal_stats = AsyncMock(return_value={"total_goals": 1, "completion_rate": 50})
    client.get_performance_score = AsyncMock(return_value={"score": 85})
    client.get_operations_actions = AsyncMock(return_value=[])
    client.get_operations_issues = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_llm_service():
    service = MagicMock(spec=LLMService)
    service.generate_single_shot_analysis = AsyncMock()
    return service


@pytest.fixture
def insights_service(mock_repo, mock_business_client, mock_llm_service):
    return InsightsService(
        conversation_repo=mock_repo,
        business_api_client=mock_business_client,
        llm_service=mock_llm_service,
        tenant_id="tenant-123",
        user_id="user-123",
    )


@pytest.mark.asyncio
async def test_generate_insights_success(insights_service, mock_llm_service):
    # Arrange
    mock_llm_response = {
        "insights": [
            {
                "title": "Test Insight",
                "description": "Test Description must be at least 20 characters long to pass validation.",
                "category": "strategy",
                "priority": "high",
                "suggested_actions": [
                    {"title": "Action 1", "description": "Desc", "effort": "low", "impact": "high"}
                ],
            }
        ]
    }
    mock_llm_service.generate_single_shot_analysis.return_value = {
        "response": json.dumps(mock_llm_response)
    }

    # Act
    result = await insights_service.generate_insights()

    # Assert
    assert isinstance(result, PaginatedResponse)
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0].title == "Test Insight"
    assert result.data[0].category == "strategy"
    assert result.data[0].priority == "high"
    assert result.pagination.total == 1


@pytest.mark.asyncio
async def test_generate_insights_insufficient_data(insights_service, mock_business_client):
    # Arrange
    # Mock empty data to trigger insufficient data check
    mock_business_client.get_organizational_context.return_value = {}
    mock_business_client.get_user_goals.return_value = []
    mock_business_client.get_goal_stats.return_value = {}

    # Act
    result = await insights_service.generate_insights()

    # Assert
    assert isinstance(result, PaginatedResponse)
    assert result.success is False
    assert len(result.data) == 0
    assert result.pagination.total == 0


@pytest.mark.asyncio
async def test_generate_insights_llm_error(insights_service, mock_llm_service):
    # Arrange
    mock_llm_service.generate_single_shot_analysis.side_effect = Exception("LLM Error")

    # Act
    result = await insights_service.generate_insights()

    # Assert
    # The service catches the exception and returns empty list, so success is True with empty data
    assert isinstance(result, PaginatedResponse)
    assert result.success is True
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_get_insights_summary_success(insights_service, mock_llm_service):
    # Arrange
    mock_llm_response = {
        "insights": [
            {
                "title": "Insight 1",
                "description": "Description 1 must be long enough to pass validation rules.",
                "category": "strategy",
                "priority": "high",
                "suggested_actions": [],
            },
            {
                "title": "Insight 2",
                "description": "Description 2 must be long enough to pass validation rules.",
                "category": "operations",
                "priority": "medium",
                "suggested_actions": [],
            },
        ]
    }
    mock_llm_service.generate_single_shot_analysis.return_value = {
        "response": json.dumps(mock_llm_response)
    }

    # Act
    summary = await insights_service.get_insights_summary("user-123")

    # Assert
    assert summary.total_insights == 2
    assert summary.by_category["strategy"] == 1
    assert summary.by_category["operations"] == 1
    assert summary.by_priority["high"] == 1
    assert summary.by_priority["medium"] == 1


@pytest.mark.asyncio
async def test_fetch_business_data_partial_failure(insights_service, mock_business_client):
    # Arrange
    # Simulate one service failing while others succeed
    mock_business_client.get_organizational_context.side_effect = Exception("API Error")

    # Act
    # Accessing private method for testing
    data = await insights_service._fetch_business_data()

    # Assert
    assert data.foundation == {}  # Should be empty dict on error
    assert len(data.goals) == 1  # Other calls should still succeed (from default fixture)


@pytest.mark.asyncio
async def test_parse_llm_response_formats(insights_service):
    # Test dict with 'response' key
    resp1 = {"response": '{"insights": []}'}
    parsed1 = insights_service._parse_llm_response(resp1)
    assert "insights" in parsed1

    # Test dict with 'analysis' key
    resp2 = {"analysis": '{"insights": []}'}
    parsed2 = insights_service._parse_llm_response(resp2)
    assert "insights" in parsed2

    # Test string response
    resp3 = '{"insights": []}'
    parsed3 = insights_service._parse_llm_response(resp3)
    assert "insights" in parsed3

    # Test invalid json
    resp4 = "Not JSON"
    parsed4 = insights_service._parse_llm_response(resp4)
    assert parsed4 == {"insights": []}  # Should return empty insights structure on error


def test_build_insights_prompt(insights_service):
    # Arrange
    data = BusinessDataContext(
        tenant_id="t1",
        foundation={"vision": "V", "purpose": "P", "core_values": ["V1", "V2"]},
        goals=[{"title": "G1", "status": "active", "progress": 10}],
        goal_stats={"total_goals": 1, "completion_rate": 10},
        performance_score={},
        recent_actions=[],
        open_issues=[],
    )

    # Act
    prompt = insights_service._build_insights_prompt(data)

    # Assert
    assert "Vision: V" in prompt
    assert "Purpose: P" in prompt
    assert "Core Values: V1, V2" in prompt
    assert "G1 (Status: active, Progress: 10%)" in prompt


@pytest.mark.asyncio
async def test_apply_filters(insights_service, mock_llm_service):
    # Arrange
    mock_llm_response = {
        "insights": [
            {
                "title": "Insight 1",
                "description": "Description 1 must be long enough to pass validation rules.",
                "category": "strategy",
                "priority": "high",
                "suggested_actions": [],
            },
            {
                "title": "Insight 2",
                "description": "Description 2 must be long enough to pass validation rules.",
                "category": "operations",
                "priority": "medium",
                "suggested_actions": [],
            },
        ]
    }
    mock_llm_service.generate_single_shot_analysis.return_value = {
        "response": json.dumps(mock_llm_response)
    }

    # Act - Filter by category
    result_cat = await insights_service.generate_insights(category="strategy")
    assert len(result_cat.data) == 1
    assert result_cat.data[0].category == "strategy"

    # Act - Filter by priority
    result_pri = await insights_service.generate_insights(priority="medium")
    assert len(result_pri.data) == 1
    assert result_pri.data[0].priority == "medium"


@pytest.mark.asyncio
async def test_pagination(insights_service, mock_llm_service):
    # Arrange
    insights = []
    for i in range(5):
        insights.append(
            {
                "title": f"Insight {i}",
                "description": f"Description for insight {i} must be long enough to pass validation rules.",
                "category": "strategy",
                "priority": "high",
                "suggested_actions": [],
            }
        )

    mock_llm_response = {"insights": insights}
    mock_llm_service.generate_single_shot_analysis.return_value = {
        "response": json.dumps(mock_llm_response)
    }

    # Act
    result = await insights_service.generate_insights(page=1, page_size=2)

    # Assert
    assert len(result.data) == 2
    assert result.pagination.total == 5
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 1
    assert result.pagination.limit == 2

    # Act - Page 2
    result2 = await insights_service.generate_insights(page=2, page_size=2)
    assert len(result2.data) == 2
    assert result2.pagination.page == 2

    # Act - Page 3
    result3 = await insights_service.generate_insights(page=3, page_size=2)
    assert len(result3.data) == 1
    assert result3.pagination.page == 3
