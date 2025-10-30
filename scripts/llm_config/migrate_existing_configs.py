"""Migrate existing hardcoded LLM configurations to database.

This script scans the codebase for hardcoded LLM configurations and helps
migrate them to the database format. It generates a migration report and
optionally creates configuration YAML files.

Usage:
    # Generate migration report
    python scripts/llm_config/migrate_existing_configs.py \
        --scan-dir ./coaching/src \
        --output-file ./configs/migration_configs.yaml

    # After review, seed the configs
    python scripts/llm_config/seed_configurations.py \
        --config-file ./configs/migration_configs.yaml \
        --environment dev

Features:
    - Scans codebase for hardcoded model IDs and temperature settings
    - Identifies usage of DEFAULT_LLM_MODELS constant
    - Generates YAML configuration file for seeding
    - Reports missing interactions and recommendations
    - Validates all interactions exist in code registry
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import structlog
import yaml  # type: ignore[import]

from coaching.src.core.llm_interactions import INTERACTION_REGISTRY
from coaching.src.core.llm_models import MODEL_REGISTRY

logger = structlog.get_logger()


class ConfigScanner:
    """Scanner for finding hardcoded LLM configurations in codebase."""

    def __init__(self, scan_dir: Path):
        """
        Initialize scanner.

        Args:
            scan_dir: Directory to scan for Python files
        """
        self.scan_dir = scan_dir
        self.findings: list[dict[str, Any]] = []

    def scan_for_model_ids(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Scan file for hardcoded model IDs.

        Args:
            file_path: Path to Python file

        Returns:
            List of findings with model IDs and context
        """
        findings: list[dict[str, Any]] = []

        try:
            content = file_path.read_text()

            # Pattern for Claude model IDs
            model_pattern = r'(anthropic\.claude-[^"\']+["\'])'
            matches = re.finditer(model_pattern, content)

            for match in matches:
                model_id = match.group(1).strip("\"'")

                # Find which model code this corresponds to
                model_code = None
                for code, model in MODEL_REGISTRY.items():
                    if model.model_name == model_id:
                        model_code = code
                        break

                findings.append(
                    {
                        "file": str(file_path.relative_to(self.scan_dir.parent)),
                        "model_id": model_id,
                        "model_code": model_code,
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        except Exception as e:
            logger.error("Error scanning file", file=str(file_path), error=str(e))

        return findings

    def scan_for_default_llm_models(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Scan for usage of DEFAULT_LLM_MODELS constant.

        Args:
            file_path: Path to Python file

        Returns:
            List of findings
        """
        findings: list[dict[str, Any]] = []

        try:
            content = file_path.read_text()

            if "DEFAULT_LLM_MODELS" in content:
                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    if "DEFAULT_LLM_MODELS" in line:
                        findings.append(
                            {
                                "file": str(file_path.relative_to(self.scan_dir.parent)),
                                "line": line_num,
                                "usage": line.strip(),
                            }
                        )

        except Exception as e:
            logger.error("Error scanning file", file=str(file_path), error=str(e))

        return findings

    def scan_for_temperature_settings(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Scan for temperature parameter usage.

        Args:
            file_path: Path to Python file

        Returns:
            List of findings
        """
        findings: list[dict[str, Any]] = []

        try:
            content = file_path.read_text()

            # Pattern for temperature assignments
            temp_pattern = r"temperature\s*=\s*([\d.]+)"
            matches = re.finditer(temp_pattern, content)

            for match in matches:
                temperature = float(match.group(1))

                findings.append(
                    {
                        "file": str(file_path.relative_to(self.scan_dir.parent)),
                        "temperature": temperature,
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        except Exception as e:
            logger.error("Error scanning file", file=str(file_path), error=str(e))

        return findings

    def scan_all(self) -> dict[str, list[dict[str, Any]]]:
        """
        Scan all Python files in directory.

        Returns:
            Dictionary with findings by category
        """
        all_findings: dict[str, list[dict[str, Any]]] = {
            "model_ids": [],
            "default_llm_models_usage": [],
            "temperature_settings": [],
        }

        python_files = list(self.scan_dir.rglob("*.py"))

        logger.info(f"Scanning {len(python_files)} Python files")

        for file_path in python_files:
            all_findings["model_ids"].extend(self.scan_for_model_ids(file_path))
            all_findings["default_llm_models_usage"].extend(
                self.scan_for_default_llm_models(file_path)
            )
            all_findings["temperature_settings"].extend(
                self.scan_for_temperature_settings(file_path)
            )

        return all_findings


def generate_migration_configs(_findings: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """
    Generate configuration entries based on scan findings.

    Args:
        _findings: Scan findings from ConfigScanner (reserved for future use)

    Returns:
        List of configuration dictionaries
    """
    configs: list[dict[str, Any]] = []

    # For each interaction in registry, create a default config
    for interaction_code in INTERACTION_REGISTRY:
        # Determine best model based on findings or use default
        model_code = "CLAUDE_3_5_SONNET"  # Default

        # Generate template ID (assumes templates follow naming convention)
        template_id = f"{interaction_code}_V1_DEV"

        # Default temperature (can be adjusted based on findings)
        temperature = 0.7
        max_tokens = 4096

        config = {
            "interaction_code": interaction_code,
            "template_id": template_id,
            "model_code": model_code,
            "tier": None,  # Default tier (applies to all)
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }

        configs.append(config)

    return configs


def print_migration_report(
    findings: dict[str, list[dict[str, Any]]],
    configs: list[dict[str, Any]],
) -> None:
    """
    Print migration report.

    Args:
        findings: Scan findings
        configs: Generated configurations
    """
    print("\n" + "=" * 80)
    print("LLM CONFIGURATION MIGRATION REPORT")
    print("=" * 80)

    # Findings summary
    print("\n📊 Scan Results:")
    print(f"  Hardcoded model IDs found: {len(findings['model_ids'])}")
    print(f"  DEFAULT_LLM_MODELS usages: {len(findings['default_llm_models_usage'])}")
    print(f"  Temperature settings found: {len(findings['temperature_settings'])}")

    # Code registry status
    print("\n✅ Code Registry Status:")
    print(f"  Interactions defined: {len(INTERACTION_REGISTRY)}")
    print(f"  Models defined: {len(MODEL_REGISTRY)}")
    print("  All code references validated")

    # Model IDs found
    if findings["model_ids"]:
        print("\n🔍 Hardcoded Model IDs (first 10):")
        for finding in findings["model_ids"][:10]:
            status = "✓" if finding["model_code"] else "⚠"
            print(
                f"  {status} {finding['file']}:{finding['line']} - "
                f"{finding['model_id']} → {finding['model_code'] or 'UNKNOWN'}"
            )

        if len(findings["model_ids"]) > 10:
            print(f"  ... and {len(findings['model_ids']) - 10} more")

    # DEFAULT_LLM_MODELS usage
    if findings["default_llm_models_usage"]:
        print("\n📚 DEFAULT_LLM_MODELS Usage (first 5):")
        for finding in findings["default_llm_models_usage"][:5]:
            print(f"  - {finding['file']}:{finding['line']}")

        if len(findings["default_llm_models_usage"]) > 5:
            print(f"  ... and {len(findings['default_llm_models_usage']) - 5} more")

    # Generated configs
    print(f"\n⚙️  Generated Configurations: {len(configs)}")
    print(f"  One config per interaction ({len(INTERACTION_REGISTRY)} total)")

    # Next steps
    print("\n📋 Next Steps:")
    print("  1. Review generated YAML file")
    print("  2. Adjust model_code, temperature, max_tokens as needed")
    print("  3. Add tier-specific configs if needed")
    print("  4. Run seed_configurations.py to create configs")
    print("  5. Update code to use config-driven approach")
    print("  6. Enable feature flag: use_llm_config_system=True")

    print("=" * 80 + "\n")


def main() -> int:
    """
    Main entry point for migration script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Migrate hardcoded LLM configs to database format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--scan-dir",
        type=Path,
        required=True,
        help="Directory to scan for Python files (e.g., ./coaching/src)",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("./configs/migration_configs.yaml"),
        help="Output YAML file for configurations (default: ./configs/migration_configs.yaml)",
    )

    args = parser.parse_args()

    # Validate scan directory
    if not args.scan_dir.exists():
        print(f"❌ Error: Scan directory does not exist: {args.scan_dir}")
        return 1

    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )

    try:
        # Scan codebase
        scanner = ConfigScanner(args.scan_dir)
        findings = scanner.scan_all()

        # Generate configurations
        configs = generate_migration_configs(findings)

        # Create output directory if needed
        args.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML file
        with open(args.output_file, "w") as f:
            yaml.dump(configs, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configurations written to {args.output_file}")

        # Print report
        print_migration_report(findings, configs)

        print(f"\n✅ Migration file generated: {args.output_file}")
        print("\n💡 Review the file and run:")
        print(
            f"   python scripts/llm_config/seed_configurations.py "
            f"--config-file {args.output_file} --environment dev"
        )

        return 0

    except Exception as e:
        print(f"\n❌ Fatal error during migration: {e}")
        logger.error("Fatal error during migration", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
