"""Seed LLM configurations to DynamoDB.

This script creates LLM configuration records in DynamoDB, linking interactions
to templates and models with specific parameters. It validates all references
against code registries and the database.

Usage:
    python scripts/llm_config/seed_configurations.py \
        --config-file ./configs/llm_configs.yaml \
        --environment dev

Features:
    - Validates interaction codes against INTERACTION_REGISTRY
    - Validates model codes against MODEL_REGISTRY
    - Validates template IDs exist in database
    - Ensures only one active config per interaction+tier
    - Reports validation errors and estimated costs
    - Deactivates previous configurations when creating new ones
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
import structlog
import yaml  # type: ignore[import]
from botocore.exceptions import ClientError

from coaching.src.core.llm_interactions import get_interaction
from coaching.src.core.llm_models import get_model
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)

logger = structlog.get_logger()


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


async def validate_template_exists(
    repository: TemplateMetadataRepository,
    template_id: str,
) -> bool:
    """
    Validate template exists in database.

    Args:
        repository: Template metadata repository
        template_id: Template identifier to validate

    Returns:
        True if template exists, False otherwise
    """
    template = await repository.get_by_id(template_id)
    return template is not None


async def validate_configuration_data(
    config_data: dict[str, Any],
    template_repo: TemplateMetadataRepository,
) -> list[str]:
    """
    Validate configuration data against registries and database.

    Args:
        config_data: Configuration dictionary from YAML
        template_repo: Template metadata repository

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate interaction_code
    interaction_code = config_data.get("interaction_code")
    if not interaction_code:
        errors.append("Missing required field: interaction_code")
    else:
        try:
            get_interaction(interaction_code)
        except ValueError as e:
            errors.append(f"Invalid interaction_code '{interaction_code}': {e}")

    # Validate model_code
    model_code = config_data.get("model_code")
    if not model_code:
        errors.append("Missing required field: model_code")
    else:
        try:
            get_model(model_code)
        except ValueError as e:
            errors.append(f"Invalid model_code '{model_code}': {e}")

    # Validate template_id
    template_id = config_data.get("template_id")
    if not template_id:
        errors.append("Missing required field: template_id")
    else:
        template_exists = await validate_template_exists(template_repo, template_id)
        if not template_exists:
            errors.append(
                f"Template not found: '{template_id}'. "
                "Run seed_templates.py first or check template_id."
            )

    # Validate parameters
    temperature = config_data.get("temperature")
    if temperature is None:
        errors.append("Missing required field: temperature")
    elif not (0.0 <= temperature <= 2.0):
        errors.append(f"temperature must be between 0.0 and 2.0, got {temperature}")

    max_tokens = config_data.get("max_tokens")
    if max_tokens is None:
        errors.append("Missing required field: max_tokens")
    elif max_tokens <= 0:
        errors.append(f"max_tokens must be > 0, got {max_tokens}")

    return errors


async def deactivate_previous_configs(
    repository: LLMConfigurationRepository,
    interaction_code: str,
    tier: str | None,
) -> int:
    """
    Deactivate previous active configurations for interaction+tier.

    Args:
        repository: Configuration repository
        interaction_code: Interaction code
        tier: Tier (None for default)

    Returns:
        Number of configs deactivated
    """
    # Get all active configs for this interaction+tier
    configs = await repository.list_all(interaction_code=interaction_code)

    count = 0
    for config in configs:
        if config.is_active and config.tier == tier:
            # Deactivate
            config.is_active = False
            config.effective_until = datetime.now(UTC)
            config.updated_at = datetime.now(UTC)
            await repository.update(config)
            count += 1

            logger.info(
                "Deactivated previous configuration",
                config_id=config.config_id,
                interaction_code=interaction_code,
                tier=tier,
            )

    return count


