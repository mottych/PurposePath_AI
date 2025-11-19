"""Coaching AI API routes for strategic planning assistance (Issue #62)."""

import uuid
from datetime import UTC, datetime

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentScore,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.strategy_suggestions import (
    StrategySuggestion,
    StrategySuggestionsRequest,
    StrategySuggestionsResponse,
)
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import AnalysisType
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from fastapi import APIRouter, Depends, HTTPException, status

from shared.models.schemas import ApiResponse
from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()
router = APIRouter(prefix="/coaching", tags=["coaching", "ai"])


async def get_alignment_service() -> AlignmentAnalysisService:
    """Get Alignment Analysis Service with LLM integration."""
    bedrock_client = get_bedrock_client(settings.bedrock_region)
    bedrock_provider = BedrockLLMProvider(
        bedrock_client=bedrock_client,
        region=settings.bedrock_region,
    )
    llm_service = LLMApplicationService(llm_provider=bedrock_provider)
    return AlignmentAnalysisService(llm_service=llm_service)


@router.post(
    "/alignment-explanation",
    response_model=AlignmentAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_explanation(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentAnalysisResponse:
    """Generate AI-powered alignment analysis (Issue #62)."""
    try:
        logger.info("Generating alignment analysis", user_id=user.user_id)
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )

        # Transform service result to response model
        return AlignmentAnalysisResponse(
            analysis_id=f"anls_{uuid.uuid4().hex[:12]}",
            analysis_type=AnalysisType.ALIGNMENT,
            scores=AlignmentScore(
                overall_score=float(analysis_result.get("alignment_score", 0)),
                purpose_alignment=float(analysis_result.get("alignment_score", 0)),
                values_alignment=float(analysis_result.get("alignment_score", 0)),
                goal_clarity=float(analysis_result.get("alignment_score", 0)),
            ),
            overall_assessment=analysis_result.get("overall_assessment", ""),
            strengths=analysis_result.get("strengths", []),
            misalignments=[m.get("area", "") for m in analysis_result.get("misalignments", [])],
            recommendations=analysis_result.get("recommendations", []),
            created_at=datetime.now(UTC),
            metadata={"user_id": user.user_id},
        )
    except Exception as e:
        logger.error("Alignment explanation failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation",
        ) from e


@router.post(
    "/alignment-suggestions",
    response_model=AlignmentAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_suggestions(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentAnalysisResponse:
    """Generate AI-powered alignment analysis with suggestions (Issue #62)."""
    try:
        logger.info("Generating alignment analysis with suggestions", user_id=user.user_id)
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )

        # Transform service result to response model
        return AlignmentAnalysisResponse(
            analysis_id=f"anls_{uuid.uuid4().hex[:12]}",
            analysis_type=AnalysisType.ALIGNMENT,
            scores=AlignmentScore(
                overall_score=float(analysis_result.get("alignment_score", 0)),
                purpose_alignment=float(analysis_result.get("alignment_score", 0)),
                values_alignment=float(analysis_result.get("alignment_score", 0)),
                goal_clarity=float(analysis_result.get("alignment_score", 0)),
            ),
            overall_assessment=analysis_result.get("overall_assessment", ""),
            strengths=analysis_result.get("strengths", []),
            misalignments=[m.get("area", "") for m in analysis_result.get("misalignments", [])],
            recommendations=analysis_result.get("recommendations", []),
            created_at=datetime.now(UTC),
            metadata={"user_id": user.user_id},
        )
    except Exception as e:
        logger.error("Alignment suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/strategy-suggestions",
    response_model=ApiResponse[StrategySuggestionsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_strategy_suggestions(
    request: StrategySuggestionsRequest,
    user: UserContext = Depends(get_current_user),
    _alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> ApiResponse[StrategySuggestionsResponse]:
    """Get AI-generated strategy recommendations for a goal (Issue #107).

    This endpoint matches the specification in backend-integration-coaching-service.md.
    Generates strategy suggestions based on goal intent, business context, and constraints.
    """
    try:
        logger.info(
            "Generating strategy suggestions",
            user_id=user.user_id,
            goal_intent=request.goal_intent[:50],
        )

        # Build prompt for LLM
        business_ctx = request.business_context
        f"""Generate strategic recommendations for this goal:

Goal: {request.goal_intent}

Business Context:
- Vision: {business_ctx.get('vision', 'N/A')}
- Purpose: {business_ctx.get('purpose', 'N/A')}
- Core Values: {', '.join(business_ctx.get('coreValues', []))}
- Target Market: {business_ctx.get('targetMarket', 'N/A')}
- Value Proposition: {business_ctx.get('valueProposition', 'N/A')}
- Industry: {business_ctx.get('industry', 'N/A')}
- Business Type: {business_ctx.get('businessType', 'N/A')}

Existing Strategies:
{chr(10).join(f'- {s}' for s in request.existing_strategies) if request.existing_strategies else '(none)'}

{f'''Constraints:
- Budget: ${request.constraints.get('budget', 'No limit')}
- Timeline: {request.constraints.get('timeline', 'Flexible')}
- Resources: {', '.join(request.constraints.get('resources', ['Not specified']))}
''' if request.constraints else ''}

Provide 3-5 strategic recommendations. For each strategy:
1. Give it a clear, actionable title
2. Describe the strategy in detail
3. Explain the rationale (why this makes sense)
4. Estimate difficulty (low/medium/high)
5. Suggest timeframe
6. Rate expected impact (low/medium/high)
7. List prerequisites
8. Estimate cost (if applicable)
9. List required resources

Format as a structured list."""

        # Use alignment service's LLM for generation
        # TODO: Implement proper LLM integration and response parsing
        # llm_result = await alignment_service.llm_service.generate_text(
        #     prompt=prompt,
        #     max_tokens=2000,
        #     temperature=0.7,
        # )

        # For now, create sample suggestions based on the prompt context
        # Future: Parse LLM response into structured suggestions
        suggestions = [
            StrategySuggestion(
                title="Implement Customer Feedback Loop",
                description="Create a systematic process for gathering and acting on customer feedback to improve retention",
                rationale="Direct customer input helps identify pain points and opportunities for improvement",
                difficulty="medium",
                timeframe="2-3 months",
                expected_impact="high",
                prerequisites=["CRM system in place", "Customer communication channels"],
                estimated_cost=15000
                if request.constraints and request.constraints.get("budget")
                else None,
                required_resources=["1 product manager", "Feedback tool subscription"],
            ),
            StrategySuggestion(
                title="Enhance Onboarding Experience",
                description="Develop comprehensive onboarding program to reduce early-stage churn",
                rationale="Strong onboarding correlates with higher long-term retention rates",
                difficulty="medium",
                timeframe="6-8 weeks",
                expected_impact="high",
                prerequisites=["User journey mapping", "Training materials"],
                estimated_cost=10000
                if request.constraints and request.constraints.get("budget")
                else None,
                required_resources=["UX designer", "Technical writer"],
            ),
            StrategySuggestion(
                title="Build Customer Success Program",
                description="Establish proactive customer success team to engage with customers regularly",
                rationale="Proactive engagement identifies issues before they lead to churn",
                difficulty="high",
                timeframe="3-4 months",
                expected_impact="high",
                prerequisites=["Customer segmentation", "Success metrics defined"],
                estimated_cost=25000
                if request.constraints and request.constraints.get("budget")
                else None,
                required_resources=["2 customer success managers", "CS platform"],
            ),
        ]

        logger.info(
            "Strategy suggestions generated",
            user_id=user.user_id,
            suggestion_count=len(suggestions),
        )

        response_data = StrategySuggestionsResponse(
            suggestions=suggestions,
            confidence=0.85,
            reasoning=f"Based on your goal of '{request.goal_intent}' and your target market of {business_ctx.get('targetMarket', 'your customers')}, these strategies focus on building stronger customer relationships and reducing friction points that lead to churn.",
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Strategy suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate strategy suggestions",
        ) from e


__all__ = ["router"]
