"""Measure analysis service.

Recommends Measures for measuring progress toward goals.
"""

import json
from typing import Any

import structlog
from coaching.src.application.analysis.base_analysis_service import BaseAnalysisService
from coaching.src.core.constants import AnalysisType

logger = structlog.get_logger()


class MeasureAnalysisService(BaseAnalysisService):
    """
    Service for Measure recommendations.

    Analyzes goals and recommends:
    - Relevant Measures to track
    - Measurement methods
    - Target values
    - Tracking frequency
    """

    def get_analysis_type(self) -> AnalysisType:
        """Return Measure analysis type."""
        return AnalysisType.MEASURE

    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build Measure analysis prompt.

        Required context:
        - goal: Goal to create Measures for
        - goal_timeline: Timeline for goal achievement
        - current_metrics: Existing metrics (optional)

        Returns:
            Formatted prompt for Measure analysis
        """
        goal = context.get("goal", "")
        goal_timeline = context.get("goal_timeline", "Not specified")
        current_metrics = context.get("current_metrics", [])

        current_metrics_str = (
            "\n".join([f"- {m}" for m in current_metrics]) if current_metrics else "None"
        )

        prompt = f"""You are an expert business coach helping a user define Measures for their goals.

**Goal:**
{goal}

**Timeline:**
{goal_timeline}

**Current Metrics:**
{current_metrics_str}

Please recommend Measures in the following JSON format:

{{
    "recommended_measures": [
        {{
            "measure_name": "<clear Measure name>",
            "description": "<what this measures>",
            "measurement_method": "<how to measure>",
            "target_value": "<specific target>",
            "current_baseline": "<current value if known, or 'TBD'>",
            "tracking_frequency": "<daily/weekly/monthly/quarterly>",
            "category": "<leading/lagging indicator>",
            "rationale": "<why this Measure matters>"
        }}
    ],
    "dashboard_structure": {{
        "primary_measures": ["<most important Measures>"],
        "secondary_measures": ["<supporting Measures>"]
    }},
    "tracking_recommendations": [
        "<best practice for tracking>"
    ],
    "success_criteria": "<what success looks like>"
}}

Recommend 5-8 specific, measurable Measures."""

        return prompt

    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse Measure analysis response.

        Args:
            llm_response: Raw LLM JSON response

        Returns:
            Structured Measure analysis result
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

            result: dict[str, Any] = json.loads(response_text.strip())

            # Validate required fields
            required_fields = [
                "recommended_measures",
                "dashboard_structure",
                "tracking_recommendations",
                "success_criteria",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            logger.debug(
                "Measure response parsed",
                measures_count=len(result["recommended_measures"]),
            )

            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Measure JSON response", error=str(e))
            return {
                "recommended_measures": [],
                "dashboard_structure": {"primary_measures": [], "secondary_measures": []},
                "tracking_recommendations": [],
                "success_criteria": "Error parsing response",
                "parse_error": str(e),
            }
        except Exception as e:
            logger.error("Failed to parse Measure response", error=str(e))
            raise


__all__ = ["MeasureAnalysisService"]
