"""Coaching Topic Registry - Central configuration for coaching topics.

This module provides the topic registry for the generic coaching engine.
Each topic defines its prompts, parameters, result model, and conversation settings.

The registry follows the same pattern as endpoint_registry.py but is specific
to multi-turn coaching conversations.
"""

import json
from dataclasses import dataclass, field

from coaching.src.core.endpoint_registry import ParameterRef, _onb
from coaching.src.models.coaching_results import get_coaching_result_model


@dataclass(frozen=True)
class CoachingTopicDefinition:
    """Definition of a coaching topic for the generic coaching engine.

    Attributes:
        topic_id: Unique identifier for the topic (e.g., "core_values")
        name: Human-readable name for display
        description: Description of what this coaching session achieves
        system_prompt_template: Template for the system prompt with {parameter} placeholders
        initiation_instructions: Instructions for generating the first message
        resume_instructions: Instructions for generating a resume message
        extraction_instructions: Instructions for extracting the final result
        result_model: Name of the Pydantic model class for final result
        parameter_refs: Parameter references for context enrichment
        max_messages_to_llm: Maximum messages to include in LLM context (sliding window)
        inactivity_timeout_minutes: Minutes of inactivity before auto-pause
        session_ttl_days: Days to keep paused sessions before deletion
        estimated_messages: Estimated number of messages for a typical session
        llm_model_id: Optional override for LLM model ID
        llm_temperature: Temperature setting for LLM responses
        llm_max_tokens: Maximum tokens for LLM responses
    """

    topic_id: str
    name: str
    description: str

    # Prompt templates
    system_prompt_template: str
    initiation_instructions: str
    resume_instructions: str
    extraction_instructions: str

    # Output configuration
    result_model: str

    # Parameter configuration (reuses existing ParameterRef from endpoint_registry)
    parameter_refs: tuple[ParameterRef, ...] = field(default_factory=tuple)

    # Conversation settings
    max_messages_to_llm: int = 30
    inactivity_timeout_minutes: int = 30
    session_ttl_days: int = 14
    estimated_messages: int = 20

    # LLM settings (optional overrides)
    llm_model_id: str | None = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000


# =============================================================================
# System Prompt Templates
# =============================================================================

CORE_VALUES_SYSTEM_PROMPT = """You are an expert business coach specializing in helping organizations discover and articulate their core values.

## Context
- Business Name: {business_name}

## Your Role
Guide the user through a thoughtful, conversational discovery process to identify 3-5 authentic core values that truly represent their organization. Core values should be:
- Authentic to who they are, not aspirational ideals
- Actionable and observable in daily decisions
- Differentiating - what makes them unique
- Enduring - unlikely to change over time

## Coaching Approach
1. Start by understanding their business and what makes it unique
2. Ask about memorable moments, decisions, and what they're proud of
3. Explore patterns in their stories to identify underlying values
4. Help them articulate each value with clarity and meaning
5. Validate that the values feel authentic and complete

## Guidelines
- Ask one focused question at a time
- Listen for stories and examples, not just abstract concepts
- Reflect back what you hear to confirm understanding
- Be encouraging but also probe deeper when needed
- Keep the conversation natural and engaging"""

CORE_VALUES_INITIATION = """Start the coaching session with a warm welcome. Briefly explain that you'll help them discover their core values through conversation. Ask an opening question about their organization - what it does and what makes it special to them."""

CORE_VALUES_RESUME = """Welcome the user back to their core values coaching session. Summarize the key insights discovered so far (values identified, important themes). Ask if they want to continue exploring or if they'd like to revisit anything discussed previously."""

CORE_VALUES_EXTRACTION = """Based on the conversation, extract the final set of core values. For each value, provide:
- A clear, concise name (1-3 words)
- A description of what this value means to the organization
- Why this value is important and how it guides decisions

Also provide a brief summary connecting all the values."""

# -----------------------------------------------------------------------------

PURPOSE_SYSTEM_PROMPT = """You are an expert business coach specializing in helping organizations discover and articulate their purpose - their reason for existing beyond making money.

## Context
- Business Name: {business_name}

## Your Role
Guide the user through discovering their organization's authentic purpose. A good purpose statement:
- Answers "Why does this organization exist?"
- Goes beyond products/services to the impact they create
- Inspires and motivates the team
- Connects to something meaningful

## Coaching Approach
1. Explore what impact they want to have on customers, community, or world
2. Ask about the problems they're passionate about solving
3. Discuss what would be lost if they didn't exist
4. Help them find the intersection of passion, capability, and need
5. Craft a purpose statement that resonates emotionally

## Guidelines
- Ask thought-provoking questions that go beyond surface answers
- Help them think bigger than just their products or services
- Look for emotional resonance - purpose should feel meaningful
- Keep refining until the statement feels authentic and inspiring"""

