"""Unified AI Engine - Single entry point for all AI interactions.

This module provides a unified interface for executing AI requests using
topic-driven configuration, supporting both single-shot and conversation flows.
"""

import json
import re
from typing import TYPE_CHECKING, Any

import structlog
from coaching.src.application.ai_engine.response_serializer import ResponseSerializer
from coaching.src.core.constants import CoachingTopic, MessageRole
from coaching.src.core.topic_registry import get_required_parameter_names_for_topic
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.ports.conversation_repository_port import ConversationRepositoryPort
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMProviderPort
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from coaching.src.infrastructure.llm.provider_factory import LLMProviderFactory
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from pydantic import BaseModel

if TYPE_CHECKING:
    from coaching.src.services.template_parameter_processor import TemplateParameterProcessor

logger = structlog.get_logger()


# Response format instructions template appended to system prompts
RESPONSE_FORMAT_INSTRUCTIONS = """

## Response Format Instructions

You MUST respond with valid JSON that matches this exact schema:

```json
{schema}
```

**Important:**
- Use the exact field names shown above (including camelCase where specified by "alias")
- Do not include any text before or after the JSON
- Ensure all required fields are present
- Follow any constraints (min/max length, enum values, etc.)
- For text fields with multiple sections or paragraphs, use newlines (\\n) to separate them for readability
- Preserve logical paragraph breaks in your responses using \\n characters"""


class UnifiedAIEngineError(Exception):
    """Base exception for Unified AI Engine errors."""

    def __init__(self, topic_id: str, reason: str) -> None:
        """Initialize engine error.

        Args:
            topic_id: Topic that caused the error
            reason: Error reason
        """
        self.topic_id = topic_id
        self.reason = reason
        super().__init__(f"AI Engine error for topic {topic_id}: {reason}")


class TopicNotFoundError(UnifiedAIEngineError):
    """Raised when topic is not found or inactive."""

    def __init__(self, topic_id: str) -> None:
        """Initialize topic not found error.

        Args:
            topic_id: Topic that was not found
        """
        super().__init__(topic_id, "Topic not found or inactive")


class ParameterValidationError(UnifiedAIEngineError):
    """Raised when parameters don't match topic schema."""

    def __init__(self, topic_id: str, missing_params: list[str]) -> None:
        """Initialize parameter validation error.

        Args:
            topic_id: Topic with validation error
            missing_params: List of missing required parameters
        """
        self.missing_params = missing_params
        super().__init__(topic_id, f"Missing required parameters: {', '.join(missing_params)}")


class PromptRenderError(UnifiedAIEngineError):
    """Raised when prompt rendering fails."""

    def __init__(self, topic_id: str, prompt_type: str, error: str) -> None:
        """Initialize prompt render error.

        Args:
            topic_id: Topic with render error
            prompt_type: Type of prompt that failed
            error: Error message
        """
        self.prompt_type = prompt_type
        super().__init__(topic_id, f"Failed to render {prompt_type} prompt: {error}")


