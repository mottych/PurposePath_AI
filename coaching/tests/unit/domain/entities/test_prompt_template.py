"""Unit tests for PromptTemplate aggregate root."""

import pytest
from coaching.src.core.constants import CoachingTopic, ConversationPhase
from coaching.src.core.types import create_template_id
from coaching.src.domain.entities.prompt_template import PromptTemplate
from pydantic import ValidationError


class TestPromptTemplateCreation:
    """Test suite for PromptTemplate creation."""

    def test_create_template_with_required_fields(self) -> None:
        """Test creating template with required fields."""
        # Arrange & Act
        template = PromptTemplate(
            template_id=create_template_id(),
            name="Core Values Introduction",
            topic=CoachingTopic.CORE_VALUES,
            phase=ConversationPhase.INTRODUCTION,
            system_prompt="You are an AI coaching assistant.",
            template_text="Hello {name}, let's explore your core values.",
            variables=["name"],
        )

        # Assert
        assert template.name == "Core Values Introduction"
        assert template.topic == CoachingTopic.CORE_VALUES
        assert template.phase == ConversationPhase.INTRODUCTION
        assert template.variables == ["name"]
        assert template.version == 1
        assert template.is_active is True

    def test_create_template_with_no_variables(self) -> None:
        """Test creating template without variables."""
        # Arrange & Act
        template = PromptTemplate(
            template_id=create_template_id(),
            name="Static Template",
            topic=CoachingTopic.PURPOSE,
            phase=ConversationPhase.EXPLORATION,
            system_prompt="You are an AI coaching assistant.",
            template_text="This is a static template with no variables.",
        )

        # Assert
        assert template.variables == []


class TestPromptTemplateValidation:
    """Test suite for template validation."""

    def test_create_template_with_empty_name_raises_error(self) -> None:
        """Test that empty name raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            PromptTemplate(
                template_id=create_template_id(),
                name="",
                topic=CoachingTopic.CORE_VALUES,
                phase=ConversationPhase.INTRODUCTION,
                system_prompt="You are an AI coaching assistant.",
                template_text="Test template",
            )

    def test_create_template_with_whitespace_only_name_raises_error(
        self,
    ) -> None:
        """Test that whitespace-only name raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            PromptTemplate(
                template_id=create_template_id(),
                name="   ",
                topic=CoachingTopic.CORE_VALUES,
                phase=ConversationPhase.INTRODUCTION,
                system_prompt="You are an AI coaching assistant.",
                template_text="Test template",
            )

    def test_create_template_with_invalid_variable_name_raises_error(
        self,
    ) -> None:
        """Test that invalid variable names raise error."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="not a valid Python identifier"):
            PromptTemplate(
                template_id=create_template_id(),
                name="Test Template",
                topic=CoachingTopic.CORE_VALUES,
                phase=ConversationPhase.INTRODUCTION,
                system_prompt="You are an AI coaching assistant.",
                template_text="Hello {user-name}",
                variables=["user-name"],  # Invalid identifier
            )


class TestPromptTemplateRendering:
    """Test suite for template rendering."""

    @pytest.fixture
    def template(self) -> PromptTemplate:
        """Fixture providing a test template."""
        return PromptTemplate(
            template_id=create_template_id(),
            name="Personalized Greeting",
            topic=CoachingTopic.CORE_VALUES,
            phase=ConversationPhase.INTRODUCTION,
            system_prompt="You are an AI coaching assistant.",
            template_text="Hello {name}, welcome to {topic} coaching!",
            variables=["name", "topic"],
        )

    def test_render_template_with_all_variables(self, template: PromptTemplate) -> None:
        """Test rendering template with all variables provided."""
        # Act
        result = template.render(name="John", topic="Core Values")

        # Assert
        assert result == "Hello John, welcome to Core Values coaching!"

    def test_render_template_with_missing_variables_raises_error(
        self, template: PromptTemplate
    ) -> None:
        """Test that missing variables raise error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required variables"):
            template.render(name="John")  # Missing 'topic'

    def test_render_template_with_no_variables(self) -> None:
        """Test rendering template without variables."""
        # Arrange
        template = PromptTemplate(
            template_id=create_template_id(),
            name="Static",
            topic=CoachingTopic.PURPOSE,
            phase=ConversationPhase.EXPLORATION,
            system_prompt="You are an AI coaching assistant.",
            template_text="This has no variables.",
        )

        # Act
        result = template.render()

        # Assert
        assert result == "This has no variables."