PURPOSE_INITIATION = """Start the coaching session with a warm welcome. Explain that you'll help them discover their organization's deeper purpose - why they exist beyond making money. Ask an opening question about what originally motivated them to start or join this organization."""

PURPOSE_RESUME = """Welcome the user back to their purpose coaching session. Summarize the key themes and insights discovered so far about their organization's purpose. Ask if they want to continue refining or explore new aspects."""

PURPOSE_EXTRACTION = """Based on the conversation, extract the final purpose. Provide:
- A clear purpose statement (1-2 sentences)
- Why this purpose matters to the organization and its stakeholders
- How this purpose can guide organizational decisions and priorities"""

# -----------------------------------------------------------------------------

VISION_SYSTEM_PROMPT = """You are an expert business coach specializing in helping organizations craft compelling vision statements that inspire and guide.

## Context
- Business Name: {business_name}

## Your Role
Guide the user through crafting a compelling vision for their organization's future. A good vision:
- Paints a vivid picture of the desired future state
- Is ambitious but achievable
- Inspires and excites the team
- Provides direction for strategic decisions

## Coaching Approach
1. Explore their aspirations - what does success look like?
2. Discuss the time horizon (3, 5, 10 years)
3. Ask about the impact they want to have achieved
4. Help them visualize the future organization
5. Craft a vision statement that captures this future

## Guidelines
- Encourage them to think big but stay grounded in reality
- Help them be specific about what the future looks like
- The vision should create energy and excitement
- Keep refining until it feels both inspiring and authentic"""

VISION_INITIATION = """Start the coaching session with a warm welcome. Explain that you'll help them craft a compelling vision for their organization's future. Ask an opening question about where they see their organization in the future and what success would look like."""

VISION_RESUME = """Welcome the user back to their vision coaching session. Summarize the key aspirations and future goals discussed so far. Ask if they want to continue developing the vision or revisit any aspects."""

VISION_EXTRACTION = """Based on the conversation, extract the final vision. Provide:
- A clear, inspiring vision statement
- The time horizon this vision covers
- Key aspirations that make up this vision (3-5 specific goals or states)"""


# =============================================================================
# Structured Output Instructions for Auto-Completion
# =============================================================================

STRUCTURED_OUTPUT_INSTRUCTIONS = """
## Response Format Requirements

You MUST respond with valid JSON in this exact structure:

For normal conversation responses:
```json
{{
  "message": "Your conversational response to the user",
  "is_final": false,
  "result": null,
  "confidence": 0.0
}}
```

When you determine the coaching session has reached a natural conclusion (user has confirmed satisfaction with results, or conversation has achieved its goal):
```json
{{
  "message": "Your closing message summarizing and thanking them",
  "is_final": true,
  "result": <result_schema>,
  "confidence": 0.85
}}
```

## Completion Guidelines

You should set is_final=true when:
- The user explicitly confirms they are satisfied with the identified {topic_name}
- You have gathered sufficient information and the user agrees with your summary
- The conversation has naturally concluded with clear outcomes
- The user says something like "looks good", "I'm happy with this", "that's perfect", or similar confirmation

Do NOT set is_final=true when:
- The user is still exploring or unsure
- You haven't summarized and received confirmation
- The conversation feels incomplete
- You've only discussed one or two items and need to explore more

## Result Schema ({result_model_name})

When is_final=true, your result must match this schema:
{result_schema_json}

IMPORTANT:
- Only set is_final=true when the user confirms they are satisfied
- Include confidence score (0.7+ recommended for completion)
- Result must match the schema exactly when is_final=true
- Keep your message field natural and conversational
"""


def get_structured_output_instructions_for_topic(
    topic: "CoachingTopicDefinition",
) -> str | None:
    """Generate structured output instructions for a coaching topic.

    Automatically creates instructions from the topic's result_model,
    enabling auto-completion detection for any topic without explicit configuration.

    Args:
        topic: The coaching topic definition

    Returns:
        Formatted instructions string, or None if result model not found

    Example:
        >>> topic = get_coaching_topic("core_values")
        >>> instructions = get_structured_output_instructions_for_topic(topic)
        >>> # Returns instructions with CoreValuesResult schema embedded
    """
    # Get the result model class from the registry
    result_model = get_coaching_result_model(topic.result_model)
    if result_model is None:
        return None

    # Generate JSON schema from the model
    schema = result_model.model_json_schema()

    # Clean up internal schema details for cleaner prompt
    schema_clean = {
        k: v for k, v in schema.items() if k not in ("$defs", "definitions", "additionalProperties")
    }

    # Format the instructions with topic-specific values
    return STRUCTURED_OUTPUT_INSTRUCTIONS.format(
        topic_name=topic.name.lower(),
        result_model_name=topic.result_model,
        result_schema_json=json.dumps(schema_clean, indent=2),
    )


