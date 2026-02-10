"""Fix script to update model codes from literal names to registry codes.

This script updates the basic_model_code and premium_model_code for coaching topics
that have the old literal model names instead of the new model registry codes.

Migration: claude-3-5-sonnet-20241022 -> CLAUDE_3_5_SONNET_V2
"""

import asyncio

import boto3

from coaching.src.core.config_multitenant import settings
from coaching.src.repositories.topic_repository import TopicRepository


async def fix_model_codes():
    """Update model codes for all coaching topics."""
    print("=" * 80)
    print("FIX COACHING TOPIC MODEL CODES")
    print("=" * 80)
    print()

    # Initialize DynamoDB
    dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
    topic_repo = TopicRepository(
        dynamodb_resource=dynamodb_resource,
        table_name=settings.topics_table,
    )

    # Get all active topics
    all_topics = await topic_repo.list_all(include_inactive=False)

    # Find topics with old model names
    topics_to_fix = []
    for t in all_topics:
        needs_fix = False
        if t.basic_model_code == "claude-3-5-sonnet-20241022":
            needs_fix = True
        if t.premium_model_code == "claude-3-5-sonnet-20241022":
            needs_fix = True

        if needs_fix:
            topics_to_fix.append(t)

    print(f"Found {len(topics_to_fix)} topics to fix:\n")

    if not topics_to_fix:
        print("No topics need fixing!")
        return

    for topic in topics_to_fix:
        print(f"  - {topic.topic_id}: {topic.topic_name}")
        print(f"    Current basic_model_code: {topic.basic_model_code}")
        print(f"    Current premium_model_code: {topic.premium_model_code}")
        print("    New codes: CLAUDE_3_5_SONNET_V2")
        print()

    # Auto-confirm for automation
    print("Auto-confirming update...")
    print()

    print()
    print("Updating topics...")

    for topic in topics_to_fix:
        try:
            # Update the model codes
            if topic.basic_model_code == "claude-3-5-sonnet-20241022":
                topic.basic_model_code = "CLAUDE_3_5_SONNET_V2"
            if topic.premium_model_code == "claude-3-5-sonnet-20241022":
                topic.premium_model_code = "CLAUDE_3_5_SONNET_V2"

            await topic_repo.update(topic=topic)
            print(f"  [SUCCESS] Updated {topic.topic_id}")
        except Exception as e:
            print(f"  [ERROR] Failed to update {topic.topic_id}: {e}")

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print("Please test the coaching session endpoints to verify the fix.")


if __name__ == "__main__":
    asyncio.run(fix_model_codes())
