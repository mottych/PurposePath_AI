#!/usr/bin/env python3
"""
GitHub Project Setup for PurposePath API Typing Cleanup
Creates issues, labels, milestones, and project tracking for systematic cleanup.
"""

import json
import subprocess
from typing import Any, cast


def run_gh_command(command: list[str]) -> str:
    """Run GitHub CLI command and return output."""
    try:
        result = subprocess.run(
            ["gh", *command],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"GitHub CLI error: {e}")
        print(f"Stderr: {e.stderr}")
        raise


def create_labels() -> None:
    """Create standardized labels for typing cleanup."""
    labels = [
        ("type-safety", "ff6b6b", "Type safety and annotation issues"),
        ("cleanup", "4ecdc4", "Code cleanup and refactoring"),
        ("architecture", "45b7d1", "Clean architecture and patterns"),
        ("priority-critical", "d63031", "Critical business logic fixes"),
        ("priority-high", "fdcb6e", "High priority infrastructure"),
        ("priority-medium", "6c5ce7", "Medium priority improvements"),
        ("priority-low", "a29bfe", "Low priority polish"),
        ("service-account", "00b894", "Account service related"),
        ("service-coaching", "00cec9", "Coaching service related"),
        ("service-traction", "55a3ff", "Traction service related"),
        ("service-shared", "fd79a8", "Shared infrastructure"),
        ("phase-1", "2d3436", "Phase 1: Foundation"),
        ("phase-2", "636e72", "Phase 2: Core Services"),
        ("phase-3", "b2bec3", "Phase 3: Systematic Patterns"),
        ("phase-4", "ddd", "Phase 4: Testing & Validation")
    ]

    print("🏷️ Creating GitHub labels...")
    for name, color, description in labels:
        try:
            run_gh_command([
                "label", "create", name,
                "--color", color,
                "--description", description
            ])
            print(f"  ✅ Created label: {name}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️ Label already exists: {name}")


def create_milestones() -> None:
    """Create milestones for each cleanup phase."""
    milestones = [
        ("Phase 1: Foundation Setup", "2025-09-25", "Establish type-safe foundation and shared infrastructure"),
        ("Phase 2: Core Services", "2025-09-26", "Fix business-critical service typing"),
        ("Phase 3: Systematic Patterns", "2025-09-27", "Address remaining systematic issues"),
        ("Phase 4: Testing & Validation", "2025-09-27", "Comprehensive validation and test cleanup")
    ]

    print("\n🎯 Creating GitHub milestones...")
    for title, due_date, description in milestones:
        try:
            run_gh_command([
                "api", "repos/:owner/:repo/milestones",
                "--method", "POST",
                "--field", f"title={title}",
                "--field", f"due_on={due_date}T23:59:59Z",
                "--field", f"description={description}"
            ])
            print(f"  ✅ Created milestone: {title}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️ Milestone may already exist: {title}")


