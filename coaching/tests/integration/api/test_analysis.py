"""Integration tests for analysis API routes (Phase 7).

Tests the analysis routes including alignment, strategy, KPI, and
operational analysis endpoints.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.main import app
from coaching.src.api.models.analysis import (
    AlignmentAnalysisResponse,
    KPIAnalysisResponse,
    OperationsAnalysisResponse,
    StrategyAnalysisResponse,
)
from coaching.src.core.constants import AnalysisType
from fastapi.testclient import TestClient


@pytest.fixture
def mock_generic_handler():
    """Create mock generic handler."""
    handler = AsyncMock()
    handler.handle_single_shot = AsyncMock()
    return handler


@pytest.fixture
def client(mock_generic_handler):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_generic_handler] = lambda: mock_generic_handler

    with TestClient(app) as c:
        yield c

    # Clean up overrides
    app.dependency_overrides = {}


class TestAlignmentAnalysis:
    """Test alignment analysis endpoint."""

    def test_alignment_analysis_success(self, client, mock_generic_handler):
        """Test successful alignment analysis."""
        # Setup mock response
        mock_response = AlignmentAnalysisResponse(
            analysis_id="test-analysis-id",
            analysis_type=AnalysisType.ALIGNMENT,
            scores={
                "overall_score": 85.0,
                "purpose_alignment": 90.0,
                "values_alignment": 82.0,
                "goal_clarity": 88.0,
            },
            overall_assessment="Strong alignment detected",
            strengths=["Clear value alignment", "Well-defined purpose"],
            misalignments=[],
            recommendations=[
                {
                    "action": "Add specific metrics to goals",
                    "priority": "medium",
                    "rationale": "Metrics improve accountability",
                }
            ],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/analysis/alignment",
            json={
                "text_to_analyze": "Our goals focus on increasing revenue while maintaining our commitment to customer service excellence.",
                "context": {
                    "purpose": "To provide exceptional customer experiences",
                    "core_values": ["Excellence", "Customer-first", "Integrity"],
                },
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["analysis_type"] == "alignment"
        assert "scores" in data
        assert data["scores"]["overall_score"] == 85.0
        assert "overall_assessment" in data
        assert "strengths" in data
        assert isinstance(data["strengths"], list)

    def test_alignment_analysis_no_auth(self, client):
        """Test alignment analysis without authentication."""
        response = client.post(
            "/api/v1/analysis/alignment",
            json={
                "text_to_analyze": "Test content",
            },
        )

        # Should fail with 401 or 422
        assert response.status_code in [401, 422]

    def test_alignment_analysis_invalid_text(self, client):
        """Test alignment analysis with invalid text."""
        response = client.post(
            "/api/v1/analysis/alignment",
            json={
                "text_to_analyze": "short",  # Too short
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should fail with validation error
        assert response.status_code == 422


class TestStrategyAnalysis:
    """Test strategy analysis endpoint."""

    def test_strategy_analysis_success(self, client, mock_generic_handler):
        """Test successful strategy analysis."""
        # Setup mock response
        mock_response = StrategyAnalysisResponse(
            analysis_id="test-strategy-id",
            analysis_type=AnalysisType.STRATEGY,
            effectiveness_score=75.0,
            overall_assessment="Strategy shows promise with room for improvement",
            strengths=["Clear market positioning", "Strong value proposition"],
            weaknesses=["Limited differentiation", "Unclear execution plan"],
            opportunities=["Growing market segment", "Partnership potential"],
            threats=[],
            recommendations=[
                {
                    "category": "Market Expansion",
                    "recommendation": "Explore adjacent markets",
                    "priority": "high",
                    "rationale": "Low-hanging fruit for growth",
                    "estimated_impact": "20-30% revenue increase",
                }
            ],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/analysis/strategy",
            json={
                "current_strategy": "We plan to grow through content marketing and strategic partnerships.",
                "context": {
                    "industry": "SaaS",
                    "market_size": "Mid-market",
                },
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "strategy"
        assert "effectiveness_score" in data
        assert data["effectiveness_score"] == 75.0
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestKPIAnalysis:
    """Test KPI analysis endpoint."""

    def test_kpi_analysis_success(self, client, mock_generic_handler):
        """Test successful KPI analysis."""
        # Setup mock response
        mock_response = KPIAnalysisResponse(
            analysis_id="test-kpi-id",
            analysis_type=AnalysisType.KPI,
            kpi_effectiveness_score=70.0,
            overall_assessment="Current KPIs cover key areas but miss important metrics",
            current_kpi_analysis=[
                {
                    "kpi": "Monthly Recurring Revenue",
                    "assessment": "Good financial metric",
                    "relevance": "high",
                }
            ],
            missing_kpis=["Customer Churn Rate", "Net Promoter Score"],
            recommended_kpis=[
                {
                    "kpi_name": "Customer Churn Rate",
                    "description": "Percentage of customers who cancel",
                    "rationale": "Critical for SaaS business health",
                    "target_range": "< 5% monthly",
                    "measurement_frequency": "monthly",
                }
            ],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        # Make request
        response = client.post(
            "/api/v1/analysis/kpi",
            json={
                "current_kpis": ["Monthly Recurring Revenue", "Active Users"],
                "context": {
                    "business_goals": ["Grow revenue", "Improve retention"],
                },
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "kpi"
        assert "kpi_effectiveness_score" in data
        assert "recommended_kpis" in data
        assert isinstance(data["recommended_kpis"], list)

    def test_kpi_analysis_empty_kpis(self, client):
        """Test KPI analysis with empty KPI list."""
        response = client.post(
            "/api/v1/analysis/kpi",
            json={
                "current_kpis": [],
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should fail with validation error
        assert response.status_code == 422


class TestOperationsAnalysis:
    """Test operations analysis endpoint."""

    def test_swot_analysis_success(self, client, mock_generic_handler):
        """Test successful SWOT analysis."""
        # Setup mock response
        mock_response = OperationsAnalysisResponse(
            analysis_id="test-swot-id",
            analysis_type=AnalysisType.SWOT,
            specific_analysis_type="swot",
            findings={
                "strengths": ["Agile team"],
                "weaknesses": ["Limited budget"],
                "opportunities": ["New market"],
                "threats": ["Competitors"],
            },
            recommendations=[],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        response = client.post(
            "/api/v1/analysis/operations",
            json={
                "analysis_type": "swot",
                "description": "Analyze our company's position in the market",
                "context": {},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "swot"
        assert data["specific_analysis_type"] == "swot"
        assert "findings" in data
        assert "strengths" in data["findings"]

    def test_root_cause_analysis_success(self, client, mock_generic_handler):
        """Test successful root cause analysis."""
        # Setup mock response
        mock_response = OperationsAnalysisResponse(
            analysis_id="test-root-cause-id",
            analysis_type=AnalysisType.ROOT_CAUSE,
            specific_analysis_type="root_cause",
            findings={
                "root_cause": "Lack of training",
                "contributing_factors": ["High turnover"],
            },
            recommendations=[],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        response = client.post(
            "/api/v1/analysis/operations",
            json={
                "analysis_type": "root_cause",
                "description": "Customer satisfaction scores have been declining for 3 months",
                "context": {},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["specific_analysis_type"] == "root_cause"
        assert "findings" in data

    def test_action_plan_analysis_success(self, client, mock_generic_handler):
        """Test successful action plan generation."""
        # Setup mock response
        mock_response = OperationsAnalysisResponse(
            analysis_id="test-action-plan-id",
            analysis_type=AnalysisType.ACTION_PLAN,
            specific_analysis_type="action_plan",
            findings={
                "steps": ["Step 1", "Step 2"],
            },
            recommendations=[],
            created_at=datetime.now(UTC),
        )
        mock_generic_handler.handle_single_shot.return_value = mock_response

        response = client.post(
            "/api/v1/analysis/operations",
            json={
                "analysis_type": "action_plan",
                "description": "Launch new product feature within 3 months",
                "context": {},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["specific_analysis_type"] == "action_plan"
        assert "findings" in data

    def test_operations_analysis_invalid_type(self, client):
        """Test operations analysis with invalid type."""
        response = client.post(
            "/api/v1/analysis/operations",
            json={
                "analysis_type": "invalid_type",
                "description": "Test description",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should fail with validation or business logic error
        assert response.status_code in [400, 422]


class TestAnalysisErrorHandling:
    """Test error handling in analysis endpoints."""

    def test_analysis_service_error(self, client, mock_generic_handler):
        """Test handling of service errors."""
        # Setup mock to raise exception
        mock_generic_handler.handle_single_shot.side_effect = Exception("Service error")

        # Make request
        response = client.post(
            "/api/v1/analysis/alignment",
            json={
                "text_to_analyze": "Test content for analysis that will fail",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 500
        assert response.status_code == 500
        data = response.json()
        # Check for either detail or message/error depending on middleware
        assert "detail" in data or "message" in data

