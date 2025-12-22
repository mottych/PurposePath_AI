"""Tests for parameter registry.

Tests for Issue #123 - Coaching Engine Improvement.

Key architectural decisions:
- `required` is NOT part of ParameterDefinition - it varies per endpoint
  and is defined in ParameterRef within endpoint_registry.py
- `retrieval_method` defines how to fetch parameters not in the request payload
- `extraction_path` defines how to extract specific values from retrieval results
"""

import pytest
from coaching.src.core.parameter_registry import (
    PARAMETER_REGISTRY,
    ParameterDefinition,
    ParameterType,
    get_all_parameter_names,
    get_enrichable_parameters,
    get_parameter_definition,
    get_parameters_by_retrieval_method,
    validate_parameter_name,
)


class TestParameterType:
    """Tests for ParameterType enum."""

    def test_all_types_exist(self) -> None:
        """Test that all expected parameter types exist."""
        expected_types = [
            "STRING",
            "INTEGER",
            "FLOAT",
            "BOOLEAN",
            "LIST",
            "DICT",
            "DATETIME",
        ]
        for type_name in expected_types:
            assert hasattr(ParameterType, type_name), f"Missing type: {type_name}"

    def test_type_values(self) -> None:
        """Test parameter type values."""
        assert ParameterType.STRING.value == "string"
        assert ParameterType.INTEGER.value == "integer"
        assert ParameterType.FLOAT.value == "float"
        assert ParameterType.BOOLEAN.value == "boolean"
        assert ParameterType.LIST.value == "list"
        assert ParameterType.DICT.value == "dict"
        assert ParameterType.DATETIME.value == "datetime"


class TestParameterDefinition:
    """Tests for ParameterDefinition dataclass."""

    def test_parameter_definition_frozen(self) -> None:
        """Test that ParameterDefinition is immutable."""
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
            description="Test parameter",
        )
        # Frozen dataclass should raise error on attribute assignment
        with pytest.raises(AttributeError):
            param.name = "changed"  # type: ignore[misc]

    def test_parameter_definition_with_default(self) -> None:
        """Test ParameterDefinition with default value."""
        param = ParameterDefinition(
            name="optional_param",
            param_type=ParameterType.STRING,
            description="Optional parameter",
            default="default_value",
        )
        assert param.default == "default_value"

    def test_parameter_definition_no_required_field(self) -> None:
        """Test that required is not part of ParameterDefinition.

        Required is per-endpoint, defined in ParameterRef in endpoint_registry.py.
        """
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
        )
        assert "required" not in param.__dataclass_fields__

    def test_parameter_definition_no_source_field(self) -> None:
        """Test that source is not part of ParameterDefinition.

        Source is per-endpoint, defined in ParameterRef in endpoint_registry.py.
        """
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
        )
        assert "source" not in param.__dataclass_fields__

    def test_parameter_definition_has_retrieval_method(self) -> None:
        """Test that ParameterDefinition has retrieval_method field."""
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
            retrieval_method="get_business_foundation",
            extraction_path="test_field",
        )
        assert param.retrieval_method == "get_business_foundation"
        assert param.extraction_path == "test_field"

    def test_parameter_definition_retrieval_defaults(self) -> None:
        """Test that retrieval fields have correct defaults."""
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
        )
        assert param.retrieval_method is None
        assert param.extraction_path == ""

    def test_parameter_definition_required_fields_only(self) -> None:
        """Test ParameterDefinition with only required fields."""
        param = ParameterDefinition(
            name="minimal",
            param_type=ParameterType.STRING,
        )
        assert param.name == "minimal"
        assert param.param_type == ParameterType.STRING
        assert param.description == ""
        assert param.default is None