def create_cleanup_issues() -> list[dict[str, Any]]:
    """Create GitHub issues for systematic typing cleanup."""

    issues: list[dict[str, Any]] = [
        # Phase 1: Foundation Setup
        {
            "title": "🏗️ Create shared type definitions and common patterns",
            "body": """## Objective
Establish foundational type definitions and patterns for consistent typing across services.

## Tasks
- [ ] Create `shared/types/` directory structure
- [ ] Define common TypedDict classes for AWS/DynamoDB responses
- [ ] Create type aliases for frequently used complex types
- [ ] Establish JSON response type patterns
- [ ] Document typing standards and patterns

## Acceptance Criteria
- [ ] Shared type definitions available for import
- [ ] Common patterns documented
- [ ] Zero type errors in shared type definitions
- [ ] Examples created for each pattern

## Files Affected
- `shared/types/common.py` (new)
- `shared/types/external.py` (new)
- `shared/types/aws.py` (new)

## Priority
Critical - Foundation for all other work

## Phase
Phase 1: Foundation Setup
""",
            "labels": ["type-safety", "priority-critical", "service-shared", "phase-1"],
            "milestone": "Phase 1: Foundation Setup"
        },

        {
            "title": "🔧 Fix shared infrastructure data access layer",
            "body": """## Objective
Fix typing issues in shared data access layer that affects all services.

## Tasks
- [ ] Fix `shared/services/data_access.py` DynamoDB typing
- [ ] Address `shared/services/aws_helpers.py` boto3 typing
- [ ] Clean up `shared/models/` with proper Pydantic v2 patterns
- [ ] Add proper type annotations for all repository methods
- [ ] Fix boto3 client/resource typing

## Acceptance Criteria
- [ ] Zero Pylance errors in shared infrastructure
- [ ] All repository methods properly typed
- [ ] boto3 operations use proper type annotations or ignores
- [ ] Comprehensive test coverage maintained

## Files Affected
- `shared/services/data_access.py`
- `shared/services/aws_helpers.py`
- `shared/services/boto3_helpers.py`
- `shared/models/multitenant.py`
- `shared/models/schemas.py`

## Priority
Critical - Affects all services

## Phase
Phase 1: Foundation Setup
""",
            "labels": ["type-safety", "priority-critical", "service-shared", "phase-1"],
            "milestone": "Phase 1: Foundation Setup"
        },

        # Phase 2: Account Service
        {
            "title": "🔐 Fix Account service authentication typing",
            "body": """## Objective
Fix typing issues in Account service authentication and authorization.

## Tasks
- [ ] Create `JWTPayload` TypedDict for JWT token structure
- [ ] Fix Google OAuth integration typing in `auth.py` line 87
- [ ] Add proper error handling types for auth failures
- [ ] Fix dependency injection typing
- [ ] Update auth middleware with proper types

## Acceptance Criteria
- [ ] Zero Pylance errors in auth modules
- [ ] JWT payload properly typed with TypedDict
- [ ] Google OAuth integration uses proper types
- [ ] Auth middleware passes strict type checking

## Files Affected
- `account/src/api/auth.py` (line 87 specifically)
- `account/src/api/dependencies.py`
- `account/src/services/auth_service.py`

## Priority
Critical - Core business logic

## Phase
Phase 2: Core Services
""",
            "labels": ["type-safety", "priority-critical", "service-account", "phase-2"],
            "milestone": "Phase 2: Core Services"
        },

        {
            "title": "💳 Fix Account service Stripe billing integration",
            "body": """## Objective
Fix typing issues in Stripe billing integration and payment processing.

## Tasks
- [ ] Replace explicit `Any` in Stripe API calls (lines 186, 224)
- [ ] Create Stripe response TypedDict classes
- [ ] Fix billing portal integration typing
- [ ] Add proper error handling for Stripe operations
- [ ] Create billing webhook typing

## Acceptance Criteria
- [ ] Zero Pylance errors in billing modules
- [ ] Stripe API calls properly typed with ignores where needed
- [ ] Billing responses use proper models
- [ ] Webhook handling fully typed

## Files Affected
- `account/src/services/billing_service.py` (lines 186, 224 specifically)
- `account/src/api/routes/billing.py`

## Priority
Critical - Payment processing

## Phase
Phase 2: Core Services
""",
            "labels": ["type-safety", "priority-critical", "service-account", "phase-2"],
            "milestone": "Phase 2: Core Services"
        },

        # Phase 2: Coaching Service
        {
            "title": "🤖 Fix Coaching service LLM provider typing",
            "body": """## Objective
Fix typing issues in LLM provider integration and orchestration.

## Tasks
- [ ] Fix `coaching/src/llm/providers/base.py` provider interface
- [ ] Fix `coaching/src/llm/orchestrator.py` conversation flow (line 42, 287, 288)
- [ ] Add proper Bedrock/OpenAI response typing
- [ ] Fix async function return types in LLM calls
- [ ] Create conversation context typing

## Acceptance Criteria
- [ ] Zero Pylance errors in LLM modules
- [ ] Provider interface properly typed
- [ ] Orchestrator conversation flow fully typed
- [ ] LLM API responses use proper models

## Files Affected
- `coaching/src/llm/providers/base.py` (lines 75, 78)
- `coaching/src/llm/orchestrator.py` (lines 42, 287, 288)
- `coaching/src/llm/providers/bedrock.py`

## Priority
Critical - Core value proposition

## Phase
Phase 2: Core Services
""",
            "labels": ["type-safety", "priority-critical", "service-coaching", "phase-2"],
            "milestone": "Phase 2: Core Services"
        },

        {
            "title": "💬 Fix Coaching service data access layer",
            "body": """## Objective
Fix typing issues in Coaching service data access and conversation management.

## Tasks
- [ ] Fix `coaching/shared/services/data_access.py` (lines 86, 160, 291, 329, 334, 339, 399, 417, 517, 521, 524)
- [ ] Add conversation repository typing
- [ ] Fix prompt management types
- [ ] Add proper message chain typing
- [ ] Fix memory system type safety

## Acceptance Criteria
- [ ] Zero Pylance errors in coaching data access
- [ ] Conversation operations properly typed
- [ ] Message management fully typed
- [ ] Memory system uses proper types

## Files Affected
- `coaching/shared/services/data_access.py`
- `coaching/src/repositories/conversation_repository.py`
- `coaching/src/repositories/prompt_repository.py`

## Priority
High - Data consistency

## Phase
Phase 2: Core Services
""",
            "labels": ["type-safety", "priority-high", "service-coaching", "phase-2"],
            "milestone": "Phase 2: Core Services"
        },

        # Phase 3: Systematic Patterns
        {
            "title": "🎯 Eliminate explicit Any annotations systematically",
            "body": """## Objective
Replace all explicit `Any` type annotations with proper types across services.

## Tasks
- [ ] Audit all explicit `Any` usage across codebase
- [ ] Create type aliases for complex structures
- [ ] Replace `Any` with proper union types where applicable
- [ ] Add `# type: ignore` with justification for unavoidable cases
- [ ] Document type decisions in code comments

## Acceptance Criteria
- [ ] No explicit `Any` annotations without justification
- [ ] Complex types have proper aliases
- [ ] All `# type: ignore` comments have explanations
- [ ] Type coverage >95% across all services

## Priority
Medium - Systematic improvement

## Phase
Phase 3: Systematic Patterns
""",
            "labels": ["type-safety", "priority-medium", "phase-3"],
            "milestone": "Phase 3: Systematic Patterns"
        },

        {
            "title": "🚀 Fix FastAPI decorator and route handler typing",
            "body": """## Objective
Fix typing issues in FastAPI route handlers and decorators.

## Tasks
- [ ] Create typed wrapper functions for common route patterns
- [ ] Fix async function return type annotations
- [ ] Establish dependency injection typing patterns
- [ ] Fix request/response model validation
- [ ] Document routing type patterns

## Acceptance Criteria
- [ ] All route handlers properly typed
- [ ] Dependency injection works with strict typing
- [ ] Request/response models validated
- [ ] Common patterns documented

## Priority
Medium - Developer experience

## Phase
Phase 3: Systematic Patterns
""",
            "labels": ["type-safety", "priority-medium", "phase-3"],
            "milestone": "Phase 3: Systematic Patterns"
        },

        # Phase 4: Testing & Validation
        {
            "title": "🧪 Fix test code typing and validation",
            "body": """## Objective
Complete typing cleanup for test suites and validation infrastructure.

## Tasks
- [ ] Add pytest fixture typing across all test files
- [ ] Fix mock object type annotations
- [ ] Create test data factory typing
- [ ] Fix async test patterns
- [ ] Add integration test typing

## Acceptance Criteria
- [ ] Zero Pylance errors in test files
- [ ] All fixtures properly typed
- [ ] Mock objects use proper annotations
- [ ] Test data factories fully typed

## Priority
Low - Test infrastructure

## Phase
Phase 4: Testing & Validation
""",
            "labels": ["type-safety", "priority-low", "phase-4"],
            "milestone": "Phase 4: Testing & Validation"
        },

        {
            "title": "✅ Final validation and documentation",
            "body": """## Objective
Complete final validation of typing cleanup and update documentation.

## Tasks
- [ ] Run Pylance validation across all services (target: 0 errors)
- [ ] Execute full test suite with type checking
- [ ] Validate CI/CD pipeline with new type requirements
- [ ] Update development documentation
- [ ] Create troubleshooting guide for future type issues

## Acceptance Criteria
- [ ] Zero Pylance errors across entire codebase
- [ ] All tests pass with strict type checking
- [ ] CI/CD enforces type safety
- [ ] Documentation updated and complete

## Priority
Critical - Project completion

## Phase
Phase 4: Testing & Validation
""",
            "labels": ["type-safety", "priority-critical", "phase-4"],
            "milestone": "Phase 4: Testing & Validation"
        }
    ]

    print("\n📋 Creating GitHub issues...")
    created_issues: list[dict[str, Any]] = []

    for issue in issues:
        try:
            title: str = str(issue["title"])
            body: str = str(issue["body"])
            issue_labels = issue.get("labels", [])
            labels: list[str] = cast(list[str], issue_labels) if isinstance(issue_labels, list) else []

            # Create the issue
            result = run_gh_command([
                "issue", "create",
                "--title", title,
                "--body", body,
                "--label", ",".join(labels)
            ])

            issue_number = result.split("/")[-1] if "/" in result else "unknown"
            print(f"  ✅ Created issue #{issue_number}: {issue['title']}")
            created_issues.append({**issue, "number": issue_number})

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to create issue: {issue['title']}")
            print(f"     Error: {e}")

    return created_issues


