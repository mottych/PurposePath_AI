"""Strategy suggestion service for AI-powered strategic recommendations.

Generates actionable strategy recommendations based on goal intent, business context,
and resource constraints using LLM analysis.
"""

import json
from typing import Any

import structlog
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.core.constants import AnalysisType

logger = structlog.get_logger()


class StrategySuggestionService(BaseAnalysisService):
    """
    Service for generating strategy suggestions.

    Analyzes:
    - Goal intent and desired outcomes
    - Business context (vision, values, market)
    - Existing strategies
    - Resource constraints

    Output:
    - List of strategic recommendations
    - Each with title, description, rationale, difficulty, impact
    - Confidence score and reasoning
    """

    def get_analysis_type(self) -> AnalysisType:
        """Return STRATEGY analysis type."""
        return AnalysisType.STRATEGY

    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build strategy suggestion prompt.

        Required context:
        - goal_intent: The goal requiring strategies
        - business_context: Dict with vision, purpose, values, etc.
        - existing_strategies: List of current strategies (optional)
        - constraints: Dict with budget, timeline, resources (optional)

        Returns:
            Formatted prompt for strategy generation
        """
        goal_intent = context.get("goal_intent", "")
        business_ctx = context.get("business_context", {})
        existing_strategies = context.get("existing_strategies", [])
        constraints = context.get("constraints", {})

        # Extract business context fields
        vision = business_ctx.get("vision", "Not defined")
        purpose = business_ctx.get("purpose", "Not defined")
        core_values = business_ctx.get("coreValues", [])
        target_market = business_ctx.get("targetMarket", "Not defined")
        value_prop = business_ctx.get("valueProposition", "Not defined")
        industry = business_ctx.get("industry", "Not specified")
        business_type = business_ctx.get("businessType", "Not specified")

        values_str = ", ".join(core_values) if core_values else "Not defined"
        existing_str = (
            "\n".join([f"- {s}" for s in existing_strategies])
            if existing_strategies
            else "None currently in place"
        )

        # Build constraints section
        constraints_section = ""
        if constraints:
            budget = constraints.get("budget")
            timeline = constraints.get("timeline")
            resources = constraints.get("resources", [])

            constraints_section = f"""
**Resource Constraints:**
- Budget: ${budget:,} if budget else 'Flexible'
- Timeline: {timeline or "Flexible"}
- Available Resources: {", ".join(resources) if resources else "To be determined"}
"""

        prompt = f"""You are an expert business strategist helping develop actionable strategies for a business goal.

**Goal:**
{goal_intent}

**Business Context:**
- Vision: {vision}
- Purpose: {purpose}
- Core Values: {values_str}
- Target Market: {target_market}
- Value Proposition: {value_prop}
- Industry: {industry}
- Business Type: {business_type}

**Existing Strategies:**
{existing_str}
{constraints_section}

Please generate 3-5 strategic recommendations to achieve this goal. For each strategy, provide:
1. **title**: Clear, actionable title (4-8 words)
2. **description**: Detailed description of the strategy (2-3 sentences)
3. **rationale**: Why this strategy makes sense given the context (2-3 sentences)
4. **difficulty**: Implementation difficulty (low/medium/high)
5. **timeframe**: Expected implementation timeframe (e.g., "2-3 months", "6 weeks")
6. **expectedImpact**: Expected business impact (low/medium/high)
7. **prerequisites**: List of prerequisites or dependencies (array)
8. **estimatedCost**: Estimated cost in dollars (number or null if not applicable)
9. **requiredResources**: List of required resources/people (array)

Respond in this exact JSON format:

{{
    "suggestions": [
        {{
            "title": "Strategy Title Here",
            "description": "Detailed description of the strategy",
            "rationale": "Why this strategy will help achieve the goal",
            "difficulty": "medium",
            "timeframe": "2-3 months",
            "expectedImpact": "high",
            "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
            "estimatedCost": 15000,
            "requiredResources": ["Resource 1", "Resource 2"]
        }}
    ],
    "confidence": 0.85,
    "reasoning": "Overall reasoning for why these strategies were recommended given the business context"
}}

Important guidelines:
- Strategies should be specific, actionable, and realistic
- Consider the business context, values, and constraints
- Build upon or complement existing strategies where appropriate
- Ensure recommendations align with the vision and purpose
- If constraints are provided, respect them in your recommendations
- Provide honest confidence score (0.0-1.0) based on information quality"""

        return prompt

    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse strategy suggestion response.

        Args:
            llm_response: Raw LLM JSON response

        Returns:
            Structured strategy suggestions result

        Expected structure:
        - suggestions: list[dict] with strategy details
        - confidence: float (0.0-1.0)
        - reasoning: str
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = llm_response.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result: dict[str, Any] = json.loads(response_text.strip())

            # Validate required fields
            required_fields = ["suggestions", "confidence", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Validate suggestions structure
            if not isinstance(result["suggestions"], list):
                raise ValueError("suggestions must be a list")

            if not result["suggestions"]:
                raise ValueError("At least one suggestion is required")

            # Validate each suggestion
            required_suggestion_fields = [
                "title",
                "description",
                "rationale",
                "difficulty",
                "timeframe",
                "expectedImpact",
            ]

            for idx, suggestion in enumerate(result["suggestions"]):
                for field in required_suggestion_fields:
                    if field not in suggestion:
                        raise ValueError(f"Suggestion {idx} missing required field: {field}")

                # Ensure optional fields have defaults
                suggestion.setdefault("prerequisites", [])
                suggestion.setdefault("estimatedCost", None)
                suggestion.setdefault("requiredResources", [])

                # Validate difficulty values
                if suggestion["difficulty"] not in ["low", "medium", "high"]:
                    logger.warning(
                        "Invalid difficulty value, defaulting to medium",
                        difficulty=suggestion["difficulty"],
                    )
                    suggestion["difficulty"] = "medium"

                # Validate expectedImpact values
                if suggestion["expectedImpact"] not in ["low", "medium", "high"]:
                    logger.warning(
                        "Invalid expectedImpact value, defaulting to medium",
                        impact=suggestion["expectedImpact"],
                    )
                    suggestion["expectedImpact"] = "medium"

            # Validate confidence range
            if not 0.0 <= result["confidence"] <= 1.0:
                logger.warning(
                    "Confidence score out of range, capping",
                    confidence=result["confidence"],
                )
                result["confidence"] = max(0.0, min(1.0, result["confidence"]))

            logger.info(
                "Strategy suggestions parsed successfully",
                suggestion_count=len(result["suggestions"]),
                confidence=result["confidence"],
            )

            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse strategy suggestions JSON", error=str(e))
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e
        except (KeyError, ValueError) as e:
            logger.error("Invalid strategy suggestions structure", error=str(e))
            raise ValueError(f"Invalid strategy suggestions structure: {e}") from e


__all__ = ["StrategySuggestionService"]
