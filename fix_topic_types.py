"""Fix script to update topic_type from 'conversation_coaching' to 'conversation'.

This script updates the topic_type for coaching topics that were incorrectly
set to 'conversation_coaching' when they should be 'conversation'.
"""

import asyncio

import boto3

from coaching.src.core.config_multitenant import settings
from coaching.src.repositories.topic_repository import TopicRepository


async def fix_topic_types():
    """Update topic_type for conversation coaching topics."""
    print("=" * 80)
    print("FIX COACHING TOPIC TYPES")
    print("=" * 80)
    print()

    # Initialize DynamoDB
    dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
    topic_repo = TopicRepository(
        dynamodb_resource=dynamodb_resource,
        table_name=settings.topics_table,
    )

    # Get all topics
    all_topics = await topic_repo.list_all(include_inactive=False)

    # Find topics with wrong topic_type
    topics_to_fix = [t for t in all_topics if t.topic_type == "conversation_coaching"]

    print(f"Found {len(topics_to_fix)} topics to fix:\n")

    if not topics_to_fix:
        print("No topics need fixing!")
        return

    for topic in topics_to_fix:
        print(f"  - {topic.topic_id}: {topic.topic_name}")
        print(f"    Current type: {topic.topic_type}")
        print("    New type: conversation")

    print()
    response = input("Update these topics? (yes/no): ")

    if response.lower() != "yes":
        print("Aborted.")
        return

    print()
    print("Updating topics...")

    for topic in topics_to_fix:
        try:
            # Update the topic_type
            topic.topic_type = "conversation"
            await topic_repo.update(topic=topic)
            print(f"  [SUCCESS] Updated {topic.topic_id}")
        except Exception as e:
            print(f"  [ERROR] Failed to update {topic.topic_id}: {e}")

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print("Please run diagnose_coaching_errors.py again to verify the fix.")


if __name__ == "__main__":
    asyncio.run(fix_topic_types())
