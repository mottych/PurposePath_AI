import pytest
from coaching.src.core.constants import TopicCategory, TopicType
from coaching.src.core.topic_seed_data import TOPIC_SEED_DATA, TopicSeedData

pytestmark = pytest.mark.unit


class TestTopicSeedData:
    """Test suite for topic seed data."""

    def test_topic_seed_data_creation(self) -> None:
        """Test creating a TopicSeedData instance."""
        seed = TopicSeedData(
            topic_id="test_topic",
            topic_name="Test Topic",
            topic_type=TopicType.SINGLE_SHOT.value,
            category=TopicCategory.ANALYSIS.value,
            description="Test description",
            default_system_prompt="System prompt",
            default_user_prompt="User prompt",
        )

        assert seed.topic_id == "test_topic"
        assert seed.topic_type == "single_shot"
        assert seed.category == "analysis"
        assert seed.temperature == 0.7  # Default value
        assert seed.max_tokens == 4096  # Default value

    def test_get_all_seed_data(self) -> None:
        """Test retrieving all seed data."""
        seeds = list(TOPIC_SEED_DATA.values())
        assert isinstance(seeds, list)
        assert len(seeds) > 0
        assert all(isinstance(s, TopicSeedData) for s in seeds)

    def test_get_seed_data_for_topic(self) -> None:
        """Test retrieving seed data for a specific topic."""
        # Get a known topic ID from the list
        target_id = next(iter(TOPIC_SEED_DATA.keys()))

        seed = TOPIC_SEED_DATA.get(target_id)
        assert seed is not None
        assert seed.topic_id == target_id

    def test_get_seed_data_for_nonexistent_topic(self) -> None:
        """Test retrieving seed data for a nonexistent topic."""
        seed = TOPIC_SEED_DATA.get("nonexistent_topic_id_12345")
        assert seed is None

    def test_all_topics_use_valid_topic_types(self) -> None:
        """Test that all topics use valid TopicType enum values."""
        valid_types = {t.value for t in TopicType}
        for topic_id, seed in TOPIC_SEED_DATA.items():
            assert seed.topic_type in valid_types, (
                f"Topic '{topic_id}' has invalid type: {seed.topic_type}"
            )

    def test_all_topics_use_valid_categories(self) -> None:
        """Test that all topics use valid TopicCategory enum values."""
        valid_categories = {c.value for c in TopicCategory}
        for topic_id, seed in TOPIC_SEED_DATA.items():
            assert seed.category in valid_categories, (
                f"Topic '{topic_id}' has invalid category: {seed.category}"
            )
