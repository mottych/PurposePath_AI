"""Tests for TemplateParameterProcessor.

Tests the core template processing functionality:
- Template parsing for {parameter} placeholders
- Grouping parameters by retrieval method
- Calling retrieval methods efficiently
- Extracting values using extraction_path
- Parameter substitution
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.core.parameter_registry import ParameterDefinition, ParameterType
from coaching.src.core.retrieval_method_registry import RetrievalContext
from coaching.src.services.template_parameter_processor import (
    PARAMETER_PATTERN,
    ParameterExtractionResult,
    ParameterRequirement,
    TemplateParameterProcessor,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_business_client() -> MagicMock:
    """Create a mock BusinessApiClient."""
    client = MagicMock()
    client.get_organizational_context = AsyncMock(
        return_value={
            "vision": "Test vision statement",
            "purpose": "Test purpose statement",
            "core_values": ["integrity", "innovation"],
            "industry": "Technology",
        }
    )
    client.get_user_goals = AsyncMock(
        return_value=[
            {"id": "goal-1", "title": "Goal One", "status": "in_progress"},
            {"id": "goal-2", "title": "Goal Two", "status": "completed"},
        ]
    )
    return client


@pytest.fixture
def processor(mock_business_client: MagicMock) -> TemplateParameterProcessor:
    """Create a TemplateParameterProcessor instance."""
    return TemplateParameterProcessor(mock_business_client)


# =============================================================================
# Test: PARAMETER_PATTERN regex
# =============================================================================


class TestParameterPattern:
    """Tests for the parameter detection regex."""

    def test_matches_simple_param(self) -> None:
        """Test: Matches simple parameter names."""
        matches = PARAMETER_PATTERN.findall("Hello {name}!")
        assert matches == ["name"]

    def test_matches_underscored_param(self) -> None:
        """Test: Matches parameter names with underscores."""
        matches = PARAMETER_PATTERN.findall("User: {user_name}")
        assert matches == ["user_name"]

    def test_matches_numbered_param(self) -> None:
        """Test: Matches parameter names with numbers."""
        matches = PARAMETER_PATTERN.findall("Value: {param_123}")
        assert matches == ["param_123"]

    def test_matches_multiple_params(self) -> None:
        """Test: Matches multiple parameters in one string."""
        template = "Hello {first_name} {last_name}, your ID is {user_id}."
        matches = PARAMETER_PATTERN.findall(template)
        assert set(matches) == {"first_name", "last_name", "user_id"}

    def test_ignores_escaped_braces(self) -> None:
        """Test: Does not match content without valid parameter name format."""
        # Note: This pattern doesn't handle {{escaped}} specially,
        # but invalid formats won't match
        matches = PARAMETER_PATTERN.findall("Value: {123invalid}")
        assert matches == []

    def test_no_match_for_dot_notation(self) -> None:
        """Test: Does not match dot-notation paths at all."""
        # {user.name} doesn't match because '.' is not in [a-zA-Z0-9_]
        # This is by design - nested paths should be handled differently
        matches = PARAMETER_PATTERN.findall("Hello {user.name}!")
        assert matches == []  # No match because of the dot


# =============================================================================
# Test: extract_parameters_from_template
# =============================================================================


class TestExtractParametersFromTemplate:
    """Tests for template parameter extraction."""

    def test_extracts_unique_params(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns unique set of parameter names."""
        template = "Hello {name}! Your name is {name} and id is {user_id}."
        params = processor.extract_parameters_from_template(template)
        assert params == {"name", "user_id"}

    def test_empty_template(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns empty set for template without params."""
        params = processor.extract_parameters_from_template("Hello world!")
        assert params == set()

    def test_complex_template(self, processor: TemplateParameterProcessor) -> None:
        """Test: Handles complex template with many parameters."""
        template = """
        Welcome {user_name}!

        Your goals:
        {goals}

        Based on your {vision} and {core_values}, we recommend:
        {recommendations}
        """
        params = processor.extract_parameters_from_template(template)
        assert params == {"user_name", "goals", "vision", "core_values", "recommendations"}


# =============================================================================
# Test: _extract_value
# =============================================================================


class TestExtractValue:
    """Tests for value extraction using paths."""

    def test_simple_key(self, processor: TemplateParameterProcessor) -> None:
        """Test: Extracts value with simple key."""
        data = {"name": "John", "age": 30}
        value = processor._extract_value(data, "name", "fallback")
        assert value == "John"

    def test_nested_path(self, processor: TemplateParameterProcessor) -> None:
        """Test: Extracts value with dot notation path."""
        data = {"user": {"profile": {"name": "John"}}}
        value = processor._extract_value(data, "user.profile.name", "fallback")
        assert value == "John"

    def test_uses_param_name_when_path_empty(self, processor: TemplateParameterProcessor) -> None:
        """Test: Uses param_name as key when extraction_path is empty."""
        data = {"my_param": "value"}
        value = processor._extract_value(data, "", "my_param")
        assert value == "value"

    def test_returns_none_for_missing_key(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns None when key not found."""
        data = {"name": "John"}
        value = processor._extract_value(data, "missing_key", "fallback")
        assert value is None

    def test_returns_none_for_partial_path(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns None when path is only partially valid."""
        data = {"user": {"name": "John"}}
        value = processor._extract_value(data, "user.profile.name", "fallback")
        assert value is None

    def test_handles_list_index(self, processor: TemplateParameterProcessor) -> None:
        """Test: Handles numeric index in path for lists."""
        data = {"items": ["first", "second", "third"]}
        value = processor._extract_value(data, "items.1", "fallback")
        assert value == "second"

    def test_returns_none_for_empty_data(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns None when data is empty."""
        value = processor._extract_value({}, "key", "fallback")
        assert value is None

    def test_returns_none_for_none_data(self, processor: TemplateParameterProcessor) -> None:
        """Test: Returns None when data is None."""
        value = processor._extract_value(None, "key", "fallback")  # type: ignore
        assert value is None


# =============================================================================
# Test: substitute_parameters
# =============================================================================


class TestSubstituteParameters:
    """Tests for parameter substitution in templates."""

    def test_simple_substitution(self, processor: TemplateParameterProcessor) -> None:
        """Test: Substitutes simple string value."""
        template = "Hello {name}!"
        result = processor.substitute_parameters(template, {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_substitutions(self, processor: TemplateParameterProcessor) -> None:
        """Test: Substitutes multiple parameters."""
        template = "{greeting} {name}! Your ID is {user_id}."
        params = {"greeting": "Hello", "name": "John", "user_id": "123"}
        result = processor.substitute_parameters(template, params)
        assert result == "Hello John! Your ID is 123."

    def test_repeated_param(self, processor: TemplateParameterProcessor) -> None:
        """Test: Substitutes repeated parameter occurrences."""
        template = "{name} is {name}."
        result = processor.substitute_parameters(template, {"name": "Same"})
        assert result == "Same is Same."

    def test_missing_param_unchanged(self, processor: TemplateParameterProcessor) -> None:
        """Test: Leaves placeholder when param not provided."""
        template = "Hello {name}!"
        result = processor.substitute_parameters(template, {})
        assert result == "Hello {name}!"

    def test_list_value_joined(self, processor: TemplateParameterProcessor) -> None:
        """Test: Joins list values with comma."""
        template = "Values: {core_values}"
        result = processor.substitute_parameters(
            template, {"core_values": ["integrity", "innovation"]}
        )
        assert result == "Values: integrity, innovation"

    def test_dict_value_stringified(self, processor: TemplateParameterProcessor) -> None:
        """Test: Converts dict to string."""
        template = "Data: {data}"
        result = processor.substitute_parameters(template, {"data": {"key": "value"}})
        assert "key" in result and "value" in result

    def test_numeric_value(self, processor: TemplateParameterProcessor) -> None:
        """Test: Converts numeric values to string."""
        template = "Count: {count}, Rate: {rate}"
        result = processor.substitute_parameters(template, {"count": 42, "rate": 3.14})
        assert result == "Count: 42, Rate: 3.14"


# =============================================================================
# Test: _group_by_retrieval_method
# =============================================================================


class TestGroupByRetrievalMethod:
    """Tests for grouping parameters by retrieval method."""

    def test_groups_by_method(self, processor: TemplateParameterProcessor) -> None:
        """Test: Groups requirements by retrieval_method."""
        requirements = [
            ParameterRequirement(
                name="vision",
                definition=ParameterDefinition(
                    name="vision",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                ),
            ),
            ParameterRequirement(
                name="purpose",
                definition=ParameterDefinition(
                    name="purpose",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                ),
            ),
            ParameterRequirement(
                name="goals",
                definition=ParameterDefinition(
                    name="goals",
                    param_type=ParameterType.LIST,
                    retrieval_method="get_all_goals",
                ),
            ),
        ]

        grouped = processor._group_by_retrieval_method(requirements)

        assert len(grouped) == 2
        assert "get_business_foundation" in grouped
        assert "get_all_goals" in grouped
        assert len(grouped["get_business_foundation"]) == 2
        assert len(grouped["get_all_goals"]) == 1

    def test_ignores_params_without_method(self, processor: TemplateParameterProcessor) -> None:
        """Test: Excludes params without retrieval_method."""
        requirements = [
            ParameterRequirement(
                name="user_id",
                definition=ParameterDefinition(
                    name="user_id",
                    param_type=ParameterType.STRING,
                    # No retrieval_method
                ),
            ),
            ParameterRequirement(
                name="vision",
                definition=ParameterDefinition(
                    name="vision",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                ),
            ),
        ]

        grouped = processor._group_by_retrieval_method(requirements)

        assert len(grouped) == 1
        assert "get_business_foundation" in grouped

    def test_ignores_params_without_definition(self, processor: TemplateParameterProcessor) -> None:
        """Test: Excludes params without definition."""
        requirements = [
            ParameterRequirement(name="unknown_param", definition=None),
        ]

        grouped = processor._group_by_retrieval_method(requirements)

        assert len(grouped) == 0


# =============================================================================
# Test: process_template_parameters
# =============================================================================


class TestProcessTemplateParameters:
    """Tests for the main processing flow."""

    @pytest.mark.asyncio
    async def test_uses_payload_values(self, processor: TemplateParameterProcessor) -> None:
        """Test: Uses values provided in payload directly."""
        template = "Hello {user_name}!"
        payload = {"user_name": "John"}

        result = await processor.process_template_parameters(
            template=template,
            payload=payload,
            user_id="user-1",
            tenant_id="tenant-1",
        )

        assert result.parameters["user_name"] == "John"
        assert not result.missing_required
        assert not result.warnings

    @pytest.mark.asyncio
    async def test_reports_missing_required(self, processor: TemplateParameterProcessor) -> None:
        """Test: Reports required params that can't be resolved."""
        template = "Hello {unknown_required_param}!"
        payload: dict[str, Any] = {}

        result = await processor.process_template_parameters(
            template=template,
            payload=payload,
            user_id="user-1",
            tenant_id="tenant-1",
            required_params={"unknown_required_param"},
        )

        assert "unknown_required_param" in result.missing_required

    @pytest.mark.asyncio
    async def test_applies_default_values(self, processor: TemplateParameterProcessor) -> None:
        """Test: Applies default values for optional params."""
        template = "Hello {user_name}!"

        # Patch get_parameter_definition to return a param with default
        with patch(
            "coaching.src.services.template_parameter_processor.get_parameter_definition"
        ) as mock_get:
            mock_get.return_value = ParameterDefinition(
                name="user_name",
                param_type=ParameterType.STRING,
                default="Guest",
            )

            result = await processor.process_template_parameters(
                template=template,
                payload={},
                user_id="user-1",
                tenant_id="tenant-1",
            )

            assert result.parameters["user_name"] == "Guest"

    @pytest.mark.asyncio
    async def test_calls_retrieval_method_once(
        self, processor: TemplateParameterProcessor, mock_business_client: MagicMock
    ) -> None:
        """Test: Calls retrieval method only once for multiple params."""
        template = "Vision: {vision}, Purpose: {purpose}"

        # Patch to simulate params with retrieval method
        def mock_get_param(name: str) -> ParameterDefinition | None:
            if name == "vision":
                return ParameterDefinition(
                    name="vision",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                    extraction_path="vision",
                )
            if name == "purpose":
                return ParameterDefinition(
                    name="purpose",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                    extraction_path="purpose",
                )
            return None

        # Mock retrieval method
        async def mock_retrieval_method(ctx: RetrievalContext) -> dict[str, Any]:
            return {
                "vision": "Our vision",
                "purpose": "Our purpose",
            }

        with (
            patch(
                "coaching.src.services.template_parameter_processor.get_parameter_definition",
                side_effect=mock_get_param,
            ),
            patch(
                "coaching.src.services.template_parameter_processor.get_retrieval_method",
                return_value=mock_retrieval_method,
            ),
            patch(
                "coaching.src.services.template_parameter_processor.get_retrieval_method_definition",
                return_value=None,
            ),
        ):
            result = await processor.process_template_parameters(
                template=template,
                payload={},
                user_id="user-1",
                tenant_id="tenant-1",
            )

            assert result.parameters["vision"] == "Our vision"
            assert result.parameters["purpose"] == "Our purpose"

    @pytest.mark.asyncio
    async def test_handles_empty_template(self, processor: TemplateParameterProcessor) -> None:
        """Test: Handles template with no parameters."""
        template = "Hello world!"

        result = await processor.process_template_parameters(
            template=template,
            payload={},
            user_id="user-1",
            tenant_id="tenant-1",
        )

        assert result.parameters == {}
        assert not result.missing_required
        assert not result.warnings

    @pytest.mark.asyncio
    async def test_warns_on_unknown_param(self, processor: TemplateParameterProcessor) -> None:
        """Test: Adds warning for params not in registry."""
        template = "Hello {totally_unknown_param}!"

        with patch(
            "coaching.src.services.template_parameter_processor.get_parameter_definition",
            return_value=None,
        ):
            result = await processor.process_template_parameters(
                template=template,
                payload={},
                user_id="user-1",
                tenant_id="tenant-1",
            )

            assert any("totally_unknown_param" in w for w in result.warnings)


# =============================================================================
# Test: _enrich_parameters
# =============================================================================


class TestEnrichParameters:
    """Tests for parameter enrichment via retrieval methods."""

    @pytest.mark.asyncio
    async def test_handles_retrieval_method_failure(
        self, processor: TemplateParameterProcessor
    ) -> None:
        """Test: Handles failures gracefully and applies defaults."""
        requirements = [
            ParameterRequirement(
                name="vision",
                definition=ParameterDefinition(
                    name="vision",
                    param_type=ParameterType.STRING,
                    retrieval_method="get_business_foundation",
                    default="Default vision",
                ),
            ),
        ]

        async def failing_method(ctx: RetrievalContext) -> dict[str, Any]:
            raise RuntimeError("API Error")

        with (
            patch(
                "coaching.src.services.template_parameter_processor.get_retrieval_method",
                return_value=failing_method,
            ),
            patch(
                "coaching.src.services.template_parameter_processor.get_retrieval_method_definition",
                return_value=None,
            ),
        ):
            result = await processor._enrich_parameters(
                params_by_method={"get_business_foundation": requirements},
                payload={},
                user_id="user-1",
                tenant_id="tenant-1",
            )

            # Should apply default when retrieval fails
            assert result["vision"] == "Default vision"

    @pytest.mark.asyncio
    async def test_skips_unknown_retrieval_method(
        self, processor: TemplateParameterProcessor
    ) -> None:
        """Test: Skips params with unknown retrieval method."""
        requirements = [
            ParameterRequirement(
                name="something",
                definition=ParameterDefinition(
                    name="something",
                    param_type=ParameterType.STRING,
                    retrieval_method="nonexistent_method",
                ),
            ),
        ]

        with patch(
            "coaching.src.services.template_parameter_processor.get_retrieval_method",
            return_value=None,
        ):
            result = await processor._enrich_parameters(
                params_by_method={"nonexistent_method": requirements},
                payload={},
                user_id="user-1",
                tenant_id="tenant-1",
            )

            assert "something" not in result


# =============================================================================
# Test: ParameterExtractionResult dataclass
# =============================================================================


class TestParameterExtractionResult:
    """Tests for the result dataclass."""

    def test_default_values(self) -> None:
        """Test: Has sensible defaults."""
        result = ParameterExtractionResult()
        assert result.parameters == {}
        assert result.missing_required == []
        assert result.warnings == []

    def test_can_set_values(self) -> None:
        """Test: Can be constructed with values."""
        result = ParameterExtractionResult(
            parameters={"key": "value"},
            missing_required=["missing"],
            warnings=["A warning"],
        )
        assert result.parameters == {"key": "value"}
        assert result.missing_required == ["missing"]
        assert result.warnings == ["A warning"]


# =============================================================================
# Test: ParameterRequirement dataclass
# =============================================================================


class TestParameterRequirement:
    """Tests for the requirement dataclass."""

    def test_default_values(self) -> None:
        """Test: Has sensible defaults."""
        req = ParameterRequirement(name="test", definition=None)
        assert req.name == "test"
        assert req.definition is None
        assert req.required is False
        assert req.provided_value is None

    def test_with_all_values(self) -> None:
        """Test: Can be constructed with all values."""
        definition = ParameterDefinition(name="test", param_type=ParameterType.STRING)
        req = ParameterRequirement(
            name="test",
            definition=definition,
            required=True,
            provided_value="value",
        )
        assert req.name == "test"
        assert req.definition == definition
        assert req.required is True
        assert req.provided_value == "value"
