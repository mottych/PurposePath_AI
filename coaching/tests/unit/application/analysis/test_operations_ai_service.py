"""Unit tests for OperationsAIService (Issue #63).

Tests all three service methods with mocked LLM service:
- analyze_strategic_alignment
- suggest_prioritization
- optimize_scheduling
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.application.analysis.operations_ai_service import OperationsAIService


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_analysis = AsyncMock()
    # Mock the response object structure
    mock_response = MagicMock()
    mock_response.content = ""
    mock_response.usage = {"total_tokens": 100}
    service.generate_analysis.return_value = mock_response
    return service


@pytest.fixture
def operations_service(mock_llm_service):
    """Create OperationsAIService with mocked LLM service."""
    return OperationsAIService(llm_service=mock_llm_service)


@pytest.fixture
def sample_actions():
    """Sample actions for testing."""
    return [
        {
            "id": "act_1",
            "title": "Launch marketing campaign",
            "description": "Launch Q4 marketing campaign for new product",
            "priority": "high",
            "status": "in_progress",
        },
        {
            "id": "act_2",
            "title": "Improve customer support",
            "description": "Implement 24/7 customer support system",
            "priority": "medium",
            "status": "planned",
        },
    ]


@pytest.fixture
def sample_goals():
    """Sample goals for testing."""
    return [
        {
            "id": "goal_1",
            "intent": "Increase revenue by 30% in Q4",
            "strategies": ["Expand market reach", "Launch new products"],
        },
        {
            "id": "goal_2",
            "intent": "Improve customer satisfaction to 90%",
            "strategies": ["Enhance support quality", "Reduce response time"],
        },
    ]


@pytest.fixture
def sample_business_foundation():
    """Sample business foundation."""
    return {
        "vision": "To be the market leader in customer experience",
        "purpose": "Empower businesses with exceptional tools",
        "coreValues": ["Customer First", "Innovation", "Excellence"],
    }


@pytest.fixture
def sample_business_context():
    """Sample business context for prioritization."""
    return {
        "currentGoals": ["Increase revenue", "Improve retention"],
        "constraints": ["Limited budget", "Small team"],
        "urgentDeadlines": ["Product launch: Nov 15"],
    }


@pytest.fixture
def sample_scheduling_constraints():
    """Sample scheduling constraints."""
    return {
        "teamCapacity": 160,
        "criticalDeadlines": [
            {"date": "2025-11-15", "description": "Product launch"}
        ],
        "teamAvailability": [
            {"personId": "dev_1", "hoursPerWeek": 40, "unavailableDates": []},
        ],
    }


# ============================================================================
# Strategic Alignment Tests
# ============================================================================


class TestAnalyzeStrategicAlignment:
    """Test suite for analyze_strategic_alignment method."""

    @pytest.mark.asyncio
    async def test_successful_alignment_analysis(
        self,
        operations_service,
        mock_llm_service,
        sample_actions,
        sample_goals,
        sample_business_foundation,
    ):
        """Test successful strategic alignment analysis."""
        # Arrange
        llm_response = """{
            "alignmentAnalysis": [
                {
                    "actionId": "act_1",
                    "alignmentScore": 85,
                    "strategicConnections": [
                        {
                            "goalId": "goal_1",
                            "goalTitle": "Increase revenue by 30%",
                            "alignmentScore": 90,
                            "impact": "high"
                        }
                    ],
                    "recommendations": [
                        "Link to specific revenue KPIs",
                        "Add measurable success criteria"
                    ]
                }
            ],
            "overallAlignment": 82,
            "insights": [
                "Strong alignment with revenue goals",
                "Consider prioritizing high-impact actions"
            ]
        }"""
        mock_llm_service.generate_analysis.return_value.content = llm_response

        # Act
        result = await operations_service.analyze_strategic_alignment(
            actions=sample_actions,
            goals=sample_goals,
            business_foundation=sample_business_foundation,
        )

        # Assert
        assert isinstance(result, dict)
        assert "alignmentAnalysis" in result
        assert "overallAlignment" in result
        assert result["overallAlignment"] == 82
        assert len(result["alignmentAnalysis"]) >= 1
        assert result["alignmentAnalysis"][0]["actionId"] == "act_1"
        assert result["alignmentAnalysis"][0]["alignmentScore"] == 85
        mock_llm_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_alignment_with_no_actions_raises_error(
        self,
        operations_service,
        sample_goals,
        sample_business_foundation,
    ):
        """Test that empty actions list raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.analyze_strategic_alignment(
                actions=[],
                goals=sample_goals,
                business_foundation=sample_business_foundation,
            )
        assert "At least one action is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_alignment_with_no_goals_raises_error(
        self,
        operations_service,
        sample_actions,
        sample_business_foundation,
    ):
        """Test that empty goals list raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.analyze_strategic_alignment(
                actions=sample_actions,
                goals=[],
                business_foundation=sample_business_foundation,
            )
        assert "At least one goal is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_alignment_with_missing_foundation_raises_error(
        self,
        operations_service,
        sample_actions,
        sample_goals,
    ):
        """Test that missing vision/purpose raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.analyze_strategic_alignment(
                actions=sample_actions,
                goals=sample_goals,
                business_foundation={},
            )
        assert "vision and purpose" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_alignment_uses_correct_temperature(
        self,
        operations_service,
        mock_llm_service,
        sample_actions,
        sample_goals,
        sample_business_foundation,
    ):
        """Test that alignment analysis uses temperature 0.6."""
        # Arrange
        mock_llm_service.generate_analysis.return_value.content = '{"alignmentAnalysis": [], "overallAlignment": 50}'

        # Act
        await operations_service.analyze_strategic_alignment(
            actions=sample_actions,
            goals=sample_goals,
            business_foundation=sample_business_foundation,
        )

        # Assert
        call_args = mock_llm_service.generate_analysis.call_args
        assert call_args[1]["temperature"] == 0.6

    @pytest.mark.asyncio
    async def test_alignment_handles_malformed_json(
        self,
        operations_service,
        mock_llm_service,
        sample_actions,
        sample_goals,
        sample_business_foundation,
    ):
        """Test fallback when LLM returns malformed JSON."""
        # Arrange
        mock_llm_service.generate_analysis.return_value.content = "Not valid JSON"

        # Act
        result = await operations_service.analyze_strategic_alignment(
            actions=sample_actions,
            goals=sample_goals,
            business_foundation=sample_business_foundation,
        )

        # Assert - Should return fallback structure
        assert isinstance(result, dict)
        assert "alignmentAnalysis" in result
        assert "overallAlignment" in result
        assert result["overallAlignment"] == 50
        assert len(result["alignmentAnalysis"]) == len(sample_actions)


