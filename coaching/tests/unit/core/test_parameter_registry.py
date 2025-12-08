"""Tests for parameter registry.

Tests for Issue #123 - Coaching Engine Improvement.
"""

from coaching.src.core.constants import ParameterSource, ParameterType
from coaching.src.core.parameter_registry import (
    PARAMETER_REGISTRY,
    ParameterDefinition,
    get_parameter,
    get_parameter_names_by_source,
    get_parameters_by_source,
    get_parameters_for_template,
    get_required_parameters,
    list_all_parameters,
)


class TestParameterDefinition:
    """Tests for ParameterDefinition dataclass."""

    def test_parameter_definition_frozen(self) -> None:
        """Test that ParameterDefinition is immutable."""
        param = ParameterDefinition(
            name="test",
            source=ParameterSource.REQUEST,
            source_path="test",
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
            source=ParameterSource.REQUEST,
            source_path="optional_param",
            param_type=ParameterType.STRING,
            required=False,
            description="Optional parameter",
            default="default_value",
        )
        assert param.required is False
        assert param.default == "default_value"


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
        ]
        for param_name in expected_params:
            assert param_name in PARAMETER_REGISTRY, f"Missing parameter: {param_name}"

    def test_all_parameters_have_required_fields(self) -> None:
        """Test that all parameters have required fields populated."""
        for name, param in PARAMETER_REGISTRY.items():
            assert param.name == name, f"Parameter name mismatch: {name}"
            assert isinstance(param.source, ParameterSource)
            assert isinstance(param.param_type, ParameterType)
            assert isinstance(param.required, bool)
            assert param.description, f"Missing description for: {name}"


class TestGetParameter:
    """Tests for get_parameter function."""

    def test_get_existing_parameter(self) -> None:
        """Test getting an existing parameter."""
        param = get_parameter("goal")
        assert param is not None
        assert param.name == "goal"
        assert param.source == ParameterSource.GOAL

    def test_get_non_existing_parameter(self) -> None:
        """Test getting a non-existing parameter returns None."""
        param = get_parameter("non_existing_parameter_xyz")
        assert param is None


class TestGetParametersBySource:
    """Tests for get_parameters_by_source function."""

    def test_get_request_parameters(self) -> None:
        """Test getting REQUEST parameters."""
        params = get_parameters_by_source(ParameterSource.REQUEST)
        assert len(params) > 0
        for param in params:
            assert param.source == ParameterSource.REQUEST

    def test_get_onboarding_parameters(self) -> None:
        """Test getting ONBOARDING parameters."""
        params = get_parameters_by_source(ParameterSource.ONBOARDING)
        assert len(params) > 0
        # Should include business_foundation
        param_names = [p.name for p in params]
        assert "business_foundation" in param_names

    def test_get_goal_parameters(self) -> None:
        """Test getting GOAL parameters."""
        params = get_parameters_by_source(ParameterSource.GOAL)
        assert len(params) > 0
        # Should include goal
        param_names = [p.name for p in params]
        assert "goal" in param_names

    def test_all_sources_have_parameters(self) -> None:
        """Test that most sources have at least one parameter."""
        # Note: Not all sources may have parameters yet
        sources_with_params = [
            ParameterSource.REQUEST,
            ParameterSource.ONBOARDING,
            ParameterSource.GOAL,
            ParameterSource.KPIS,
            ParameterSource.CONVERSATION,
            ParameterSource.COMPUTED,
        ]
        for source in sources_with_params:
            params = get_parameters_by_source(source)
            assert len(params) > 0, f"No parameters for source: {source}"


class TestGetParametersForTemplate:
    """Tests for get_parameters_for_template function."""

    def test_group_params_by_source(self) -> None:
        """Test that parameters are grouped by source."""
        param_names = ["goal", "business_foundation", "user_message"]
        result = get_parameters_for_template(param_names)

        # Should have multiple source groups
        assert len(result) >= 2

        # Verify correct grouping
        assert ParameterSource.GOAL in result
        assert ParameterSource.ONBOARDING in result
        assert ParameterSource.REQUEST in result

    def test_empty_list_returns_empty_dict(self) -> None:
        """Test that empty parameter list returns empty dict."""
        result = get_parameters_for_template([])
        assert result == {}

    def test_unknown_params_are_ignored(self) -> None:
        """Test that unknown parameters are skipped."""
        result = get_parameters_for_template(["unknown_param_xyz"])
        assert result == {}


class TestGetRequiredParameters:
    """Tests for get_required_parameters function."""

    def test_returns_only_required(self) -> None:
        """Test that only required parameters are returned."""
        required = get_required_parameters()
        for param in required:
            assert param.required is True


class TestListAllParameters:
    """Tests for list_all_parameters function."""

    def test_returns_all_parameters(self) -> None:
        """Test that all parameters are returned."""
        all_params = list_all_parameters()
        assert len(all_params) == len(PARAMETER_REGISTRY)


class TestGetParameterNamesBySource:
    """Tests for get_parameter_names_by_source function."""

    def test_returns_names_only(self) -> None:
        """Test that only names are returned."""
        names = get_parameter_names_by_source(ParameterSource.REQUEST)
        assert all(isinstance(name, str) for name in names)
        # Verify actual parameter exists
        for name in names:
            assert name in PARAMETER_REGISTRY
