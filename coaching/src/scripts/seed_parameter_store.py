#!/usr/bin/env python3
"""Seed AWS Parameter Store with default model configuration.

This script initializes or updates the default model codes in AWS Systems Manager
Parameter Store, enabling runtime configuration of fallback models for topic creation.

Usage:
    python -m coaching.src.scripts.seed_parameter_store [options]

Options:
    --stage STAGE              Environment stage (dev, staging, prod). Default: dev
    --region REGION            AWS region. Default: us-east-1
    --basic-model CODE         Basic model code. Default: CLAUDE_3_5_SONNET_V2
    --premium-model CODE       Premium model code. Default: CLAUDE_OPUS_4_5
    --force                    Overwrite existing parameters
    --dry-run                  Show what would be done without making changes

Examples:
    # Seed dev environment with defaults
    python -m coaching.src.scripts.seed_parameter_store --stage dev

    # Seed production with specific models
    python -m coaching.src.scripts.seed_parameter_store \
        --stage prod \
        --basic-model CLAUDE_3_5_SONNET_V2 \
        --premium-model CLAUDE_OPUS_4_5 \
        --force

    # Dry run to see what would happen
    python -m coaching.src.scripts.seed_parameter_store --dry-run
"""

import argparse
import sys

import structlog
from coaching.src.services.parameter_store_service import ParameterStoreService

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
    print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed AWS Parameter Store with default model configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Environment stage (default: dev)",
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )

    parser.add_argument(
        "--basic-model",
        type=str,
        default="CLAUDE_3_5_SONNET_V2",
        help="Basic model code (default: CLAUDE_3_5_SONNET_V2)",
    )

    parser.add_argument(
        "--premium-model",
        type=str,
        default="CLAUDE_OPUS_4_5",
        help="Premium model code (default: CLAUDE_OPUS_4_5)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing parameters",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    print_header(f"Parameter Store Seeding - {args.stage.upper()} Environment")
    print_info(f"Region: {args.region}")
    print_info(f"Basic Model: {args.basic_model}")
    print_info(f"Premium Model: {args.premium_model}")
    print_info(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    print()

    # Initialize Parameter Store service
    param_service = ParameterStoreService(region=args.region, stage=args.stage)

    # Parameter paths
    basic_param = f"/purposepath/{args.stage}/models/default_basic"
    premium_param = f"/purposepath/{args.stage}/models/default_premium"

    print_info("Parameter paths:")
    print(f"  - {basic_param}")
    print(f"  - {premium_param}")
    print()

    # Check if parameters already exist
    try:
        current_basic, current_premium = param_service.get_default_models()
        params_exist = True
        print_info("Current parameters found:")
        print(f"  - Basic: {current_basic}")
        print(f"  - Premium: {current_premium}")
        print()
    except Exception:
        params_exist = False
        print_info("No existing parameters found")
        print()

    # Check if update needed
    if params_exist and not args.force:
        print_warning("Parameters already exist. Use --force to overwrite.")
        return 0

    # Dry run mode
    if args.dry_run:
        print_warning("DRY RUN MODE - No changes will be made")
        if params_exist:
            print_info(f"Would update: {basic_param} → {args.basic_model}")
            print_info(f"Would update: {premium_param} → {args.premium_model}")
        else:
            print_info(f"Would create: {basic_param} = {args.basic_model}")
            print_info(f"Would create: {premium_param} = {args.premium_model}")
        return 0

    # Update parameters
    try:
        success = param_service.update_default_models(
            basic_model_code=args.basic_model,
            premium_model_code=args.premium_model,
            updated_by=f"seed_script_{args.stage}",
        )

        if success:
            print_success("Parameters successfully seeded!")
            print()
            print_info("Verify with:")
            print(f"  aws ssm get-parameter --name {basic_param} --region {args.region}")
            print(f"  aws ssm get-parameter --name {premium_param} --region {args.region}")
            return 0
        else:
            print_error("Failed to seed parameters")
            return 1

    except Exception as e:
        print_error(f"Error seeding parameters: {e}")
        logger.error("Seeding failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
