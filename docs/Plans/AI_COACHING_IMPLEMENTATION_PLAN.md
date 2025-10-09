# PurposePath AI Coaching Service - Implementation Plan

**Document Version:** 1.0.0  
**Last Updated:** October 8, 2025  
**Status:** Implementation Guide - Ready for Development  
**Branch:** feature/phase3-service-architecture  
**Companion Document:** AI_COACHING_ARCHITECTURE_DESIGN.md (Part 1)

---

## Part 2: Detailed Design & Implementation Plan

---

## 📋 Table of Contents

1. [Implementation Overview](#implementation-overview)
2. [Data Models & Type Definitions](#data-models--type-definitions)
3. [Domain Layer Implementation](#domain-layer-implementation)
4. [Service Layer Implementation](#service-layer-implementation)
5. [Infrastructure Layer Implementation](#infrastructure-layer-implementation)
6. [API Layer Implementation](#api-layer-implementation)
7. [Step-by-Step Implementation Roadmap](#step-by-step-implementation-roadmap)
8. [Testing Strategy & Implementation](#testing-strategy--implementation)
9. [Deployment & Migration Plan](#deployment--migration-plan)

---

## 🎯 Implementation Overview

### Implementation Approach

This implementation plan follows a **bottom-up approach** with clear phases:

1. **Foundation** - Core domain models, types, and interfaces
2. **Infrastructure** - Repositories, LLM providers, external clients
3. **Domain Logic** - Business rules, domain services, workflows
4. **Application Services** - Service orchestration, use case implementation
5. **API Layer** - Endpoint implementation, request/response handling
6. **Integration** - Step Functions orchestration, context enrichment
7. **Testing** - Unit, integration, and E2E tests
8. **Deployment** - Infrastructure setup, CI/CD, monitoring

### Key Principles

- ✅ **Type Safety First** - Every component uses Pydantic models
- ✅ **Test-Driven Development** - Tests written before/alongside implementation
- ✅ **Incremental Delivery** - Each phase produces working, testable code
- ✅ **Documentation as Code** - Docstrings, type hints, ADRs
- ✅ **Clean Architecture** - Strict dependency rules (domain ← service ← infrastructure ← API)

---

## 📦 Data Models & Type Definitions

### Core Type System

#### Domain IDs (Strong Typing)

```python
# coaching/src/core/types.py

from typing import NewType
from uuid import UUID, uuid4

# Domain entity IDs (compile-time type safety)
ConversationId = NewType('ConversationId', str)
TemplateId = NewType('TemplateId', str)
AnalysisRequestId = NewType('AnalysisRequestId', str)
UserId = NewType('UserId', str)
TenantId = NewType('TenantId', str)

def create_conversation_id() -> ConversationId:
    """Generate a new conversation ID."""
    return ConversationId(str(uuid4()))

def create_template_id(topic: str, version: str) -> TemplateId:
    """Generate a template ID from topic and version."""
    return TemplateId(f"{topic}:{version}")

def create_analysis_request_id() -> AnalysisRequestId:
    """Generate a new analysis request ID."""
    return AnalysisRequestId(str(uuid4()))
```

#### Enums and Constants

```python
# coaching/src/core/constants.py

from enum import Enum

class CoachingTopic(str, Enum):
    """Supported coaching topics."""
    CORE_VALUES = "core_values"
    PURPOSE = "purpose"
    VISION = "vision"
    GOAL_SETTING = "goal_setting"

class AnalysisType(str, Enum):
    """Types of one-shot analysis."""
    ALIGNMENT_SCORING = "alignment_scoring"
    ALIGNMENT_EXPLANATION = "alignment_explanation"
    ALIGNMENT_SUGGESTIONS = "alignment_suggestions"
    STRATEGY_RECOMMENDATIONS = "strategy_recommendations"
    KPI_RECOMMENDATIONS = "kpi_recommendations"
    SWOT_ANALYSIS = "swot_analysis"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    FIVE_WHYS = "five_whys"
    ACTION_PLAN_GENERATION = "action_plan_generation"
    ACTION_OPTIMIZATION = "action_optimization"
    PRIORITIZATION_SUGGESTIONS = "prioritization_suggestions"
    SCHEDULING_SUGGESTIONS = "scheduling_suggestions"
    ISSUE_CATEGORIZATION = "issue_categorization"
    IMPACT_ASSESSMENT = "impact_assessment"

class ConversationStatus(str, Enum):
    """Conversation lifecycle states."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"

class ConversationPhase(str, Enum):
    """Phases in coaching conversations."""
    INTRODUCTION = "introduction"
    EXPLORATION = "exploration"
    DEEPENING = "deepening"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    COMPLETION = "completion"

class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Phase progression weights for progress calculation
PHASE_PROGRESS_WEIGHTS: dict[ConversationPhase, float] = {
    ConversationPhase.INTRODUCTION: 0.1,
    ConversationPhase.EXPLORATION: 0.3,
    ConversationPhase.DEEPENING: 0.5,
    ConversationPhase.SYNTHESIS: 0.7,
    ConversationPhase.VALIDATION: 0.9,
    ConversationPhase.COMPLETION: 1.0,
}
```

### Domain Value Objects

#### Message Value Object

```python
# coaching/src/domain/value_objects/message.py

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from coaching.src.core.constants import MessageRole

class Message(BaseModel):
    """An immutable message in a conversation.
    
    Value object representing a single message exchange.
    """
    
    role: MessageRole = Field(..., description="Who sent the message")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the message was created"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata"
    )
    
    class Config:
        frozen = True  # Immutable
        
    def __repr__(self) -> str:
        return f"Message(role={self.role.value}, length={len(self.content)})"
```

#### Alignment Score Value Object

```python
# coaching/src/domain/value_objects/alignment_score.py

from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ComponentScores(BaseModel):
    """Breakdown of alignment score components."""
    
    intent_alignment: float = Field(..., ge=0, le=100)
    strategy_alignment: float = Field(..., ge=0, le=100)
    kpi_relevance: float = Field(..., ge=0, le=100)
    
class FoundationAlignment(BaseModel):
    """Alignment with business foundation elements."""
    
    vision_alignment: float = Field(..., ge=0, le=100)
    purpose_alignment: float = Field(..., ge=0, le=100)
    values_alignment: float = Field(..., ge=0, le=100)

class AlignmentScore(BaseModel):
    """Immutable alignment score value object.
    
    Represents the result of alignment analysis between a goal
    and the business foundation.
    """
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall alignment score")
    component_scores: ComponentScores = Field(..., description="Component breakdown")
    foundation_alignment: FoundationAlignment = Field(..., description="Foundation alignment")
    explanation: str = Field(..., min_length=10, description="Why this score")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in scoring")
    
    class Config:
        frozen = True
    
    @field_validator('suggestions')
    @classmethod
    def validate_suggestions(cls, v: list[str]) -> list[str]:
        """Ensure suggestions are meaningful."""
        return [s for s in v if len(s.strip()) > 10]
    
    def is_well_aligned(self, threshold: float = 75.0) -> bool:
        """Check if alignment meets threshold."""
        return self.overall_score >= threshold
    
    def get_weakest_component(self) -> tuple[str, float]:
        """Identify weakest alignment component."""
        scores = {
            "intent": self.component_scores.intent_alignment,
            "strategy": self.component_scores.strategy_alignment,
            "kpi": self.component_scores.kpi_relevance,
        }
        weakest = min(scores.items(), key=lambda x: x[1])
        return weakest
```

#### Strategy Recommendation Value Object

```python
# coaching/src/domain/value_objects/strategy_recommendation.py

from pydantic import BaseModel, Field

class StrategyRecommendation(BaseModel):
    """Immutable strategy recommendation value object."""
    
    description: str = Field(..., min_length=20, description="Strategy description")
    rationale: str = Field(..., min_length=30, description="Why this strategy")
    feasibility_score: float = Field(..., ge=0, le=100, description="How feasible")
    estimated_impact: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        description="Expected impact level"
    )
    timeframe: str = Field(..., description="Expected timeframe (e.g., '3-6 months')")
    resources_required: list[str] = Field(default_factory=list, description="Required resources")
    risks: list[str] = Field(default_factory=list, description="Potential risks")
    success_metrics: list[str] = Field(default_factory=list, description="How to measure success")
    
    class Config:
        frozen = True
    
    def is_highly_feasible(self, threshold: float = 70.0) -> bool:
        """Check if strategy is highly feasible."""
        return self.feasibility_score >= threshold
```

#### Enriched Context Value Object

```python
# coaching/src/domain/value_objects/enriched_context.py

from typing import Any, Optional
from pydantic import BaseModel, Field

class BusinessFoundation(BaseModel):
    """Business foundation data."""
    
    vision: Optional[str] = None
    purpose: Optional[str] = None
    core_values: list[str] = Field(default_factory=list)
    target_market: Optional[str] = None
    value_proposition: Optional[str] = None
    business_name: Optional[str] = None

class GoalContext(BaseModel):
    """Goal-related context."""
    
    goal_id: Optional[str] = None
    goal_title: Optional[str] = None
    goal_intent: Optional[str] = None
    strategies: list[dict[str, Any]] = Field(default_factory=list)
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    progress: Optional[float] = None

class OperationsContext(BaseModel):
    """Operations-related context."""
    
    active_issues: list[dict[str, Any]] = Field(default_factory=list)
    pending_actions: list[dict[str, Any]] = Field(default_factory=list)
    recent_decisions: list[dict[str, Any]] = Field(default_factory=list)
    team_capacity: Optional[dict[str, Any]] = None

class UserContext(BaseModel):
    """User-specific context."""
    
    user_id: str
    tenant_id: str
    role: str
    preferences: dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    timezone: str = "UTC"

class EnrichedContext(BaseModel):
    """Complete enriched context for prompt injection.
    
    This value object contains all business data fetched
    from the .NET database via Step Functions.
    """
    
    user_context: UserContext
    business_foundation: Optional[BusinessFoundation] = None
    goal_context: Optional[GoalContext] = None
    operations_context: Optional[OperationsContext] = None
    custom_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom context data"
    )
    
    class Config:
        frozen = True
    
    def to_prompt_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for prompt injection."""
        return {
            "user": self.user_context.model_dump(),
            "business_foundation": (
                self.business_foundation.model_dump() if self.business_foundation else {}
            ),
            "goal_context": self.goal_context.model_dump() if self.goal_context else {},
            "operations_context": (
                self.operations_context.model_dump() if self.operations_context else {}
            ),
            **self.custom_data,
        }
```

### Domain Entities

#### Conversation Entity (Aggregate Root)

```python
# coaching/src/domain/entities/conversation.py

from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from coaching.src.core.constants import (
    ConversationStatus,
    ConversationPhase,
    MessageRole,
    PHASE_PROGRESS_WEIGHTS,
)
from coaching.src.core.types import ConversationId, UserId, TenantId
from coaching.src.domain.value_objects.message import Message
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from coaching.src.domain.events.conversation_events import (
    ConversationInitiated,
    MessageAdded,
    ConversationCompleted,
    ConversationPaused,
)

class Conversation(BaseModel):
    """Conversation aggregate root.
    
    Represents a complete coaching conversation with all its state,
    messages, and business rules.
    
    Aggregate invariants:
    - Conversation must have at least one message (initial greeting)
    - Cannot add messages to completed/abandoned conversations
    - Phase transitions must follow defined progression
    - TTL is set to 30 days from last update
    """
    
    # Identity
    conversation_id: ConversationId
    user_id: UserId
    tenant_id: TenantId
    topic: str
    
    # State
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: list[Message] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    
    # Configuration
    llm_config: dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    ttl: Optional[int] = None
    
    # Domain events (not persisted)
    _events: list[Any] = Field(default_factory=list, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Set TTL to 30 days from creation
        if not self.ttl:
            expiry = self.created_at + timedelta(days=30)
            self.ttl = int(expiry.timestamp())
    
    # Business rule enforcement
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation.
        
        Business Rules:
        - Cannot add messages to non-active conversations
        - User messages increment response count
        - Updates conversation timestamp
        - Extends TTL
        
        Args:
            role: Who sent the message
            content: Message content
            metadata: Optional metadata
            
        Raises:
            ValueError: If conversation is not active
        """
        if not self.is_active():
            raise ValueError(
                f"Cannot add message to {self.status.value} conversation"
            )
        
        # Create and add message
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        
        # Update state
        self.updated_at = datetime.now(timezone.utc)
        
        if role == MessageRole.USER:
            self.context.response_count += 1
        
        # Extend TTL
        expiry = self.updated_at + timedelta(days=30)
        self.ttl = int(expiry.timestamp())
        
        # Emit domain event
        self._events.append(MessageAdded(
            conversation_id=self.conversation_id,
            role=role.value,
            content_length=len(content),
            timestamp=self.updated_at,
        ))
    
    def transition_phase(self, new_phase: ConversationPhase) -> None:
        """Transition to a new conversation phase.
        
        Business Rules:
        - Phases must progress forward (no backwards transitions)
        - Must be in active status
        
        Args:
            new_phase: Target phase
            
        Raises:
            ValueError: If transition is invalid
        """
        if not self.is_active():
            raise ValueError("Cannot transition phase of non-active conversation")
        
        # Validate phase progression
        current_weight = PHASE_PROGRESS_WEIGHTS[self.context.phase]
        new_weight = PHASE_PROGRESS_WEIGHTS[new_phase]
        
        if new_weight <= current_weight:
            raise ValueError(
                f"Invalid phase transition: {self.context.phase.value} -> {new_phase.value}"
            )
        
        self.context.phase = new_phase
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_completed(self) -> None:
        """Mark conversation as completed.
        
        Business Rules:
        - Must be in active or paused status
        - Sets completion timestamp
        - Emits completion event
        """
        if self.status not in [ConversationStatus.ACTIVE, ConversationStatus.PAUSED]:
            raise ValueError(f"Cannot complete conversation in {self.status.value} status")
        
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at
        
        # Emit domain event
        self._events.append(ConversationCompleted(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            topic=self.topic,
            message_count=len(self.messages),
            duration_seconds=int((self.completed_at - self.created_at).total_seconds()),
        ))
    
    def mark_paused(self, reason: Optional[str] = None) -> None:
        """Mark conversation as paused."""
        if not self.is_active():
            raise ValueError("Can only pause active conversations")
        
        self.status = ConversationStatus.PAUSED
        self.paused_at = datetime.now(timezone.utc)
        self.updated_at = self.paused_at
        
        self._events.append(ConversationPaused(
            conversation_id=self.conversation_id,
            reason=reason,
            timestamp=self.paused_at,
        ))
    
    def resume(self) -> None:
        """Resume a paused conversation."""
        if self.status != ConversationStatus.PAUSED:
            raise ValueError(f"Cannot resume {self.status.value} conversation")
        
        self.status = ConversationStatus.ACTIVE
        self.paused_at = None
        self.updated_at = datetime.now(timezone.utc)
    
    # Query methods
    
    def is_active(self) -> bool:
        """Check if conversation can accept new messages."""
        return self.status == ConversationStatus.ACTIVE
    
    def calculate_progress(self) -> float:
        """Calculate conversation progress (0-1)."""
        return PHASE_PROGRESS_WEIGHTS.get(self.context.phase, 0.0)
    
    def get_conversation_history(
        self,
        max_messages: Optional[int] = None,
        include_system: bool = False
    ) -> list[dict[str, str]]:
        """Get conversation history for LLM context.
        
        Args:
            max_messages: Limit to recent N messages
            include_system: Include system messages
            
        Returns:
            List of message dictionaries
        """
        messages = self.messages
        
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
    
    def get_domain_events(self) -> list[Any]:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events
    
    class Config:
        arbitrary_types_allowed = True
```

#### Conversation Context Value Object

```python
# coaching/src/domain/value_objects/conversation_context.py

from typing import Any
from pydantic import BaseModel, Field

from coaching.src.core.constants import ConversationPhase

class ConversationContext(BaseModel):
    """Mutable context tracking conversation state.
    
    Note: While technically mutable, this should only be modified
    through the Conversation aggregate to maintain invariants.
    """
    
    # Conversation phase
    phase: ConversationPhase = ConversationPhase.INTRODUCTION
    
    # Insights and discoveries
    identified_values: list[str] = Field(default_factory=list)
    key_insights: list[str] = Field(default_factory=list)
    
    # Progress tracking
    progress_markers: dict[str, Any] = Field(default_factory=dict)
    categories_explored: list[str] = Field(default_factory=list)
    response_count: int = 0
    deepening_count: int = 0
    
    # Multi-tenant fields
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    business_context: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    
    def add_identified_value(self, value: str) -> None:
        """Add a newly identified value."""
        if value not in self.identified_values:
            self.identified_values.append(value)
    
    def add_insight(self, insight: str) -> None:
        """Add a key insight."""
        if insight not in self.key_insights:
            self.key_insights.append(insight)
    
    def mark_category_explored(self, category: str) -> None:
        """Mark a category as explored."""
        if category not in self.categories_explored:
            self.categories_explored.append(category)
    
    def is_ready_for_synthesis(
        self,
        min_values: int = 5,
        min_responses: int = 10
    ) -> bool:
        """Check if enough exploration has occurred for synthesis."""
        return (
            len(self.identified_values) >= min_values and
            self.response_count >= min_responses
        )
```

#### Prompt Template Entity

```python
# coaching/src/domain/entities/prompt_template.py

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

from coaching.src.core.types import TemplateId

class PromptPlaceholder(BaseModel):
    """Definition of a placeholder in the template."""
    
    name: str = Field(..., description="Placeholder name (e.g., {{user_name}})")
    description: str = Field(..., description="What this placeholder represents")
    required: bool = Field(default=True, description="Whether this placeholder is required")
    default_value: Optional[str] = Field(None, description="Default value if not provided")
    data_type: str = Field(default="string", description="Expected data type")

class LLMConfiguration(BaseModel):
    """LLM configuration for this template."""
    
    model: str = Field(..., description="Model identifier (e.g., claude-3-sonnet)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stop_sequences: list[str] = Field(default_factory=list)

class PromptTemplate(BaseModel):
    """Prompt template aggregate root.
    
    Represents a versioned prompt template with metadata,
    placeholders, and LLM configuration.
    
    Templates are immutable once published - modifications create new versions.
    """
    
    # Identity
    template_id: TemplateId
    topic: str = Field(..., description="What this template is for")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    
    # Template content
    system_prompt: str = Field(..., min_length=50, description="System instructions")
    initial_message: str = Field(..., min_length=20, description="First message to user")
    
    # Metadata
    placeholders: list[PromptPlaceholder] = Field(
        default_factory=list,
        description="Placeholders in the template"
    )
    llm_config: LLMConfiguration = Field(..., description="LLM settings")
    
    # Status
    is_published: bool = Field(default=False, description="Whether template is active")
    is_deprecated: bool = Field(default=False, description="Whether template is deprecated")
    
    # Tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    created_by: str = Field(..., description="User ID who created this")
    
    # Usage tracking (not part of core domain - could be separate aggregate)
    usage_count: int = Field(default=0, description="How many times used")
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Ensure topic is valid."""
        valid_topics = [
            "core_values", "purpose", "vision", "goal_setting",
            "alignment", "strategy", "kpi", "swot", "root_cause", "action_plan"
        ]
        if v not in valid_topics:
            raise ValueError(f"Invalid topic: {v}")
        return v
    
    def publish(self, publisher_id: str) -> None:
        """Publish the template for use.
        
        Business Rules:
        - Can only publish unpublished templates
        - Cannot publish deprecated templates
        """
        if self.is_published:
            raise ValueError("Template is already published")
        if self.is_deprecated:
            raise ValueError("Cannot publish deprecated template")
        
        self.is_published = True
        self.published_at = datetime.now(timezone.utc)
    
    def deprecate(self, reason: str) -> None:
        """Deprecate the template.
        
        Business Rules:
        - Can deprecate any template
        - Once deprecated, cannot be un-deprecated
        """
        self.is_deprecated = True
        self.deprecated_at = datetime.now(timezone.utc)
    
    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
    
    def get_required_placeholders(self) -> list[str]:
        """Get list of required placeholder names."""
        return [p.name for p in self.placeholders if p.required]
    
    def validate_context(self, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate that provided context has all required placeholders.
        
        Returns:
            Tuple of (is_valid, missing_placeholders)
        """
        required = set(self.get_required_placeholders())
        provided = set(context.keys())
        missing = required - provided
        
        return len(missing) == 0, list(missing)
    
    class Config:
        frozen = True  # Immutable once created
```

---

## 🔷 Domain Layer Implementation

### Domain Services

#### Alignment Calculator Service

```python
# coaching/src/domain/services/alignment_calculator.py

from typing import Any
from pydantic import BaseModel

from coaching.src.domain.value_objects.alignment_score import (
    AlignmentScore,
    ComponentScores,
    FoundationAlignment,
)

class AlignmentCalculationInput(BaseModel):
    """Input for alignment calculation."""
    
    goal_intent: str
    strategies: list[dict[str, Any]]
    kpis: list[dict[str, Any]]
    business_foundation: dict[str, Any]

class AlignmentCalculatorService:
    """Domain service for calculating alignment scores.
    
    This is a stateless domain service that encapsulates complex
    business logic for alignment scoring.
    """
    
    def calculate_alignment(
        self,
        input_data: AlignmentCalculationInput
    ) -> AlignmentScore:
        """Calculate comprehensive alignment score.
        
        This is a placeholder for the actual algorithm.
        In production, this would use ML models or complex heuristics.
        
        Args:
            input_data: Alignment calculation input
            
        Returns:
            Complete alignment score
        """
        # Component scoring
        intent_score = self._score_intent_alignment(
            input_data.goal_intent,
            input_data.business_foundation
        )
        strategy_score = self._score_strategy_alignment(
            input_data.strategies,
            input_data.business_foundation
        )
        kpi_score = self._score_kpi_relevance(
            input_data.kpis,
            input_data.goal_intent
        )
        
        # Foundation alignment
        vision_score = self._score_vision_alignment(
            input_data.goal_intent,
            input_data.business_foundation.get("vision", "")
        )
        purpose_score = self._score_purpose_alignment(
            input_data.goal_intent,
            input_data.business_foundation.get("purpose", "")
        )
        values_score = self._score_values_alignment(
            input_data.goal_intent,
            input_data.business_foundation.get("core_values", [])
        )
        
        # Calculate overall score (weighted average)
        overall = (
            intent_score * 0.3 +
            strategy_score * 0.3 +
            kpi_score * 0.2 +
            vision_score * 0.1 +
            purpose_score * 0.05 +
            values_score * 0.05
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            overall_score=overall,
            component_scores=(intent_score, strategy_score, kpi_score),
            foundation_scores=(vision_score, purpose_score, values_score)
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            intent_score, strategy_score, kpi_score,
            vision_score, purpose_score, values_score
        )
        
        return AlignmentScore(
            overall_score=overall,
            component_scores=ComponentScores(
                intent_alignment=intent_score,
                strategy_alignment=strategy_score,
                kpi_relevance=kpi_score,
            ),
            foundation_alignment=FoundationAlignment(
                vision_alignment=vision_score,
                purpose_alignment=purpose_score,
                values_alignment=values_score,
            ),
            explanation=explanation,
            suggestions=suggestions,
            confidence=0.85,
        )
    
    def _score_intent_alignment(
        self,
        goal_intent: str,
        foundation: dict[str, Any]
    ) -> float:
        """Score how well goal intent aligns with foundation."""
        # Placeholder algorithm
        # In production: use NLP similarity, keyword matching, or ML model
        return 80.0
    
    def _score_strategy_alignment(
        self,
        strategies: list[dict[str, Any]],
        foundation: dict[str, Any]
    ) -> float:
        """Score strategy-to-foundation alignment."""
        if not strategies:
            return 50.0  # Penalty for no strategies
        return 85.0
    
    def _score_kpi_relevance(
        self,
        kpis: list[dict[str, Any]],
        goal_intent: str
    ) -> float:
        """Score KPI relevance to goal."""
        if not kpis:
            return 50.0  # Penalty for no KPIs
        return 90.0
    
    def _score_vision_alignment(self, goal: str, vision: str) -> float:
        """Score alignment with vision."""
        if not vision:
            return 70.0  # No vision to compare
        return 80.0
    
    def _score_purpose_alignment(self, goal: str, purpose: str) -> float:
        """Score alignment with purpose."""
        if not purpose:
            return 70.0
        return 85.0
    
    def _score_values_alignment(
        self,
        goal: str,
        values: list[str]
    ) -> float:
        """Score alignment with core values."""
        if not values:
            return 70.0
        return 90.0
    
    def _generate_explanation(
        self,
        overall_score: float,
        component_scores: tuple[float, float, float],
        foundation_scores: tuple[float, float, float]
    ) -> str:
        """Generate human-readable explanation."""
        intent, strategy, kpi = component_scores
        vision, purpose, values = foundation_scores
        
        if overall_score >= 80:
            tone = "excellent"
        elif overall_score >= 60:
            tone = "good"
        else:
            tone = "moderate"
        
        return (
            f"This goal shows {tone} alignment with your business foundation. "
            f"The goal intent is {self._describe_score(intent)} aligned, "
            f"strategies are {self._describe_score(strategy)} aligned, "
            f"and KPIs are {self._describe_score(kpi)} relevant."
        )
    
    def _describe_score(self, score: float) -> str:
        """Convert score to descriptive term."""
        if score >= 85:
            return "strongly"
        elif score >= 70:
            return "well"
        elif score >= 50:
            return "moderately"
        else:
            return "weakly"
    
    def _generate_suggestions(
        self,
        intent: float,
        strategy: float,
        kpi: float,
        vision: float,
        purpose: float,
        values: float
    ) -> list[str]:
        """Generate improvement suggestions based on scores."""
        suggestions = []
        
        if intent < 70:
            suggestions.append(
                "Consider refining the goal statement to more explicitly connect with your vision and purpose."
            )
        
        if strategy < 70:
            suggestions.append(
                "Review your strategies to ensure they directly support the core values and vision."
            )
        
        if kpi < 70:
            suggestions.append(
                "Add more specific, measurable KPIs that track progress toward the goal."
            )
        
        if vision < 70:
            suggestions.append(
                "Ensure the goal contributes to your long-term vision for the organization."
            )
        
        if values < 70:
            suggestions.append(
                "Align the goal more closely with your core values by incorporating value-driven language."
            )
        
        return suggestions
```

#### Phase Transition Service

```python
# coaching/src/domain/services/phase_transition_service.py

from typing import Optional

from coaching.src.core.constants import ConversationPhase
from coaching.src.domain.entities.conversation import Conversation

class PhaseTransitionService:
    """Domain service for managing conversation phase transitions.
    
    Encapsulates business rules for when and how to transition
    between conversation phases.
    """
    
    def should_transition_to_exploration(
        self,
        conversation: Conversation
    ) -> bool:
        """Check if conversation is ready for exploration phase.
        
        Rules:
        - Must have at least 2 user responses
        - Must be in introduction phase
        """
        return (
            conversation.context.phase == ConversationPhase.INTRODUCTION and
            conversation.context.response_count >= 2
        )
    
    def should_transition_to_deepening(
        self,
        conversation: Conversation
    ) -> bool:
        """Check if ready for deepening phase.
        
        Rules:
        - Must have explored at least 3 categories
        - Must have at least 5 user responses
        - Must be in exploration phase
        """
        return (
            conversation.context.phase == ConversationPhase.EXPLORATION and
            len(conversation.context.categories_explored) >= 3 and
            conversation.context.response_count >= 5
        )
    
    def should_transition_to_synthesis(
        self,
        conversation: Conversation,
        min_values: int = 5
    ) -> bool:
        """Check if ready for synthesis phase.
        
        Rules:
        - Must have identified minimum values
        - Must have sufficient responses
        - Must be in deepening phase
        """
        return (
            conversation.context.phase == ConversationPhase.DEEPENING and
            conversation.context.is_ready_for_synthesis(
                min_values=min_values,
                min_responses=10
            )
        )
    
    def should_transition_to_validation(
        self,
        conversation: Conversation
    ) -> bool:
        """Check if ready for validation phase.
        
        Rules:
        - Must have synthesized insights
        - Must be in synthesis phase
        """
        return (
            conversation.context.phase == ConversationPhase.SYNTHESIS and
            len(conversation.context.key_insights) > 0
        )
    
    def should_complete_conversation(
        self,
        conversation: Conversation,
        user_confirmed: bool = False
    ) -> bool:
        """Check if conversation should be completed.
        
        Rules:
        - Must be in validation or completion phase
        - User must have confirmed (for validation phase)
        """
        if conversation.context.phase == ConversationPhase.COMPLETION:
            return True
        
        if conversation.context.phase == ConversationPhase.VALIDATION:
            return user_confirmed
        
        return False
    
    def get_next_phase(
        self,
        conversation: Conversation
    ) -> Optional[ConversationPhase]:
        """Determine next phase for conversation.
        
        Returns None if no transition should occur.
        """
        current = conversation.context.phase
        
        if current == ConversationPhase.INTRODUCTION:
            if self.should_transition_to_exploration(conversation):
                return ConversationPhase.EXPLORATION
        
        elif current == ConversationPhase.EXPLORATION:
            if self.should_transition_to_deepening(conversation):
                return ConversationPhase.DEEPENING
        
        elif current == ConversationPhase.DEEPENING:
            if self.should_transition_to_synthesis(conversation):
                return ConversationPhase.SYNTHESIS
        
        elif current == ConversationPhase.SYNTHESIS:
            if self.should_transition_to_validation(conversation):
                return ConversationPhase.VALIDATION
        
        elif current == ConversationPhase.VALIDATION:
            # Validation to completion requires explicit confirmation
            return None
        
        return None
```

### Domain Events

```python
# coaching/src/domain/events/conversation_events.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from coaching.src.core.types import ConversationId, UserId

class DomainEvent(BaseModel):
    """Base class for all domain events."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationInitiated(DomainEvent):
    """Raised when a new conversation is started."""
    
    conversation_id: ConversationId
    user_id: UserId
    topic: str
    tenant_id: str

class MessageAdded(DomainEvent):
    """Raised when a message is added to conversation."""
    
    conversation_id: ConversationId
    role: str
    content_length: int
    timestamp: datetime

class PhaseTransitioned(DomainEvent):
    """Raised when conversation moves to new phase."""
    
    conversation_id: ConversationId
    from_phase: str
    to_phase: str

class ConversationCompleted(DomainEvent):
    """Raised when conversation is completed."""
    
    conversation_id: ConversationId
    user_id: UserId
    topic: str
    message_count: int
    duration_seconds: int

class ConversationPaused(DomainEvent):
    """Raised when conversation is paused."""
    
    conversation_id: ConversationId
    reason: Optional[str]
    timestamp: datetime

class AnalysisRequested(DomainEvent):
    """Raised when one-shot analysis is requested."""
    
    analysis_id: str
    analysis_type: str
    user_id: UserId
    tenant_id: str

class AnalysisCompleted(DomainEvent):
    """Raised when analysis is completed."""
    
    analysis_id: str
    analysis_type: str
    duration_ms: int
    token_count: int
```

---

*To be continued in next section...*

This document is comprehensive and will continue with:
- Service Layer Implementation
- Infrastructure Layer Implementation  
- API Layer Implementation
- Step-by-Step Implementation roadmap
- Testing Strategy
- Deployment Plan

**Document Status**: Part 2 - Section 1-3 Complete (Data Models, Domain Layer)  
**Next**: Service Layer Implementation (Section 4)

---

## Implementation Status Update (October 9, 2025)

**IMPORTANT**: This implementation plan has been reorganized into a more actionable, phased approach.

**See**: `REVISED_IMPLEMENTATION_ROADMAP.md` for:
- Structured 8-phase implementation (12-15 weeks)
- Testing integrated into each phase
- Observability from Phase 1 (not Phase 7)
- Clear migration strategy
- GitHub issues (#2-#23) aligned with phases

**Summary**: `PLAN_UPDATE_SUMMARY.md`

This document remains valuable for detailed technical specifications and design patterns.
