"""Integration tests for analysis API routes (Phase 7).

Tests the analysis routes including alignment, strategy, KPI, and
operational analysis endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from coaching.src.api.main_v2 import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAlignmentAnalysis:
    """Test alignment analysis endpoint."""

    @patch("coaching.src.api.routes.analysis.get_alignment_service")
    def test_alignment_analysis_success(self, mock_service_dep, client):
        """Test successful alignment analysis."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.analyze = AsyncMock(
            return_value={
                "alignment_score": 85.0,
                "purpose_alignment": 90.0,
                "values_alignment": 82.0,
                "goal_clarity": 88.0,
                "overall_assessment": "Strong alignment detected",
                "strengths": ["Clear value alignment", "Well-defined purpose"],
                "misalignments": [],
                "recommendations": [
                    {
                        "action": "Add specific metrics to goals",
                        "priority": "medium",
                        "rationale": "Metrics improve accountability",
                    }
                ],
            }
        )
        mock_service_dep.return_value = mock_service

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
        assert response.status_code == 201
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

    @patch("coaching.src.api.routes.analysis.get_strategy_service")
    def test_strategy_analysis_success(self, mock_service_dep, client):
        """Test successful strategy analysis."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.analyze = AsyncMock(
            return_value={
                "effectiveness_score": 75.0,
                "overall_assessment": "Strategy shows promise with room for improvement",
                "strengths": ["Clear market positioning", "Strong value proposition"],
                "weaknesses": ["Limited differentiation", "Unclear execution plan"],
                "opportunities": ["Growing market segment", "Partnership potential"],
                "recommendations": [
                    {
                        "category": "Market Expansion",
                        "recommendation": "Explore adjacent markets",
                        "priority": "high",
                        "rationale": "Low-hanging fruit for growth",
                        "estimated_impact": "20-30% revenue increase",
                    }
                ],
            }
        )
        mock_service_dep.return_value = mock_service

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
        assert response.status_code == 201
        data = response.json()
        assert data["analysis_type"] == "strategy"
        assert "effectiveness_score" in data
        assert data["effectiveness_score"] == 75.0
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestKPIAnalysis:
    """Test KPI analysis endpoint."""

    @patch("coaching.src.api.routes.analysis.get_kpi_service")
    def test_kpi_analysis_success(self, mock_service_dep, client):
        """Test successful KPI analysis."""
        # Setup mock
        mock_service = AsyncMock()
        mock_service.analyze = AsyncMock(
            return_value={
                "kpi_effectiveness_score": 70.0,
                "overall_assessment": "Current KPIs cover key areas but miss important metrics",
                "current_kpi_analysis": [
                    {
                        "kpi": "Monthly Recurring Revenue",
                        "assessment": "Good financial metric",
                        "relevance": "high",
                    }
                ],
                "missing_kpis": ["Customer Churn Rate", "Net Promoter Score"],
                "recommended_kpis": [
                    {
                        "kpi_name": "Customer Churn Rate",
                        "description": "Percentage of customers who cancel",
                        "rationale": "Critical for SaaS business health",
                        "target_range": "< 5% monthly",
                        "measurement_frequency": "monthly",
                    }
                ],
            }
        )
        mock_service_dep.return_value = mock_service

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
        assert response.status_code == 201
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

    def test_swot_analysis_success(self, client):
        """Test successful SWOT analysis."""
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
        assert response.status_code == 201
        data = response.json()
        assert data["analysis_type"] == "operations"
        assert data["specific_analysis_type"] == "swot"
        assert "findings" in data
        assert "strengths" in data["findings"]
        assert "weaknesses" in data["findings"]
        assert "opportunities" in data["findings"]
        assert "threats" in data["findings"]

    def test_root_cause_analysis_success(self, client):
        """Test successful root cause analysis."""
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
        assert response.status_code == 201
        data = response.json()
        assert data["specific_analysis_type"] == "root_cause"
        assert "findings" in data

    def test_action_plan_analysis_success(self, client):
        """Test successful action plan generation."""
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
        assert response.status_code == 201
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

    @patch("coaching.src.api.routes.analysis.get_alignment_service")
    def test_analysis_service_error(self, mock_service_dep, client):
        """Test handling of service errors."""
        # Setup mock to raise exception
        mock_service = AsyncMock()
        mock_service.analyze = AsyncMock(side_effect=Exception("Service error"))
        mock_service_dep.return_value = mock_service

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
        assert "error" in data
