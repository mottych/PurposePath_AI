import pytest
from coaching.src.core.topic_seed_data import TOPIC_SEED_DATA, TopicSeedData

pytestmark = pytest.mark.unit


class TestTopicSeedData:
    """Test suite for topic seed data."""

    def test_topic_seed_data_creation(self) -> None:
        """Test creating a TopicSeedData instance."""
        seed = TopicSeedData(
            topic_id="test_topic",
            topic_name="Test Topic",
            topic_type="test_type",
            category="test_category",
            description="Test description",
            default_system_prompt="System prompt",
            default_user_prompt="User prompt",
        )

        assert seed.topic_id == "test_topic"
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
