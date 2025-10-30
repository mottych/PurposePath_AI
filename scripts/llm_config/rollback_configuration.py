"""Rollback LLM configurations to previous state.

This script helps manage configuration rollbacks by creating snapshots
and restoring previous configurations when needed.

Usage:
    # Create snapshot before making changes
    python scripts/llm_config/rollback_configuration.py \
        --action snapshot \
        --environment dev \
        --snapshot-name "pre-production-update"

    # List available snapshots
    python scripts/llm_config/rollback_configuration.py \
        --action list \
        --environment dev

    # Rollback to specific snapshot
    python scripts/llm_config/rollback_configuration.py \
        --action rollback \
        --environment dev \
        --snapshot-name "pre-production-update"

Features:
    - Create configuration snapshots
    - List available snapshots with metadata
    - Rollback to previous snapshot
    - Disable specific configurations
    - Re-enable default configurations
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
import structlog

from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)

logger = structlog.get_logger()


class SnapshotManager:
    """Manages configuration snapshots for rollback capability."""

    def __init__(self, snapshots_dir: Path):
        """
        Initialize snapshot manager.

        Args:
            snapshots_dir: Directory to store snapshots
        """
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(
        self,
        configs: list[LLMConfiguration],
        environment: str,
        snapshot_name: str,
        description: str = "",
    ) -> Path:
        """
        Create snapshot of configurations.

        Args:
            configs: List of configurations to snapshot
            environment: Deployment environment
            snapshot_name: Name for the snapshot
            description: Optional description

        Returns:
            Path to snapshot file
        """
        # Create snapshot data
        snapshot_data = {
            "snapshot_name": snapshot_name,
            "environment": environment,
            "description": description,
            "created_at": datetime.now(UTC).isoformat(),
            "total_configs": len(configs),
            "configurations": [config.model_dump(mode="json") for config in configs],
        }

        # Generate filename with timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{environment}_{snapshot_name}_{timestamp}.json"
        snapshot_path = self.snapshots_dir / filename

        # Write snapshot
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2, default=str)

        logger.info(
            "Snapshot created",
            snapshot_path=str(snapshot_path),
            total_configs=len(configs),
        )

        return snapshot_path

    def list_snapshots(self, environment: str | None = None) -> list[dict[str, Any]]:
        """
        List available snapshots.

        Args:
            environment: Optional environment filter

        Returns:
            List of snapshot metadata
        """
        snapshots = []

        for snapshot_file in sorted(self.snapshots_dir.glob("*.json")):
            try:
                with open(snapshot_file) as f:
                    snapshot_data = json.load(f)

                # Filter by environment if specified
                if environment and snapshot_data.get("environment") != environment:
                    continue

                snapshots.append(
                    {
                        "file": snapshot_file.name,
                        "snapshot_name": snapshot_data.get("snapshot_name"),
                        "environment": snapshot_data.get("environment"),
                        "created_at": snapshot_data.get("created_at"),
                        "total_configs": snapshot_data.get("total_configs"),
                        "description": snapshot_data.get("description", ""),
                    }
                )

            except Exception as e:
                logger.error("Error reading snapshot", file=str(snapshot_file), error=str(e))

        return snapshots

    def load_snapshot(self, snapshot_name: str, environment: str) -> dict[str, Any] | None:
        """
        Load snapshot by name and environment.

        Args:
            snapshot_name: Snapshot name
            environment: Environment

        Returns:
            Snapshot data or None if not found
        """
        # Find snapshot file matching name and environment
        for snapshot_file in self.snapshots_dir.glob(f"{environment}_{snapshot_name}_*.json"):
            try:
                with open(snapshot_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error loading snapshot", file=str(snapshot_file), error=str(e))

        return None


async def create_snapshot_action(
    config_repo: LLMConfigurationRepository,
    snapshot_manager: SnapshotManager,
    environment: str,
    snapshot_name: str,
    description: str,
) -> int:
    """
    Create snapshot of current configurations.

    Args:
        config_repo: Configuration repository
        snapshot_manager: Snapshot manager
        environment: Environment
        snapshot_name: Snapshot name
        description: Snapshot description

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Creating configuration snapshot", snapshot_name=snapshot_name)

    try:
        # Get all active configs
        all_configs = await config_repo.list_all()
        active_configs = [c for c in all_configs if c.is_active]

        # Create snapshot
        snapshot_path = snapshot_manager.create_snapshot(
            configs=active_configs,
            environment=environment,
            snapshot_name=snapshot_name,
            description=description,
        )

        print("\n✅ Snapshot created successfully!")
        print(f"   File: {snapshot_path}")
        print(f"   Configurations captured: {len(active_configs)}")
        print(f"   Environment: {environment}")

        return 0

    except Exception as e:
        print(f"\n❌ Error creating snapshot: {e}")
        logger.error("Snapshot creation failed", error=str(e), exc_info=True)
        return 1


