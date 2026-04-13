"""Unit tests for async AI API models."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from coaching.src.api.models.async_ai import AsyncAIRequest

pytestmark = pytest.mark.unit


class TestAsyncAIRequest:
    """Canonical execute-async envelope validation."""

    def test_valid_email_insight_envelope(self) -> None:
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
        assert request.topic_id == "goal_created_email_insight"
        assert request.auth_context.service_token == "service-token"

    def test_valid_onboarding_category(self) -> None:
        request = AsyncAIRequest(
            eventId="evt-1",
            requestId="req-1",
            occurredAtUtc=datetime.now(UTC),
            sourceService="PurposePath_Web",
            schemaVersion="2.0",
            correlationId="corr-1",
            idempotencyKey="idem-1",
            retryAttempt=0,
            tenantId="tenant_1",
            userId="user_1",
            topicCategory="onboarding",
            topicId="niche_review",
            eventSignal="user_requested",
            locale="en-US",
            timezone="UTC",
            activityData={"current_value": "x"},
            authContext={
                "serviceToken": "service-token",
                "expiresAtUtc": datetime.now(UTC) + timedelta(minutes=5),
                "issuer": "PurposePath_Api",
                "tokenType": "service_enrichment",
            },
        )
        assert request.topic_category == "onboarding"

    def test_missing_required_fields_fails(self) -> None:
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

    def test_minimal_topic_only_payload_rejected(self) -> None:
        """Old topicId+parameters-only shape is not accepted."""
        with pytest.raises(ValidationError):
            AsyncAIRequest(
                topicId="niche_review",
                parameters={"current_value": "test"},
            )

    def test_missing_service_token_fails(self) -> None:
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

    def test_expired_service_token_fails(self) -> None:
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

    def test_invalid_token_type_fails(self) -> None:
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

    def test_unknown_topic_category_fails(self) -> None:
        with pytest.raises(ValidationError, match="topicCategory"):
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
                topicCategory="not_a_real_category",
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
