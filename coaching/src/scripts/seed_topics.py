#!/usr/bin/env python3
"""Seed all topics from endpoint registry into DynamoDB and S3.

This script uses the TopicSeedingService to automatically seed all 44 topics
from the endpoint registry and topic seed data into their respective stores.

Usage:
    python -m coaching.src.scripts.seed_topics [options]

Options:
    --force-update          Update existing topics with seed data
    --dry-run              Show what would be done without making changes
    --topic-id TOPIC_ID    Seed only a specific topic
    --validate-only        Only run validation without seeding
    --deactivate-orphans   Deactivate topics that no longer have endpoints

Examples:
    # Seed all new topics (skip existing)
    python -m coaching.src.scripts.seed_topics

    # Force update all topics
    python -m coaching.src.scripts.seed_topics --force-update

    # Dry run to see what would happen
    python -m coaching.src.scripts.seed_topics --force-update --dry-run

    # Seed a specific topic
    python -m coaching.src.scripts.seed_topics --topic-id alignment_check --force-update

    # Validate topics without seeding
    python -m coaching.src.scripts.seed_topics --validate-only

    # Deactivate orphaned topics
    python -m coaching.src.scripts.seed_topics --deactivate-orphans
"""

import argparse
import asyncio
import sys

import boto3
import structlog
from coaching.src.core.config_multitenant import settings
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from coaching.src.services.topic_seeding_service import TopicSeedingService

# Configure structured logging
logger = structlog.get_logger()


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str) -> None:
    """Print colored header text."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * len(text))


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.OKCYAN}[i] {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_skipped(text: str) -> None:
    """Print skipped message."""
    print(f"{Colors.OKBLUE}⏭️  {text}{Colors.ENDC}")


async def seed_all_topics(
    seeding_service: TopicSeedingService,
    *,
    force_update: bool = False,
    dry_run: bool = False,
) -> int:
    """Seed all topics from registry.

    Args:
        seeding_service: Topic seeding service instance
        force_update: Whether to update existing topics
        dry_run: Whether to run in dry-run mode

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_header("Topic Seeding Report")
    print_info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print_info(f"Force Update: {force_update}")

    try:
        result = await seeding_service.seed_all_topics(
            force_update=force_update,
            dry_run=dry_run,
        )

        # Display results
        print("\n" + Colors.BOLD + "Results:" + Colors.ENDC)

        if result.created:
            print(f"\n{Colors.OKGREEN}Created Topics ({len(result.created)}):{Colors.ENDC}")
            for topic_id in sorted(result.created):
                print_success(topic_id)

        if result.updated:
            print(f"\n{Colors.OKCYAN}Updated Topics ({len(result.updated)}):{Colors.ENDC}")
            for topic_id in sorted(result.updated):
                print_info(f"{topic_id} (updated configuration)")

        if result.skipped:
            print(f"\n{Colors.OKBLUE}Skipped Topics ({len(result.skipped)}):{Colors.ENDC}")
            for topic_id in sorted(result.skipped):
                print_skipped(f"{topic_id} (already exists, no force-update)")

        if result.deactivated:
            print(f"\n{Colors.WARNING}Deactivated Topics ({len(result.deactivated)}):{Colors.ENDC}")
            for topic_id in sorted(result.deactivated):
                print_warning(f"{topic_id} (no endpoint)")

        if result.errors:
            print(f"\n{Colors.FAIL}Errors ({len(result.errors)}):{Colors.ENDC}")
            for topic_id, error in result.errors:
                print_error(f"{topic_id}: {error}")

        # Summary
        print_header("Summary")
        print(f"Total Topics:     {result.total_processed}")
        print(f"Created:          {len(result.created)}")
        print(f"Updated:          {len(result.updated)}")
        print(f"Skipped:          {len(result.skipped)}")
        print(f"Deactivated:      {len(result.deactivated)}")
        print(f"Errors:           {len(result.errors)}")

        if result.is_successful:
            print_success("\nSeeding completed successfully")
            return 0
        else:
            print_error(f"\nSeeding completed with {len(result.errors)} error(s)")
            return 1

    except Exception as e:
        logger.error("Fatal error during seeding", error=str(e), exc_info=True)
        print_error(f"Fatal error: {e}")
        return 1


