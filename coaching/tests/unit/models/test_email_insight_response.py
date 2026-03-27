"""Unit tests for EmailInsightResponse model."""

from datetime import UTC, datetime

import pytest
from coaching.src.models.responses import EmailInsightResponse
from pydantic import ValidationError


@pytest.mark.unit
class TestEmailInsightResponse:
    """Tests for the EmailInsightResponse schema model."""

    def test_valid_email_insight_response(self) -> None:
        """Should validate a fully populated payload."""
        payload = EmailInsightResponse(
            schemaVersion="1.0",
            title="Great start on your goal",
            summary="You turned intention into action. Keep momentum with one next step.",
            blocks=[
                {"type": "paragraph", "text": "This is a strong first step."},
                {
                    "type": "list",
                    "items": ["Define a weekly milestone.", "Schedule a check-in this week."],
                },
                {
                    "type": "cta",
                    "label": "Review your goal",
                    "action": "open_goal",
                    "url": "https://app.purposepath.com/goals/goal_123",
                },
            ],
            confidence=0.82,
            generationMeta={
                "modelId": "gpt-5",
                "promptVersion": "goal_created_email_insight@v1",
                "traceId": "trace-123",
                "generatedAtUtc": datetime.now(UTC),
            },
        )

        assert payload.schema_version == "1.0"
        assert payload.blocks[0].type == "paragraph"
        assert payload.blocks[1].type == "list"
        assert payload.blocks[2].type == "cta"
        assert payload.generation_meta.model_id == "gpt-5"

    def test_invalid_block_type_fails_validation(self) -> None:
        """Should reject unsupported block types."""
        with pytest.raises(ValidationError):
            EmailInsightResponse(
                schemaVersion="1.0",
                title="Great start",
                summary="Summary text",
                blocks=[{"type": "heading", "text": "Not supported in v1"}],
                generationMeta={
                    "modelId": "gpt-5",
                    "promptVersion": "v1",
                    "traceId": "trace-1",
                    "generatedAtUtc": datetime.now(UTC),
                },
            )

    def test_missing_generation_meta_fails_validation(self) -> None:
        """Should enforce required generation metadata."""
        with pytest.raises(ValidationError):
            EmailInsightResponse(
                schemaVersion="1.0",
                title="Great start",
                summary="Summary text",
                blocks=[{"type": "paragraph", "text": "Body text"}],
            )

    def test_title_length_constraint_enforced(self) -> None:
        """Should enforce title max length (120)."""
        with pytest.raises(ValidationError):
            EmailInsightResponse(
                schemaVersion="1.0",
                title="x" * 121,
                summary="Summary text",
                blocks=[{"type": "paragraph", "text": "Body text"}],
                generationMeta={
                    "modelId": "gpt-5",
                    "promptVersion": "v1",
                    "traceId": "trace-1",
                    "generatedAtUtc": datetime.now(UTC),
                },
            )

    def test_confidence_enum_is_valid(self) -> None:
        """Should accept enum confidence values."""
        payload = EmailInsightResponse(
            schemaVersion="1.0",
            title="Great start",
            summary="Summary text",
            blocks=[{"type": "paragraph", "text": "Body text"}],
            confidence="high",
            generationMeta={
                "modelId": "gpt-5",
                "promptVersion": "v1",
                "traceId": "trace-1",
                "generatedAtUtc": datetime.now(UTC),
            },
        )

        assert payload.confidence == "high"
