"""Test admin topics endpoint locally."""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment
os.environ["AWS_REGION"] = "us-east-1"
os.environ["TOPICS_TABLE_NAME"] = "purposepath-topics-dev"


async def test_admin_topics_endpoint():
    """Test that admin topics endpoint returns 48 topics from registry."""
    from coaching.src.api.routes.admin.topics import list_all_topics_with_defaults
    from coaching.src.core.endpoint_registry import ENDPOINT_REGISTRY

    # Mock AWS resources
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_table.scan = MagicMock(return_value={"Items": []})  # Empty DB
    mock_dynamodb.Table.return_value = mock_table

    # Mock request
    from fastapi import Request
    from unittest.mock import MagicMock

    mock_request = MagicMock(spec=Request)

    # Patch boto3.resource
    with patch("boto3.resource", return_value=mock_dynamodb):
        # Call endpoint
        response = await list_all_topics_with_defaults(
            include_inactive=True, request=mock_request
        )

    print(f"✓ ENDPOINT_REGISTRY has {len(ENDPOINT_REGISTRY)} endpoints")
    print(f"✓ API returned {response.total} topics")
    print(f"✓ Topics array length: {len(response.topics)}")

    assert response.total == len(ENDPOINT_REGISTRY), (
        f"Expected {len(ENDPOINT_REGISTRY)} topics, got {response.total}"
    )

    # Show sample topics
    print("\nFirst 10 topics:")
    for topic in response.topics[:10]:
        print(
            f"  - {topic.topic_id}: {topic.topic_name} "
            f"(category={topic.category}, active={topic.is_active})"
        )

    # Count by status
    active_count = sum(1 for t in response.topics if t.is_active)
    print(f"\n✓ Active: {active_count}")
    print(f"✓ Inactive: {response.total - active_count}")

    print("\n✅ Admin topics endpoint works correctly with ENDPOINT_REGISTRY!")


if __name__ == "__main__":
    asyncio.run(test_admin_topics_endpoint())