async def seed_single_topic(
    seeding_service: TopicSeedingService,
    topic_id: str,
    *,
    force_update: bool = False,
) -> int:
    """Seed a single topic.

    Args:
        seeding_service: Topic seeding service instance
        topic_id: Topic ID to seed
        force_update: Whether to update if exists

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_header(f"Seeding Topic: {topic_id}")
    print_info(f"Force Update: {force_update}")

    try:
        success = await seeding_service.seed_topic(
            topic_id=topic_id,
            force_update=force_update,
        )

        if success:
            print_success(f"Topic '{topic_id}' seeded successfully")
            return 0
        else:
            print_error(f"Failed to seed topic '{topic_id}'")
            return 1

    except Exception as e:
        logger.error("Error seeding topic", topic_id=topic_id, error=str(e), exc_info=True)
        print_error(f"Error: {e}")
        return 1


async def validate_topics(seeding_service: TopicSeedingService) -> int:
    """Validate topics without seeding.

    Args:
        seeding_service: Topic seeding service instance

    Returns:
        Exit code (0 for valid, 1 for invalid)
    """
    print_header("Topic Validation Report")

    try:
        report = await seeding_service.validate_topics()

        if report.missing_topics:
            print(f"\n{Colors.FAIL}Missing Topics ({len(report.missing_topics)}):{Colors.ENDC}")
            print_error("These endpoints have no seed data:")
            for topic_id in sorted(report.missing_topics):
                print(f"  - {topic_id}")

        if report.orphaned_topics:
            print(
                f"\n{Colors.WARNING}Orphaned Topics ({len(report.orphaned_topics)}):{Colors.ENDC}"
            )
            print_warning("These topics have no endpoints:")
            for topic_id in sorted(report.orphaned_topics):
                print(f"  - {topic_id}")

        if report.missing_prompts:
            print(
                f"\n{Colors.WARNING}Missing Prompts ({len(report.missing_prompts)}):{Colors.ENDC}"
            )
            print_warning("These topics are missing S3 prompts:")
            for entry in sorted(report.missing_prompts):
                print(f"  - {entry}")

        if report.invalid_parameters:
            print(
                f"\n{Colors.FAIL}Invalid Parameters ({len(report.invalid_parameters)}):{Colors.ENDC}"
            )
            print_error("These topics have invalid parameter schemas:")
            for entry in sorted(report.invalid_parameters):
                print(f"  - {entry}")

        # Summary
        print_header("Validation Summary")
        if report.is_valid:
            print_success("All validations passed ✓")
            return 0
        else:
            print_error("Validation failed ✗")
            print(f"Missing Topics:      {len(report.missing_topics)}")
            print(f"Orphaned Topics:     {len(report.orphaned_topics)}")
            print(f"Missing Prompts:     {len(report.missing_prompts)}")
            print(f"Invalid Parameters:  {len(report.invalid_parameters)}")
            return 1

    except Exception as e:
        logger.error("Error during validation", error=str(e), exc_info=True)
        print_error(f"Validation error: {e}")
        return 1


async def deactivate_orphans(seeding_service: TopicSeedingService, *, dry_run: bool = False) -> int:
    """Deactivate orphaned topics.

    Args:
        seeding_service: Topic seeding service instance
        dry_run: Whether to run in dry-run mode

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_header("Deactivating Orphaned Topics")
    print_info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")

    try:
        deactivated = await seeding_service.deactivate_orphaned_topics(dry_run=dry_run)

        if deactivated:
            print(f"\n{Colors.WARNING}Deactivated Topics ({len(deactivated)}):{Colors.ENDC}")
            for topic_id in sorted(deactivated):
                print_warning(f"{topic_id}")
            print_info(f"\nDeactivated {len(deactivated)} orphaned topic(s)")
        else:
            print_success("No orphaned topics found")

        return 0

    except Exception as e:
        logger.error("Error deactivating orphans", error=str(e), exc_info=True)
        print_error(f"Error: {e}")
        return 1


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed topics from endpoint registry into DynamoDB and S3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Update existing topics with seed data",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    parser.add_argument(
        "--topic-id",
        type=str,
        help="Seed only a specific topic by ID",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation without seeding",
    )

    parser.add_argument(
        "--deactivate-orphans",
        action="store_true",
        help="Deactivate topics that no longer have endpoints",
    )

    return parser.parse_args()


async def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Initialize AWS clients
    dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region)
    s3_client = boto3.client("s3", region_name=settings.aws_region)

    # Initialize repositories and services
    topic_repo = TopicRepository(
        dynamodb_resource=dynamodb_resource,
        table_name=settings.topics_table,
    )

    s3_storage = S3PromptStorage(
        bucket_name=settings.prompts_bucket,
        s3_client=s3_client,
    )

    seeding_service = TopicSeedingService(
        topic_repo=topic_repo,
        s3_storage=s3_storage,
    )

    # Execute requested operation
    if args.validate_only:
        return await validate_topics(seeding_service)

    elif args.deactivate_orphans:
        return await deactivate_orphans(seeding_service, dry_run=args.dry_run)

    elif args.topic_id:
        return await seed_single_topic(
            seeding_service,
            topic_id=args.topic_id,
            force_update=args.force_update,
        )

    else:
        return await seed_all_topics(
            seeding_service,
            force_update=args.force_update,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
