"""Strategy analysis service.

Generates strategic recommendations based on user's goals, current situation, and context.
"""

import json
from typing import Any

import structlog
from src.application.analysis.base_analysis_service import BaseAnalysisService
from src.core.constants import AnalysisType

logger = structlog.get_logger()


class StrategyAnalysisService(BaseAnalysisService):
    """
    Service for strategy recommendations.

    Analyzes user's situation and provides:
    - Strategic recommendations
    - Implementation approaches
    - Risk assessment
    - Success metrics
    """

    def get_analysis_type(self) -> AnalysisType:
        """Return STRATEGY analysis type."""
        return AnalysisType.STRATEGY

    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build strategy analysis prompt.

        Required context:
        - goal: Primary goal to strategize for
        - current_situation: Current state description
        - constraints: Known constraints (optional)
        - resources: Available resources (optional)

        Returns:
            Formatted prompt for strategy analysis
        """
        goal = context.get("goal", "")
        current_situation = context.get("current_situation", "")
        constraints = context.get("constraints", [])
        resources = context.get("resources", [])

        constraints_str = (
            "\n".join([f"- {c}" for c in constraints]) if constraints else "None specified"
        )
        resources_str = "\n".join([f"- {r}" for r in resources]) if resources else "None specified"

        prompt = f"""You are an expert strategic business coach helping a user develop strategies to achieve their goals.

**Primary Goal:**
{goal}

**Current Situation:**
{current_situation}

**Constraints:**
{constraints_str}

**Available Resources:**
{resources_str}

Please provide strategic recommendations in the following JSON format:

{{
    "strategic_approach": "<overall strategic direction>",
    "strategies": [
        {{
            "name": "<strategy name>",
            "description": "<detailed description>",
            "rationale": "<why this strategy>",
            "implementation_steps": [
                "<specific step>"
            ],
            "timeline": "<estimated timeline>",
            "priority": "<high/medium/low>"
        }}
    ],
    "risks": [
        {{
            "risk": "<potential risk>",
            "mitigation": "<how to mitigate>",
            "severity": "<high/medium/low>"
        }}
    ],
    "success_metrics": [
        "<measurable metric>"
    ],
    "quick_wins": [
        "<immediate action for momentum>"
    ]
}}

Provide 3-5 actionable strategies."""

        return prompt

    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse strategy analysis response.

        Args:
            llm_response: Raw LLM JSON response

        Returns:
            Structured strategy analysis result
        """
        try:
            # Clean response
            response_text = llm_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            # Validate required fields
            required_fields = ["strategic_approach", "strategies", "risks", "success_metrics"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            logger.debug(
                "Strategy response parsed",
                strategies_count=len(result["strategies"]),
                risks_count=len(result["risks"]),
            )

            return result  # type: ignore[no-any-return]

        except json.JSONDecodeError as e:
            logger.error("Failed to parse strategy JSON response", error=str(e))
            return {
                "strategic_approach": "Error parsing response",
                "strategies": [],
                "risks": [],
                "success_metrics": [],
                "quick_wins": [],
                "parse_error": str(e),
            }
        except Exception as e:
            logger.error("Failed to parse strategy response", error=str(e))
            raise


__all__ = ["StrategyAnalysisService"]
