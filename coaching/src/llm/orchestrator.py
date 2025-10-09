"""LLM orchestrator for managing multiple providers and conversations.

NOTE: This orchestrator is being phased out in favor of the new LLMServiceAdapter
from Issue #82. The adapter provides multi-provider support with fallback capabilities
while maintaining backward compatibility.

This module is kept for legacy compatibility but new code should use the adapter.
"""

from typing import Any, Dict, List, Optional

import structlog
from coaching.src.core.constants import DEFAULT_LLM_MODELS
from coaching.src.llm.memory import ConversationMemory
from coaching.src.llm.providers.base import LLMProvider
from coaching.src.llm.providers.bedrock import BedrockProvider
from coaching.src.services.cache_service import CacheService

logger = structlog.get_logger()


class LLMOrchestrator:
    """Orchestrates LLM interactions across providers.

    DEPRECATED: This class is maintained for backward compatibility.
    New implementations should use LLMServiceAdapter from Issue #82
    which provides enhanced multi-provider support and fallback mechanisms.
    """

    def __init__(
        self,
        bedrock_client: Any,
        cache_service: CacheService,
        default_model: Optional[str] = None,
        provider_manager: Optional[Any] = None,
    ):
        """Initialize LLM orchestrator.

        Args:
            bedrock_client: AWS Bedrock client
            cache_service: Cache service for memory management
            default_model: Default model to use
            provider_manager: Optional provider manager for multi-provider support (Issue #82)
        """
        self.bedrock_client = bedrock_client
        self.cache_service = cache_service
        self.default_model = default_model or "anthropic.claude-3-sonnet-20240229-v1:0"
        self.provider_manager = provider_manager

        # Initialize providers
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

        # Memory store for active conversations
        self.memory_store: Dict[str, ConversationMemory] = {}

        logger.info(
            "LLMOrchestrator initialized",
            default_model=self.default_model,
            has_provider_manager=provider_manager is not None,
        )

    def _initialize_providers(self) -> None:
        """Initialize available LLM providers."""
        # Initialize Bedrock providers for different models
        for topic, model_id in DEFAULT_LLM_MODELS.items():
            provider_key = f"bedrock_{model_id}"
            if provider_key not in self.providers:
                self.providers[provider_key] = BedrockProvider(
                    client=self.bedrock_client, model_id=model_id
                )

    def get_provider(self, model_id: Optional[str] = None) -> LLMProvider:
        """Get LLM provider for a specific model.

        Args:
            model_id: Model identifier

        Returns:
            LLM provider instance
        """
        model_id = model_id or self.default_model
        provider_key = f"bedrock_{model_id}"

        if provider_key not in self.providers:
            self.providers[provider_key] = BedrockProvider(
                client=self.bedrock_client, model_id=model_id
            )

        return self.providers[provider_key]

    async def get_response(
        self,
        conversation_id: str,
        topic: str,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Get LLM response for a conversation.

        Args:
            conversation_id: Conversation identifier
            topic: Coaching topic
            messages: Conversation messages
            system_prompt: System prompt
            model_id: Optional model override
            **kwargs: Additional parameters

        Returns:
            Response dictionary with content and metadata
        """
        # Get or create memory for conversation
        memory = await self.get_conversation_memory(conversation_id)

        # Add messages to memory
        for msg in messages[-2:]:  # Only add recent messages to avoid duplication
            if msg not in memory.messages:
                memory.add_message(msg["role"], msg["content"])

        # Get provider
        provider = self.get_provider(model_id)

        # Prepare messages with memory context
        contextualized_messages = self._prepare_messages_with_context(
            messages, memory, system_prompt
        )

        # Generate response
        response_text = await provider.generate_response(
            messages=contextualized_messages, system_prompt=system_prompt, **kwargs
        )

        # Add response to memory
        memory.add_message("assistant", response_text)

        # Save memory to cache
        await self.save_conversation_memory(conversation_id, memory)

        # Extract insights if needed
        insights = await self.extract_insights(response_text, topic, provider)

        return {
            "response": response_text,
            "insights": insights,
            "memory_summary": memory.get_summary(),
            "token_count": provider.count_tokens(response_text),
        }

    async def analyze_response(
        self, conversation_id: str, user_response: str, topic: str, model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a user response for insights.

        Args:
            conversation_id: Conversation identifier
            user_response: User's response text
            topic: Coaching topic
            model_id: Optional model override

        Returns:
            Analysis results
        """
        provider = self.get_provider(model_id)

        # Create analysis prompt based on topic
        analysis_prompt = self._create_analysis_prompt(topic)

        # Analyze response
        analysis: Dict[str, Any] = await provider.analyze_text(
            text=user_response, analysis_prompt=analysis_prompt
        )

        return analysis

    async def get_conversation_memory(self, conversation_id: str) -> ConversationMemory:
        """Get or create conversation memory.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation memory instance
        """
        # Check in-memory store first
        if conversation_id in self.memory_store:
            return self.memory_store[conversation_id]

        # Try to load from cache
        cached_memory = await self.cache_service.get_conversation_memory(conversation_id)

        if cached_memory:
            memory = ConversationMemory.from_dict(cached_memory)
        else:
            memory = ConversationMemory(max_token_limit=4000)

        self.memory_store[conversation_id] = memory
        return memory

    async def save_conversation_memory(
        self, conversation_id: str, memory: ConversationMemory
    ) -> None:
        """Save conversation memory to cache.

        Args:
            conversation_id: Conversation identifier
            memory: Conversation memory instance
        """
        await self.cache_service.save_conversation_memory(conversation_id, memory.to_dict())

    def _prepare_messages_with_context(
        self, messages: List[Dict[str, str]], memory: ConversationMemory, system_prompt: str
    ) -> List[Dict[str, str]]:
        """Prepare messages with memory context."""
        context = memory.get_context()
        enhanced_prompt = system_prompt
        if context:
            enhanced_prompt = f"{system_prompt}\n\nConversation Context:\n{context}"

        messages_with_context: List[Dict[str, str]] = memory.get_messages_for_llm()
        if messages_with_context:
            first_message = messages_with_context[0]
            if first_message.get("role") == "system":
                first_message["content"] = enhanced_prompt
            else:
                messages_with_context.insert(0, {"role": "system", "content": enhanced_prompt})
        else:
            messages_with_context = [{"role": "system", "content": enhanced_prompt}]

        messages_with_context.extend(messages)
        return messages_with_context

    def _create_analysis_prompt(self, topic: str) -> str:
        """Create analysis prompt based on topic.

        Args:
            topic: Coaching topic

        Returns:
            Analysis prompt
        """
        prompts = {
            "core_values": """
                Analyze this response for:
                1. Key themes or values expressed
                2. Emotional indicators
                3. Patterns or contradictions
                4. Areas requiring clarification

                Return as JSON with keys: themes, emotions, patterns, clarifications
            """,
            "purpose": """
                Analyze this response for:
                1. Passion indicators
                2. Impact orientation
                3. Personal meaning markers
                4. Alignment with values

                Return as JSON with keys: passions, impact, meaning, alignment
            """,
            "vision": """
                Analyze this response for:
                1. Future orientation
                2. Specificity level
                3. Ambition indicators
                4. Feasibility markers

                Return as JSON with keys: future_focus, specificity, ambition, feasibility
            """,
            "goals": """
                Analyze this response for:
                1. SMART criteria presence
                2. Priority indicators
                3. Resource requirements
                4. Potential obstacles

                Return as JSON with keys: smart_criteria, priorities, resources, obstacles
            """,
        }

        return prompts.get(topic, prompts["core_values"])

    async def extract_insights(self, response: str, topic: str, provider: LLMProvider) -> List[str]:
        """Extract key insights from a response.

        Args:
            response: Response text
            topic: Coaching topic
            provider: LLM provider

        Returns:
            List of insights
        """
        # Simple insight extraction for now
        insights = []

        # Look for key phrases that indicate insights
        insight_markers = [
            "I notice that",
            "It seems like",
            "This suggests",
            "You appear to",
            "Your response indicates",
        ]

        for marker in insight_markers:
            if marker.lower() in response.lower():
                # Extract the sentence containing the marker
                sentences = response.split(".")
                for sentence in sentences:
                    if marker.lower() in sentence.lower():
                        insights.append(sentence.strip())
                        break

        return insights[:5]  # Limit to 5 insights
