#!/usr/bin/env python3
"""
Type validation script for PurposePath API
Provides accurate error counting and categorization for systematic fixing
"""
import subprocess
import sys
from pathlib import Path


def run_mypy_on_service(service_dir: str, config_file: str | None = None) -> tuple[int, list[str]]:
    """Run mypy on a specific service with its configuration."""
    service_path = Path(service_dir)
    if not service_path.exists():
        print(f"Warning: Service directory {service_dir} does not exist")
        return 0, []

    if config_file and Path(service_dir) / config_file:
        config_path = Path(service_dir) / config_file
    else:
        config_path = None

    # Run with comprehensive error detection including unused ignores
    cmd = [
        "python", "-m", "mypy", ".",
        "--show-error-codes",
        "--no-error-summary",
        "--warn-unused-ignores",
        "--warn-return-any",
        "--strict"
    ]

    if config_path and config_path.exists():
        cmd.extend(["--config-file", str(config_path)])
        print(f"Using config: {config_path}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=service_path,
            timeout=60
        )
        output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        error_lines = [line for line in output_lines if ': error:' in line]
        return len(error_lines), error_lines
    except subprocess.TimeoutExpired:
        print(f"Timeout running mypy on {service_dir}")
        return -1, []
    except Exception as e:
        print(f"Error running mypy on {service_dir}: {e}")
        return -1, []


def run_mypy_check(target: str = ".", exclude_patterns: list[str] | None = None) -> tuple[int, list[str]]:
    """Run mypy and return error count and error list."""
    cmd = ["python", "-m", "mypy", target, "--show-error-codes", "--no-error-summary"]

    if exclude_patterns:
        for pattern in exclude_patterns:
            cmd.extend(["--exclude", pattern])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        error_lines = [line for line in output_lines if ': error:' in line]
        return len(error_lines), error_lines
    except Exception as e:
        print(f"Error running mypy: {e}")
        return -1, []


def categorize_errors(error_lines: list[str]) -> dict[str, list[str]]:
    """Categorize errors by type for systematic fixing."""
    categories: dict[str, list[str]] = {
        "test_files": [],
        "stub_files": [],
        "script_files": [],
        "core_app": [],
        "no_untyped_def": [],
        "unused_ignore": [],
        "assignment_issues": [],
        "boto3_typing": [],
        "other": []
    }

    for error in error_lines:
        if "test" in error.lower():
            categories["test_files"].append(error)
        elif "stub" in error.lower():
            categories["stub_files"].append(error)
        elif "script" in error.lower():
            categories["script_files"].append(error)
        elif "[no-untyped-def]" in error:
            categories["no_untyped_def"].append(error)
        elif "[unused-ignore]" in error:
            categories["unused_ignore"].append(error)
        elif "[assignment]" in error:
            categories["assignment_issues"].append(error)
        elif "boto3" in error.lower() or "client" in error.lower():
            categories["boto3_typing"].append(error)
        elif any(app in error for app in ["account/src", "coaching/src", "traction/src", "shared/services"]):
            categories["core_app"].append(error)
        else:
            categories["other"].append(error)

    return categories


def validate_service_with_config() -> tuple[int, dict[str, tuple[int, list[str]]]]:
    """Validate each service using its own configuration."""
    services = {
        "account": "account",
        "coaching": "coaching",
        "traction": "traction",
        "shared": "shared"
    }

    results: dict[str, tuple[int, list[str]]] = {}
    total_errors = 0

    print("🔧 Service-Specific Validation (Using Service Configs)")
    print("-" * 60)

    for service_name, service_dir in services.items():
        service_path = Path(service_dir)
        if not service_path.exists():
            print(f"⚠️  {service_name}: Directory not found")
            continue

        print(f"Checking {service_name}...")
        error_count, error_list = run_mypy_on_service(service_dir, "pyproject.toml")
        results[service_name] = (error_count, error_list)
        total_errors += error_count

        if error_count == 0:
            print(f"✅ {service_name}: No errors")
        else:
            print(f"❌ {service_name}: {error_count} errors")
            for error in error_list[:3]:  # Show first 3
                print(f"   {error}")
            if len(error_list) > 3:
                print(f"   ... and {len(error_list) - 3} more")
        print()

    return total_errors, results


def print_validation_report() -> tuple[int, int, dict[str, list[str]]]:
    """Print comprehensive validation report."""
    print("=" * 80)
    print("🔍 PurposePath API Type Validation Report")
    print("=" * 80)

    # First run service-specific validation
    service_errors, _service_results = validate_service_with_config()
    print(f"Service-Specific Total: {service_errors} errors")
    print("=" * 80)

    # 1. Core Application Check
    print("\n📊 CORE APPLICATION (Business Logic)")
    core_count, core_errors = run_mypy_check(".", [".*test.*", ".*stub.*", "scripts/*"])
    print(f"Errors: {core_count}")
    if core_count == 0:
        print("✅ ZERO ERRORS - Core application is type-safe!")
    else:
        print("❌ Errors found in core application")
        for error in core_errors[:5]:  # Show first 5
            print(f"  - {error}")
        if len(core_errors) > 5:
            print(f"  ... and {len(core_errors) - 5} more")

    # 2. Full Project Check
    print("\n📊 FULL PROJECT (Including Tests, Stubs, Scripts)")
    total_count, all_errors = run_mypy_check(".")
    print(f"Total Errors: {total_count}")

    categories: dict[str, list[str]] = {}
    if total_count > 0:
        categories = categorize_errors(all_errors)
        print("\n📋 Error Breakdown by Category:")
        for category, errors in categories.items():
            if errors:
                print(f"  {category.replace('_', ' ').title()}: {len(errors)} errors")

        print("\n🎯 Recommended Fix Order:")
        if categories["no_untyped_def"]:
            print(f"  1. Missing type annotations: {len(categories['no_untyped_def'])} (easiest)")
        if categories["unused_ignore"]:
            print(f"  2. Unused type ignores: {len(categories['unused_ignore'])} (cleanup)")
        if categories["boto3_typing"]:
            print(f"  3. AWS client typing: {len(categories['boto3_typing'])} (helper pattern)")
        if categories["assignment_issues"]:
            print(f"  4. Assignment issues: {len(categories['assignment_issues'])} (casting)")
        if categories["stub_files"]:
            print(f"  5. Stub files: {len(categories['stub_files'])} (optional)")

    print("\n" + "=" * 80)
    return total_count, core_count, categories


if __name__ == "__main__":
    total_errors, core_errors, error_categories = print_validation_report()

    # Exit with error count for CI/CD integration
    sys.exit(min(total_errors, 255) if total_errors > 0 else 0)
