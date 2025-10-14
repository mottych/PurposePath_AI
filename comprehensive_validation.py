#!/usr/bin/env python3
"""
Comprehensive type validation script that tries multiple mypy configurations
to catch all possible type issues that IDEs might detect
"""
import subprocess
import sys


def run_mypy_with_config(target: str, config_name: str, extra_flags: list[str] | None = None) -> tuple[int, list[str]]:
    """Run mypy with specific configuration and return errors."""
    if extra_flags is None:
        extra_flags = []

    cmd = ["python", "-m", "mypy", target, "--show-error-codes", "--no-error-summary", *extra_flags]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        error_lines = [line for line in output_lines if ': error:' in line]

        if error_lines:
            print(f"\n🔍 {config_name} Configuration:")
            print(f"Command: {' '.join(cmd)}")
            print(f"Errors found: {len(error_lines)}")
            for error in error_lines[:5]:  # Show first 5
                print(f"  {error}")
            if len(error_lines) > 5:
                print(f"  ... and {len(error_lines) - 5} more")

        return len(error_lines), error_lines
    except Exception as e:
        print(f"Error running {config_name}: {e}")
        return -1, []


def comprehensive_validation(file_path: str) -> None:
    """Run comprehensive validation with multiple mypy configurations."""
    print(f"🔍 Comprehensive Validation: {file_path}")
    print("=" * 80)

    # Test different mypy configurations that might catch different issues
    configs = [
        ("Standard", []),
        ("Strict", ["--strict"]),
        ("Warn Return Any", ["--warn-return-any"]),
        ("Strict + Warn Return Any", ["--strict", "--warn-return-any"]),
        ("Ultra Strict", ["--strict", "--warn-return-any", "--warn-unused-ignores", "--disallow-any-expr"]),
        ("No Implicit Optional", ["--strict", "--no-implicit-optional"]),
        ("Disallow Untyped Calls", ["--disallow-untyped-calls", "--disallow-untyped-defs"]),
        ("All Warnings", [
            "--strict",
            "--warn-return-any",
            "--warn-unused-ignores",
            "--warn-redundant-casts",
            "--warn-unused-configs",
            "--disallow-any-generics",
            "--disallow-subclassing-any"
        ])
    ]

    total_unique_errors = set()

    for config_name, flags in configs:
        _error_count, errors = run_mypy_with_config(file_path, config_name, flags)
        if errors:
            total_unique_errors.update(errors)

    if not total_unique_errors:
        print("\n✅ No errors found with any configuration!")
    else:
        print(f"\n❌ Total unique errors across all configurations: {len(total_unique_errors)}")
        print("\nAll unique errors:")
        for error in sorted(total_unique_errors)[:10]:  # Show first 10 unique errors
            print(f"  {error}")
        if len(total_unique_errors) > 10:
            print(f"  ... and {len(total_unique_errors) - 10} more unique errors")


if __name__ == "__main__":
    file_to_check = sys.argv[1] if len(sys.argv) > 1 else "shared/services/data_access.py"
    comprehensive_validation(file_to_check)