def close_existing_typing_issues() -> None:
    """Close existing typing-related issues to clean slate."""
    print("\n🗂️ Checking for existing typing issues...")

    try:
        # Get open issues related to typing
        result = run_gh_command([
            "issue", "list",
            "--search", "type typing mypy pylance error",
            "--state", "open",
            "--json", "number,title"
        ])

        if result.strip():
            issues = json.loads(result)
            print(f"Found {len(issues)} existing typing-related issues")

            for issue in issues:
                try:
                    run_gh_command([
                        "issue", "close", str(issue["number"]),
                        "--comment", "Closing in favor of systematic typing cleanup project. See new issues with phase-based organization."
                    ])
                    print(f"  ✅ Closed issue #{issue['number']}: {issue['title']}")
                except subprocess.CalledProcessError:
                    print(f"  ⚠️ Could not close issue #{issue['number']}")
        else:
            print("No existing typing issues found")

    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print("Could not query existing issues - continuing with new issue creation")


def setup_development_toolchain() -> None:
    """Set up development environment and toolchain."""
    print("\n🛠️ Setting up development toolchain...")

    # Create VS Code workspace settings
    vscode_dir = ".vscode"
    settings_content: dict[str, Any] = {
        "python.analysis.typeCheckingMode": "strict",
        "python.analysis.autoImportCompletions": True,
        "python.analysis.completeFunctionParens": True,
        "python.linting.mypyEnabled": True,
        "python.linting.enabled": True,
        "python.formatting.provider": "black",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.organizeImports": True,
            "source.fixAll": True
        },
        "files.exclude": {
            "**/__pycache__": True,
            "**/.pytest_cache": True,
            "**/.mypy_cache": True
        }
    }

    try:
        import os
        os.makedirs(vscode_dir, exist_ok=True)

        with open(f"{vscode_dir}/settings.json", "w") as f:
            json.dump(settings_content, f, indent=2)
        print("  ✅ Created VS Code workspace settings")

    except Exception as e:
        print(f"  ⚠️ Could not create VS Code settings: {e}")


def main() -> None:
    """Main setup function."""
    print("🚀 Setting up PurposePath API Typing Cleanup Project")
    print("=" * 60)

    # Check if GitHub CLI is available
    try:
        run_gh_command(["--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) not found. Please install it first:")
        print("   https://cli.github.com/")
        return

    # Setup project infrastructure
    create_labels()
    create_milestones()
    close_existing_typing_issues()
    created_issues = create_cleanup_issues()
    setup_development_toolchain()

    print("\n🎉 Project setup complete!")
    print(f"📊 Created {len(created_issues)} issues across 4 phases")
    print("🏷️ Organized with labels and milestones")
    print("🛠️ Development toolchain configured")

    print("\n📋 Next Steps:")
    print("1. Review created issues on GitHub")
    print("2. Assign team members to appropriate issues")
    print("3. Begin with Phase 1 foundation work")
    print("4. Follow systematic approach through all phases")
    print("5. Validate completion with Pylance showing zero errors")


if __name__ == "__main__":
    main()