class TestPromptTemplateActivation:
    """Test suite for template activation."""

    @pytest.fixture
    def template(self) -> PromptTemplate:
        """Fixture providing a test template."""
        return PromptTemplate(
            template_id=create_template_id(),
            name="Test Template",
            topic=CoachingTopic.CORE_VALUES,
            phase=ConversationPhase.INTRODUCTION,
            system_prompt="You are an AI coaching assistant.",
            template_text="Test {var}",
            variables=["var"],
        )

    def test_deactivate_active_template(self, template: PromptTemplate) -> None:
        """Test deactivating an active template."""
        # Arrange
        assert template.is_active is True

        # Act
        template.deactivate()

        # Assert
        assert template.is_active is False

    def test_deactivate_inactive_template_raises_error(self, template: PromptTemplate) -> None:
        """Test that deactivating inactive template raises error."""
        # Arrange
        template.deactivate()

        # Act & Assert
        with pytest.raises(ValueError, match="already inactive"):
            template.deactivate()

    def test_activate_inactive_template(self, template: PromptTemplate) -> None:
        """Test activating an inactive template."""
        # Arrange
        template.deactivate()

        # Act
        template.activate()

        # Assert
        assert template.is_active is True

    def test_activate_active_template_raises_error(self, template: PromptTemplate) -> None:
        """Test that activating active template raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="already active"):
            template.activate()


class TestPromptTemplateVersioning:
    """Test suite for template versioning."""

    @pytest.fixture
    def template(self) -> PromptTemplate:
        """Fixture providing a test template."""
        return PromptTemplate(
            template_id=create_template_id(),
            name="Versioned Template",
            topic=CoachingTopic.GOALS,
            phase=ConversationPhase.DEEPENING,
            system_prompt="You are an AI coaching assistant.",
            template_text="Original text with {var}",
            variables=["var"],
        )

    def test_create_new_version_increments_version_number(self, template: PromptTemplate) -> None:
        """Test that creating new version increments version."""
        # Arrange
        assert template.version == 1

        # Act
        template.create_new_version("Updated text with {var}", ["var"])

        # Assert
        assert template.version == 2

    def test_create_new_version_updates_template_text(self, template: PromptTemplate) -> None:
        """Test that new version updates template text."""
        # Act
        new_text = "New text with {var} and {other}"
        template.create_new_version(new_text, ["var", "other"])

        # Assert
        assert template.template_text == new_text
        assert template.variables == ["var", "other"]

    def test_create_new_version_with_empty_text_raises_error(
        self, template: PromptTemplate
    ) -> None:
        """Test that empty new text raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="cannot be empty"):
            template.create_new_version("", [])


class TestPromptTemplateUtilityMethods:
    """Test suite for utility methods."""

    def test_get_variable_placeholders(self) -> None:
        """Test getting variable placeholders."""
        # Arrange
        template = PromptTemplate(
            template_id=create_template_id(),
            name="Test",
            topic=CoachingTopic.VISION,
            phase=ConversationPhase.SYNTHESIS,
            system_prompt="You are an AI coaching assistant.",
            template_text="Test {name} and {value}",
            variables=["name", "value"],
        )

        # Act
        placeholders = template.get_variable_placeholders()

        # Assert
        assert placeholders == ["{name}", "{value}"]

    def test_get_variable_placeholders_empty(self) -> None:
        """Test getting placeholders for template with no variables."""
        # Arrange
        template = PromptTemplate(
            template_id=create_template_id(),
            name="Static",
            topic=CoachingTopic.PURPOSE,
            phase=ConversationPhase.EXPLORATION,
            system_prompt="You are an AI coaching assistant.",
            template_text="No variables here",
        )

        # Act
        placeholders = template.get_variable_placeholders()

        # Assert
        assert placeholders == []