class UnifiedAIEngine:
    """Unified engine for all AI interactions via topic configuration.

    This engine replaces individual service classes (AlignmentService,
    StrategyService, etc.) with a single topic-driven implementation.

    Key Features:
        - Topic-driven configuration (no hardcoded logic)
        - Support for single-shot and conversation flows
        - Automatic prompt loading from S3
        - Parameter validation against topic schema
        - Response serialization to expected models
        - Comprehensive error handling and logging

    Architecture:
        1. Load topic configuration from DynamoDB
        2. Validate request parameters against topic schema
        3. Load and render prompts from S3
        4. Execute LLM call with topic model configuration
        5. Serialize response to expected structure
        6. Return strongly-typed result
    """

    def __init__(
        self,
        *,
        topic_repo: TopicRepository,
        s3_storage: S3PromptStorage,
        provider_factory: LLMProviderFactory,
        response_serializer: ResponseSerializer,
        conversation_repo: ConversationRepositoryPort | None = None,
        llm_provider: LLMProviderPort | None = None,  # Deprecated, use provider_factory
    ) -> None:
        """Initialize unified AI engine.

        Args:
            topic_repo: Repository for topic data
            s3_storage: Storage service for prompt content
            provider_factory: Factory for creating LLM providers based on model
            response_serializer: Serializer for response formatting
            conversation_repo: Optional repository for conversation persistence
            llm_provider: DEPRECATED - use provider_factory. Kept for backward compat.
        """
        self.topic_repo = topic_repo
        self.s3_storage = s3_storage
        self.provider_factory = provider_factory
        self.response_serializer = response_serializer
        self.conversation_repo = conversation_repo
        # Support legacy llm_provider parameter for backward compatibility
        self._legacy_provider = llm_provider
        self.logger = logger.bind(service="unified_ai_engine")

    async def execute_single_shot(
        self,
        *,
        topic_id: str,
        parameters: dict[str, Any],
        response_model: type[BaseModel],
        user_id: str | None = None,
        tenant_id: str | None = None,
        template_processor: "TemplateParameterProcessor | None" = None,
    ) -> BaseModel:
        """Execute single-shot AI request using topic configuration.

        Flow:
        1. Get topic configuration from DynamoDB
        2. Load prompts from S3
        3. Enrich parameters (if template_processor is provided)
        4. Validate parameters against topic schema
        5. Render prompts with enriched parameters
        6. Call LLM using topic model config
        7. Serialize response to expected model
        8. Return typed result

        Args:
            topic_id: Topic identifier
            parameters: Request parameters to inject into prompts
            response_model: Expected response model class
            user_id: Optional user ID for parameter enrichment
            tenant_id: Optional tenant ID for parameter enrichment
            template_processor: Optional processor for automatic parameter enrichment
                (created per-request with user's JWT token for API calls)

        Returns:
            Instance of response_model with AI-generated data

        Raises:
            TopicNotFoundError: If topic doesn't exist or is inactive
            ParameterValidationError: If required parameters are missing
            PromptRenderError: If prompt rendering fails
            SerializationError: If response serialization fails
        """
        self.logger.info(
            "Executing single-shot AI request",
            topic_id=topic_id,
            response_model=response_model.__name__,
            param_count=len(parameters),
        )

        # Step 1: Get topic configuration
        topic = await self._get_active_topic(topic_id)

        # Step 2: Load prompts from S3
        system_prompt_content = await self._load_prompt(topic, "system")
        user_prompt_content = await self._load_prompt(topic, "user")

        # Step 3: Enrich parameters if template processor is provided
        enriched_params = await self._enrich_parameters(
            parameters=parameters,
            system_prompt=system_prompt_content,
            user_prompt=user_prompt_content,
            topic=topic,
            user_id=str(user_id or parameters.get("user_id", "")),
            tenant_id=str(tenant_id or parameters.get("tenant_id", "")),
            template_processor=template_processor,
        )

        # Step 4: Validate parameters (after enrichment)
        self._validate_parameters(topic, enriched_params)

        # Step 5: Render prompts with enriched parameters
        rendered_system = self._render_prompt(
            topic_id, "system", system_prompt_content, enriched_params
        )
        rendered_user = self._render_prompt(topic_id, "user", user_prompt_content, enriched_params)

        # Step 5.5: Inject response format instructions into system prompt
        # Also get the JSON schema for structured output providers (OpenAI)
        rendered_system, response_schema = self._inject_response_format_with_schema(
            rendered_system, response_model
        )

        # Step 6: Get provider and resolved model name from factory
        provider, model_name = self.provider_factory.get_provider_for_model(topic.model_code)

        # Step 7: Call LLM with topic configuration
        messages = [LLMMessage(role="user", content=rendered_user)]

        llm_response = await provider.generate(
            messages=messages,
            model=model_name,  # Use resolved model name, not model code
            temperature=topic.temperature,
            max_tokens=topic.max_tokens,
            system_prompt=rendered_system,
            response_schema=response_schema,  # Pass schema for structured output
        )

        self.logger.info(
            "LLM generation completed",
            topic_id=topic_id,
            model=llm_response.model,
            tokens_used=llm_response.usage.get("total_tokens", 0),
            finish_reason=llm_response.finish_reason,
        )

        # Step 7: Serialize response
        result = await self.response_serializer.serialize(
            ai_response=llm_response.content,
            response_model=response_model,
            topic_id=topic_id,
        )

        self.logger.info(
            "Single-shot execution completed",
            topic_id=topic_id,
            result_type=type(result).__name__,
        )

        return result

    async def _enrich_parameters(
        self,
        *,
        parameters: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        topic: LLMTopic,
        user_id: str,
        tenant_id: str,
        template_processor: "TemplateParameterProcessor | None" = None,
    ) -> dict[str, Any]:
        """Enrich parameters by fetching missing values via retrieval methods.

        If template_processor is not provided, returns parameters unchanged.
        Otherwise, analyzes templates to find needed parameters and enriches
        any that are missing from the provided parameters.

        Args:
            parameters: Original request parameters
            system_prompt: System prompt template
            user_prompt: User prompt template
            topic: Topic configuration (for required params info)
            user_id: User ID for API calls
            tenant_id: Tenant ID for API calls
            template_processor: Optional processor for parameter enrichment

        Returns:
            Enriched parameters dictionary
        """
        if template_processor is None:
            # No enrichment - return original parameters
            return parameters

        # Combine both templates for parameter detection
        combined_template = f"{system_prompt}\n{user_prompt}"

        # Get required parameter names from endpoint registry
        required_params = get_required_parameter_names_for_topic(topic.topic_id)

        self.logger.debug(
            "Enriching parameters",
            topic_id=topic.topic_id,
            required_params=list(required_params),
            provided_params=list(parameters.keys()),
        )

        # Process templates and enrich missing parameters
        result = await template_processor.process_template_parameters(
            template=combined_template,
            payload=parameters,
            user_id=user_id,
            tenant_id=tenant_id,
            required_params=required_params,
        )

        # Log any warnings
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(
                    "Parameter enrichment warning",
                    topic_id=topic.topic_id,
                    warning=warning,
                )

        # Check for missing required params
        if result.missing_required:
            self.logger.error(
                "Required parameters could not be resolved",
                topic_id=topic.topic_id,
                missing=result.missing_required,
            )
            raise ParameterValidationError(topic.topic_id, result.missing_required)

        # Merge enriched params with original (original takes precedence)
        enriched = {**result.parameters, **parameters}

        self.logger.info(
            "Parameter enrichment completed",
            topic_id=topic.topic_id,
            original_count=len(parameters),
            enriched_count=len(enriched),
            added_count=len(enriched) - len(parameters),
        )

        return enriched

    async def _get_active_topic(self, topic_id: str) -> LLMTopic:
        """Get topic and verify it's active.

        Args:
            topic_id: Topic identifier

        Returns:
            Active LLMTopic entity

        Raises:
            TopicNotFoundError: If topic not found or inactive
        """
        topic = await self.topic_repo.get(topic_id=topic_id)

        if topic is None:
            self.logger.error("Topic not found", topic_id=topic_id)
            raise TopicNotFoundError(topic_id)

        if not topic.is_active:
            self.logger.error("Topic is inactive", topic_id=topic_id)
            raise TopicNotFoundError(topic_id)

        return topic

    def _validate_parameters(self, topic: LLMTopic, parameters: dict[str, Any]) -> None:
        """Validate request parameters against topic schema.

        Uses endpoint registry to determine required parameters.

        Args:
            topic: Topic with parameter definitions
            parameters: Request parameters to validate

        Raises:
            ParameterValidationError: If required parameters are missing
        """
        # Get required parameters from endpoint registry
        required_params = get_required_parameter_names_for_topic(topic.topic_id)
        missing_params = [name for name in required_params if name not in parameters]

        if missing_params:
            self.logger.error(
                "Parameter validation failed",
                topic_id=topic.topic_id,
                missing_params=missing_params,
            )
            raise ParameterValidationError(topic.topic_id, missing_params)

        self.logger.debug(
            "Parameter validation passed",
            topic_id=topic.topic_id,
            param_count=len(parameters),
        )

    async def _load_prompt(self, topic: LLMTopic, prompt_type: str) -> str:
        """Load prompt content from S3.

        Args:
            topic: Topic with prompt information
            prompt_type: Type of prompt (system, user, assistant)

        Returns:
            Prompt content

        Raises:
            PromptRenderError: If prompt not found
        """
        prompt_content = await self.s3_storage.get_prompt(
            topic_id=topic.topic_id,
            prompt_type=prompt_type,
        )

        if prompt_content is None:
            self.logger.error(
                "Prompt not found",
                topic_id=topic.topic_id,
                prompt_type=prompt_type,
            )
            raise PromptRenderError(topic.topic_id, prompt_type, "Prompt not found in S3")

        return prompt_content

    def _render_prompt(
        self,
        topic_id: str,
        prompt_type: str,
        template: str,
        parameters: dict[str, Any],
    ) -> str:
        """Render prompt template with parameters.

        Uses Python string formatting with named placeholders.

        Args:
            topic_id: Topic identifier for logging
            prompt_type: Type of prompt for logging
            template: Prompt template with {variable} placeholders
            parameters: Parameters to inject

        Returns:
            Rendered prompt string

        Raises:
            PromptRenderError: If rendering fails
        """
        try:
            # Use safe_substitute to avoid KeyError for missing keys
            # Convert all parameter values to strings for template rendering
            safe_params = {
                k: str(v) if not isinstance(v, dict | list) else str(v)
                for k, v in parameters.items()
            }

            # Support both Jinja2-style {{param}} and Python-style {param}
            rendered = self._substitute_template_params(template, safe_params)

            self.logger.debug(
                "Prompt rendered",
                topic_id=topic_id,
                prompt_type=prompt_type,
                template_length=len(template),
                rendered_length=len(rendered),
            )

            return rendered

        except KeyError as e:
            error_msg = f"Missing template variable: {e}"
            self.logger.error(
                "Prompt rendering failed",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=error_msg,
            )
            raise PromptRenderError(topic_id, prompt_type, error_msg) from e

        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                "Unexpected error during prompt rendering",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=error_msg,
                exc_info=True,
            )
            raise PromptRenderError(topic_id, prompt_type, error_msg) from e

    def _substitute_template_params(
        self,
        template: str,
        params: dict[str, str],
    ) -> str:
        """Substitute parameters into template with support for both brace styles.

        Supports:
        - Jinja2-style: {{param_name}} -> value
        - Python-style: {param_name} -> value (backward compatibility)

        Args:
            template: Template string with placeholders
            params: Parameter name to value mapping

        Returns:
            Template with all placeholders substituted
        """
        result = template

        # First, substitute Jinja2-style double braces {{param}}
        for name, value in params.items():
            result = result.replace(f"{{{{{name}}}}}", value)

        # Then, substitute Python-style single braces {param}
        # Use regex to avoid matching {{escaped}} patterns
        for name, value in params.items():
            # Match {name} but not {{name}}
            pattern = r"(?<!\{)\{" + re.escape(name) + r"\}(?!\})"
            result = re.sub(pattern, value.replace("\\", "\\\\"), result)

        return result

    def _inject_response_format_with_schema(
        self,
        system_prompt: str,
        response_model: type[BaseModel],
    ) -> tuple[str, dict[str, Any] | None]:
        """Inject JSON response format instructions and return schema for structured output.

        Appends structured format instructions based on the response model's
        JSON schema, ensuring the LLM knows exactly what structure to return.
        Also returns the full schema for providers that support structured output.

        Args:
            system_prompt: Rendered system prompt
            response_model: Target response model class

        Returns:
            Tuple of (updated system prompt, JSON schema for structured output)
        """
        try:
            # Get full schema for structured output (OpenAI Responses API)
            full_schema = response_model.model_json_schema()

            # Prepare schema for OpenAI structured output (needs specific format)
            structured_schema = self._prepare_schema_for_structured_output(
                full_schema, response_model.__name__
            )

            # Create a simplified schema for the prompt (remove internal details)
            simplified = self._simplify_schema_for_prompt(full_schema)

            # Format as pretty JSON
            schema_json = json.dumps(simplified, indent=2)

            # Append format instructions to system prompt
            format_instructions = RESPONSE_FORMAT_INSTRUCTIONS.format(schema=schema_json)

            self.logger.debug(
                "Injected response format instructions with schema",
                response_model=response_model.__name__,
                schema_size=len(schema_json),
                has_structured_schema=structured_schema is not None,
            )

            return system_prompt + format_instructions, structured_schema

        except Exception as e:
            # If schema generation fails, log warning but don't fail the request
            self.logger.warning(
                "Failed to inject response format instructions",
                response_model=response_model.__name__,
                error=str(e),
            )
            return system_prompt, None

    def _prepare_schema_for_structured_output(
        self,
        schema: dict[str, Any],
        model_name: str,
    ) -> dict[str, Any]:
        """Prepare JSON schema for OpenAI structured output format.

        OpenAI's structured output requires a specific schema format with
        additionalProperties set to false for strict validation.

        Args:
            schema: Pydantic JSON schema
            model_name: Name of the response model

        Returns:
            Schema prepared for OpenAI structured output
        """
        # Create a copy to avoid modifying the original
        prepared = dict(schema)

        # Ensure title is set
        if "title" not in prepared:
            prepared["title"] = model_name

        # Add additionalProperties: false for strict mode
        prepared["additionalProperties"] = False

        # Recursively add additionalProperties to nested objects
        self._add_additional_properties_false(prepared)

        return prepared

    def _add_additional_properties_false(self, schema: dict[str, Any]) -> None:
        """Recursively add additionalProperties: false to all object schemas.

        Args:
            schema: JSON schema dict to modify in place
        """
        if schema.get("type") == "object":
            schema["additionalProperties"] = False
            for prop in schema.get("properties", {}).values():
                self._add_additional_properties_false(prop)

        # Handle $defs (nested model definitions)
        for definition in schema.get("$defs", {}).values():
            self._add_additional_properties_false(definition)

        # Handle items in arrays
        if "items" in schema:
            self._add_additional_properties_false(schema["items"])

        # Handle anyOf/oneOf/allOf
        for key in ["anyOf", "oneOf", "allOf"]:
            if key in schema:
                for item in schema[key]:
                    self._add_additional_properties_false(item)

    def _inject_response_format(
        self,
        system_prompt: str,
        response_model: type[BaseModel],
    ) -> str:
        """Inject JSON response format instructions into system prompt.

        DEPRECATED: Use _inject_response_format_with_schema instead.

        Appends structured format instructions based on the response model's
        JSON schema, ensuring the LLM knows exactly what structure to return.

        Args:
            system_prompt: Rendered system prompt
            response_model: Target response model class

        Returns:
            System prompt with appended format instructions
        """
        result, _ = self._inject_response_format_with_schema(system_prompt, response_model)
        return result

    def _simplify_schema_for_prompt(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Simplify JSON schema for LLM prompt injection.

        Removes internal Pydantic details and creates a cleaner schema
        that's easier for the LLM to understand.

        Args:
            schema: Full Pydantic JSON schema

        Returns:
            Simplified schema dict
        """
        result: dict[str, Any] = {}

        # Include title if present
        if "title" in schema:
            result["title"] = schema["title"]

        # Process properties
        if "properties" in schema:
            result["properties"] = {}
            for name, prop in schema["properties"].items():
                simplified_prop: dict[str, Any] = {}

                # Include type
                if "type" in prop:
                    simplified_prop["type"] = prop["type"]
                elif "anyOf" in prop:
                    # Handle Optional types
                    types = [t.get("type") for t in prop["anyOf"] if "type" in t]
                    simplified_prop["type"] = types[0] if types else "any"

                # Include description
                if "description" in prop:
                    simplified_prop["description"] = prop["description"]

                # Include constraints
                for constraint in [
                    "minLength",
                    "maxLength",
                    "minimum",
                    "maximum",
                    "minItems",
                    "maxItems",
                    "enum",
                ]:
                    if constraint in prop:
                        simplified_prop[constraint] = prop[constraint]

                # Handle array items
                if prop.get("type") == "array" and "items" in prop:
                    items = prop["items"]
                    if "$ref" in items:
                        # Resolve reference from $defs
                        ref_name = items["$ref"].split("/")[-1]
                        if "$defs" in schema and ref_name in schema["$defs"]:
                            simplified_prop["items"] = self._simplify_schema_for_prompt(
                                schema["$defs"][ref_name]
                            )
                    else:
                        simplified_prop["items"] = self._simplify_schema_for_prompt(items)

                result["properties"][name] = simplified_prop

        # Include required fields
        if "required" in schema:
            result["required"] = schema["required"]

        return result

    # ========== Conversation Methods ==========

    async def get_initial_prompt(self, topic_id: str) -> str:
        """Get initial prompt (system prompt) for a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            System prompt content

        Raises:
            TopicNotFoundError: If topic doesn't exist
            PromptRenderError: If prompt not found
        """
        topic = await self._get_active_topic(topic_id)
        return await self._load_prompt(topic, "system")

    async def initiate_conversation(
        self,
        *,
        topic_id: str,
        user_id: UserId,
        tenant_id: TenantId,
        initial_parameters: dict[str, Any] | None = None,
    ) -> Conversation:
        """Initiate a new coaching conversation using topic configuration.

        Args:
            topic_id: Topic identifier for conversation
            user_id: User initiating the conversation
            tenant_id: Tenant identifier for multi-tenancy
            initial_parameters: Optional initial context parameters

        Returns:
            Created Conversation entity

        Raises:
            TopicNotFoundError: If topic doesn't exist or is inactive
            UnifiedAIEngineError: If conversation creation fails
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError(topic_id, "Conversation repository not configured")

        self.logger.info(
            "Initiating conversation",
            topic_id=topic_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        # Get topic configuration
        topic = await self._get_active_topic(topic_id)

        # Verify topic type supports conversations
        if topic.topic_type != "conversation_coaching":
            raise UnifiedAIEngineError(
                topic_id,
                f"Topic type '{topic.topic_type}' does not support conversations",
            )

        # Create conversation entity
        from coaching.src.core.types import create_conversation_id

        conversation_id = create_conversation_id()

        # Convert initial parameters to context if provided
        context = ConversationContext()
        if initial_parameters:
            # Map known fields if they exist in initial_parameters
            # This is a simplified mapping, might need adjustment based on actual usage
            context = ConversationContext(metadata=initial_parameters)

        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            tenant_id=tenant_id,
            topic=CoachingTopic(topic_id),
            messages=[],
            context=context,
        )

        # Save conversation
        await self.conversation_repo.save(conversation)

        self.logger.info(
            "Conversation initiated",
            conversation_id=conversation_id,
            topic_id=topic_id,
        )

        return conversation

    async def send_message(
        self,
        *,
        conversation_id: ConversationId,
        user_message: str,
        tenant_id: TenantId,
    ) -> dict[str, Any]:
        """Send message in existing conversation.

        Args:
            conversation_id: Conversation identifier
            user_message: User's message content
            tenant_id: Tenant identifier for isolation

        Returns:
            Dictionary with AI response and conversation state

        Raises:
            UnifiedAIEngineError: If conversation not found or send fails
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        self.logger.info(
            "Sending message",
            conversation_id=conversation_id,
            message_length=len(user_message),
        )

        # Load conversation
        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        # Get topic
        topic = await self._get_active_topic(conversation.topic)

        # Build conversation history for context
        messages = self._build_message_history(conversation, user_message)

        # Load system prompt
        system_prompt_content = await self._load_prompt(topic, "system")
        rendered_system = self._render_prompt(
            conversation.topic,
            "system",
            system_prompt_content,
            conversation.context.model_dump(),
        )

        # Get provider and resolved model name from factory
        provider, model_name = self.provider_factory.get_provider_for_model(topic.model_code)

        # Call LLM with resolved model name
        llm_response = await provider.generate(
            messages=messages,
            model=model_name,  # Use resolved model name, not model code
            temperature=topic.temperature,
            max_tokens=topic.max_tokens,
            system_prompt=rendered_system,
        )

        # Serialize conversation response
        response_data = await self.response_serializer.serialize_conversation(
            ai_response=llm_response.content,
            topic=topic,
        )

        # Update conversation with messages
        conversation.add_message(role=MessageRole.USER, content=user_message)
        conversation.add_message(role=MessageRole.ASSISTANT, content=llm_response.content)

        # Save updated conversation
        await self.conversation_repo.save(conversation)

        self.logger.info(
            "Message sent successfully",
            conversation_id=conversation_id,
            response_length=len(llm_response.content),
        )

        return response_data

    async def pause_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> None:
        """Pause conversation (save state).

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.mark_paused()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation paused", conversation_id=conversation_id)

    async def resume_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> Conversation:
        """Resume paused conversation.

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Resumed Conversation entity

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.resume()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation resumed", conversation_id=conversation_id)

        return conversation

    async def complete_conversation(
        self,
        *,
        conversation_id: ConversationId,
        tenant_id: TenantId,
    ) -> Conversation:
        """Mark conversation as complete.

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Completed Conversation entity

        Raises:
            UnifiedAIEngineError: If conversation not found
        """
        if self.conversation_repo is None:
            raise UnifiedAIEngineError("unknown", "Conversation repository not configured")

        conversation = await self.conversation_repo.get_by_id(conversation_id, tenant_id)
        if conversation is None:
            raise UnifiedAIEngineError("unknown", f"Conversation {conversation_id} not found")

        conversation.mark_completed()
        await self.conversation_repo.save(conversation)

        self.logger.info("Conversation completed", conversation_id=conversation_id)

        return conversation

    def _build_message_history(
        self, conversation: Conversation, new_message: str
    ) -> list[LLMMessage]:
        """Build message history for LLM context.

        Args:
            conversation: Conversation entity with history
            new_message: New user message to add

        Returns:
            List of LLM messages including history and new message
        """
        messages = []

        # Add conversation history (limit to recent messages for context window)
        max_history = 10  # Configurable based on model context window
        recent_messages = conversation.messages[-max_history:]

        for msg in recent_messages:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        # Add new user message
        messages.append(LLMMessage(role="user", content=new_message))

        return messages


__all__ = [
    "ParameterValidationError",
    "PromptRenderError",
    "TopicNotFoundError",
    "UnifiedAIEngine",
    "UnifiedAIEngineError",
]