# ============================================================================
# Prioritization Tests
# ============================================================================


class TestSuggestPrioritization:
    """Test suite for suggest_prioritization method."""

    @pytest.mark.asyncio
    async def test_successful_prioritization_suggestions(
        self,
        operations_service,
        mock_llm_service,
        sample_business_context,
    ):
        """Test successful prioritization suggestions."""
        # Arrange
        actions = [
            {
                "id": "act_1",
                "title": "Critical bug fix",
                "currentPriority": "medium",
                "dueDate": "2025-11-10",
                "impact": "high",
                "effort": "low",
                "status": "planned",
                "linkedGoals": ["goal_1"],
            }
        ]
        llm_response = """[
            {
                "actionId": "act_1",
                "suggestedPriority": "critical",
                "currentPriority": "medium",
                "reasoning": "High impact bug affecting revenue goals",
                "confidence": 0.92,
                "urgencyFactors": ["Upcoming product launch", "Customer complaints"],
                "impactFactors": ["Revenue impact", "Customer satisfaction"],
                "recommendedAction": "escalate",
                "estimatedBusinessValue": 50000
            }
        ]"""
        mock_llm_service.generate_analysis.return_value.content = llm_response

        # Act
        result = await operations_service.suggest_prioritization(
            actions=actions,
            business_context=sample_business_context,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["actionId"] == "act_1"
        assert result[0]["suggestedPriority"] == "critical"
        assert result[0]["confidence"] == 0.92
        assert result[0]["recommendedAction"] == "escalate"
        mock_llm_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_prioritization_with_no_actions_raises_error(
        self,
        operations_service,
        sample_business_context,
    ):
        """Test that empty actions list raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.suggest_prioritization(
                actions=[],
                business_context=sample_business_context,
            )
        assert "At least one action is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_prioritization_uses_correct_temperature(
        self,
        operations_service,
        mock_llm_service,
        sample_business_context,
    ):
        """Test that prioritization uses temperature 0.5."""
        # Arrange
        actions = [{"id": "act_1", "title": "Test", "currentPriority": "medium", "status": "planned", "linkedGoals": []}]
        mock_llm_service.generate_analysis.return_value.content = '[]'

        # Act
        await operations_service.suggest_prioritization(
            actions=actions,
            business_context=sample_business_context,
        )

        # Assert
        call_args = mock_llm_service.generate_analysis.call_args
        assert call_args[1]["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_prioritization_handles_malformed_json(
        self,
        operations_service,
        mock_llm_service,
        sample_business_context,
    ):
        """Test fallback when LLM returns malformed JSON."""
        # Arrange
        actions = [{"id": "act_1", "title": "Test", "currentPriority": "medium", "status": "planned", "linkedGoals": []}]
        mock_llm_service.generate_analysis.return_value.content = "Invalid JSON"

        # Act
        result = await operations_service.suggest_prioritization(
            actions=actions,
            business_context=sample_business_context,
        )

        # Assert - Should return fallback suggestions
        assert isinstance(result, list)
        assert len(result) == len(actions)
        assert result[0]["actionId"] == "act_1"
        assert result[0]["confidence"] == 0.5
        assert result[0]["recommendedAction"] == "maintain"


# ============================================================================
# Scheduling Tests
# ============================================================================


class TestOptimizeScheduling:
    """Test suite for optimize_scheduling method."""

    @pytest.mark.asyncio
    async def test_successful_scheduling_optimization(
        self,
        operations_service,
        mock_llm_service,
        sample_scheduling_constraints,
    ):
        """Test successful scheduling optimization."""
        # Arrange
        actions = [
            {
                "id": "act_1",
                "title": "Develop feature",
                "estimatedDuration": 40,
                "dependencies": [],
                "assignedTo": "dev_1",
                "currentStartDate": None,
                "currentDueDate": None,
                "priority": "high",
            }
        ]
        llm_response = """[
            {
                "actionId": "act_1",
                "suggestedStartDate": "2025-11-01",
                "suggestedDueDate": "2025-11-05",
                "reasoning": "Optimal schedule considering team capacity",
                "confidence": 0.88,
                "dependencies": [],
                "resourceConsiderations": ["dev_1 has 40h available"],
                "risks": ["Tight deadline before product launch"],
                "alternativeSchedules": [
                    {
                        "startDate": "2025-11-08",
                        "dueDate": "2025-11-12",
                        "rationale": "More buffer time before launch"
                    }
                ]
            }
        ]"""
        mock_llm_service.generate_analysis.return_value.content = llm_response

        # Act
        result = await operations_service.optimize_scheduling(
            actions=actions,
            constraints=sample_scheduling_constraints,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["actionId"] == "act_1"
        assert result[0]["suggestedStartDate"] == "2025-11-01"
        assert result[0]["confidence"] == 0.88
        assert len(result[0]["alternativeSchedules"]) >= 1
        mock_llm_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_scheduling_with_no_actions_raises_error(
        self,
        operations_service,
        sample_scheduling_constraints,
    ):
        """Test that empty actions list raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.optimize_scheduling(
                actions=[],
                constraints=sample_scheduling_constraints,
            )
        assert "At least one action is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scheduling_with_no_capacity_raises_error(
        self,
        operations_service,
    ):
        """Test that missing team capacity raises ValueError."""
        # Arrange
        actions = [{"id": "act_1", "title": "Test", "estimatedDuration": 40, "priority": "high"}]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.optimize_scheduling(
                actions=actions,
                constraints={},
            )
        assert "Team capacity is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_scheduling_uses_correct_temperature(
        self,
        operations_service,
        mock_llm_service,
        sample_scheduling_constraints,
    ):
        """Test that scheduling uses temperature 0.4."""
        # Arrange
        actions = [{"id": "act_1", "title": "Test", "estimatedDuration": 40, "priority": "high"}]
        mock_llm_service.generate_analysis.return_value.content = '[]'

        # Act
        await operations_service.optimize_scheduling(
            actions=actions,
            constraints=sample_scheduling_constraints,
        )

        # Assert
        call_args = mock_llm_service.generate_analysis.call_args
        assert call_args[1]["temperature"] == 0.4

    @pytest.mark.asyncio
    async def test_scheduling_handles_malformed_json(
        self,
        operations_service,
        mock_llm_service,
        sample_scheduling_constraints,
    ):
        """Test fallback when LLM returns malformed JSON."""
        # Arrange
        actions = [{"id": "act_1", "title": "Test", "estimatedDuration": 40, "priority": "high"}]
        mock_llm_service.generate_analysis.return_value.content = "Not JSON"

        # Act
        result = await operations_service.optimize_scheduling(
            actions=actions,
            constraints=sample_scheduling_constraints,
        )

        # Assert - Should return fallback schedules
        assert isinstance(result, list)
        assert len(result) == len(actions)
        assert result[0]["actionId"] == "act_1"
        assert "suggestedStartDate" in result[0]
        assert result[0]["confidence"] == 0.5


