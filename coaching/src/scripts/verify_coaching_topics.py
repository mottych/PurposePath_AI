#!/usr/bin/env python3
"""Verify coaching topics were seeded correctly.

This script checks that all expected coaching topics exist in DynamoDB
and have the correct configuration.
"""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    pass

from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import CoachingTopic
from coaching.src.repositories.topic_repository import TopicRepository

logger = structlog.get_logger()

EXPECTED_TOPICS = [
    CoachingTopic.CORE_VALUES.value,
    CoachingTopic.PURPOSE.value,
    CoachingTopic.VISION.value,
    CoachingTopic.GOALS.value,
]


async def verify_topics() -> dict[str, Any]:
    """Verify all coaching topics exist and are properly configured.

    Returns:
        Dictionary with verification results
    """
    import boto3

    # Initialize repository
    dynamodb: Any = boto3.resource("dynamodb", region_name=settings.aws_region)
    repo = TopicRepository(dynamodb_resource=dynamodb, table_name=settings.llm_prompts_table)

    logger.info(
        "Verifying coaching topics",
        table=settings.llm_prompts_table,
        bucket=settings.prompts_bucket,
    )

    results: dict[str, Any] = {
        "found": [],
        "missing": [],
        "errors": [],
    }

    for topic_id in EXPECTED_TOPICS:
        try:
            topic = await repo.get(topic_id=topic_id)

            if topic:
                # Get parameters from registry, not from entity
                from coaching.src.core.endpoint_registry import get_parameters_for_topic

                params = get_parameters_for_topic(topic_id)
                logger.info(
                    "Topic found",
                    topic_id=topic_id,
                    name=topic.topic_name,
                    type=topic.topic_type,
                    prompts=len(topic.prompts),
                    parameters=len(params),
                    active=topic.is_active,
                )
                results["found"].append(
                    {
                        "topic_id": topic_id,
                        "name": topic.topic_name,
                        "prompts": len(topic.prompts),
                        "parameters": len(params),
                        "active": topic.is_active,
                    }
                )
            else:
                logger.error("Topic NOT FOUND", topic_id=topic_id)
                results["missing"].append(topic_id)

        except Exception as e:
            logger.error("Error verifying topic", topic_id=topic_id, error=str(e))
            results["errors"].append({"topic_id": topic_id, "error": str(e)})

    # List all coaching topics via GSI
    try:
        coaching_topics = await repo.list_by_type(
            topic_type="conversation_coaching", include_inactive=True
        )
        logger.info("Total coaching topics in table", count=len(coaching_topics))
        results["total_in_table"] = len(coaching_topics)
    except Exception as e:
        logger.error("Error listing topics", error=str(e))
        results["list_error"] = str(e)

    return results


def main() -> int:
    """Main entry point for verification script.

    Returns:
        Exit code (0 if all topics found, 1 otherwise)
    """
    try:
        logger.info("=" * 70)
        logger.info("Coaching Topics Verification")
        logger.info("=" * 70)

        results = asyncio.run(verify_topics())

        logger.info("=" * 70)
        logger.info("Verification Results")
        logger.info("=" * 70)
        logger.info(f"✓ Found: {len(results['found'])}/{len(EXPECTED_TOPICS)}")
        logger.info(f"✗ Missing: {len(results['missing'])}")
        logger.info(f"⚠ Errors: {len(results['errors'])}")

        if results["missing"]:
            logger.error("Missing topics", topics=results["missing"])

        if results["errors"]:
            logger.error("Errors encountered", errors=results["errors"])

        logger.info("=" * 70)

        # Return 0 only if all topics found and no errors
        if len(results["found"]) == len(EXPECTED_TOPICS) and not results["errors"]:
            logger.info("✓ All coaching topics verified successfully")
            return 0
        else:
            logger.error("✗ Verification failed - some topics missing or errors occurred")
            return 1

    except Exception as e:
        logger.error("Verification script failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main", "verify_topics"]
