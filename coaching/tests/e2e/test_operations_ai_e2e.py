"""End-to-end tests for Operations AI endpoints with real LLM providers.

Tests one-shot AI analysis endpoints:
- Strategic alignment analysis
- Prioritization suggestions
- Scheduling suggestions
- Root cause analysis
- Action plan generation
"""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_strategic_alignment_analysis_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test strategic alignment analysis with real Bedrock LLM.

    Validates:
    - Real LLM generates quality analysis
    - Response structure is correct
    - Analysis contains actionable insights
    """
    payload = {
        "core_values": ["Innovation", "Customer Trust", "Excellence"],
        "purpose": "To empower businesses through innovative technology solutions",
        "current_state": "Focusing on product development but lacking market strategy",
        "desired_state": "Market leader in enterprise SaaS solutions",
    }

    response = await e2e_client.post("/api/operations-ai/strategic-alignment", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    # Validate response structure
    assert "alignment_score" in data
    assert 0.0 <= data["alignment_score"] <= 1.0

    assert "strengths" in data
    assert len(data["strengths"]) > 0
    assert all(len(s) > 10 for s in data["strengths"])  # Real content, not placeholders

    assert "gaps" in data
    assert len(data["gaps"]) > 0

    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert all(len(r) > 20 for r in data["recommendations"])  # Detailed recommendations


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_prioritization_suggestions_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test prioritization suggestions with real LLM.

    Validates:
    - Multiple initiatives analyzed
    - Priority scoring makes sense
    - Reasoning is provided
    """
    payload = {
        "initiatives": [
            {
                "name": "Launch mobile app",
                "description": "Develop iOS and Android apps",
                "estimated_effort": "6 months",
                "potential_impact": "High - Reach 50% more customers",
            },
            {
                "name": "Improve onboarding",
                "description": "Streamline user onboarding process",
                "estimated_effort": "2 months",
                "potential_impact": "Medium - Reduce churn by 15%",
            },
            {
                "name": "Enterprise features",
                "description": "Add SSO, RBAC, audit logs",
                "estimated_effort": "4 months",
                "potential_impact": "High - Enable enterprise sales",
            },
        ],
        "business_context": {
            "stage": "Growth",
            "resources": "Small team",
            "timeline": "Q1 2026",
        },
    }

    response = await e2e_client.post("/api/operations-ai/prioritization-suggestions", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "prioritized_initiatives" in data
    assert len(data["prioritized_initiatives"]) == 3

    # Validate each initiative has priority and reasoning
    for initiative in data["prioritized_initiatives"]:
        assert "priority" in initiative
        assert initiative["priority"] in ["high", "medium", "low"]
        assert "reasoning" in initiative
        assert len(initiative["reasoning"]) > 50  # Detailed reasoning


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_root_cause_analysis_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test root cause analysis with real LLM.

    Validates:
    - Problem analysis depth
    - Multiple root causes identified
    - Suggestions provided
    """
    payload = {
        "problem_statement": "Customer churn increased by 25% in Q3",
        "context": {
            "industry": "SaaS",
            "customer_segment": "SMB",
            "recent_changes": [
                "Raised pricing by 20%",
                "Launched competitor product",
                "Support response time increased",
            ],
        },
        "observed_symptoms": [
            "Exit surveys mention pricing concerns",
            "Support tickets increased 40%",
            "Feature adoption decreased",
        ],
    }

    response = await e2e_client.post("/api/operations-ai/root-cause-suggestions", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "root_causes" in data
    assert len(data["root_causes"]) >= 2  # Should identify multiple causes

    for cause in data["root_causes"]:
        assert "cause" in cause
        assert "evidence" in cause
        assert "likelihood" in cause
        assert cause["likelihood"] in ["high", "medium", "low"]

    assert "analysis_method" in data
    assert len(data["analysis_method"]) > 50


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_action_plan_generation_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test action plan generation with real LLM.

    Validates:
    - Comprehensive action steps
    - Timeline estimation
    - Resource allocation
    """
    payload = {
        "goal": "Launch new product feature by Q2 2026",
        "current_situation": "Feature is 30% complete, needs design review and testing",
        "constraints": [
            "Limited dev resources",
            "Must not affect existing features",
            "Budget: $50k",
        ],
        "timeline": "3 months",
    }

    response = await e2e_client.post("/api/operations-ai/action-suggestions", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "action_items" in data
    assert len(data["action_items"]) >= 3

    for action in data["action_items"]:
        assert "title" in action
        assert "description" in action
        assert "timeline" in action
        assert "owner" in action
        assert len(action["description"]) > 30  # Detailed description

    # Validate timeline is realistic
    assert "timeline_summary" in data
    assert "success_metrics" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_scheduling_suggestions_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test scheduling suggestions with real LLM.

    Validates:
    - Tasks scheduled appropriately
    - Dependencies considered
    - Timeline realistic
    """
    payload = {
        "tasks": [
            {
                "name": "Requirements gathering",
                "duration": "1 week",
                "dependencies": [],
            },
            {
                "name": "Design mockups",
                "duration": "2 weeks",
                "dependencies": ["Requirements gathering"],
            },
            {
                "name": "Development",
                "duration": "4 weeks",
                "dependencies": ["Design mockups"],
            },
            {
                "name": "Testing",
                "duration": "2 weeks",
                "dependencies": ["Development"],
            },
        ],
        "start_date": "2026-01-06",
        "constraints": {
            "team_size": 5,
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        },
    }

    response = await e2e_client.post("/api/operations-ai/scheduling-suggestions", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "schedule" in data
    assert len(data["schedule"]) == 4  # All tasks scheduled

    for task in data["schedule"]:
        assert "task_name" in task
        assert "start_date" in task
        assert "end_date" in task
        assert "parallel_tasks" in task

    assert "critical_path" in data
    assert "total_duration" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_operations_ai_error_handling(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test error handling for invalid inputs.

    Validates:
    - Proper validation
    - Clear error messages
    - No LLM calls for invalid input
    """
    # Invalid payload - missing required fields
    invalid_payload = {"core_values": []}  # Empty values

    response = await e2e_client.post("/api/operations-ai/strategic-alignment", json=invalid_payload)

    # Should return 400 or 422 for validation errors
    assert response.status_code in [400, 422]

    error_data = response.json()
    assert "detail" in error_data or "error" in error_data


__all__ = []  # Test module, no exports
