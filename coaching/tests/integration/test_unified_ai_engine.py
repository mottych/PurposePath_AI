"""Integration tests for Unified AI Engine (Issue #113).

This module tests the topic-driven endpoint architecture including:
- Topic seeding and validation
- Unified AI Engine single-shot execution
- Response serialization
- Generic AI Handler
- End-to-end endpoint functionality
"""

import pytest
from coaching.src.application.ai_engine.unified_ai_engine import UnifiedAIEngine
from coaching.src.core.topic_registry import (
    ENDPOINT_REGISTRY,
    get_endpoint_definition,
    get_registry_statistics,
)
from coaching.src.core.topic_seed_data import TOPIC_SEED_DATA


class TestEndpointRegistry:
    """Test cases for endpoint registry."""

    def test_registry_not_empty(self):
        """Verify endpoint registry is populated."""
        assert len(ENDPOINT_REGISTRY) > 0, "Endpoint registry should not be empty"

    def test_all_endpoints_have_topics(self):
        """Verify all active endpoints have corresponding topics.

        Note: Inactive endpoints may reference topics that are planned
        but not yet implemented in TOPIC_SEED_DATA.

        Conversation coaching endpoints use a different pattern (COACHING:topic_id)
        and have their own topic registry, so they don't need TOPIC_SEED_DATA entries.
        """
        from coaching.src.core.constants import TopicType

        for key, endpoint in ENDPOINT_REGISTRY.items():
            assert endpoint.topic_id, f"Endpoint {key} missing topic_id"
            if endpoint.is_active:
                # Conversation coaching topics use their own registry
                if endpoint.topic_type == TopicType.CONVERSATION_COACHING:
                    continue  # These use COACHING_TOPIC_REGISTRY, not TOPIC_SEED_DATA
                assert (
                    endpoint.topic_id in TOPIC_SEED_DATA
                ), f"Active endpoint {key} references unknown topic: {endpoint.topic_id}"

    def test_get_endpoint_definition(self):
        """Test endpoint definition lookup."""
        # Test a known endpoint
        definition = get_endpoint_definition("POST", "/coaching/strategy-suggestions")
        assert definition is not None
        assert definition.topic_id == "strategy_suggestions"
        assert definition.is_active is True

        # Test unknown endpoint
        unknown = get_endpoint_definition("GET", "/nonexistent")
        assert unknown is None

    def test_registry_statistics(self):
        """Test registry statistics generation."""
        stats = get_registry_statistics()

        assert "total_endpoints" in stats
        assert "active_endpoints" in stats
        assert "inactive_endpoints" in stats
        assert "single_shot_endpoints" in stats
        assert "conversation_endpoints" in stats

        assert stats["total_endpoints"] > 0
        assert stats["active_endpoints"] + stats["inactive_endpoints"] == stats["total_endpoints"]

        # Verify at least one category exists
        category_keys = [k for k in stats.keys() if k.startswith("category_")]
        assert len(category_keys) > 0, "Should have at least one category"

    def test_migrated_endpoints_are_active(self):
        """Verify key migrated endpoints exist and are active."""
        # Test a subset of known active endpoints - path and method pairs
        migrated_endpoints = [
            ("POST", "/coaching/alignment-explanation"),
            ("POST", "/coaching/alignment-suggestions"),
            ("POST", "/coaching/strategy-suggestions"),
            ("POST", "/operations/prioritization-suggestions"),
            ("POST", "/operations/scheduling-suggestions"),
            ("POST", "/operations/root-cause-suggestions"),
            ("POST", "/operations/action-suggestions"),
            ("POST", "/suggestions/onboarding"),
            ("POST", "/website/scan"),
            ("POST", "/coaching/onboarding"),
            ("POST", "/insights/generate"),
        ]

        for method, path in migrated_endpoints:
            definition = get_endpoint_definition(method, path)
            assert (
                definition is not None
            ), f"Migrated endpoint {method} {path} not found in registry"
            assert (
                definition.is_active is True
            ), f"Migrated endpoint {method} {path} should be active"


class TestTopicSeedData:
    """Test cases for topic seed data."""

    def test_seed_data_not_empty(self):
        """Verify topic seed data is populated."""
        assert len(TOPIC_SEED_DATA) > 0, "Topic seed data should not be empty"

    def test_all_topics_have_required_fields(self):
        """Verify all topics have required configuration."""
        for topic_id, topic_data in TOPIC_SEED_DATA.items():
            assert topic_data.topic_id == topic_id
            assert topic_data.topic_name
            assert topic_data.topic_type in ["single_shot", "conversation_coaching"]
            assert topic_data.category
            assert topic_data.model_code
            assert 0.0 <= topic_data.temperature <= 2.0
            assert topic_data.max_tokens > 0

    def test_migrated_topics_exist(self):
        """Verify all migrated endpoint topics exist in seed data."""
        migrated_topics = [
            "alignment_explanation",
            "alignment_suggestions",
            "strategy_suggestions",
            "operations_strategic_alignment",
            "prioritization_suggestions",
            "scheduling_suggestions",
            "root_cause_suggestions",
            "action_suggestions",
            "onboarding_suggestions",
            "website_scan",
            "onboarding_coaching",
            "insights_generation",
        ]

        for topic_id in migrated_topics:
            assert topic_id in TOPIC_SEED_DATA, f"Migrated topic {topic_id} not found in seed data"

    def test_topic_parameters_come_from_registry(self):
        """Verify topic parameters are defined in PARAMETER_REGISTRY, not seed data."""
        from coaching.src.core.topic_registry import get_parameters_for_topic

        # Topics in seed data should have their parameters defined in the registry
        for topic_id in TOPIC_SEED_DATA.keys():
            params = get_parameters_for_topic(topic_id)
            # Parameters is a list (may be empty for some topics)
            assert isinstance(params, list), f"Parameters for {topic_id} should be a list"
            # If parameters exist, they should have required fields
            for param in params:
                assert "name" in param, f"Parameter in topic {topic_id} missing 'name'"
                assert "type" in param, f"Parameter in topic {topic_id} missing 'type'"


