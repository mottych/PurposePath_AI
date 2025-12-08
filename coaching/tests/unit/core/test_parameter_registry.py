"""Tests for parameter registry.

Tests for Issue #123 - Coaching Engine Improvement.
Note: Source information moved to endpoint_registry.py - same parameter can come
from different sources depending on endpoint context.
"""

from coaching.src.core.constants import ParameterType
from coaching.src.core.parameter_registry import (
    PARAMETER_REGISTRY,
    ParameterDefinition,
    get_parameter,
    get_parameters_by_type,
    get_required_parameters,
    list_all_parameters,
)


class TestParameterDefinition:
    """Tests for ParameterDefinition dataclass."""

    def test_parameter_definition_frozen(self) -> None:
        """Test that ParameterDefinition is immutable."""
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
            required=True,
            description="Test parameter",
        )
        # Frozen dataclass should raise error on attribute assignment
        try:
            param.name = "changed"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass  # Expected for frozen dataclass

    def test_parameter_definition_with_default(self) -> None:
        """Test ParameterDefinition with default value."""
        param = ParameterDefinition(
            name="optional_param",
            param_type=ParameterType.STRING,
            required=False,
            description="Optional parameter",
            default="default_value",
        )
        assert param.required is False
        assert param.default == "default_value"

    def test_parameter_definition_no_source_field(self) -> None:
        """Test that source is not part of ParameterDefinition.

        Source is defined per-endpoint in endpoint_registry.py, not here.
        """
        param = ParameterDefinition(
            name="test",
            param_type=ParameterType.STRING,
        )
        assert not hasattr(param, "source") or "source" not in param.__dataclass_fields__


class TestParameterRegistry:
    """Tests for PARAMETER_REGISTRY."""

    def test_registry_is_not_empty(self) -> None:
        """Test that the registry contains parameters."""
        assert len(PARAMETER_REGISTRY) > 0

    def test_registry_has_expected_parameters(self) -> None:
        """Test that registry contains key parameters."""
        expected_params = [
            "url",
            "goal",
            "business_foundation",
            "conversation_history",
            "user_message",
            "alignment_score",
            "kpis",
            "action",  # Not action_item
            "issue",
            "tenant_id",
            "user_id",
        ]
        for param_name in expected_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_all_parameters_have_required_fields(self) -> None:
        """Test that all parameters have required fields populated."""
        for name, param in PARAMETER_REGISTRY.items():
            assert param.name == name, f"Parameter name mismatch: {name}"
            assert isinstance(param.param_type, ParameterType)
            assert isinstance(param.required, bool)
            assert param.description, f"Missing description for: {name}"

    def test_registry_parameter_count(self) -> None:
        """Test that registry has expected parameter count."""
        # Should have 67 parameters based on spec
        assert len(PARAMETER_REGISTRY) >= 60, "Registry should have at least 60 parameters"


class TestGetParameter:
    """Tests for get_parameter function."""

    def test_get_existing_parameter(self) -> None:
        """Test getting an existing parameter."""
        param = get_parameter("goal")
        assert param is not None
        assert param.name == "goal"
        assert param.param_type == ParameterType.OBJECT

    def test_get_non_existing_parameter(self) -> None:
        """Test getting a non-existing parameter returns None."""
        param = get_parameter("non_existing_parameter_xyz")
        assert param is None

    def test_get_string_parameter(self) -> None:
        """Test getting a string type parameter."""
        param = get_parameter("url")
        assert param is not None
        assert param.param_type == ParameterType.STRING

    def test_get_array_parameter(self) -> None:
        """Test getting an array type parameter."""
        param = get_parameter("conversation_history")
        assert param is not None
        assert param.param_type == ParameterType.ARRAY


class TestGetParametersByType:
    """Tests for get_parameters_by_type function."""

    def test_get_string_parameters(self) -> None:
        """Test getting STRING type parameters."""
        params = get_parameters_by_type(ParameterType.STRING)
        assert len(params) > 0
        for param in params:
            assert param.param_type == ParameterType.STRING

    def test_get_object_parameters(self) -> None:
        """Test getting OBJECT type parameters."""
        params = get_parameters_by_type(ParameterType.OBJECT)
        assert len(params) > 0
        for param in params:
            assert param.param_type == ParameterType.OBJECT

    def test_get_array_parameters(self) -> None:
        """Test getting ARRAY type parameters."""
        params = get_parameters_by_type(ParameterType.ARRAY)
        assert len(params) > 0
        for param in params:
            assert param.param_type == ParameterType.ARRAY

    def test_get_integer_parameters(self) -> None:
        """Test getting INTEGER type parameters."""
        params = get_parameters_by_type(ParameterType.INTEGER)
        # May be empty or have items
        for param in params:
            assert param.param_type == ParameterType.INTEGER


class TestGetRequiredParameters:
    """Tests for get_required_parameters function."""

    def test_returns_only_required(self) -> None:
        """Test that only required parameters are returned."""
        required = get_required_parameters()
        for param in required:
            assert param.required is True

    def test_required_includes_core_params(self) -> None:
        """Test that core required parameters are included."""
        required = get_required_parameters()
        required_names = [p.name for p in required]
        # These should be required
        assert "tenant_id" in required_names
        assert "user_id" in required_names


class TestListAllParameters:
    """Tests for list_all_parameters function."""

    def test_returns_all_parameters(self) -> None:
        """Test that all parameters are returned."""
        all_params = list_all_parameters()
        assert len(all_params) == len(PARAMETER_REGISTRY)

    def test_returns_list_of_definitions(self) -> None:
        """Test that returned items are ParameterDefinition."""
        all_params = list_all_parameters()
        for param in all_params:
            assert isinstance(param, ParameterDefinition)
