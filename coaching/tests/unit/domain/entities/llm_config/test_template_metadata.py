"""Unit tests for TemplateMetadata domain entity."""

from datetime import datetime, timedelta

import pytest
from coaching.src.core.llm_interactions import ParameterValidationError
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from pydantic import ValidationError


class TestTemplateMetadata:
    """Tests for TemplateMetadata domain entity."""

    def test_create_valid_template_metadata(self) -> None:
        """Test creating valid template metadata."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        assert metadata.template_id == "test_template_123"
        assert metadata.template_code == "ALIGNMENT_ANALYSIS_V1"
        assert metadata.interaction_code == "ALIGNMENT_ANALYSIS"
        assert metadata.name == "Test Template"
        assert metadata.is_active is True
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)

    def test_template_metadata_validation_name_length(self) -> None:
        """Test name length validation."""
        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            TemplateMetadata(
                template_id="test_template_123",
                template_code="ALIGNMENT_ANALYSIS_V1",
                interaction_code="ALIGNMENT_ANALYSIS",
                name="",  # Empty
                description="Test template description",
                s3_bucket="test-bucket",
                s3_key="templates/test_template.jinja2",
                version="1.0.0",
                created_by="test_user",
            )

        assert "name" in str(exc_info.value).lower()

    def test_template_metadata_validation_description_length(self) -> None:
        """Test description length validation."""
        # Empty description should fail
        with pytest.raises(ValidationError) as exc_info:
            TemplateMetadata(
                template_id="test_template_123",
                template_code="ALIGNMENT_ANALYSIS_V1",
                interaction_code="ALIGNMENT_ANALYSIS",
                name="Test Template",
                description="",  # Empty
                s3_bucket="test-bucket",
                s3_key="templates/test_template.jinja2",
                version="1.0.0",
                created_by="test_user",
            )

        assert "description" in str(exc_info.value).lower()

    def test_template_metadata_defaults(self) -> None:
        """Test default values for template metadata."""
        before = datetime.utcnow()
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )
        after = datetime.utcnow()

        # Check defaults
        assert metadata.is_active is True
        assert before <= metadata.created_at <= after
        assert before <= metadata.updated_at <= after

    def test_get_parameters_from_registry(self) -> None:
        """Test retrieving parameters from interaction registry."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        params = metadata.get_parameters()

        assert "required" in params
        assert "optional" in params
        assert "all_parameters" in params
        assert isinstance(params["required"], list)
        assert isinstance(params["optional"], list)
        assert len(params["all_parameters"]) == len(params["required"]) + len(params["optional"])

    def test_get_parameters_invalid_interaction(self) -> None:
        """Test error when interaction not in registry."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="INVALID_V1",
            interaction_code="INVALID_INTERACTION",  # Not in registry
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        with pytest.raises(ValueError) as exc_info:
            metadata.get_parameters()

        error_msg = str(exc_info.value)
        assert "Unknown interaction code" in error_msg
        assert "INVALID_INTERACTION" in error_msg

    def test_validate_template_content_valid(self) -> None:
        """Test validating template content with valid parameters."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        # Template with all required parameters
        template_content = """
        Analyze alignment for: {{ goal_text }}
        Purpose: {{ purpose }}
        Values: {{ values }}
        """

        # Should not raise
        metadata.validate_template_content(template_content)

    def test_validate_template_content_missing_required(self) -> None:
        """Test error when template missing required parameters."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        # Template missing required 'values' parameter
        template_content = """
        Analyze alignment for: {{ goal_text }}
        Purpose: {{ purpose }}
        """

        with pytest.raises(ParameterValidationError) as exc_info:
            metadata.validate_template_content(template_content)

        assert "missing required parameters" in str(exc_info.value).lower()

    def test_validate_template_content_unsupported_param(self) -> None:
        """Test error when template uses unsupported parameter."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        # Template with unsupported parameter
        template_content = """
        Analyze alignment for: {{ goal_text }}
        Purpose: {{ purpose }}
        Values: {{ values }}
        Invalid: {{ unsupported_param }}
        """

        with pytest.raises(ParameterValidationError) as exc_info:
            metadata.validate_template_content(template_content)

        assert "unsupported parameters" in str(exc_info.value).lower()

    def test_get_s3_location(self) -> None:
        """Test getting S3 location URI."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="my-bucket",
            s3_key="templates/folder/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        location = metadata.get_s3_location()

        assert location == "s3://my-bucket/templates/folder/test_template.jinja2"
        assert location.startswith("s3://")

    def test_template_metadata_repr(self) -> None:
        """Test string representation for debugging."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        repr_str = repr(metadata)

        assert "TemplateMetadata" in repr_str
        assert "test_template_123" in repr_str
        assert "ALIGNMENT_ANALYSIS_V1" in repr_str
        assert "ALIGNMENT_ANALYSIS" in repr_str

    def test_template_metadata_mutability(self) -> None:
        """Test that template metadata can be updated (not frozen)."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        # Should allow updates
        metadata.is_active = False
        metadata.updated_at = datetime.utcnow() + timedelta(hours=1)

        assert metadata.is_active is False

    def test_template_metadata_json_serialization(self) -> None:
        """Test JSON serialization with datetime encoding."""
        metadata = TemplateMetadata(
            template_id="test_template_123",
            template_code="ALIGNMENT_ANALYSIS_V1",
            interaction_code="ALIGNMENT_ANALYSIS",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template.jinja2",
            version="1.0.0",
            created_by="test_user",
        )

        # Convert to dict with JSON encoders
        data = metadata.model_dump(mode="json")

        assert isinstance(data, dict)
        assert data["template_id"] == "test_template_123"
        assert "created_at" in data
        assert "updated_at" in data


__all__ = []  # Test module, no exports