# ============================================================================
# Root Cause Suggestions Tests (Issue #64)
# ============================================================================


class TestSuggestRootCauseMethods:
    """Test suite for suggest_root_cause_methods method."""

    @pytest.mark.asyncio
    async def test_successful_root_cause_suggestions(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test successful root cause method suggestions."""
        # Arrange
        issue = {
            "issueTitle": "Customer retention declining",
            "issueDescription": "We've seen a 20% drop in customer retention over the last quarter",
            "businessImpact": "high",
        }
        context = {
            "reportedBy": "Sales team",
            "dateReported": "2025-10-20",
            "affectedAreas": ["Customer Success", "Sales"],
            "relatedActions": ["act_123"],
        }
        
        llm_response = """[
            {
                "method": "five_whys",
                "confidence": 0.92,
                "suggestions": {
                    "fiveWhys": {
                        "suggestedQuestions": [
                            "Why is customer retention declining?",
                            "Why are customers choosing competitors?"
                        ],
                        "potentialRootCauses": [
                            "Product quality issues",
                            "Poor customer support"
                        ]
                    }
                },
                "reasoning": "Five Whys is ideal for operational issues"
            },
            {
                "method": "swot",
                "confidence": 0.85,
                "suggestions": {
                    "swot": {
                        "strengths": ["Strong brand"],
                        "weaknesses": ["Limited support staff"],
                        "opportunities": ["Automation"],
                        "threats": ["Competitors"]
                    }
                },
                "reasoning": "SWOT helps identify strategic factors"
            }
        ]"""
        mock_llm_service.generate_analysis.return_value.content = llm_response

        # Act
        result = await operations_service.suggest_root_cause_methods(
            issue=issue,
            context=context,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["method"] == "five_whys"
        assert result[0]["confidence"] == 0.92
        assert "fiveWhys" in result[0]["suggestions"]
        assert len(result[0]["suggestions"]["fiveWhys"]["suggestedQuestions"]) >= 2
        mock_llm_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_root_cause_with_missing_title_raises_error(
        self,
        operations_service,
    ):
        """Test that missing issue title raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.suggest_root_cause_methods(
                issue={"issueDescription": "Test"},
                context={},
            )
        assert "title and description" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_root_cause_uses_correct_temperature(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test that root cause analysis uses temperature 0.6."""
        # Arrange
        issue = {
            "issueTitle": "Test issue",
            "issueDescription": "Test description",
            "businessImpact": "medium",
        }
        mock_llm_service.generate_analysis.return_value.content = '[]'

        # Act
        await operations_service.suggest_root_cause_methods(
            issue=issue,
            context={},
        )

        # Assert
        call_args = mock_llm_service.generate_analysis.call_args
        assert call_args[1]["temperature"] == 0.6

    @pytest.mark.asyncio
    async def test_root_cause_handles_malformed_json(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test fallback when LLM returns malformed JSON."""
        # Arrange
        issue = {
            "issueTitle": "Test issue",
            "issueDescription": "Test description",
            "businessImpact": "medium",
        }
        mock_llm_service.generate_analysis.return_value.content = "Not JSON"

        # Act
        result = await operations_service.suggest_root_cause_methods(
            issue=issue,
            context={},
        )

        # Assert - Should return fallback suggestions
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["method"] == "five_whys"
        assert result[0]["confidence"] == 0.7
        assert "fiveWhys" in result[0]["suggestions"]


# ============================================================================
# Action Plan Generation Tests (Issue #64)
# ============================================================================


class TestGenerateActionPlan:
    """Test suite for generate_action_plan method."""

    @pytest.mark.asyncio
    async def test_successful_action_plan_generation(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test successful action plan generation."""
        # Arrange
        issue = {
            "title": "System performance degradation",
            "description": "API response times have increased by 300%",
            "impact": "critical",
            "rootCause": "Database query optimization needed",
        }
        constraints = {
            "timeline": "2 weeks",
            "budget": 10000,
            "availableResources": ["2 backend developers", "1 DBA"],
        }
        context = {
            "relatedGoals": ["Improve system reliability"],
            "currentActions": ["Monitoring implementation"],
            "businessPriorities": ["Customer experience", "System stability"],
        }
        
        llm_response = """[
            {
                "title": "Optimize database queries",
                "description": "Review and optimize slow queries identified in logs",
                "priority": "critical",
                "estimatedDuration": 40,
                "estimatedCost": 5000,
                "assignmentSuggestion": "Senior Backend Developer + DBA",
                "dependencies": [],
                "confidence": 0.95,
                "reasoning": "Directly addresses identified root cause",
                "expectedOutcome": "50% reduction in response times",
                "risks": ["May require schema changes"]
            },
            {
                "title": "Implement query caching",
                "description": "Add Redis caching layer for frequent queries",
                "priority": "high",
                "estimatedDuration": 24,
                "estimatedCost": 3000,
                "assignmentSuggestion": "Backend Developer",
                "dependencies": ["Optimize database queries"],
                "confidence": 0.88,
                "reasoning": "Prevents similar issues in future",
                "expectedOutcome": "Further 30% performance improvement",
                "risks": ["Cache invalidation complexity"]
            }
        ]"""
        mock_llm_service.generate_analysis.return_value.content = llm_response

        # Act
        result = await operations_service.generate_action_plan(
            issue=issue,
            constraints=constraints,
            context=context,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Optimize database queries"
        assert result[0]["priority"] == "critical"
        assert result[0]["estimatedDuration"] == 40
        assert result[0]["confidence"] == 0.95
        assert len(result[0]["risks"]) > 0
        mock_llm_service.generate_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_plan_with_missing_title_raises_error(
        self,
        operations_service,
    ):
        """Test that missing issue title raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await operations_service.generate_action_plan(
                issue={"description": "Test"},
                constraints={},
                context={},
            )
        assert "title and description" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_action_plan_uses_correct_temperature(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test that action plan generation uses temperature 0.5."""
        # Arrange
        issue = {
            "title": "Test issue",
            "description": "Test description",
            "impact": "medium",
        }
        mock_llm_service.generate_analysis.return_value.content = '[]'

        # Act
        await operations_service.generate_action_plan(
            issue=issue,
            constraints={},
            context={},
        )

        # Assert
        call_args = mock_llm_service.generate_analysis.call_args
        assert call_args[1]["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_action_plan_handles_malformed_json(
        self,
        operations_service,
        mock_llm_service,
    ):
        """Test fallback when LLM returns malformed JSON."""
        # Arrange
        issue = {
            "title": "Test issue",
            "description": "Test description",
            "impact": "medium",
        }
        mock_llm_service.generate_analysis.return_value.content = "Not JSON"

        # Act
        result = await operations_service.generate_action_plan(
            issue=issue,
            constraints={},
            context={},
        )

        # Assert - Should return fallback actions
        assert isinstance(result, list)
        assert len(result) >= 2
        assert result[0]["title"] == "Investigate root cause"
        assert result[0]["priority"] == "high"
        assert result[0]["confidence"] == 0.8
        assert len(result[0]["risks"]) > 0
