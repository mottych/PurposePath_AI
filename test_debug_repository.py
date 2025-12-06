"""Debug test: Trace through list_all_with_enum_defaults locally."""
import asyncio
import os
from unittest.mock import MagicMock

os.environ["AWS_REGION"] = "us-east-1"
os.environ["TOPICS_TABLE_NAME"] = "purposepath-topics-dev"


async def test():
    """Test repository method."""
    from coaching.src.core.endpoint_registry import ENDPOINT_REGISTRY
    from coaching.src.repositories.topic_repository import TopicRepository

    print(f"✓ ENDPOINT_REGISTRY loaded: {len(ENDPOINT_REGISTRY)} endpoints")

    # Mock DynamoDB
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_table.scan = MagicMock(return_value={"Items": []})
    mock_dynamodb.Table.return_value = mock_table

    # Create repository
    repo = TopicRepository(dynamodb_resource=mock_dynamodb, table_name="test")

    print("\nCalling list_all_with_enum_defaults(include_inactive=True)...")
    topics = await repo.list_all_with_enum_defaults(include_inactive=True)

    print(f"\n✓ Returned {len(topics)} topics")
    print(f"✓ Expected {len(ENDPOINT_REGISTRY)} topics")

    if len(topics) == len(ENDPOINT_REGISTRY):
        print("\n✅ SUCCESS! Method works correctly")
    else:
        print(f"\n❌ FAIL! Expected {len(ENDPOINT_REGISTRY)} but got {len(topics)}")
        print(f"\nFirst few topics: {[t.topic_id for t in topics[:5]]}")


if __name__ == "__main__":
    asyncio.run(test())
