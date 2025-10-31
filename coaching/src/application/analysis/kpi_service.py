"""KPI analysis service.

Recommends Key Performance Indicators for measuring progress toward goals.
"""

import json
from typing import Any

import structlog
from src.application.analysis.base_analysis_service import BaseAnalysisService
from src.core.constants import AnalysisType

logger = structlog.get_logger()


class KPIAnalysisService(BaseAnalysisService):
    """
    Service for KPI recommendations.

    Analyzes goals and recommends:
    - Relevant KPIs to track
    - Measurement methods
    - Target values
    - Tracking frequency
    """

    def get_analysis_type(self) -> AnalysisType:
        """Return KPI analysis type."""
        return AnalysisType.KPI

    def build_prompt(self, context: dict[str, Any]) -> str:
        """
        Build KPI analysis prompt.

        Required context:
        - goal: Goal to create KPIs for
        - goal_timeline: Timeline for goal achievement
        - current_metrics: Existing metrics (optional)

        Returns:
            Formatted prompt for KPI analysis
        """
        goal = context.get("goal", "")
        goal_timeline = context.get("goal_timeline", "Not specified")
        current_metrics = context.get("current_metrics", [])

        current_metrics_str = (
            "\n".join([f"- {m}" for m in current_metrics]) if current_metrics else "None"
        )

        prompt = f"""You are an expert business coach helping a user define Key Performance Indicators (KPIs) for their goals.

**Goal:**
{goal}

**Timeline:**
{goal_timeline}

**Current Metrics:**
{current_metrics_str}

Please recommend KPIs in the following JSON format:

{{
    "recommended_kpis": [
        {{
            "kpi_name": "<clear KPI name>",
            "description": "<what this measures>",
            "measurement_method": "<how to measure>",
            "target_value": "<specific target>",
            "current_baseline": "<current value if known, or 'TBD'>",
            "tracking_frequency": "<daily/weekly/monthly/quarterly>",
            "category": "<leading/lagging indicator>",
            "rationale": "<why this KPI matters>"
        }}
    ],
    "dashboard_structure": {{
        "primary_kpis": ["<most important KPIs>"],
        "secondary_kpis": ["<supporting KPIs>"]
    }},
    "tracking_recommendations": [
        "<best practice for tracking>"
    ],
    "success_criteria": "<what success looks like>"
}}

Recommend 5-8 specific, measurable KPIs."""

        return prompt

    def parse_response(self, llm_response: str) -> dict[str, Any]:
        """
        Parse KPI analysis response.

        Args:
            llm_response: Raw LLM JSON response

        Returns:
            Structured KPI analysis result
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
            required_fields = [
                "recommended_kpis",
                "dashboard_structure",
                "tracking_recommendations",
                "success_criteria",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            logger.debug(
                "KPI response parsed",
                kpis_count=len(result["recommended_kpis"]),
            )

            return result  # type: ignore[no-any-return]

        except json.JSONDecodeError as e:
            logger.error("Failed to parse KPI JSON response", error=str(e))
            return {
                "recommended_kpis": [],
                "dashboard_structure": {"primary_kpis": [], "secondary_kpis": []},
                "tracking_recommendations": [],
                "success_criteria": "Error parsing response",
                "parse_error": str(e),
            }
        except Exception as e:
            logger.error("Failed to parse KPI response", error=str(e))
            raise


__all__ = ["KPIAnalysisService"]
