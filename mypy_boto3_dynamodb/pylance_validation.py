#!/usr/bin/env python3
"""
Pylance-compatible mypy validation script
Attempts to replicate VS Code Pylance's stricter type checking
"""
import subprocess
import sys
from pathlib import Path


def run_pylance_style_mypy(target_dir: str) -> tuple[int, list[str]]:
    """Run mypy with Pylance-style strict settings (matching VS Code strict mode)."""
    cmd = [
        sys.executable, "-m", "mypy", target_dir,
        "--strict",
        "--show-error-codes",
        "--no-error-summary",
        "--warn-return-any",
        "--warn-unused-ignores",
        "--warn-redundant-casts",
        "--warn-unused-configs",
        "--disallow-any-generics",
        "--disallow-any-unimported",
        "--disallow-any-expr",
        "--disallow-any-decorated",
        "--disallow-any-explicit",
        "--disallow-subclassing-any",
        "--warn-incomplete-stub",
        "--check-untyped-defs",
        "--disallow-incomplete-defs",
        "--disallow-untyped-decorators",
        "--implicit-reexport",
        "--no-implicit-optional"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Filter out some noise and focus on real errors
        error_lines = []
        for line in output_lines:
            if ': error:' in line and not any(skip in line for skip in [
                'note:', 'found module', 'Success:', 'Skipping'
            ]):
                error_lines.append(line)

        return len(error_lines), error_lines
    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout running mypy on {target_dir}")
        return -1, []
    except Exception as e:
        print(f"❌ Error running mypy on {target_dir}: {e}")
        return -1, []


def validate_specific_service(service: str) -> None:
    """Validate a specific service with Pylance-style checking."""
    service_path = Path(service)
    if not service_path.exists():
        print(f"⚠️ Service {service} not found")
        return

    print(f"\n🔍 Pylance-Style Validation: {service}")
    print("=" * 60)

    error_count, errors = run_pylance_style_mypy(service)

    if error_count <= 0:
        print("✅ No errors found!")
        return

    print(f"❌ Found {error_count} errors:")

    # Group errors by file for easier review
    file_errors: dict[str, list[str]] = {}
    for error in errors:
        if ':' in error:
            file_part = error.split(':', 2)
            if len(file_part) >= 2:
                file_path = file_part[0]
                line_num = file_part[1]
                error_msg = ':'.join(file_part[2:]) if len(file_part) > 2 else error

                if file_path not in file_errors:
                    file_errors[file_path] = []
                file_errors[file_path].append(f"  Line {line_num}{error_msg}")

    # Print grouped results
    for file_path, file_error_list in sorted(file_errors.items()):
        print(f"\n📄 {file_path}")
        for error in file_error_list[:10]:  # Limit to first 10 per file
            print(error)
        if len(file_error_list) > 10:
            print(f"  ... and {len(file_error_list) - 10} more errors")


def main() -> None:
    """Run Pylance-style validation on all services."""
    services = ["account", "coaching", "traction", "shared"]

    print("🎯 Pylance-Compatible Type Validation")
    print("=" * 80)

    for service in services:
        validate_specific_service(service)
        # Add a small delay to avoid overwhelming output

    print("\n🎯 Use this to systematically find all Pylance errors!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single service mode
        validate_specific_service(sys.argv[1])
    else:
        # All services mode
        main()
