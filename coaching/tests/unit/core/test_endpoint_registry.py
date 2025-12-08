"""Tests for endpoint registry.

Tests for Issue #123 - Coaching Engine Improvement.
"""

from coaching.src.core.constants import TopicCategory, TopicType
from coaching.src.core.endpoint_registry import (
    ENDPOINT_REGISTRY,
    EndpointDefinition,
    get_endpoint_by_topic_id,
    get_endpoint_definition,
    get_registry_statistics,
    get_topic_for_endpoint,
    list_all_endpoints,
    list_endpoints_by_category,
    list_endpoints_by_topic_type,
    validate_registry,
)


class TestEndpointDefinition:
    """Tests for EndpointDefinition dataclass."""

    def test_endpoint_definition_frozen(self) -> None:
        """Test that EndpointDefinition is immutable."""
        endpoint = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test_topic",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test endpoint",
        )
        # Frozen dataclass should raise error on attribute assignment
        try:
            endpoint.endpoint_path = "/changed"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass  # Expected for frozen dataclass

    def test_endpoint_definition_with_parameter_refs(self) -> None:
        """Test EndpointDefinition with parameter references."""
        endpoint = EndpointDefinition(
            endpoint_path="/test",
            http_method="POST",
            topic_id="test_topic",
            response_model="TestResponse",
            topic_type=TopicType.SINGLE_SHOT,
            category=TopicCategory.ANALYSIS,
            description="Test endpoint",
            parameter_refs=("goal", "business_foundation"),
        )
        assert len(endpoint.parameter_refs) == 2
        assert "goal" in endpoint.parameter_refs


class TestEndpointRegistry:
    """Tests for ENDPOINT_REGISTRY."""

    def test_registry_is_not_empty(self) -> None:
        """Test that the registry contains endpoints."""
        assert len(ENDPOINT_REGISTRY) > 0

    def test_registry_has_expected_endpoints(self) -> None:
        """Test that registry contains key endpoints."""
        expected_keys = [
            "POST:/coaching/alignment-check",
            "POST:/conversations/initiate",
            "POST:/analysis/alignment",
        ]
        for key in expected_keys:
            assert key in ENDPOINT_REGISTRY, f"Missing endpoint: {key}"

    def test_all_endpoints_have_required_fields(self) -> None:
        """Test that all endpoints have required fields populated."""
        for key, endpoint in ENDPOINT_REGISTRY.items():
            assert endpoint.endpoint_path, f"Missing endpoint_path: {key}"
            assert endpoint.http_method, f"Missing http_method: {key}"
            assert endpoint.topic_id, f"Missing topic_id: {key}"
            assert endpoint.response_model, f"Missing response_model: {key}"
            assert isinstance(endpoint.topic_type, TopicType), f"Invalid topic_type: {key}"
            assert isinstance(endpoint.category, TopicCategory), f"Invalid category: {key}"
            assert endpoint.description, f"Missing description: {key}"

    def test_all_endpoints_have_valid_methods(self) -> None:
        """Test that all endpoints have valid HTTP methods."""
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        for key, endpoint in ENDPOINT_REGISTRY.items():
            assert (
                endpoint.http_method.upper() in valid_methods
            ), f"Invalid method for {key}: {endpoint.http_method}"


class TestGetEndpointDefinition:
    """Tests for get_endpoint_definition function."""

    def test_get_existing_endpoint(self) -> None:
        """Test getting an existing endpoint."""
        endpoint = get_endpoint_definition("POST", "/coaching/alignment-check")
        assert endpoint is not None
        assert endpoint.topic_id == "alignment_check"

    def test_get_non_existing_endpoint(self) -> None:
        """Test getting a non-existing endpoint returns None."""
        endpoint = get_endpoint_definition("POST", "/non/existing/path")
        assert endpoint is None

    def test_get_endpoint_case_insensitive_method(self) -> None:
        """Test that method lookup is case-insensitive."""
        endpoint1 = get_endpoint_definition("POST", "/coaching/alignment-check")
        endpoint2 = get_endpoint_definition("post", "/coaching/alignment-check")
        assert endpoint1 == endpoint2


class TestListEndpointsByCategory:
    """Tests for list_endpoints_by_category function."""

    def test_list_analysis_category(self) -> None:
        """Test listing ANALYSIS category endpoints."""
        endpoints = list_endpoints_by_category(TopicCategory.ANALYSIS)
        assert len(endpoints) > 0
        for endpoint in endpoints:
            assert endpoint.category == TopicCategory.ANALYSIS

    def test_list_strategic_planning_category(self) -> None:
        """Test listing STRATEGIC_PLANNING category endpoints."""
        endpoints = list_endpoints_by_category(TopicCategory.STRATEGIC_PLANNING)
        assert len(endpoints) > 0
        for endpoint in endpoints:
            assert endpoint.category == TopicCategory.STRATEGIC_PLANNING