class TestParameterRegistry:
    """Tests for PARAMETER_REGISTRY."""

    def test_registry_is_not_empty(self) -> None:
        """Test that the registry contains parameters."""
        assert len(PARAMETER_REGISTRY) > 0

    def test_registry_has_core_parameters(self) -> None:
        """Test that registry contains core parameters."""
        core_params = [
            "user_id",
            "tenant_id",
            "user_message",
            "conversation_id",
        ]
        for param_name in core_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_registry_has_business_foundation_parameters(self) -> None:
        """Test that registry contains business foundation parameters."""
        business_params = [
            "business_foundation",
            "core_values",
            "mission_statement",
            "vision_statement",
            "company_name",
            "industry",
        ]
        for param_name in business_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_registry_has_goal_parameters(self) -> None:
        """Test that registry contains goal parameters."""
        goal_params = [
            "goal_id",
            "goal",
            "goal_title",
            "goal_description",
            "goals_list",
        ]
        for param_name in goal_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_registry_has_user_input_parameters(self) -> None:
        """Test that registry contains user input parameters."""
        user_params = [
            "user_message",
            "user_input",
            "topic",
        ]
        for param_name in user_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_conversation_context_is_not_template_parameter(self) -> None:
        """Test that conversation context params are NOT in template registry.

        Conversation context (history, summary, previous_response) is handled via
        message passing to the LLM, not as template parameters. The LLM can generate
        summaries from the message history when needed (e.g., resume prompts).
        """
        # These should NOT be template parameters
        removed_params = ["conversation_history", "conversation_summary", "previous_response"]
        for param_name in removed_params:
            assert param_name not in PARAMETER_REGISTRY, (
                f"Parameter {param_name} should not be in registry - "
                "conversation context is handled via message passing"
            )

    def test_all_parameters_have_name(self) -> None:
        """Test that all parameters have matching names."""
        for name, param in PARAMETER_REGISTRY.items():
            assert param.name == name, f"Parameter name mismatch: {name} vs {param.name}"

    def test_all_parameters_have_valid_type(self) -> None:
        """Test that all parameters have valid types."""
        for name, param in PARAMETER_REGISTRY.items():
            assert isinstance(param.param_type, ParameterType), f"Invalid type for: {name}"

    def test_registry_parameter_count(self) -> None:
        """Test that registry has expected minimum parameter count."""
        # We have 67+ parameters across all categories
        assert (
            len(PARAMETER_REGISTRY) >= 50
        ), f"Expected at least 50 parameters, got {len(PARAMETER_REGISTRY)}"


class TestGetParameterDefinition:
    """Tests for get_parameter_definition function."""

    def test_get_existing_parameter(self) -> None:
        """Test getting an existing parameter."""
        param = get_parameter_definition("goal")
        assert param is not None
        assert param.name == "goal"
        assert param.param_type == ParameterType.DICT

    def test_get_non_existing_parameter(self) -> None:
        """Test getting a non-existing parameter returns None."""
        param = get_parameter_definition("non_existing_parameter_xyz")
        assert param is None

    def test_get_string_parameter(self) -> None:
        """Test getting a string type parameter."""
        param = get_parameter_definition("user_id")
        assert param is not None
        assert param.param_type == ParameterType.STRING

    def test_get_list_parameter(self) -> None:
        """Test getting a list type parameter."""
        param = get_parameter_definition("core_values")
        assert param is not None
        assert param.param_type == ParameterType.LIST

    def test_get_dict_parameter(self) -> None:
        """Test getting a dict type parameter."""
        param = get_parameter_definition("business_foundation")
        assert param is not None
        assert param.param_type == ParameterType.DICT


class TestGetParametersByRetrievalMethod:
    """Tests for get_parameters_by_retrieval_method function."""

    def test_get_business_foundation_parameters(self) -> None:
        """Test getting parameters using get_business_foundation method."""
        params = get_parameters_by_retrieval_method("get_business_foundation")
        assert len(params) > 0
        param_names = [p.name for p in params]
        assert "core_values" in param_names
        assert "mission_statement" in param_names
        assert "vision_statement" in param_names

    def test_get_goal_by_id_parameters(self) -> None:
        """Test getting parameters using get_goal_by_id method."""
        params = get_parameters_by_retrieval_method("get_goal_by_id")
        assert len(params) > 0
        param_names = [p.name for p in params]
        assert "goal" in param_names
        assert "goal_title" in param_names

    def test_conversation_context_not_in_retrieval_methods(self) -> None:
        """Test that conversation context is not retrieved via retrieval methods.

        Conversation context is handled via message passing to the LLM,
        not as template parameters retrieved from external APIs.
        """
        params = get_parameters_by_retrieval_method("get_conversation_context")
        assert len(params) == 0  # No retrieval method for conversation context

        # Verify these params don't exist in registry (handled via message passing)
        assert get_parameter_definition("conversation_history") is None
        assert get_parameter_definition("conversation_summary") is None
        assert get_parameter_definition("previous_response") is None

    def test_get_nonexistent_method_returns_empty(self) -> None:
        """Test that nonexistent retrieval method returns empty list."""
        params = get_parameters_by_retrieval_method("nonexistent_method")
        assert params == []


