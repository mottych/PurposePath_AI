"""Unit tests for async AI API models."""

from datetime import UTC, datetime

import pytest
from coaching.src.api.models.async_ai import AsyncAIRequest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


class TestAsyncAIRequest:
    """Tests for legacy and v2 async request contracts."""

    def test_legacy_request_is_valid(self) -> None:
        """Legacy payload remains valid for backwards compatibility."""
        request = AsyncAIRequest(
            topic_id="niche_review",
            parameters={"current_value": "Test value"},
        )
        assert request.is_backend_contract_v2 is False
        assert request.parameters["current_value"] == "Test value"

    def test_v2_request_is_valid(self) -> None:
        """V2 backend-triggered payload validates with required fields."""
        request = AsyncAIRequest(
            eventId="evt-1",
            occurredAtUtc=datetime.now(UTC),
            sourceService="PurposePath_Api",
            schemaVersion="2.0",
            correlationId="corr-1",
            idempotencyKey="idem-1",
            retryAttempt=0,
            tenantId="tenant_1",
            userId="user_1",
            topicCategory="email_insight",
            topicId="goal_created_email_insight",
            eventSignal="goal_created",
            locale="en-US",
            timezone="UTC",
            activityData={"goal_id": "goal_1"},
            authContext={
                "serviceToken": "service-token",
                "expiresAtUtc": datetime.now(UTC),
                "issuer": "PurposePath_Api",
                "tokenType": "service_enrichment",
            },
        )
        assert request.is_backend_contract_v2 is True
        assert request.topic_id == "goal_created_email_insight"
        assert request.auth_context is not None
        assert request.auth_context.service_token == "service-token"

    def test_v2_missing_required_fields_fails(self) -> None:
        """V2 payload should fail if required fields are missing."""
        with pytest.raises(ValidationError):
            AsyncAIRequest(
                topicId="goal_created_email_insight",
                topicCategory="email_insight",
                activityData={"goal_id": "goal_1"},
                authContext={
                    "serviceToken": "service-token",
                    "expiresAtUtc": datetime.now(UTC),
                    "issuer": "PurposePath_Api",
                    "tokenType": "service_enrichment",
                },
            )