class TestListEndpointsByTopicType:
    """Tests for list_endpoints_by_topic_type function."""

    def test_list_single_shot_endpoints(self) -> None:
        """Test listing SINGLE_SHOT type endpoints."""
        endpoints = list_endpoints_by_topic_type(TopicType.SINGLE_SHOT)
        assert len(endpoints) > 0
        for endpoint in endpoints:
            assert endpoint.topic_type == TopicType.SINGLE_SHOT

    def test_list_conversation_endpoints(self) -> None:
        """Test listing CONVERSATION_COACHING type endpoints."""
        endpoints = list_endpoints_by_topic_type(TopicType.CONVERSATION_COACHING)
        assert len(endpoints) > 0
        for endpoint in endpoints:
            assert endpoint.topic_type == TopicType.CONVERSATION_COACHING


class TestListAllEndpoints:
    """Tests for list_all_endpoints function."""

    def test_list_all_returns_all_when_inactive_included(self) -> None:
        """Test that inactive endpoints are included when active_only=False."""
        all_endpoints = list_all_endpoints(active_only=False)
        active_endpoints = list_all_endpoints(active_only=True)
        assert len(all_endpoints) >= len(active_endpoints)

    def test_list_active_only(self) -> None:
        """Test that only active endpoints are returned by default."""
        active_endpoints = list_all_endpoints(active_only=True)
        for endpoint in active_endpoints:
            assert endpoint.is_active is True


class TestGetTopicForEndpoint:
    """Tests for get_topic_for_endpoint function."""

    def test_get_topic_for_existing_endpoint(self) -> None:
        """Test getting topic ID for existing endpoint."""
        topic_id = get_topic_for_endpoint("POST", "/coaching/alignment-check")
        assert topic_id == "alignment_check"

    def test_get_topic_for_non_existing_endpoint(self) -> None:
        """Test getting topic ID for non-existing endpoint returns None."""
        topic_id = get_topic_for_endpoint("POST", "/non/existing")
        assert topic_id is None


class TestGetEndpointByTopicId:
    """Tests for get_endpoint_by_topic_id function."""

    def test_get_endpoint_by_topic(self) -> None:
        """Test getting endpoint by topic ID."""
        endpoint = get_endpoint_by_topic_id("alignment_check")
        assert endpoint is not None
        assert endpoint.topic_id == "alignment_check"

    def test_get_endpoint_by_non_existing_topic(self) -> None:
        """Test getting endpoint by non-existing topic returns None."""
        endpoint = get_endpoint_by_topic_id("non_existing_topic_xyz")
        assert endpoint is None


class TestValidateRegistry:
    """Tests for validate_registry function."""

    def test_validate_returns_dict(self) -> None:
        """Test that validate_registry returns a dictionary."""
        results = validate_registry()
        assert isinstance(results, dict)
        assert "duplicate_topics" in results
        assert "invalid_methods" in results
        assert "missing_descriptions" in results

    def test_no_invalid_methods(self) -> None:
        """Test that there are no invalid HTTP methods."""
        results = validate_registry()
        assert len(results["invalid_methods"]) == 0

    def test_no_missing_descriptions(self) -> None:
        """Test that all endpoints have descriptions."""
        results = validate_registry()
        assert len(results["missing_descriptions"]) == 0


class TestGetRegistryStatistics:
    """Tests for get_registry_statistics function."""

    def test_statistics_returns_expected_keys(self) -> None:
        """Test that statistics returns expected keys."""
        stats = get_registry_statistics()
        assert "total_endpoints" in stats
        assert "active_endpoints" in stats
        assert "inactive_endpoints" in stats
        assert "conversation_endpoints" in stats
        assert "single_shot_endpoints" in stats

    def test_statistics_counts_are_consistent(self) -> None:
        """Test that statistics counts are consistent."""
        stats = get_registry_statistics()
        assert stats["total_endpoints"] == (stats["active_endpoints"] + stats["inactive_endpoints"])

    def test_endpoint_counts_match_registry(self) -> None:
        """Test that endpoint counts match registry size."""
        stats = get_registry_statistics()
        assert stats["total_endpoints"] == len(ENDPOINT_REGISTRY)