class TestGetEnrichableParameters:
    """Tests for get_enrichable_parameters function."""

    def test_returns_only_enrichable(self) -> None:
        """Test that only parameters with retrieval_method are returned."""
        enrichable = get_enrichable_parameters()
        for param in enrichable:
            assert param.retrieval_method is not None

    def test_enrichable_includes_business_foundation(self) -> None:
        """Test that business foundation params are enrichable."""
        enrichable = get_enrichable_parameters()
        names = [p.name for p in enrichable]
        assert "core_values" in names
        assert "mission_statement" in names

    def test_enrichable_includes_goal_params(self) -> None:
        """Test that goal params are enrichable."""
        enrichable = get_enrichable_parameters()
        names = [p.name for p in enrichable]
        assert "goal" in names
        assert "goal_title" in names

    def test_non_enrichable_excluded(self) -> None:
        """Test that params without retrieval method are excluded."""
        enrichable = get_enrichable_parameters()
        names = [p.name for p in enrichable]
        # user_message doesn't have retrieval method
        assert "user_message" not in names


class TestGetAllParameterNames:
    """Tests for get_all_parameter_names function."""

    def test_returns_all_names(self) -> None:
        """Test that all parameter names are returned."""
        names = get_all_parameter_names()
        assert len(names) == len(PARAMETER_REGISTRY)

    def test_returns_list_of_strings(self) -> None:
        """Test that returned items are strings."""
        names = get_all_parameter_names()
        for name in names:
            assert isinstance(name, str)

    def test_contains_expected_names(self) -> None:
        """Test that expected names are in the list."""
        names = get_all_parameter_names()
        assert "user_id" in names
        assert "tenant_id" in names
        assert "goal" in names


class TestValidateParameterName:
    """Tests for validate_parameter_name function."""

    def test_valid_parameter_name(self) -> None:
        """Test validating an existing parameter name."""
        assert validate_parameter_name("user_id") is True
        assert validate_parameter_name("goal") is True

    def test_invalid_parameter_name(self) -> None:
        """Test validating a non-existing parameter name."""
        assert validate_parameter_name("nonexistent_param") is False
        assert validate_parameter_name("") is False


class TestRetrievalMethodExtraction:
    """Tests for retrieval method and extraction path configuration."""

    def test_business_foundation_extraction_paths(self) -> None:
        """Test that business foundation params have correct extraction paths."""
        core_values = get_parameter_definition("core_values")
        assert core_values is not None
        assert core_values.retrieval_method == "get_business_foundation"
        assert core_values.extraction_path == "core_values"

        mission = get_parameter_definition("mission_statement")
        assert mission is not None
        assert mission.retrieval_method == "get_business_foundation"
        assert mission.extraction_path == "mission_statement"

    def test_goal_extraction_paths(self) -> None:
        """Test that goal params have correct extraction paths."""
        goal_title = get_parameter_definition("goal_title")
        assert goal_title is not None
        assert goal_title.retrieval_method == "get_goal_by_id"
        assert goal_title.extraction_path == "title"

    def test_conversation_params_not_in_registry(self) -> None:
        """Test that conversation params are NOT template parameters.

        Conversation context (history, summary, previous_response) is handled
        via message passing to the LLM, not as template parameters. The LLM
        generates summaries from the message history when needed.
        """
        # These params should NOT exist in the registry
        assert get_parameter_definition("conversation_history") is None
        assert get_parameter_definition("conversation_summary") is None
        assert get_parameter_definition("previous_response") is None

    def test_full_object_extraction(self) -> None:
        """Test params that return full objects (empty extraction_path)."""
        bf = get_parameter_definition("business_foundation")
        assert bf is not None
        assert bf.retrieval_method == "get_business_foundation"
        assert bf.extraction_path == ""

        goal = get_parameter_definition("goal")
        assert goal is not None
        assert goal.retrieval_method == "get_goal_by_id"
        assert goal.extraction_path == ""


class TestDefaultValues:
    """Tests for default value configuration."""

    def test_string_defaults(self) -> None:
        """Test string parameters with defaults."""
        user_name = get_parameter_definition("user_name")
        assert user_name is not None
        assert user_name.default == "User"

        topic = get_parameter_definition("topic")
        assert topic is not None
        assert topic.default == ""

    def test_list_defaults(self) -> None:
        """Test list parameters with defaults."""
        core_values = get_parameter_definition("core_values")
        assert core_values is not None
        assert core_values.default == []

    def test_integer_defaults(self) -> None:
        """Test integer parameters with defaults."""
        target_length = get_parameter_definition("target_length")
        assert target_length is not None
        assert target_length.default == 500

    def test_parameters_without_defaults(self) -> None:
        """Test parameters that have no default (None)."""
        user_id = get_parameter_definition("user_id")
        assert user_id is not None
        assert user_id.default is None

        user_message = get_parameter_definition("user_message")
        assert user_message is not None
        assert user_message.default is None