async def list_snapshots_action(
    snapshot_manager: SnapshotManager,
    environment: str | None,
) -> int:
    """
    List available snapshots.

    Args:
        snapshot_manager: Snapshot manager
        environment: Optional environment filter

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Listing snapshots", environment=environment)

    try:
        snapshots = snapshot_manager.list_snapshots(environment=environment)

        if not snapshots:
            print("\nNo snapshots found.")
            return 0

        print(f"\n{'=' * 80}")
        print("AVAILABLE SNAPSHOTS")
        print(f"{'=' * 80}\n")

        for snapshot in snapshots:
            print(f"📸 {snapshot['snapshot_name']}")
            print(f"   Environment: {snapshot['environment']}")
            print(f"   Created: {snapshot['created_at']}")
            print(f"   Configurations: {snapshot['total_configs']}")
            if snapshot.get("description"):
                print(f"   Description: {snapshot['description']}")
            print(f"   File: {snapshot['file']}")
            print()

        print(f"Total snapshots: {len(snapshots)}")
        print(f"{'=' * 80}\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error listing snapshots: {e}")
        logger.error("List snapshots failed", error=str(e), exc_info=True)
        return 1


async def rollback_action(
    config_repo: LLMConfigurationRepository,
    snapshot_manager: SnapshotManager,
    environment: str,
    snapshot_name: str,
    dry_run: bool = False,
) -> int:
    """
    Rollback to snapshot.

    Args:
        config_repo: Configuration repository
        snapshot_manager: Snapshot manager
        environment: Environment
        snapshot_name: Snapshot name
        dry_run: If True, show what would happen without making changes

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Rolling back to snapshot", snapshot_name=snapshot_name, dry_run=dry_run)

    try:
        # Load snapshot
        snapshot_data = snapshot_manager.load_snapshot(snapshot_name, environment)

        if not snapshot_data:
            print(f"\n❌ Snapshot not found: {snapshot_name} for environment: {environment}")
            return 1

        snapshot_configs = snapshot_data.get("configurations", [])

        print("\n🔄 Rollback Plan:")
        print(f"   Snapshot: {snapshot_name}")
        print(f"   Created: {snapshot_data.get('created_at')}")
        print(f"   Configurations to restore: {len(snapshot_configs)}")

        if dry_run:
            print("\n   ⚠️  DRY RUN - No changes will be made")

        # Get current active configs
        current_configs = await config_repo.list_all()
        active_current = [c for c in current_configs if c.is_active]

        print(f"\n   Current active configurations: {len(active_current)}")
        print(f"\n{'=' * 80}")

        if not dry_run:
            # Deactivate all current configs
            for config in active_current:
                config.is_active = False
                config.effective_until = datetime.now(UTC)
                config.updated_at = datetime.now(UTC)
                await config_repo.update(config)

            print(f"✅ Deactivated {len(active_current)} current configurations")

            # Restore snapshot configs
            restored_count = 0
            for config_data in snapshot_configs:
                # Create new configuration from snapshot
                config = LLMConfiguration.model_validate(config_data)

                # Update timestamps
                config.created_at = datetime.now(UTC)
                config.updated_at = datetime.now(UTC)
                config.effective_from = datetime.now(UTC)

                await config_repo.create(config)
                restored_count += 1

            print(f"✅ Restored {restored_count} configurations from snapshot")
            print("\n🎉 Rollback completed successfully!")
        else:
            print(f"\n📋 Would deactivate {len(active_current)} current configurations")
            print(f"📋 Would restore {len(snapshot_configs)} configurations from snapshot")
            print("\nTo execute rollback, run without --dry-run flag")

        return 0

    except Exception as e:
        print(f"\n❌ Error during rollback: {e}")
        logger.error("Rollback failed", error=str(e), exc_info=True)
        return 1


async def main() -> int:
    """
    Main entry point for rollback script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Rollback LLM configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["snapshot", "list", "rollback"],
        help="Action to perform",
    )

    parser.add_argument(
        "--environment",
        type=str,
        help="Deployment environment (required for snapshot/rollback)",
    )

    parser.add_argument(
        "--snapshot-name",
        type=str,
        help="Snapshot name (required for snapshot/rollback)",
    )

    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Snapshot description (optional for snapshot action)",
    )

    parser.add_argument(
        "--snapshots-dir",
        type=Path,
        default=Path("./snapshots/llm_configs"),
        help="Directory for snapshots (default: ./snapshots/llm_configs)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes (rollback only)",
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    args = parser.parse_args()

    # Validate required arguments based on action
    if args.action in ["snapshot", "rollback"]:
        if not args.environment:
            print("❌ Error: --environment is required for snapshot/rollback actions")
            return 1
        if not args.snapshot_name:
            print("❌ Error: --snapshot-name is required for snapshot/rollback actions")
            return 1

    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )

    # Initialize components
    snapshot_manager = SnapshotManager(args.snapshots_dir)

    # Execute action
    try:
        if args.action == "list":
            return await list_snapshots_action(snapshot_manager, args.environment)

        # For snapshot/rollback, need repository
        dynamodb = boto3.resource("dynamodb", region_name=args.region)
        config_repo = LLMConfigurationRepository(
            dynamodb_resource=dynamodb,
            table_name="llm_configurations",
        )

        if args.action == "snapshot":
            return await create_snapshot_action(
                config_repo,
                snapshot_manager,
                args.environment,
                args.snapshot_name,
                args.description,
            )

        elif args.action == "rollback":
            return await rollback_action(
                config_repo,
                snapshot_manager,
                args.environment,
                args.snapshot_name,
                args.dry_run,
            )

        return 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error("Fatal error during operation", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
