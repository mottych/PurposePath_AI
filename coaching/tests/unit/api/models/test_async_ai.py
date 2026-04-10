"""Unit tests for async AI API models."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from coaching.src.api.models.async_ai import AsyncAIRequest

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
            requestId="req-1",
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
                "expiresAtUtc": datetime.now(UTC) + timedelta(minutes=5),
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
                    "expiresAtUtc": datetime.now(UTC) + timedelta(minutes=5),
                    "issuer": "PurposePath_Api",
                    "tokenType": "service_enrichment",
                },
            )

    def test_v2_missing_service_token_fails(self) -> None:
        """V2 payload should fail when service token is missing."""
        with pytest.raises(ValidationError):
            AsyncAIRequest(
                eventId="evt-1",
                requestId="req-1",
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
                    "expiresAtUtc": datetime.now(UTC),
                    "issuer": "PurposePath_Api",
                    "tokenType": "service_enrichment",
                },
            )

    def test_v2_expired_service_token_fails(self) -> None:
        """V2 payload should fail when authContext token is expired."""
        with pytest.raises(ValidationError, match="expired"):
            AsyncAIRequest(
                eventId="evt-1",
                requestId="req-1",
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
                    "expiresAtUtc": datetime(2000, 1, 1, tzinfo=UTC),
                    "issuer": "PurposePath_Api",
                    "tokenType": "service_enrichment",
                },
            )

    def test_v2_invalid_token_type_fails(self) -> None:
        """V2 payload should fail deterministic token type validation."""
        with pytest.raises(ValidationError, match="service_enrichment"):
            AsyncAIRequest(
                eventId="evt-1",
                requestId="req-1",
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
                    "expiresAtUtc": datetime.now(UTC) + timedelta(minutes=5),
                    "issuer": "PurposePath_Api",
                    "tokenType": "wrong_scope",
                },
            )
