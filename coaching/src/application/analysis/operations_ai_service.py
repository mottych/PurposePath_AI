"""Operations AI Service for strategic operations management (Issues #63 & #64)."""

import json
from datetime import datetime, timedelta
from typing import Any

import structlog
from coaching.src.application.llm.llm_service import LLMApplicationService

logger = structlog.get_logger()


class OperationsAIService:
    """Service for AI-powered operations management."""

    def __init__(self, llm_service: LLMApplicationService):
        self.llm_service = llm_service
        logger.info("OperationsAIService initialized")

    async def analyze_strategic_alignment(
        self,
        actions: list[dict[str, Any]],
        goals: list[dict[str, Any]],
        business_foundation: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze how well actions align with business goals and foundation."""
        logger.info(
            "Analyzing strategic alignment", action_count=len(actions), goal_count=len(goals)
        )

        if not actions:
            raise ValueError("At least one action is required")
        if not goals:
            raise ValueError("At least one goal is required")
        if not business_foundation.get("vision") or not business_foundation.get("purpose"):
            raise ValueError("Business foundation must include vision and purpose")

        actions_summary = self._format_actions_for_prompt(actions)
        goals_summary = self._format_goals_for_prompt(goals)
        foundation_summary = self._format_foundation_for_prompt(business_foundation)

        prompt = f"""You are an expert strategic business analyst. Analyze how well the following actions align with business goals and foundation.

**Business Foundation:**
{foundation_summary}

**Business Goals:**
{goals_summary}

**Actions to Analyze:**
{actions_summary}

Format your response as JSON with alignmentAnalysis (array), overallAlignment (number), and insights (array)."""

        llm_response = await self.llm_service.generate_analysis(
            analysis_prompt=prompt,
            context={
                "actions": actions,
                "goals": goals,
                "business_foundation": business_foundation,
            },
            temperature=0.6,
        )

        try:
            response_text = llm_response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            analysis = json.loads(response_text.strip())
            logger.info(
                "Strategic alignment analysis completed",
                overall_score=analysis.get("overallAlignment"),
            )
            return analysis
        except json.JSONDecodeError:
            return {
                "alignmentAnalysis": [
                    {
                        "actionId": a.get("id"),
                        "alignmentScore": 50,
                        "strategicConnections": [],
                        "recommendations": ["Review alignment"],
                    }
                    for a in actions
                ],
                "overallAlignment": 50,
                "insights": ["Unable to complete detailed analysis"],
            }

    async def suggest_prioritization(
        self,
        actions: list[dict[str, Any]],
        business_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate AI-powered prioritization suggestions for actions."""
        logger.info("Generating prioritization suggestions", action_count=len(actions))

        if not actions:
            raise ValueError("At least one action is required")

        actions_summary = self._format_prioritization_actions(actions)
        context_summary = self._format_business_context(business_context)

        prompt = f"""You are an expert project prioritization analyst. Suggest optimal priorities for these actions.

**Business Context:**
{context_summary}

**Actions:**
{actions_summary}

Format as JSON array with actionId, suggestedPriority, currentPriority, reasoning, confidence, urgencyFactors, impactFactors, recommendedAction, estimatedBusinessValue."""

        llm_response = await self.llm_service.generate_analysis(
            analysis_prompt=prompt,
            context={"actions": actions, "business_context": business_context},
            temperature=0.5,
        )

        try:
            response_text = llm_response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            suggestions = json.loads(response_text.strip())
            logger.info("Prioritization suggestions generated", suggestions_count=len(suggestions))
            return suggestions
        except json.JSONDecodeError:
            return [
                {
                    "actionId": a.get("id"),
                    "suggestedPriority": a.get("currentPriority", "medium"),
                    "currentPriority": a.get("currentPriority", "medium"),
                    "reasoning": "Unable to analyze",
                    "confidence": 0.5,
                    "urgencyFactors": ["Requires review"],
                    "impactFactors": ["Assessment needed"],
                    "recommendedAction": "maintain",
                    "estimatedBusinessValue": None,
                }
                for a in actions
            ]

    async def optimize_scheduling(
        self,
        actions: list[dict[str, Any]],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate optimized scheduling suggestions for actions."""
        logger.info("Generating scheduling suggestions", action_count=len(actions))

        if not actions:
            raise ValueError("At least one action is required")
        if not constraints.get("teamCapacity"):
            raise ValueError("Team capacity is required")

        actions_summary = self._format_scheduling_actions(actions)
        constraints_summary = self._format_constraints(constraints)

        prompt = f"""You are an expert project scheduling optimizer. Suggest optimal schedules.

**Constraints:**
{constraints_summary}

**Actions:**
{actions_summary}

Format as JSON array with actionId, suggestedStartDate, suggestedDueDate, reasoning, confidence, dependencies, resourceConsiderations, risks, alternativeSchedules."""

        llm_response = await self.llm_service.generate_analysis(
            analysis_prompt=prompt,
            context={"actions": actions, "constraints": constraints},
            temperature=0.4,
        )

        try:
            response_text = llm_response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            schedules = json.loads(response_text.strip())
            logger.info("Scheduling suggestions generated", schedules_count=len(schedules))
            return schedules
        except json.JSONDecodeError:
            today = datetime.now().date()
            return [
                {
                    "actionId": a.get("id"),
                    "suggestedStartDate": today.isoformat(),
                    "suggestedDueDate": (today + timedelta(days=7)).isoformat(),
                    "reasoning": "Default schedule",
                    "confidence": 0.5,
                    "dependencies": [],
                    "resourceConsiderations": ["Requires review"],
                    "risks": ["Not optimized"],
                    "alternativeSchedules": [],
                }
                for a in actions
            ]

    async def suggest_root_cause_methods(
        self,
        issue: dict[str, Any],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """AI-powered root cause analysis method selection (Issue #64)."""
        logger.info("Suggesting root cause analysis methods")

        if not issue.get("issueTitle") or not issue.get("issueDescription"):
            raise ValueError("Issue title and description are required")

        issue_summary = self._format_issue_for_root_cause(issue, context)

        prompt = f"""You are an expert problem-solving analyst. Suggest the most appropriate root cause analysis methods.

**Issue:**
{issue_summary}

Suggest 1-3 methods (five_whys, fishbone, swot, pareto) with method, confidence, suggestions, and reasoning. Format as JSON array."""

        llm_response = await self.llm_service.generate_analysis(
            analysis_prompt=prompt,
            context={"issue": issue, "context": context},
            temperature=0.6,
        )

        try:
            response_text = llm_response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            suggestions = json.loads(response_text.strip())
            logger.info(
                "Root cause method suggestions generated", suggestions_count=len(suggestions)
            )
            return suggestions
        except json.JSONDecodeError:
            return [
                {
                    "method": "five_whys",
                    "confidence": 0.7,
                    "suggestions": {
                        "fiveWhys": {
                            "suggestedQuestions": [
                                "Why did this occur?",
                                "Why wasn't it prevented?",
                            ],
                            "potentialRootCauses": ["Process gaps", "Communication issues"],
                        }
                    },
                    "reasoning": "Five Whys is a good general-purpose method",
                }
            ]

    async def generate_action_plan(
        self,
        issue: dict[str, Any],
        constraints: dict[str, Any],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate actionable plan with AI insights (Issue #64)."""
        logger.info("Generating action plan suggestions")

        if not issue.get("title") or not issue.get("description"):
            raise ValueError("Issue title and description are required")

        issue_summary = self._format_issue_for_action_plan(issue)
        constraints_summary = self._format_action_constraints(constraints)
        context_summary = self._format_action_context(context)

        prompt = f"""You are an expert project manager. Generate a comprehensive action plan.

**Issue:**
{issue_summary}

**Constraints:**
{constraints_summary}

**Context:**
{context_summary}

Generate 3-5 actions with title, description, priority, estimatedDuration, estimatedCost, assignmentSuggestion, dependencies, confidence, reasoning, expectedOutcome, risks. Format as JSON array."""

        llm_response = await self.llm_service.generate_analysis(
            analysis_prompt=prompt,
            context={"issue": issue, "constraints": constraints, "context": context},
            temperature=0.5,
        )

        try:
            response_text = llm_response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            actions = json.loads(response_text.strip())
            logger.info("Action plan generated", actions_count=len(actions))
            return actions
        except json.JSONDecodeError:
            return [
                {
                    "title": "Investigate root cause",
                    "description": "Conduct investigation",
                    "priority": "high",
                    "estimatedDuration": 16,
                    "estimatedCost": None,
                    "assignmentSuggestion": "Team lead",
                    "dependencies": [],
                    "confidence": 0.8,
                    "reasoning": "Understanding root cause is essential",
                    "expectedOutcome": "Clear identification",
                    "risks": ["May take longer"],
                },
                {
                    "title": "Implement solution",
                    "description": "Design and implement solution",
                    "priority": "high",
                    "estimatedDuration": 40,
                    "estimatedCost": None,
                    "assignmentSuggestion": "Development team",
                    "dependencies": ["Investigate root cause"],
                    "confidence": 0.75,
                    "reasoning": "Direct action to resolve",
                    "expectedOutcome": "Issue resolved",
                    "risks": ["May need iterations"],
                },
            ]

    def _format_actions_for_prompt(self, actions: list[dict[str, Any]]) -> str:
        lines = [
            f"{i}. **{a.get('title')}** (ID: {a.get('id')})\n   Description: {a.get('description', 'N/A')}\n   Priority: {a.get('priority', 'N/A')}\n   Status: {a.get('status', 'N/A')}"
            for i, a in enumerate(actions, 1)
        ]
        return "\n\n".join(lines)

    def _format_goals_for_prompt(self, goals: list[dict[str, Any]]) -> str:
        lines = [
            f"{i}. **{g.get('intent')}** (ID: {g.get('id')})\n   Strategies: {', '.join(g.get('strategies', [])) or 'None'}"
            for i, g in enumerate(goals, 1)
        ]
        return "\n\n".join(lines)

    def _format_foundation_for_prompt(self, foundation: dict[str, Any]) -> str:
        return f"- Vision: {foundation.get('vision', 'Not defined')}\n- Purpose: {foundation.get('purpose', 'Not defined')}\n- Core Values: {', '.join(foundation.get('coreValues', []))}"

    def _format_prioritization_actions(self, actions: list[dict[str, Any]]) -> str:
        lines = [
            f"{i}. **{a.get('title')}** (ID: {a.get('id')})\n   Current Priority: {a.get('currentPriority', 'N/A')}\n   Due Date: {a.get('dueDate', 'Not set')}\n   Status: {a.get('status', 'N/A')}"
            for i, a in enumerate(actions, 1)
        ]
        return "\n\n".join(lines)

    def _format_business_context(self, context: dict[str, Any]) -> str:
        return f"- Current Goals: {', '.join(context.get('currentGoals', [])) or 'Not specified'}\n- Constraints: {', '.join(context.get('constraints', [])) or 'None'}\n- Urgent Deadlines: {', '.join(context.get('urgentDeadlines', [])) or 'None'}"

    def _format_scheduling_actions(self, actions: list[dict[str, Any]]) -> str:
        lines = [
            f"{i}. **{a.get('title')}** (ID: {a.get('id')})\n   Duration: {a.get('estimatedDuration', 'N/A')} hours\n   Priority: {a.get('priority', 'N/A')}"
            for i, a in enumerate(actions, 1)
        ]
        return "\n\n".join(lines)

    def _format_constraints(self, constraints: dict[str, Any]) -> str:
        return f"- Team Capacity: {constraints.get('teamCapacity', 'N/A')} hours\n- Critical Deadlines: {len(constraints.get('criticalDeadlines', []))} deadlines"

    def _format_issue_for_root_cause(self, issue: dict[str, Any], context: dict[str, Any]) -> str:
        return f"**Title:** {issue.get('issueTitle', 'Untitled')}\n**Description:** {issue.get('issueDescription', 'No description')}\n**Impact:** {issue.get('businessImpact', 'Unknown')}"

    def _format_issue_for_action_plan(self, issue: dict[str, Any]) -> str:
        return f"**Title:** {issue.get('title', 'Untitled')}\n**Description:** {issue.get('description', 'No description')}\n**Impact:** {issue.get('impact', 'Unknown')}"

    def _format_action_constraints(self, constraints: dict[str, Any]) -> str:
        return f"- Timeline: {constraints.get('timeline', 'Not specified')}\n- Budget: ${constraints.get('budget', 0):,}"

    def _format_action_context(self, context: dict[str, Any]) -> str:
        return f"- Related Goals: {', '.join(context.get('relatedGoals', [])) or 'None'}\n- Current Actions: {', '.join(context.get('currentActions', [])) or 'None'}"


__all__ = ["OperationsAIService"]
