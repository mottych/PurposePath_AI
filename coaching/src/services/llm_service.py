"""LLM service for AI coaching interactions."""

import json
from typing import Any, Dict, List, Optional

import structlog
from coaching.src.core.constants import DEFAULT_LLM_MODELS, CoachingTopic
from coaching.src.llm.providers.manager import ProviderManager
from coaching.src.services.llm_service_adapter import LLMServiceAdapter
from coaching.src.services.prompt_service import PromptService
from coaching.src.workflows.orchestrator import WorkflowOrchestrator

from ..models.llm_models import BusinessContextForLLM, LLMResponse, SessionOutcomes

logger = structlog.get_logger()


class LLMService:
    """Service for LLM interactions with multitenant support.

    This service now uses the LLMServiceAdapter for multi-provider support
    and graceful fallback while maintaining backward compatibility.
    """

    def __init__(
        self,
        provider_manager: ProviderManager,
        workflow_orchestrator: WorkflowOrchestrator,
        prompt_service: PromptService,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        default_provider: str = "bedrock",
        fallback_providers: Optional[List[str]] = None,
    ):
        """Initialize LLM service.

        Args:
            provider_manager: Provider manager for multi-provider support
            workflow_orchestrator: Workflow orchestrator for LangGraph workflows
            prompt_service: Prompt service
            tenant_id: Tenant identifier for multitenant context
            user_id: User identifier for multitenant context
            default_provider: Default provider to use (bedrock, anthropic, openai)
            fallback_providers: List of fallback providers in priority order
        """
        self.provider_manager = provider_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.prompt_service = prompt_service
        self.tenant_id = tenant_id
        self.user_id = user_id

        # Initialize the adapter for multi-provider support
        self.adapter = LLMServiceAdapter(
            provider_manager=provider_manager,
            workflow_orchestrator=workflow_orchestrator,
            default_provider=default_provider,
            fallback_providers=fallback_providers or ["anthropic", "openai"],
        )

        logger.info(
            "LLM service initialized",
            tenant_id=tenant_id,
            user_id=user_id,
            default_provider=default_provider,
        )

    async def generate_coaching_response(
        self,
        conversation_id: str,
        topic: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        business_context: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Generate a coaching response with business context.

        Args:
            conversation_id: Conversation identifier
            topic: Coaching topic
            user_message: User's message
            conversation_history: Conversation history
            business_context: Business context for the coaching session

        Returns:
            Response dictionary with AI response and metadata
        """
        # Load prompt template
        template = await self.prompt_service.get_template(topic)

        # Get model for topic
        model_id = DEFAULT_LLM_MODELS.get(
            CoachingTopic(topic), "anthropic.claude-3-sonnet-20240229-v1:0"
        )

        # Enhance system prompt with business context
        enhanced_system_prompt = template.system_prompt
        if business_context:
            # Convert to structured business context for better handling
            business_ctx = BusinessContextForLLM.from_dict(business_context)
            context_enhancement = business_ctx.format_for_prompt()
            if context_enhancement:
                enhanced_system_prompt += context_enhancement

        # Prepare messages from conversation history
        messages = conversation_history + [{"role": "user", "content": user_message}]

        # Use adapter for multi-provider support with fallback
        adapter_response = await self.adapter.get_response(
            conversation_id=conversation_id,
            topic=topic,
            messages=messages,
            system_prompt=enhanced_system_prompt,
            model_id=model_id,
            temperature=template.llm_config.temperature,
            max_tokens=template.llm_config.max_tokens,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
        )

        # Extract response data
        response_text = adapter_response.get("response", "")
        insights = adapter_response.get("insights", [])
        token_count = adapter_response.get("token_count", 0)
        provider_used = adapter_response.get("provider", "bedrock")

        # Create structured response
        llm_response = LLMResponse(
            response=response_text,
            token_usage=token_count,
            cost=self._calculate_cost(token_count, model_id),
            model_id=model_id,
            conversation_id=conversation_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            follow_up_question=None,  # Can be extracted from insights
            insights=insights,
            is_complete=adapter_response.get("status") == "completed",
            metadata={
                "provider": provider_used,
                "workflow_id": adapter_response.get("workflow_id"),
            },
        )

        return llm_response

    async def extract_session_outcomes(
        self,
        conversation_history: List[Dict[str, str]],
        topic: str,
        ai_response: Optional[Dict[str, Any]] = None,
    ) -> SessionOutcomes:
        """Extract actionable outcomes from a completed coaching session.

        Args:
            conversation_history: Complete conversation history
            topic: Coaching topic
            ai_response: Final AI response (optional)

        Returns:
            Extracted outcomes with confidence score
        """
        try:
            # Create outcome extraction prompt
            outcome_prompt = f"""
            Based on this coaching conversation about {topic}, extract the key outcomes
            and insights that should be captured for the organization's business data.

            Return a JSON response with:
            - extracted_data: The specific data/insights to be saved
            - confidence: A confidence score from 0-1 indicating reliability
            - summary: Brief summary of the session outcomes
            - business_impact: Potential impact on business operations

            Focus on concrete, actionable insights rather than general observations.
            """

            # Prepare workflow input for analysis
            analysis_input = {
                "conversation_id": f"outcome_{conversation_history[-1].get('timestamp', 'unknown')}",
                "conversation_history": conversation_history,
                "analysis_prompt": outcome_prompt,
                "topic": f"{topic}_outcomes",
                "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "temperature": 0.3,  # Lower temperature for more consistent extraction
                "max_tokens": 1000,
                "system_prompt": "You are an expert at extracting business insights from coaching conversations.",
            }

            # Use workflow orchestrator for analysis
            from coaching.src.workflows.base import WorkflowType

            workflow_state = await self.workflow_orchestrator.start_workflow(
                workflow_type=WorkflowType.SINGLE_SHOT_ANALYSIS,
                user_id="system",  # System-level analysis
                initial_input=analysis_input,
            )

            # Extract analysis result from workflow state
            analysis_response = workflow_state.step_data.get("response", "")

            # Parse and validate the response
            if analysis_response:
                try:
                    outcomes_data = json.loads(analysis_response)

                    # Validate and create SessionOutcomes
                    if not outcomes_data.get("extracted_data") or "confidence" not in outcomes_data:
                        return SessionOutcomes.create_error("Invalid outcome format")

                    # Validate confidence score
                    confidence = float(outcomes_data.get("confidence", 0))
                    outcomes_data["confidence"] = min(max(confidence, 0.0), 1.0)

                    return SessionOutcomes.from_dict(outcomes_data)

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse outcome extraction: {e}")
                    return SessionOutcomes.create_error("Failed to parse outcomes")

            return SessionOutcomes.create_error("No outcomes extracted")

        except Exception as e:
            logger.error(f"Error extracting session outcomes: {e}")
            return SessionOutcomes.create_error(str(e))

    async def generate_single_shot_analysis(
        self,
        topic: str,
        user_input: str,
        business_context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "general",
    ) -> Dict[str, Any]:
        """Generate a single-shot analysis without conversation context.

        Args:
            topic: Coaching topic
            user_input: User's input to analyze
            business_context: Business context for the analysis
            analysis_type: Type of analysis (general, assessment, recommendation)

        Returns:
            Analysis response with insights and recommendations
        """
        try:
            # Load prompt template
            template = await self.prompt_service.get_template(topic)

            # Get model for topic
            model_id = DEFAULT_LLM_MODELS.get(
                CoachingTopic(topic), "anthropic.claude-3-sonnet-20240229-v1:0"
            )

            # Create analysis-specific system prompt
            analysis_prompt = self._create_analysis_system_prompt(
                template.system_prompt, analysis_type, business_context
            )

            # Use adapter for analysis with fallback support
            analysis_response = await self.adapter.analyze_response(
                conversation_id=f"analysis_{topic}_{analysis_type}",
                user_response=user_input,
                topic=topic,
                model_id=model_id,
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                analysis_type=analysis_type,
                system_prompt=analysis_prompt,
                temperature=template.llm_config.temperature,
                max_tokens=template.llm_config.max_tokens,
            )

            # Extract analysis data
            analysis_data = analysis_response.get("analysis", {})
            insights = analysis_response.get("insights", [])
            confidence = analysis_response.get("confidence", 0.8)

            # Create structured response
            return {
                "analysis": analysis_data,
                "insights": insights,
                "recommendations": (
                    analysis_data.get("recommendations", [])
                    if isinstance(analysis_data, dict)
                    else []
                ),
                "confidence_score": confidence,
                "analysis_type": analysis_type,
                "topic": topic,
                "token_usage": 0,  # Can be calculated if needed
                "cost": 0.0,
                "model_id": model_id,
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "provider": analysis_response.get("provider", "bedrock"),
            }

        except Exception as e:
            logger.error(f"Error generating single-shot analysis: {e}")
            return {
                "analysis": f"Error: {str(e)}",
                "insights": [],
                "recommendations": [],
                "confidence_score": 0.0,
                "analysis_type": analysis_type,
                "topic": topic,
                "error": str(e),
            }

    def _create_analysis_system_prompt(
        self,
        base_prompt: str,
        analysis_type: str,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create system prompt for single-shot analysis.

        Args:
            base_prompt: Base system prompt from template
            analysis_type: Type of analysis
            business_context: Business context for the analysis

        Returns:
            Enhanced system prompt for analysis
        """
        analysis_prompts = {
            "general": """
            Provide a comprehensive analysis of the user's input focusing on:
            1. Key themes and patterns
            2. Strengths and areas for improvement
            3. Actionable insights
            4. Specific recommendations

            Format your response as structured analysis with clear sections.
            """,
            "assessment": """
            Conduct a thorough assessment of the user's input focusing on:
            1. Current state evaluation
            2. Gap analysis
            3. Readiness indicators
            4. Development priorities

            Provide scores and specific feedback where applicable.
            """,
            "recommendation": """
            Generate specific, actionable recommendations based on the user's input:
            1. Immediate actions (next 30 days)
            2. Short-term goals (3-6 months)
            3. Long-term development (6+ months)
            4. Resources and support needed

            Prioritize recommendations by impact and feasibility.
            """,
        }

        enhanced_prompt = base_prompt
        enhanced_prompt += f"\n\nAnalysis Type: {analysis_type}\n"
        enhanced_prompt += analysis_prompts.get(analysis_type, analysis_prompts["general"])

        # Add business context if provided
        if business_context:
            business_ctx = BusinessContextForLLM.from_dict(business_context)
            context_enhancement = business_ctx.format_for_prompt()
            if context_enhancement:
                enhanced_prompt += f"\n\nBusiness Context:\n{context_enhancement}"

        return enhanced_prompt

    def _calculate_cost(self, token_count: int, model_id: str) -> float:
        """Calculate cost based on token count and model.

        Args:
            token_count: Number of tokens used
            model_id: Model identifier

        Returns:
            Estimated cost in USD
        """
        # Approximate pricing (tokens per $1)
        # These are estimates and should be updated with actual pricing
        pricing = {
            "claude-3-opus": 0.000015,  # per token
            "claude-3-sonnet": 0.000003,
            "claude-3-haiku": 0.00000025,
            "gpt-4": 0.00003,
            "gpt-3.5-turbo": 0.000002,
        }

        # Find matching model prefix
        cost_per_token = 0.000003  # default to sonnet pricing
        for model_prefix, price in pricing.items():
            if model_prefix in model_id.lower():
                cost_per_token = price
                break

        return token_count * cost_per_token

    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of the LLM service and providers.

        Returns:
            Health check results
        """
        health: Dict[str, Any] = await self.adapter.health_check()
        return health

    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all available providers.

        Returns:
            Provider availability and status information
        """
        status: Dict[str, Any] = await self.adapter.get_provider_status()
        return status
