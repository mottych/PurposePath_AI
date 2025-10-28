"""
Single-shot analysis workflow template.

Implements a LangGraph-based linear analysis flow with:
- Input validation
- Analysis execution
- Insight extraction
- Response formatting
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from coaching.src.llm.providers.manager import provider_manager
from langgraph.graph import StateGraph

from .base import BaseWorkflow, WorkflowState, WorkflowType

logger = structlog.get_logger(__name__)


class AnalysisWorkflowTemplate(BaseWorkflow):
    """LangGraph workflow template for single-shot analysis."""

    @property
    def workflow_type(self) -> WorkflowType:
        """Get the workflow type."""
        return WorkflowType.SINGLE_SHOT_ANALYSIS

    @property
    def workflow_steps(self) -> list[str]:
        """Get list of workflow step names."""
        return [
            "input_validation",
            "analysis_execution",
            "insight_extraction",
            "response_formatting",
            "completion",
        ]

    async def build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build the LangGraph workflow graph for single-shot analysis."""
        # Create StateGraph with our enhanced state type
        # LangGraph prefers TypedDict but supports dict at runtime
        graph = StateGraph(dict[str, Any])

        # Add nodes for each step in the analysis
        graph.add_node("input_validation", self.input_validation_node)
        graph.add_node("analysis_execution", self.analysis_execution_node)
        graph.add_node("insight_extraction", self.insight_extraction_node)
        graph.add_node("response_formatting", self.response_formatting_node)
        graph.add_node("completion", self.completion_node)

        # Define linear flow for single-shot analysis
        graph.set_entry_point("input_validation")

        # Linear progression through analysis steps
        graph.add_edge("input_validation", "analysis_execution")
        graph.add_edge("analysis_execution", "insight_extraction")
        graph.add_edge("insight_extraction", "response_formatting")
        graph.add_edge("response_formatting", "completion")

        # Completion is the end
        graph.set_finish_point("completion")

        return graph

    async def create_initial_state(self, user_input: dict[str, Any]) -> WorkflowState:
        """Create initial workflow state from user input."""
        # Handle both direct input (tests) and graph_state (orchestrator)
        # If "messages" key exists, this is graph_state from orchestrator
        if "messages" in user_input:
            # Use existing graph_state structure
            content = user_input.get("messages", [{}])[0].get("content", "")
            analysis_type = user_input.get("analysis_type", "general")
        else:
            # Direct initial_input from tests
            content = user_input.get("content", "")
            analysis_type = user_input.get("analysis_type", "general")

        return WorkflowState(
            workflow_id=user_input.get("workflow_id", ""),
            workflow_type=self.workflow_type,
            user_id=user_input.get("user_id", ""),
            session_id=user_input.get("session_id"),
            conversation_history=[
                {
                    "role": "user",
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_type": analysis_type,
                }
            ],
            current_step="input_validation",
            workflow_context={
                "provider_id": user_input.get("provider_id"),
                "analysis_type": analysis_type,
                "analysis_focus": user_input.get("analysis_focus", []),
            },
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

    async def validate_state(self, state: WorkflowState) -> bool:
        """Validate workflow state is consistent."""
        required_fields = ["workflow_id", "user_id", "current_step"]
        has_content = bool(
            state.conversation_history and state.conversation_history[0].get("content")
        )
        return (
            all(getattr(state, field, None) is not None for field in required_fields)
            and has_content
        )

    # Node implementations
    async def input_validation_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Validate and prepare input for analysis."""
        logger.info("Executing input validation", workflow_id=state.get("workflow_id"))

        # Get the input content - check both messages (orchestrator) and conversation_history (workflow template)
        messages = state.get("messages") or state.get("conversation_history", [])
        if not messages:
            state["status"] = "failed"
            state["step_data"] = {"error": "No input provided for analysis"}
            return state

        user_input = messages[0].get("content", "").strip()
        analysis_type = state.get("analysis_type") or state.get("workflow_context", {}).get(
            "analysis_type", "general"
        )

        # Validate input content
        validation_result = {
            "is_valid": True,
            "content_length": len(user_input),
            "analysis_type": analysis_type,
            "validation_notes": [],
        }

        # Check for minimum content length
        if len(user_input) < 10:
            validation_result["is_valid"] = False
            validation_result["validation_notes"].append("Input too short for meaningful analysis")

        # Check for maximum content length
        if len(user_input) > 5000:
            validation_result["validation_notes"].append("Input truncated to 5000 characters")
            user_input = user_input[:5000]
            messages[0]["content"] = user_input

        # Set analysis focus based on type
        analysis_focuses = {
            "values": ["core values", "beliefs", "principles", "what matters most"],
            "goals": ["objectives", "aspirations", "targets", "desired outcomes"],
            "emotions": ["feelings", "emotional state", "mood", "emotional patterns"],
            "challenges": ["obstacles", "difficulties", "problems", "barriers"],
            "general": ["themes", "patterns", "insights", "key points"],
        }

        state["analysis_focus"] = analysis_focuses.get(analysis_type, analysis_focuses["general"])
        state["step_data"] = {"validation": validation_result}
        state["current_step"] = "input_validation"
        state["updated_at"] = datetime.utcnow().isoformat()

        # If validation failed, skip to completion
        if not validation_result["is_valid"]:
            state["status"] = "failed"

        return state

    async def analysis_execution_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the core analysis."""
        logger.info("Executing analysis", workflow_id=state.get("workflow_id"))

        # Skip if validation failed
        if state.get("status") == "failed":
            return state

        provider = provider_manager.get_provider(state.get("provider_id"))

        # Get analysis input - check both messages (orchestrator) and conversation_history (workflow template)
        messages = state.get("messages") or state.get("conversation_history", [])
        content_to_analyze = messages[0].get("content", "") if messages else ""
        analysis_type = state.get("analysis_type") or state.get("workflow_context", {}).get(
            "analysis_type", "general"
        )
        analysis_focus = state.get("analysis_focus", [])

        # Create analysis prompt based on type
        analysis_prompt = self._create_analysis_prompt(analysis_type, analysis_focus)

        try:
            # Execute analysis
            analysis_result = await provider.analyze_text(  # type: ignore[attr-defined]
                text=content_to_analyze,
                analysis_prompt=analysis_prompt,
                **state.get("model_config", {}),
            )

            # Store analysis results
            state["step_data"]["analysis"] = {
                "input_content": content_to_analyze,
                "analysis_type": analysis_type,
                "analysis_result": (
                    analysis_result.model_dump()
                    if hasattr(analysis_result, "model_dump")
                    else str(analysis_result)
                ),
                "analysis_focus": analysis_focus,
                "timestamp": datetime.utcnow().isoformat(),
            }

            state["current_step"] = "analysis_execution"

        except Exception as e:
            logger.error("Analysis execution failed", error=str(e))
            state["status"] = "failed"
            state["step_data"]["analysis"] = {
                "error": str(e),
                "analysis_type": analysis_type,
            }

        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    async def insight_extraction_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Extract structured insights from analysis."""
        logger.info("Executing insight extraction", workflow_id=state.get("workflow_id"))

        # Skip if previous steps failed
        if state.get("status") == "failed":
            return state

        analysis_data = state.get("step_data", {}).get("analysis", {})
        analysis_result = analysis_data.get("analysis_result", {})
        analysis_type = analysis_data.get("analysis_type", "general")

        # Extract insights based on analysis type
        insights = self._extract_insights_by_type(analysis_type, analysis_result)

        # Create insight summary
        insight_summary = {
            "total_insights": len(insights),
            "categories": list({insight.get("category", "general") for insight in insights}),
            "confidence_scores": [insight.get("confidence", 0.5) for insight in insights],
            "key_themes": self._identify_key_themes(insights),
        }

        # Store extracted insights
        if "results" not in state:
            state["results"] = {}

        state["results"]["insights"] = insights
        state["results"]["insight_summary"] = insight_summary
        state["step_data"]["insight_extraction"] = {
            "insights_count": len(insights),
            "extraction_method": f"{analysis_type}_based",
            "timestamp": datetime.utcnow().isoformat(),
        }

        state["current_step"] = "insight_extraction"
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    async def response_formatting_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Format the analysis results into a user-friendly response."""
        logger.info("Executing response formatting", workflow_id=state.get("workflow_id"))

        # Skip if previous steps failed
        if state.get("status") == "failed":
            error_message = {
                "role": "assistant",
                "content": "I'm sorry, but I wasn't able to complete the analysis. Please try again with different input.",
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Safely append to messages list
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(error_message)
            return state

        insights = state.get("results", {}).get("insights", [])
        insight_summary = state.get("results", {}).get("insight_summary", {})
        analysis_type = state.get("analysis_type", "general")

        # Format response based on analysis type
        formatted_response = self._format_response_by_type(analysis_type, insights, insight_summary)

        # Create response message
        response_message = {
            "role": "assistant",
            "content": formatted_response,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_metadata": {
                "insights_count": len(insights),
                "analysis_type": analysis_type,
                "categories": insight_summary.get("categories", []),
            },
        }

        # Safely append to messages list
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(response_message)
        state["step_data"]["response_formatting"] = {
            "response_length": len(formatted_response),
            "format_type": f"{analysis_type}_format",
            "timestamp": datetime.utcnow().isoformat(),
        }

        state["current_step"] = "response_formatting"
        state["updated_at"] = datetime.utcnow().isoformat()
        return state

    async def completion_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """Complete the analysis workflow."""
        logger.info("Executing completion", workflow_id=state.get("workflow_id"))

        # Set completion status
        if state.get("status") != "failed":
            state["status"] = "completed"

        state["current_step"] = "completion"
        state["completed_at"] = datetime.utcnow().isoformat()
        state["updated_at"] = datetime.utcnow().isoformat()

        # Add final results summary
        if "results" not in state:
            state["results"] = {}

        state["results"]["analysis_complete"] = True
        state["results"]["processing_time"] = self._calculate_processing_time(state)

        return state

    # Helper methods
    def _create_analysis_prompt(self, analysis_type: str, analysis_focus: list[str]) -> str:
        """Create analysis prompt based on type and focus."""
        base_prompt = f"Analyze the following text with focus on {', '.join(analysis_focus)}."

        prompts = {
            "values": f"""
            {base_prompt}

            Identify and analyze:
            1. Core values being expressed or implied
            2. Belief systems and principles
            3. What the person considers important
            4. Value conflicts or alignments
            5. Underlying motivations

            Return structured analysis as JSON with keys: core_values, beliefs, importance_indicators, conflicts, motivations
            """,
            "goals": f"""
            {base_prompt}

            Identify and analyze:
            1. Explicit goals or objectives mentioned
            2. Implicit aspirations or desires
            3. Short-term vs long-term objectives
            4. Goal clarity and specificity
            5. Potential obstacles to achievement

            Return structured analysis as JSON with keys: explicit_goals, implicit_goals, timeframes, clarity_level, obstacles
            """,
            "emotions": f"""
            {base_prompt}

            Identify and analyze:
            1. Emotional states expressed
            2. Emotional patterns or triggers
            3. Emotional intensity levels
            4. Emotional regulation strategies
            5. Emotional needs or concerns

            Return structured analysis as JSON with keys: current_emotions, patterns, intensity, regulation, needs
            """,
            "challenges": f"""
            {base_prompt}

            Identify and analyze:
            1. Explicit challenges or problems mentioned
            2. Implicit difficulties or obstacles
            3. Problem complexity and scope
            4. Current coping strategies
            5. Potential solutions or approaches

            Return structured analysis as JSON with keys: explicit_challenges, implicit_difficulties, complexity, coping_strategies, potential_solutions
            """,
            "general": f"""
            {base_prompt}

            Identify and analyze:
            1. Main themes and topics
            2. Key insights or revelations
            3. Patterns or recurring elements
            4. Important details or nuances
            5. Overall tone and context

            Return structured analysis as JSON with keys: themes, insights, patterns, details, tone
            """,
        }

        return prompts.get(analysis_type, prompts["general"])

    def _extract_insights_by_type(
        self, analysis_type: str, analysis_result: Any
    ) -> list[dict[str, Any]]:
        """Extract insights based on analysis type."""
        insights = []

        if isinstance(analysis_result, dict):
            for category, data in analysis_result.items():
                if isinstance(data, list):
                    for item in data:
                        insights.append(
                            {
                                "content": str(item),
                                "category": category,
                                "type": analysis_type,
                                "confidence": 0.8,  # Default confidence
                            }
                        )
                elif isinstance(data, str) and data.strip():
                    insights.append(
                        {
                            "content": data,
                            "category": category,
                            "type": analysis_type,
                            "confidence": 0.7,
                        }
                    )

        return insights

    def _identify_key_themes(self, insights: list[dict[str, Any]]) -> list[str]:
        """Identify key themes from insights."""
        themes = []
        categories: dict[str, list[str]] = {}

        for insight in insights:
            category = insight.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(insight["content"])

        # Extract themes from categories with multiple insights
        for category, items in categories.items():
            if len(items) > 1:
                themes.append(f"{category.replace('_', ' ').title()}")

        return themes[:5]  # Top 5 themes

    def _format_response_by_type(
        self, analysis_type: str, insights: list[dict[str, Any]], summary: dict[str, Any]
    ) -> str:
        """Format response based on analysis type."""
        if not insights:
            return "I wasn't able to extract specific insights from your input. Could you provide more detail or context?"

        response_templates = {
            "values": "Based on your input, here are the key values and beliefs I identified:\n\n",
            "goals": "Here's my analysis of the goals and objectives in your message:\n\n",
            "emotions": "I noticed these emotional elements in what you shared:\n\n",
            "challenges": "Here are the challenges and potential solutions I identified:\n\n",
            "general": "Here's my analysis of your input:\n\n",
        }

        response = response_templates.get(analysis_type, response_templates["general"])

        # Group insights by category
        categories: dict[str, list[str]] = {}
        for insight in insights:
            category = insight.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(insight["content"])

        # Format each category
        for category, items in categories.items():
            category_title = category.replace("_", " ").title()
            response += f"**{category_title}:**\n"
            for i, item in enumerate(items[:3], 1):  # Limit to 3 items per category
                response += f"{i}. {item}\n"
            response += "\n"

        # Add summary if there are key themes
        themes = summary.get("key_themes", [])
        if themes:
            response += f"**Key Themes:** {', '.join(themes)}\n\n"

        response += f"This analysis identified {summary.get('total_insights', 0)} specific insights across {len(categories)} categories."

        return response

    def _calculate_processing_time(self, state: dict[str, Any]) -> float:
        """Calculate processing time in seconds."""
        created_at = state.get("created_at")
        completed_at = state.get("completed_at")

        if created_at and completed_at:
            try:
                start = datetime.fromisoformat(created_at)
                end = datetime.fromisoformat(completed_at)
                return (end - start).total_seconds()
            except ValueError:
                pass

        return 0.0
