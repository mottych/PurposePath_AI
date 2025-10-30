"""Seed LLM prompt templates to S3 and DynamoDB.

This script uploads Jinja2 template files to S3 and creates corresponding
metadata records in DynamoDB. It validates templates against the code-based
interaction registry to ensure all references are valid.

Usage:
    python scripts/llm_config/seed_templates.py \
        --templates-dir ./templates \
        --bucket purposepath-prompts-dev \
        --environment dev

Features:
    - Validates templates exist for all interactions in registry
    - Validates Jinja2 template syntax
    - Extracts template parameters and validates against interaction requirements
    - Uploads to S3 with versioning
    - Creates metadata records in DynamoDB
    - Reports missing templates and validation errors
"""

import argparse
import asyncio
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
import structlog
from botocore.exceptions import ClientError
from jinja2 import Template as Jinja2Template
from jinja2 import TemplateSyntaxError

from coaching.src.core.llm_interactions import (
    INTERACTION_REGISTRY,
    LLMInteraction,
    ParameterValidationError,
)
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)

logger = structlog.get_logger()


def extract_template_parameters(template_content: str) -> list[str]:
    """
    Extract parameter names from Jinja2 template.

    Args:
        template_content: Template content string

    Returns:
        List of unique parameter names found in template
    """
    # Match {{ variable }}, {% set variable %}, etc.
    pattern = r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\||}})"
    matches = re.findall(pattern, template_content)

    # Also match {% for/if variable %}
    loop_pattern = r"{%\s*(?:for|if)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+"
    loop_matches = re.findall(loop_pattern, template_content)

    parameters = set(matches + loop_matches)

    # Remove Jinja2 built-ins
    builtins = {"loop", "super", "self", "varargs", "kwargs", "true", "false", "none"}
    parameters = parameters - builtins

    return sorted(parameters)


def validate_template_syntax(template_content: str, template_file: str) -> None:
    """
    Validate Jinja2 template syntax.

    Args:
        template_content: Template content to validate
        template_file: File path for error reporting

    Raises:
        TemplateSyntaxError: If template has invalid syntax
    """
    try:
        Jinja2Template(template_content)
    except TemplateSyntaxError as e:
        raise TemplateSyntaxError(
            f"Template syntax error in {template_file}: {e}",
            lineno=e.lineno,
        ) from e


