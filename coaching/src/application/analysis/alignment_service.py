"""Alignment analysis service.

Analyzes how well user's actions/plans align with their purpose, values, and goals.
Provides scoring, explanation, and improvement suggestions.
"""

import json
from typing import Any

import structlog
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.core.constants import AnalysisType

logger = structlog.get_logger()


class AlignmentAnalysisService(BaseAnalysisService):
    """
    Service for alignment analysis.

    Analyzes alignment between:
    - Actions and purpose/values
    - Plans and goals
    - Current state and desired state

    Output:
    - Alignment score (0-100)
    - Explanation of score
    - Specific misalignments identified
    - Recommendations for improvement
    """

    def get_analysis_type(self) -> AnalysisType:
        """Return ALIGNMENT analysis type."""
        return AnalysisType.ALIGNMENT

    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build alignment analysis prompt.

        Required context:
        - user_id: User identifier
        - purpose: User's purpose statement (optional)
        - values: List of core values (optional)
        - goals: User's goals (optional)
        - current_actions: Current activities/plans to analyze

        Returns:
            Formatted prompt for alignment analysis
        """
        purpose = context.get("purpose", "Not defined")
        values = context.get("values", [])
        goals = context.get("goals", [])
        current_actions = context.get("current_actions", "")

        values_str = ", ".join(values) if values else "Not defined"
        goals_str = "\n".join([f"- {g}" for g in goals]) if goals else "Not defined"

        prompt = f"""You are an expert business coach analyzing alignment between a user's purpose, values, goals, and their current actions/plans.

**User's Purpose:**
{purpose}

**User's Core Values:**
{values_str}

**User's Goals:**
{goals_str}

**Current Actions/Plans to Analyze:**
{current_actions}

Please analyze the alignment and provide your response in the following JSON format:

{{
    "alignment_score": <number 0-100>,
    "overall_assessment": "<brief summary of alignment>",
    "strengths": [
        "<areas where actions align well with purpose/values/goals>"
    ],
    "misalignments": [
        {{
            "area": "<what's misaligned>",
            "explanation": "<why it's misaligned>",
            "impact": "<high/medium/low>"
        }}
    ],
    "recommendations": [
        {{
            "action": "<specific recommendation>",
            "rationale": "<why this will improve alignment>",
            "priority": "<high/medium/low>"
        }}
    ]
}}

Provide a thorough, actionable analysis."""

        return prompt

    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse alignment analysis response.

        Args:
            llm_response: Raw LLM JSON response

        Returns:
            Structured alignment analysis result

        Expected structure:
        - alignment_score: int (0-100)
        - overall_assessment: str
        - strengths: list[str]
        - misalignments: list[dict]
        - recommendations: list[dict]
        """
        try:
            # Try to extract JSON from response (may have markdown code blocks)
            response_text = llm_response.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())

            # Validate required fields
            required_fields = [
                "alignment_score",
                "overall_assessment",
                "strengths",
                "misalignments",
                "recommendations",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Validate alignment score range
            if not 0 <= result["alignment_score"] <= 100:
                logger.warning(
                    "Alignment score out of range, capping",
                    score=result["alignment_score"],
                )
                result["alignment_score"] = max(0, min(100, result["alignment_score"]))

            logger.debug(
                "Alignment response parsed",
                score=result["alignment_score"],
                misalignments_count=len(result["misalignments"]),
                recommendations_count=len(result["recommendations"]),
            )

            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse alignment JSON response", error=str(e))
            # Return fallback structure
            return {
                "alignment_score": 0,
                "overall_assessment": "Error parsing response",
                "strengths": [],
                "misalignments": [],
                "recommendations": [],
                "parse_error": str(e),
            }
        except Exception as e:
            logger.error("Failed to parse alignment response", error=str(e))
            raise


__all__ = ["AlignmentAnalysisService"]
