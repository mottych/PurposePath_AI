#!/usr/bin/env python3
"""Seed coaching topics from enum into unified LLM topics table.

Run once after infrastructure deployment to migrate existing coaching
topics into the new unified DynamoDB table structure.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import CoachingTopic
from coaching.src.domain.entities.llm_topic import LLMTopic, ParameterDefinition, PromptInfo
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage

logger = structlog.get_logger()

# Mapping of coaching topics to their configurations
COACHING_TOPICS_CONFIG: dict[CoachingTopic, dict[str, Any]] = {
    CoachingTopic.CORE_VALUES: {
        "topic_name": "Core Values Discovery",
        "description": "Discover your core values through guided conversation",
        "display_order": 1,
        "allowed_parameters": [
            {
                "name": "user_name",
                "type": "string",
                "required": True,
                "description": "User's display name",
            },
            {
                "name": "user_id",
                "type": "string",
                "required": True,
                "description": "User identifier",
            },
            {
                "name": "conversation_history",
                "type": "array",
                "required": False,
                "description": "Previous messages",
            },
        ],
        "config": {
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "supports_streaming": True,
            "max_turns": 20,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
        },
    },
    CoachingTopic.PURPOSE: {
        "topic_name": "Life Purpose Exploration",
        "description": "Explore and define your life purpose through reflective dialogue",
        "display_order": 2,
        "allowed_parameters": [
            {
                "name": "user_name",
                "type": "string",
                "required": True,
                "description": "User's display name",
            },
            {
                "name": "user_id",
                "type": "string",
                "required": True,
                "description": "User identifier",
            },
            {
                "name": "conversation_history",
                "type": "array",
                "required": False,
                "description": "Previous messages",
            },
        ],
        "config": {
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "supports_streaming": True,
            "max_turns": 20,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
        },
    },
    CoachingTopic.VISION: {
        "topic_name": "Vision Statement Creation",
        "description": "Create your personal or organizational vision statement",
        "display_order": 3,
        "allowed_parameters": [
            {
                "name": "user_name",
                "type": "string",
                "required": True,
                "description": "User's display name",
            },
            {
                "name": "user_id",
                "type": "string",
                "required": True,
                "description": "User identifier",
            },
            {
                "name": "conversation_history",
                "type": "array",
                "required": False,
                "description": "Previous messages",
            },
        ],
        "config": {
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "supports_streaming": True,
            "max_turns": 20,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
        },
    },
    CoachingTopic.GOALS: {
        "topic_name": "Goal Setting & Planning",
        "description": "Set and plan actionable goals with structured guidance",
        "display_order": 4,
        "allowed_parameters": [
            {
                "name": "user_name",
                "type": "string",
                "required": True,
                "description": "User's display name",
            },
            {
                "name": "user_id",
                "type": "string",
                "required": True,
                "description": "User identifier",
            },
            {
                "name": "conversation_history",
                "type": "array",
                "required": False,
                "description": "Previous messages",
            },
        ],
        "config": {
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "supports_streaming": True,
            "max_turns": 20,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
        },
    },
}


async def migrate_existing_prompts(
    topic_id: str, s3_storage: S3PromptStorage, s3_client: S3Client
) -> list[PromptInfo]:
    """Migrate existing prompts from old format to new format.

    Old: prompts/{topic}/latest.yaml (single file with both prompts)
    New: prompts/{topic_id}/system.md and prompts/{topic_id}/user.md

    Args:
        topic_id: Topic identifier
        s3_storage: S3 prompt storage service
        s3_client: Boto3 S3 client

    Returns:
        List of PromptInfo objects for migrated prompts
    """
    prompts: list[PromptInfo] = []
    old_s3_key = f"prompts/{topic_id}/latest.yaml"

    try:
        # Try to load existing YAML file
        import yaml

        response = s3_client.get_object(Bucket=settings.prompts_bucket, Key=old_s3_key)
        content = response["Body"].read().decode("utf-8")
        old_template: dict[str, Any] = yaml.safe_load(content)

        # Extract prompts
        system_prompt = old_template.get("system_prompt", "")
        user_prompt = old_template.get("user_prompt_template", "")

        # Save to new format (separate markdown files)
        if system_prompt:
            system_key = await s3_storage.save_prompt(
                topic_id=topic_id, prompt_type="system", content=system_prompt
            )
            prompts.append(
                PromptInfo(
                    prompt_type="system",
                    s3_bucket=settings.prompts_bucket,
                    s3_key=system_key,
                    updated_at=datetime.now(UTC),
                    updated_by="seed_script",
                )
            )
            logger.info("Migrated system prompt", topic_id=topic_id)

        if user_prompt:
            user_key = await s3_storage.save_prompt(
                topic_id=topic_id, prompt_type="user", content=user_prompt
            )
            prompts.append(
                PromptInfo(
                    prompt_type="user",
                    s3_bucket=settings.prompts_bucket,
                    s3_key=user_key,
                    updated_at=datetime.now(UTC),
                    updated_by="seed_script",
                )
            )
            logger.info("Migrated user prompt", topic_id=topic_id)

        logger.info("Successfully migrated prompts", topic_id=topic_id, count=len(prompts))

    except Exception as e:
        logger.warning(
            "No existing prompts found for migration",
            topic_id=topic_id,
            error=str(e),
        )
        logger.info("Admin will need to create prompts manually via API", topic_id=topic_id)

    return prompts


async def seed_coaching_topics() -> dict[str, int]:
    """Seed all coaching topics into DynamoDB.

    Returns:
        Dictionary with 'created' and 'skipped' counts
    """
    import boto3

    # Initialize dependencies
    dynamodb: Any = boto3.resource("dynamodb", region_name=settings.aws_region)
    s3_client: S3Client = boto3.client("s3", region_name=settings.aws_region)

    topic_repo = TopicRepository(dynamodb_resource=dynamodb, table_name=settings.llm_prompts_table)
    s3_storage = S3PromptStorage(bucket_name=settings.prompts_bucket, s3_client=s3_client)

    logger.info(
        "Starting coaching topics seed",
        table=settings.llm_prompts_table,
        bucket=settings.prompts_bucket,
    )

    seeded_count = 0
    skipped_count = 0

    for topic_enum, config in COACHING_TOPICS_CONFIG.items():
        topic_id = topic_enum.value

        # Check if already exists
        existing = await topic_repo.get(topic_id=topic_id)
        if existing:
            logger.info("Topic already exists, skipping", topic_id=topic_id)
            skipped_count += 1
            continue

        # Migrate existing prompts if they exist
        prompts = await migrate_existing_prompts(topic_id, s3_storage, s3_client)

        # Extract model configuration from topic config
        model_config = config["config"]

        # Separate core model parameters from additional topic configuration
        model_code = model_config.get("default_model", "anthropic.claude-3-sonnet-20240229-v1:0")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 2000)
        top_p = model_config.get("top_p", 1.0)

        additional_config = {
            key: value
            for key, value in model_config.items()
            if key
            not in {
                "default_model",
                "temperature",
                "max_tokens",
                "top_p",
            }
        }

        # Create topic entity with explicit model configuration
        topic = LLMTopic(
            topic_id=topic_id,
            topic_name=config["topic_name"],
            topic_type="conversation_coaching",
            category="coaching",
            description=config.get("description"),
            display_order=config["display_order"],
            is_active=True,
            model_code=model_code,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            allowed_parameters=[ParameterDefinition(**p) for p in config["allowed_parameters"]],
            prompts=prompts,
            additional_config=additional_config,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="seed_script",
        )

        # Save to DynamoDB
        await topic_repo.create(topic=topic)

        logger.info(
            "Successfully seeded topic",
            topic_id=topic_id,
            topic_name=topic.topic_name,
            prompts_count=len(prompts),
        )
        seeded_count += 1

    logger.info(
        "Seeding complete",
        created=seeded_count,
        skipped=skipped_count,
        total=len(COACHING_TOPICS_CONFIG),
    )

    return {"created": seeded_count, "skipped": skipped_count}


def main() -> int:
    """Main entry point for script execution.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("=" * 70)
        logger.info("Coaching Topics Seed Script")
        logger.info("=" * 70)

        result = asyncio.run(seed_coaching_topics())

        logger.info("=" * 70)
        logger.info(
            "Seed complete",
            created=result["created"],
            skipped=result["skipped"],
        )
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.error("Seed script failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main", "seed_coaching_topics"]