def validate_template_against_interaction(
    interaction: LLMInteraction,
    template_params: list[str],
    template_file: str,
) -> list[str]:
    """
    Validate template parameters against interaction requirements.

    Args:
        interaction: LLMInteraction from registry
        template_params: Parameters extracted from template
        template_file: File path for error reporting

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    try:
        interaction.validate_template_parameters(template_params)
    except ParameterValidationError as e:
        errors.append(f"{template_file}: {e}")

    return errors


async def upload_template_to_s3(
    s3_client: Any,
    bucket: str,
    template_file: Path,
    interaction_code: str,
    environment: str,
) -> str:
    """
    Upload template file to S3.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        template_file: Path to template file
        interaction_code: Interaction code
        environment: Deployment environment

    Returns:
        S3 key where template was uploaded
    """
    # S3 key structure: templates/{environment}/{interaction_code}/v{version}.jinja2
    # For initial seeding, use v1
    s3_key = f"templates/{environment}/{interaction_code}/v1.jinja2"

    # Read template content
    template_content = template_file.read_text()

    # Upload to S3
    s3_client.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=template_content.encode("utf-8"),
        ContentType="text/plain",
        Metadata={
            "interaction_code": interaction_code,
            "environment": environment,
            "uploaded_at": datetime.now(UTC).isoformat(),
        },
    )

    logger.info(
        "Template uploaded to S3",
        interaction_code=interaction_code,
        bucket=bucket,
        s3_key=s3_key,
    )

    return s3_key


async def create_template_metadata(
    repository: TemplateMetadataRepository,
    interaction_code: str,
    _template_params: list[str],
    bucket: str,
    s3_key: str,
    environment: str,
    created_by: str,
) -> TemplateMetadata:
    """
    Create template metadata record in DynamoDB.

    Args:
        repository: Template metadata repository
        interaction_code: Interaction code
        _template_params: Parameters extracted from template (unused, kept for signature)
        bucket: S3 bucket name
        s3_key: S3 key where template is stored
        environment: Deployment environment
        created_by: User who created the template

    Returns:
        Created TemplateMetadata entity
    """
    # Generate IDs
    template_code = f"{interaction_code}_V1"
    template_id = f"{template_code}_{environment.upper()}"

    # Get interaction for metadata
    interaction = INTERACTION_REGISTRY[interaction_code]

    # Create metadata
    metadata = TemplateMetadata(
        template_id=template_id,
        template_code=template_code,
        interaction_code=interaction_code,
        name=f"{interaction.description} Template V1",
        description=f"Template for {interaction.description} ({environment})",
        version="1",
        s3_bucket=bucket,
        s3_key=s3_key,
        is_active=True,  # Set as active for initial seeding
        created_by=created_by,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    # Save to DynamoDB
    await repository.create(metadata)

    logger.info(
        "Template metadata created",
        template_id=template_id,
        interaction_code=interaction_code,
    )

    return metadata


async def seed_templates(
    templates_dir: Path,
    bucket: str,
    environment: str,
    region: str = "us-east-1",
    created_by: str = "seed_script",
) -> dict[str, Any]:
    """
    Seed all templates from directory to S3 and DynamoDB.

    Args:
        templates_dir: Directory containing template files
        bucket: S3 bucket name
        environment: Deployment environment
        region: AWS region
        created_by: User identifier

    Returns:
        Dictionary with seeding results and statistics
    """
    logger.info(
        "Starting template seeding",
        templates_dir=str(templates_dir),
        bucket=bucket,
        environment=environment,
    )

    # Initialize AWS clients
    s3_client = boto3.client("s3", region_name=region)
    dynamodb = boto3.resource("dynamodb", region_name=region)

    # Initialize repository
    table_name = "prompt_templates_metadata"  # Default table name
    repository = TemplateMetadataRepository(
        dynamodb_resource=dynamodb,
        table_name=table_name,
    )

    # Results tracking
    results: dict[str, Any] = {
        "total_interactions": len(INTERACTION_REGISTRY),
        "templates_found": 0,
        "templates_uploaded": 0,
        "metadata_created": 0,
        "errors": [],
        "missing_templates": [],
        "validation_errors": [],
    }

    # Check for template files
    # Expected naming: {INTERACTION_CODE}.jinja2
    for interaction_code, interaction in INTERACTION_REGISTRY.items():
        template_file = templates_dir / f"{interaction_code}.jinja2"

        if not template_file.exists():
            results["missing_templates"].append(interaction_code)
            logger.warning(
                "Template file not found",
                interaction_code=interaction_code,
                expected_file=str(template_file),
            )
            continue

        results["templates_found"] += 1

        try:
            # Read template content
            template_content = template_file.read_text()

            # Validate Jinja2 syntax
            validate_template_syntax(template_content, str(template_file))

            # Extract parameters
            template_params = extract_template_parameters(template_content)

            # Validate against interaction requirements
            validation_errors = validate_template_against_interaction(
                interaction, template_params, str(template_file)
            )

            if validation_errors:
                results["validation_errors"].extend(validation_errors)
                logger.error(
                    "Template validation failed",
                    interaction_code=interaction_code,
                    errors=validation_errors,
                )
                continue

            # Upload to S3
            s3_key = await upload_template_to_s3(
                s3_client, bucket, template_file, interaction_code, environment
            )
            results["templates_uploaded"] += 1

            # Create metadata in DynamoDB
            await create_template_metadata(
                repository,
                interaction_code,
                template_params,
                bucket,
                s3_key,
                environment,
                created_by,
            )
            results["metadata_created"] += 1

            logger.info(
                "Template seeded successfully",
                interaction_code=interaction_code,
                template_id=f"{interaction_code}_v1_{environment}",
            )

        except TemplateSyntaxError as e:
            error_msg = f"{interaction_code}: Template syntax error - {e}"
            results["errors"].append(error_msg)
            logger.error("Template syntax error", interaction_code=interaction_code, error=str(e))

        except ClientError as e:
            error_msg = f"{interaction_code}: AWS error - {e}"
            results["errors"].append(error_msg)
            logger.error(
                "AWS error during template seeding",
                interaction_code=interaction_code,
                error=str(e),
            )

        except Exception as e:
            error_msg = f"{interaction_code}: Unexpected error - {e}"
            results["errors"].append(error_msg)
            logger.error(
                "Unexpected error during template seeding",
                interaction_code=interaction_code,
                error=str(e),
                exc_info=True,
            )

    return results


def print_seeding_report(results: dict[str, Any]) -> None:
    """
    Print seeding results report.

    Args:
        results: Results dictionary from seed_templates
    """
    print("\n" + "=" * 80)
    print("TEMPLATE SEEDING REPORT")
    print("=" * 80)

    print(f"\nTotal interactions in registry: {results['total_interactions']}")
    print(f"Template files found: {results['templates_found']}")
    print(f"Templates uploaded to S3: {results['templates_uploaded']}")
    print(f"Metadata records created: {results['metadata_created']}")

    if results["missing_templates"]:
        print(f"\n⚠️  Missing templates ({len(results['missing_templates'])}):")
        for interaction_code in results["missing_templates"]:
            print(f"  - {interaction_code}")

    if results["validation_errors"]:
        print(f"\n❌ Validation errors ({len(results['validation_errors'])}):")
        for error in results["validation_errors"]:
            print(f"  - {error}")

    if results["errors"]:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  - {error}")

    # Success summary
    success_rate = (
        (results["metadata_created"] / results["total_interactions"] * 100)
        if results["total_interactions"] > 0
        else 0
    )

    print(f"\n{'✅' if success_rate == 100 else '⚠️ '} Success rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("\n🎉 All templates seeded successfully!")
    elif results["metadata_created"] > 0:
        print(f"\n⚠️  Partially complete. {results['metadata_created']} templates seeded.")
    else:
        print("\n❌ Seeding failed. No templates were successfully seeded.")

    print("=" * 80 + "\n")


async def main() -> int:
    """
    Main entry point for template seeding script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Seed LLM prompt templates to S3 and DynamoDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--templates-dir",
        type=Path,
        required=True,
        help="Directory containing template files (e.g., ./templates)",
    )

    parser.add_argument(
        "--bucket",
        type=str,
        required=True,
        help="S3 bucket name (e.g., purposepath-prompts-dev)",
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

    # Validate templates directory exists
    if not args.templates_dir.exists():
        print(f"❌ Error: Templates directory does not exist: {args.templates_dir}")
        return 1

    if not args.templates_dir.is_dir():
        print(f"❌ Error: Templates path is not a directory: {args.templates_dir}")
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
        results = await seed_templates(
            templates_dir=args.templates_dir,
            bucket=args.bucket,
            environment=args.environment,
            region=args.region,
            created_by=args.created_by,
        )

        # Print report
        print_seeding_report(results)

        # Return success if all templates seeded
        if results["metadata_created"] == results["total_interactions"]:
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ Fatal error during seeding: {e}")
        logger.error("Fatal error during template seeding", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