async def create_configuration(
    repository: LLMConfigurationRepository,
    config_data: dict[str, Any],
    environment: str,
    created_by: str,
) -> LLMConfiguration:
    """
    Create configuration record in DynamoDB.

    Args:
        repository: Configuration repository
        config_data: Configuration dictionary from YAML
        environment: Deployment environment
        created_by: User who created the config

    Returns:
        Created LLMConfiguration entity
    """
    interaction_code = config_data["interaction_code"]
    tier = config_data.get("tier")

    # Generate config ID
    tier_suffix = f"_{tier}" if tier else "_default"
    config_id = f"{interaction_code}{tier_suffix}_{environment}"

    # Create configuration
    config = LLMConfiguration(
        config_id=config_id,
        interaction_code=interaction_code,
        template_id=config_data["template_id"],
        model_code=config_data["model_code"],
        tier=tier,
        temperature=config_data["temperature"],
        max_tokens=config_data["max_tokens"],
        top_p=config_data.get("top_p", 1.0),
        frequency_penalty=config_data.get("frequency_penalty", 0.0),
        presence_penalty=config_data.get("presence_penalty", 0.0),
        is_active=True,
        effective_from=datetime.now(UTC),
        effective_until=None,
        created_by=created_by,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Save to DynamoDB
    await repository.create(config)

    logger.info(
        "Configuration created",
        config_id=config_id,
        interaction_code=interaction_code,
        tier=tier,
    )

    return config


async def calculate_estimated_costs(
    configs: list[LLMConfiguration],
) -> dict[str, Any]:
    """
    Calculate estimated costs for configurations.

    Args:
        configs: List of configurations

    Returns:
        Dictionary with cost estimates
    """
    total_cost_per_1k = 0.0
    costs_by_model: dict[str, float] = {}

    for config in configs:
        model = get_model(config.model_code)
        cost = model.cost_per_1k_tokens

        total_cost_per_1k += cost
        if model.code not in costs_by_model:
            costs_by_model[model.code] = 0.0
        costs_by_model[model.code] += cost

    return {
        "total_cost_per_1k_tokens": total_cost_per_1k,
        "costs_by_model": costs_by_model,
    }


async def seed_configurations(
    config_file: Path,
    environment: str,
    region: str = "us-east-1",
    created_by: str = "seed_script",
) -> dict[str, Any]:
    """
    Seed configurations from YAML file to DynamoDB.

    Args:
        config_file: Path to YAML configuration file
        environment: Deployment environment
        region: AWS region
        created_by: User identifier

    Returns:
        Dictionary with seeding results and statistics
    """
    logger.info(
        "Starting configuration seeding",
        config_file=str(config_file),
        environment=environment,
    )

    # Load configuration file
    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    configurations = config_data.get("configurations", [])

    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb", region_name=region)

    # Initialize repositories
    config_table_name = "llm_configurations"
    template_table_name = "prompt_templates_metadata"

    config_repo = LLMConfigurationRepository(
        dynamodb_resource=dynamodb,
        table_name=config_table_name,
    )

    template_repo = TemplateMetadataRepository(
        dynamodb_resource=dynamodb,
        table_name=template_table_name,
    )

    # Results tracking
    results: dict[str, Any] = {
        "total_configs": len(configurations),
        "valid_configs": 0,
        "created_configs": 0,
        "deactivated_configs": 0,
        "validation_errors": [],
        "errors": [],
    }

    created_configs: list[LLMConfiguration] = []

    # Process each configuration
    for idx, config_data in enumerate(configurations):
        interaction_code = config_data.get("interaction_code", f"config_{idx}")

        try:
            # Validate configuration
            validation_errors = await validate_configuration_data(config_data, template_repo)

            if validation_errors:
                results["validation_errors"].extend(
                    [f"{interaction_code}: {err}" for err in validation_errors]
                )
                logger.error(
                    "Configuration validation failed",
                    interaction_code=interaction_code,
                    errors=validation_errors,
                )
                continue

            results["valid_configs"] += 1

            # Deactivate previous configs for this interaction+tier
            tier = config_data.get("tier")
            deactivated = await deactivate_previous_configs(
                config_repo,
                interaction_code,
                tier,
            )
            results["deactivated_configs"] += deactivated

            # Create new configuration
            config = await create_configuration(
                config_repo,
                config_data,
                environment,
                created_by,
            )
            created_configs.append(config)
            results["created_configs"] += 1

            logger.info(
                "Configuration seeded successfully",
                config_id=config.config_id,
                interaction_code=interaction_code,
            )

        except ClientError as e:
            error_msg = f"{interaction_code}: AWS error - {e}"
            results["errors"].append(error_msg)
            logger.error(
                "AWS error during configuration seeding",
                interaction_code=interaction_code,
                error=str(e),
            )

        except Exception as e:
            error_msg = f"{interaction_code}: Unexpected error - {e}"
            results["errors"].append(error_msg)
            logger.error(
                "Unexpected error during configuration seeding",
                interaction_code=interaction_code,
                error=str(e),
                exc_info=True,
            )

    # Calculate estimated costs
    if created_configs:
        costs = await calculate_estimated_costs(created_configs)
        results["estimated_costs"] = costs

    return results


def print_seeding_report(results: dict[str, Any]) -> None:
    """
    Print seeding results report.

    Args:
        results: Results dictionary from seed_configurations
    """
    print("\n" + "=" * 80)
    print("CONFIGURATION SEEDING REPORT")
    print("=" * 80)

    print(f"\nTotal configurations in file: {results['total_configs']}")
    print(f"Valid configurations: {results['valid_configs']}")
    print(f"Configurations created: {results['created_configs']}")
    print(f"Previous configurations deactivated: {results['deactivated_configs']}")

    # Validation errors
    if results["validation_errors"]:
        print(f"\n❌ Validation errors ({len(results['validation_errors'])}):")
        for error in results["validation_errors"]:
            print(f"  - {error}")

    # General errors
    if results["errors"]:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  - {error}")

    # Cost estimates
    if "estimated_costs" in results:
        costs = results["estimated_costs"]
        print("\n💰 Estimated Costs:")
        print(f"  Total cost per 1K tokens: ${costs['total_cost_per_1k_tokens']:.4f}")
        print("\n  By model:")
        for model_code, cost in costs["costs_by_model"].items():
            print(f"    {model_code}: ${cost:.4f} per 1K tokens")

    # Success summary
    success_rate = (
        (results["created_configs"] / results["total_configs"] * 100)
        if results["total_configs"] > 0
        else 0
    )

    print(f"\n{'✅' if success_rate == 100 else '⚠️ '} Success rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n🎉 All configurations seeded successfully!")
    elif results["created_configs"] > 0:
        print(f"\n⚠️  Partially complete. {results['created_configs']} configurations seeded.")
    else:
        print("\n❌ Seeding failed. No configurations were successfully seeded.")

    print("=" * 80 + "\n")


async def main() -> int:
    """
    Main entry point for configuration seeding script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Seed LLM configurations to DynamoDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        required=True,
        help="Path to YAML configuration file (e.g., ./configs/llm_configs.yaml)",
    )

    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        choices=["dev", "staging", "production"],
        help="Deployment environment",
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    parser.add_argument(
        "--created-by",
        type=str,
        default="seed_script",
        help="User identifier for created_by field (default: seed_script)",
    )

    args = parser.parse_args()

    # Validate config file exists
    if not args.config_file.exists():
        print(f"❌ Error: Configuration file does not exist: {args.config_file}")
        return 1

    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )

    # Run seeding
    try:
        results = await seed_configurations(
            config_file=args.config_file,
            environment=args.environment,
            region=args.region,
            created_by=args.created_by,
        )

        # Print report
        print_seeding_report(results)

        # Return success if all configs seeded
        if results["created_configs"] == results["total_configs"]:
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ Fatal error during seeding: {e}")
        logger.error("Fatal error during configuration seeding", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
