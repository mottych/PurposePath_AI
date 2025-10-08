#!/usr/bin/env python3
"""
Comprehensive validation script for typing cleanup project setup.
Run this script to verify all components are properly configured before beginning cleanup.
"""

import json
import subprocess
import sys
from pathlib import Path


class ProjectValidator:
    """Validates typing cleanup project setup and readiness."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results: list[tuple[str, bool, str]] = []

    def log(self, test_name: str, success: bool, message: str) -> None:
        """Log validation result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.results.append((test_name, success, message))

    def run_command(self, cmd: list[str], capture_output: bool = True) -> tuple[bool, str]:
        """Run shell command and return success status and output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)

    def check_documentation_exists(self) -> None:
        """Verify all required documentation files exist."""
        required_docs = [
            "docs/README.md",
            "docs/TYPING_CLEANUP_STRATEGY.md",
            "docs/DEVELOPMENT_STANDARDS.md",
            "docs/EXECUTION_PLAN.md",
            "setup_github_project.py",
            "pylance_validation.py"
        ]

        for doc in required_docs:
            doc_path = self.project_root / doc
            exists = doc_path.exists()
            size = doc_path.stat().st_size if exists else 0

            if exists and size > 1000:  # At least 1KB of content
                self.log(f"Documentation: {doc}", True, f"Exists ({size:,} bytes)")
            else:
                self.log(f"Documentation: {doc}", False, f"Missing or empty (size: {size})")

    def check_python_environment(self) -> None:
        """Verify Python environment and required packages."""
        # Check Python version
        success, output = self.run_command([sys.executable, "--version"])
        if success and "Python 3." in output:
            version = output.strip().split()[-1]
            self.log("Python Version", True, f"Python {version} detected")
        else:
            self.log("Python Version", False, "Python not found or invalid version")

        # Check required packages
        required_packages = [
            "mypy", "black", "isort", "flake8", "pre-commit",
            "fastapi", "pydantic", "boto3", "stripe"
        ]

        success, output = self.run_command([sys.executable, "-m", "pip", "list", "--format=json"])
        if success:
            try:
                installed = json.loads(output)
                installed_names = {pkg["name"].lower() for pkg in installed}

                for package in required_packages:
                    if package.lower() in installed_names:
                        # Get version info
                        pkg_info = next((p for p in installed if p["name"].lower() == package.lower()), None)
                        version = pkg_info["version"] if pkg_info else "unknown"
                        self.log(f"Package: {package}", True, f"v{version} installed")
                    else:
                        self.log(f"Package: {package}", False, "Not installed")

            except json.JSONDecodeError:
                self.log("Package Check", False, "Failed to parse pip list output")
        else:
            self.log("Package Check", False, "Failed to run pip list")

    def check_git_setup(self) -> None:
        """Verify git repository and GitHub CLI setup."""
        # Check if we're in a git repository
        success, output = self.run_command(["git", "status", "--porcelain"])
        if success:
            self.log("Git Repository", True, "Valid git repository")

            # Check for uncommitted changes
            if output.strip():
                self.log("Git Status", False, f"Uncommitted changes detected:\n{output[:200]}...")
            else:
                self.log("Git Status", True, "Working tree clean")

            # Check current branch
            success, branch = self.run_command(["git", "branch", "--show-current"])
            if success:
                self.log("Git Branch", True, f"Current branch: {branch.strip()}")
        else:
            self.log("Git Repository", False, "Not a git repository")

        # Check GitHub CLI
        success, output = self.run_command(["gh", "auth", "status"])
        if success and "Logged in to github.com" in output:
            self.log("GitHub CLI", True, "Authenticated and ready")
        else:
            self.log("GitHub CLI", False, "Not authenticated or not installed")

    def check_vscode_extensions(self) -> None:
        """Check if required VS Code extensions are installed."""
        success, output = self.run_command(["code", "--list-extensions"])
        if success:
            extensions = output.lower().split('\n')
            required_extensions = {
                "ms-python.pylance": "Pylance",
                "ms-python.mypy-type-checker": "Mypy Type Checker",
                "ms-python.black-formatter": "Black Formatter",
                "ms-python.isort": "isort"
            }

            for ext_id, ext_name in required_extensions.items():
                if ext_id.lower() in extensions:
                    self.log(f"VS Code Extension: {ext_name}", True, "Installed")
                else:
                    self.log(f"VS Code Extension: {ext_name}", False, "Not installed")
        else:
            self.log("VS Code Extensions", False, "VS Code not found or not in PATH")

    def check_service_structure(self) -> None:
        """Verify expected project structure exists."""
        expected_services = ["account", "coaching", "traction"]
        expected_shared = ["shared"]

        for service in expected_services:
            service_path = self.project_root / service
            src_path = service_path / "src"

            if service_path.exists() and src_path.exists():
                # Count Python files
                py_files = list(src_path.rglob("*.py"))
                self.log(f"Service: {service}", True, f"Found with {len(py_files)} Python files")
            else:
                self.log(f"Service: {service}", False, "Missing or incomplete structure")

        for shared in expected_shared:
            shared_path = self.project_root / shared
            if shared_path.exists():
                py_files = list(shared_path.rglob("*.py"))
                self.log(f"Shared: {shared}", True, f"Found with {len(py_files)} Python files")
            else:
                self.log(f"Shared: {shared}", False, "Missing")

    def test_validation_script(self) -> None:
        """Test the Pylance validation script."""
        validation_script = self.project_root / "pylance_validation.py"
        if not validation_script.exists():
            self.log("Validation Script", False, "pylance_validation.py not found")
            return

        # Test with a simple service (try both with and without args)
        success, output = self.run_command([sys.executable, "pylance_validation.py", "shared"])
        if not success:
            success, output = self.run_command([sys.executable, "pylance_validation.py"])

        if success and ("errors found" in output.lower() or "no errors found" in output.lower() or "pass validation" in output.lower()):
            # Extract error count if possible
            lines = output.split('\n')
            error_line = next((line for line in lines if ("errors found" in line.lower() or "no errors found" in line.lower())), "")
            self.log("Validation Script", True, f"Working - {error_line.strip() or 'Completed successfully'}")
        else:
            self.log("Validation Script", False, f"Failed or unexpected output: {output[:200]}...")

    def test_github_script(self) -> None:
        """Test the GitHub setup script (dry run)."""
        setup_script = self.project_root / "setup_github_project.py"
        if not setup_script.exists():
            self.log("GitHub Setup Script", False, "setup_github_project.py not found")
            return

        # Read the script to verify it has the expected structure
        try:
            content = setup_script.read_text(encoding='utf-8')
            if '"label", "create"' in content and '"issue", "create"' in content and "GitHub" in content:
                self.log("GitHub Setup Script", True, "Contains expected GitHub CLI commands")
            else:
                self.log("GitHub Setup Script", False, "Missing expected GitHub CLI integration")
        except Exception as e:
            self.log("GitHub Setup Script", False, f"Error reading script: {e}")

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 PurposePath Typing Cleanup Project Validation")
        print("=" * 60)
        print()

        self.check_documentation_exists()
        print()

        self.check_python_environment()
        print()

        self.check_git_setup()
        print()

        self.check_vscode_extensions()
        print()

        self.check_service_structure()
        print()

        self.test_validation_script()
        print()

        self.test_github_script()
        print()

        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        failed_tests = total_tests - passed_tests

        print("📊 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📋 Total:  {total_tests}")
        print()

        if failed_tests == 0:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✨ Your environment is ready for typing cleanup execution.")
            print("🚀 Next step: Run 'python setup_github_project.py' to begin")
        else:
            print("⚠️  Some validations failed. Please address the issues above before proceeding.")
            print()
            print("💡 Common fixes:")
            print("   • Install missing packages: pip install -r requirements-dev.txt")
            print("   • Install GitHub CLI: https://cli.github.com/")
            print("   • Install VS Code extensions: code --install-extension ms-python.pylance")
            print("   • Authenticate GitHub CLI: gh auth login")

        print()
        return failed_tests == 0

def main():
    """Main validation function."""
    validator = ProjectValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
