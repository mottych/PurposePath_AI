"""Unit tests for LLMConfiguration domain entity."""

from datetime import datetime, timedelta

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from pydantic import ValidationError


class TestLLMConfiguration:
    """Tests for LLMConfiguration domain entity."""

    def test_create_valid_configuration(self) -> None:
        """Test creating valid LLM configuration."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        assert config.config_id == "test_config_123"
        assert config.interaction_code == "ALIGNMENT_ANALYSIS"
        assert config.template_id == "template_123"
        assert config.model_code == "CLAUDE_3_SONNET"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.is_active is True
        assert config.tier is None  # Default is None (all tiers)
        assert isinstance(config.created_at, datetime)

    def test_configuration_with_tier(self) -> None:
        """Test configuration with specific tier."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        assert config.tier == "premium"

    def test_temperature_validation_range(self) -> None:
        """Test temperature must be between 0.0 and 2.0."""
        # Valid temperature
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=1.5,
            max_tokens=4096,
            created_by="test_user",
        )
        assert config.temperature == 1.5

        # Too low
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=-0.1,
                max_tokens=4096,
                created_by="test_user",
            )

        # Too high
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=2.1,
                max_tokens=4096,
                created_by="test_user",
            )

    def test_max_tokens_validation(self) -> None:
        """Test max_tokens must be greater than 0."""
        # Valid max_tokens
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=1000,
            created_by="test_user",
        )
        assert config.max_tokens == 1000

        # Zero should fail
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=0.7,
                max_tokens=0,
                created_by="test_user",
            )

    def test_top_p_validation_range(self) -> None:
        """Test top_p must be between 0.0 and 1.0."""
        # Valid top_p
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
            created_by="test_user",
        )
        assert config.top_p == 0.9

        # Too high
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=0.7,
                max_tokens=4096,
                top_p=1.1,
                created_by="test_user",
            )

    def test_penalty_validation_ranges(self) -> None:
        """Test frequency and presence penalties must be between -2.0 and 2.0."""
        # Valid penalties
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            frequency_penalty=0.5,
            presence_penalty=-0.5,
            created_by="test_user",
        )
        assert config.frequency_penalty == 0.5
        assert config.presence_penalty == -0.5

        # Frequency penalty too high
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=0.7,
                max_tokens=4096,
                frequency_penalty=2.1,
                created_by="test_user",
            )

        # Presence penalty too low
        with pytest.raises(ValidationError):
            LLMConfiguration(
                config_id="test_config_123",
                interaction_code="ALIGNMENT_ANALYSIS",
                template_id="template_123",
                model_code="CLAUDE_3_SONNET",
                temperature=0.7,
                max_tokens=4096,
                presence_penalty=-2.1,
                created_by="test_user",
            )

    def test_applies_to_tier_null_config_tier(self) -> None:
        """Test config with null tier applies to all tiers."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier=None,  # Applies to all
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        # Should apply to any tier
        assert config.applies_to_tier("basic") is True
        assert config.applies_to_tier("premium") is True
        assert config.applies_to_tier("enterprise") is True
        assert config.applies_to_tier(None) is True

    def test_applies_to_tier_specific(self) -> None:
        """Test config with specific tier only applies to that tier."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        # Should only apply to premium tier
        assert config.applies_to_tier("premium") is True
        assert config.applies_to_tier("basic") is False
        assert config.applies_to_tier("enterprise") is False
        assert config.applies_to_tier(None) is False

    def test_is_currently_effective_within_range(self) -> None:
        """Test configuration is effective within date range."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            effective_from=now - timedelta(days=1),
            effective_until=now + timedelta(days=1),
            created_by="test_user",
        )

        assert config.is_currently_effective() is True

    def test_is_currently_effective_before_start(self) -> None:
        """Test configuration not effective before start date."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            effective_from=now + timedelta(days=1),  # Future
            created_by="test_user",
        )

        assert config.is_currently_effective() is False

    def test_is_currently_effective_after_end(self) -> None:
        """Test configuration not effective after end date."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            effective_from=now - timedelta(days=2),
            effective_until=now - timedelta(days=1),  # Past
            created_by="test_user",
        )

        assert config.is_currently_effective() is False

    def test_is_currently_effective_no_end_date(self) -> None:
        """Test configuration with no end date remains effective."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            effective_from=now - timedelta(days=1),
            effective_until=None,  # No end date
            created_by="test_user",
        )

        assert config.is_currently_effective() is True

    def test_is_usable_all_conditions_met(self) -> None:
        """Test configuration is usable when all conditions met."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            effective_from=now - timedelta(days=1),
            effective_until=now + timedelta(days=1),
            created_by="test_user",
        )

        assert config.is_usable("premium") is True

    def test_is_usable_inactive(self) -> None:
        """Test inactive configuration is not usable."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            is_active=False,  # Inactive
            effective_from=now - timedelta(days=1),
            created_by="test_user",
        )

        assert config.is_usable("premium") is False

    def test_is_usable_wrong_tier(self) -> None:
        """Test configuration not usable for wrong tier."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            effective_from=now - timedelta(days=1),
            created_by="test_user",
        )

        assert config.is_usable("basic") is False

    def test_is_usable_not_effective(self) -> None:
        """Test configuration not usable when outside effective dates."""
        now = datetime.utcnow()
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            effective_from=now + timedelta(days=1),  # Future
            created_by="test_user",
        )

        assert config.is_usable("premium") is False

    def test_configuration_repr(self) -> None:
        """Test string representation for debugging."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        repr_str = repr(config)

        assert "LLMConfiguration" in repr_str
        assert "test_config_123" in repr_str
        assert "ALIGNMENT_ANALYSIS" in repr_str
        assert "CLAUDE_3_SONNET" in repr_str
        assert "premium" in repr_str

    def test_configuration_repr_no_tier(self) -> None:
        """Test string representation with null tier."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            tier=None,
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        repr_str = repr(config)

        assert "tier=all" in repr_str

    def test_configuration_mutability(self) -> None:
        """Test that configuration can be updated (not frozen)."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        # Should allow updates
        config.is_active = False
        config.temperature = 0.9
        config.updated_at = datetime.utcnow() + timedelta(hours=1)

        assert config.is_active is False
        assert config.temperature == 0.9

    def test_configuration_json_serialization(self) -> None:
        """Test JSON serialization with datetime encoding."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        # Convert to dict with JSON encoders
        data = config.model_dump(mode="json")

        assert isinstance(data, dict)
        assert data["config_id"] == "test_config_123"
        assert "created_at" in data
        assert "updated_at" in data
        assert "effective_from" in data

    def test_configuration_defaults(self) -> None:
        """Test default values for optional fields."""
        config = LLMConfiguration(
            config_id="test_config_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=0.7,
            max_tokens=4096,
            created_by="test_user",
        )

        # Check defaults
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.is_active is True
        assert config.tier is None
        assert config.effective_until is None
        assert isinstance(config.effective_from, datetime)


__all__ = []  # Test module, no exports