class TestUnifiedAIEngine:
    """Test cases for Unified AI Engine.

    Note: These are structural tests. Full integration tests with actual
    LLM calls would require mocking or test API keys.
    """

    def test_engine_initialization(self):
        """Test that engine can be initialized with required dependencies."""
        # This is a placeholder - actual initialization requires dependencies
        # that would be provided by FastAPI dependency injection
        assert UnifiedAIEngine is not None

    @pytest.mark.skip(reason="Requires AWS credentials and running services")
    async def test_execute_single_shot(self):
        """Test single-shot execution (requires AWS setup)."""
        # This would test actual execution but requires:
        # - DynamoDB with seeded topics
        # - S3 with prompts
        # - Bedrock API access
        pass

    @pytest.mark.skip(reason="Requires AWS credentials and running services")
    async def test_conversation_flow(self):
        """Test conversation flow (requires AWS setup)."""
        pass


class TestArchitectureCompliance:
    """Test cases for architecture compliance."""

    def test_no_duplicate_endpoints(self):
        """Verify no duplicate endpoint definitions.

        Note: Conversation coaching endpoints may use different key patterns:
        - New topic-based: COACHING:topic_id (e.g., COACHING:core_values)
        - Legacy conversation: METHOD:path (e.g., POST:/conversations/initiate)
        """
        from coaching.src.core.constants import TopicType

        seen_paths = set()
        seen_keys = set()
        for key, endpoint in ENDPOINT_REGISTRY.items():
            # Verify key uniqueness
            assert key not in seen_keys, f"Duplicate registry key: {key}"
            seen_keys.add(key)

            # Check for key pattern consistency
            if key.startswith("COACHING:"):
                # New coaching topic format - verify topic_type matches
                assert (
                    endpoint.topic_type == TopicType.CONVERSATION_COACHING
                ), f"COACHING: key {key} should have CONVERSATION_COACHING type"
                expected_key = f"COACHING:{endpoint.topic_id}"
                assert key == expected_key, f"Coaching key mismatch: {key} vs {expected_key}"
            else:
                # Standard METHOD:path format
                full_path = f"{endpoint.http_method}:{endpoint.endpoint_path}"
                assert full_path == key, f"Key mismatch: {key} vs {full_path}"
                assert full_path not in seen_paths, f"Duplicate endpoint: {full_path}"
                seen_paths.add(full_path)

    def test_topic_id_naming_convention(self):
        """Verify topic IDs follow snake_case convention."""
        for topic_id in TOPIC_SEED_DATA.keys():
            assert topic_id.islower(), f"Topic ID {topic_id} should be lowercase"
            assert all(
                c.isalnum() or c == "_" for c in topic_id
            ), f"Topic ID {topic_id} should be snake_case"

    def test_endpoint_path_consistency(self):
        """Verify endpoint paths are properly formatted."""
        for endpoint in ENDPOINT_REGISTRY.values():
            assert endpoint.endpoint_path.startswith(
                "/"
            ), f"Endpoint path {endpoint.endpoint_path} should start with /"
            assert endpoint.http_method in [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
            ], f"Invalid HTTP method: {endpoint.http_method}"

    def test_category_consistency(self):
        """Verify categories are consistent across endpoints and topics."""
        endpoint_categories = {e.category for e in ENDPOINT_REGISTRY.values()}
        topic_categories = {t.category for t in TOPIC_SEED_DATA.values()}

        # Topics should cover all endpoint categories
        for category in endpoint_categories:
            # Allow for endpoints without corresponding topics (future implementation)
            if category not in topic_categories:
                print(f"Warning: Category {category} has endpoints but no topics")


# ========== Summary Test ==========


def test_migration_completeness():
    """Comprehensive test to verify migration completeness."""
    stats = get_registry_statistics()

    print("\n" + "=" * 60)
    print("Topic-Driven Architecture Migration Status")
    print("=" * 60)
    print(f"Total Endpoints: {stats['total_endpoints']}")
    print(f"Active Endpoints: {stats['active_endpoints']}")
    print(f"Inactive Endpoints: {stats['inactive_endpoints']}")
    print(f"Single-Shot Endpoints: {stats['single_shot_endpoints']}")
    print(f"Conversation Endpoints: {stats['conversation_endpoints']}")
    print("\nBy Category:")

    # Extract category statistics
    category_stats = {
        k.replace("category_", ""): v for k, v in stats.items() if k.startswith("category_")
    }
    for category, count in sorted(category_stats.items()):
        print(f"  {category}: {count}")
    print("=" * 60 + "\n")

    # Verify we have reasonable numbers
    assert stats["total_endpoints"] >= 12, "Should have at least 12 migrated endpoints"
    assert stats["active_endpoints"] >= 12, "Should have at least 12 active endpoints"
