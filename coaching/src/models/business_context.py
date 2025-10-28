"""
Business context models for coaching API integration.

These models define the business data structure that the coaching service
can receive via request payload (from frontend) or orchestration (Step Functions).
This replaces direct database access to business-data table owned by .NET API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User information for coaching context."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    email: str = Field(..., description="User email")
    role: str | None = Field(None, description="User role/title")


class TenantContext(BaseModel):
    """Tenant/company information for coaching context."""

    id: str = Field(..., description="Tenant ID")
    company: str = Field(..., description="Company name")
    industry: str | None = Field(None, description="Industry sector")
    size: str | None = Field(None, description="Company size")


class GoalContext(BaseModel):
    """Goal information for coaching context."""

    id: str = Field(..., description="Goal ID")
    title: str = Field(..., description="Goal title")
    description: str | None = Field(None, description="Goal description")
    status: str = Field(..., description="Goal status")
    target_value: float | None = Field(None, description="Target numeric value")
    current_value: float | None = Field(None, description="Current progress value")
    due_date: datetime | None = Field(None, description="Goal due date")


class ActionContext(BaseModel):
    """Action/task information for coaching context."""

    id: str = Field(..., description="Action ID")
    title: str = Field(..., description="Action title")
    description: str | None = Field(None, description="Action description")
    status: str = Field(..., description="Action status")
    due_date: datetime | None = Field(None, description="Action due date")
    goal_id: str | None = Field(None, description="Associated goal ID")


class KpiContext(BaseModel):
    """KPI information for coaching context."""

    id: str = Field(..., description="KPI ID")
    name: str = Field(..., description="KPI name")
    current_value: float | None = Field(None, description="Current KPI value")
    target_value: float | None = Field(None, description="Target KPI value")
    unit: str | None = Field(None, description="KPI unit (%, $, etc.)")


class BusinessContext(BaseModel):
    """
    Complete business context for coaching requests.

    This replaces direct database access to business-data table.
    Can be populated by:
    1. Frontend sending relevant data in request
    2. Step Functions calling .NET API for enriched data
    """

    user: UserContext | None = Field(None, description="User information")
    tenant: TenantContext | None = Field(None, description="Tenant/company information")
    goals: list[GoalContext] = Field(default_factory=list, description="Relevant goals")
    recent_actions: list[ActionContext] = Field(
        default_factory=list, description="Recent actions/tasks"
    )
    kpis: list[KpiContext] = Field(default_factory=list, description="Key performance indicators")

    # Metadata
    data_scope: str | None = Field(
        None, description="Scope of included data (lightweight, full, etc.)"
    )
    retrieved_at: datetime | None = Field(None, description="When business data was retrieved")


class CoachingRequest(BaseModel):
    """
    Enhanced coaching request with optional business context.

    Supports both patterns:
    1. Lightweight: Frontend sends small business_context
    2. Orchestrated: Step Functions enriches with full business_context
    """

    message: str = Field(..., description="User's coaching request/question")
    conversation_id: str | None = Field(None, description="Existing conversation ID")
    session_id: str | None = Field(None, description="Coaching session ID")
    topic: str | None = Field(None, description="Coaching topic (goals, values, etc.)")

    # Business context (replaces direct database access)
    business_context: BusinessContext | None = Field(
        None, description="Business data context for personalized coaching"
    )

    # Request metadata
    source: str | None = Field(
        "direct",
        description="Request source: 'direct' (frontend) or 'orchestrated' (Step Functions)",
    )


class CoachingResponse(BaseModel):
    """Coaching service response with conversation tracking."""

    message: str = Field(..., description="AI coaching response")
    conversation_id: str = Field(..., description="Conversation ID for tracking")
    session_id: str | None = Field(None, description="Session ID if applicable")

    # Response metadata
    business_context_used: bool = Field(
        default=False, description="Whether business context was used in response"
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list, description="Suggested follow-up questions/actions"
    )