def get_system_prompt_with_structured_output(
    topic: "CoachingTopicDefinition",
    context: dict[str, object],
) -> str:
    """Get the complete system prompt with structured output instructions.

    Renders the topic's system prompt template with context values, then
    automatically appends structured output instructions based on the
    topic's result_model.

    Args:
        topic: The coaching topic definition
        context: Context values for template variable substitution

    Returns:
        Complete system prompt ready for LLM, including structured output instructions

    Example:
        >>> topic = get_coaching_topic("core_values")
        >>> context = {"business_name": "Acme Corp"}
        >>> prompt = get_system_prompt_with_structured_output(topic, context)
        >>> # Returns full prompt with {business_name} replaced and
        >>> # structured output instructions appended
    """
    # Render the base system prompt with context
    system_prompt = topic.system_prompt_template
    for key, value in context.items():
        placeholder = "{" + key + "}"
        if placeholder in system_prompt:
            system_prompt = system_prompt.replace(placeholder, str(value))

    # Append structured output instructions
    structured_instructions = get_structured_output_instructions_for_topic(topic)
    if structured_instructions:
        system_prompt = f"{system_prompt}\n{structured_instructions}"

    return system_prompt


# =============================================================================
# Topic Registry
# =============================================================================

COACHING_TOPIC_REGISTRY: dict[str, CoachingTopicDefinition] = {
    "core_values": CoachingTopicDefinition(
        topic_id="core_values",
        name="Core Values Discovery",
        description="Discover and articulate your organization's authentic core values through guided coaching.",
        system_prompt_template=CORE_VALUES_SYSTEM_PROMPT,
        initiation_instructions=CORE_VALUES_INITIATION,
        resume_instructions=CORE_VALUES_RESUME,
        extraction_instructions=CORE_VALUES_EXTRACTION,
        result_model="CoreValuesResult",
        parameter_refs=(_onb("business_name", "businessName"),),
        max_messages_to_llm=30,
        inactivity_timeout_minutes=30,
        session_ttl_days=14,
        estimated_messages=20,
        llm_temperature=0.7,
        llm_max_tokens=2000,
    ),
    "purpose": CoachingTopicDefinition(
        topic_id="purpose",
        name="Purpose Discovery",
        description="Define your organization's deeper purpose and reason for existing through guided coaching.",
        system_prompt_template=PURPOSE_SYSTEM_PROMPT,
        initiation_instructions=PURPOSE_INITIATION,
        resume_instructions=PURPOSE_RESUME,
        extraction_instructions=PURPOSE_EXTRACTION,
        result_model="PurposeResult",
        parameter_refs=(_onb("business_name", "businessName"),),
        max_messages_to_llm=30,
        inactivity_timeout_minutes=30,
        session_ttl_days=14,
        estimated_messages=18,
        llm_temperature=0.7,
        llm_max_tokens=2000,
    ),
    "vision": CoachingTopicDefinition(
        topic_id="vision",
        name="Vision Crafting",
        description="Craft a compelling vision for your organization's future through guided coaching.",
        system_prompt_template=VISION_SYSTEM_PROMPT,
        initiation_instructions=VISION_INITIATION,
        resume_instructions=VISION_RESUME,
        extraction_instructions=VISION_EXTRACTION,
        result_model="VisionResult",
        parameter_refs=(_onb("business_name", "businessName"),),
        max_messages_to_llm=30,
        inactivity_timeout_minutes=30,
        session_ttl_days=14,
        estimated_messages=16,
        llm_temperature=0.7,
        llm_max_tokens=2000,
    ),
}


# =============================================================================
# Registry Access Functions
# =============================================================================


def get_coaching_topic(topic_id: str) -> CoachingTopicDefinition | None:
    """Get a coaching topic definition by ID.

    Args:
        topic_id: The topic identifier (e.g., "core_values")

    Returns:
        The topic definition, or None if not found
    """
    return COACHING_TOPIC_REGISTRY.get(topic_id)


def list_coaching_topics() -> list[CoachingTopicDefinition]:
    """Get all registered coaching topics.

    Returns:
        List of all coaching topic definitions
    """
    return list(COACHING_TOPIC_REGISTRY.values())


def get_coaching_topic_ids() -> list[str]:
    """Get all registered coaching topic IDs.

    Returns:
        List of topic ID strings
    """
    return list(COACHING_TOPIC_REGISTRY.keys())


def is_valid_coaching_topic(topic_id: str) -> bool:
    """Check if a topic ID is a valid coaching topic.

    Args:
        topic_id: The topic identifier to check

    Returns:
        True if the topic exists in the registry
    """
    return topic_id in COACHING_TOPIC_REGISTRY
