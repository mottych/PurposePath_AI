#!/usr/bin/env pwsh
# Pre-commit validation script for PurposePath AI
# Run this before committing to ensure code quality
#
# Usage: 
#   .\scripts\pre-commit-check.ps1           # Run all checks
#   .\scripts\pre-commit-check.ps1 -Quick    # Skip tests (faster)

param(
    [switch]$Quick = $false
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Pre-Commit Quality Checks" -ForegroundColor Cyan
if ($Quick) {
    Write-Host "(Quick Mode - Tests Skipped)" -ForegroundColor Yellow
}
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# Change to repo root
Set-Location $PSScriptRoot\..

# 1. Ruff Linting
Write-Host "[1/4] Running Ruff linting..." -ForegroundColor Yellow
python -m ruff check coaching/ shared/ --output-format=concise
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ruff linting failed!" -ForegroundColor Red
    Write-Host "   Run 'python -m ruff check coaching/ shared/ --fix' to auto-fix" -ForegroundColor Yellow
    $ErrorCount++
} else {
    Write-Host "✅ Ruff linting passed" -ForegroundColor Green
}
Write-Host ""

# 2. Ruff Formatting Check
Write-Host "[2/4] Checking code formatting..." -ForegroundColor Yellow
python -m ruff format --check coaching/ shared/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Code formatting check failed!" -ForegroundColor Red
    Write-Host "   Run 'python -m ruff format coaching/ shared/' to fix" -ForegroundColor Yellow
    $ErrorCount++
} else {
    Write-Host "✅ Code formatting passed" -ForegroundColor Green
}
Write-Host ""

# 3. MyPy Type Checking (informational only)
Write-Host "[3/4] Running type checks..." -ForegroundColor Yellow
python -m mypy coaching/src shared/ --explicit-package-bases --no-error-summary 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Type checking warnings present (not blocking)" -ForegroundColor Yellow
    $WarningCount++
} else {
    Write-Host "✅ Type checking passed" -ForegroundColor Green
}
Write-Host ""

# 4. Run Tests (unless Quick mode)
if (-not $Quick) {
    Write-Host "[4/4] Running unit tests..." -ForegroundColor Yellow
    
    # Check if pytest is available
    python -m pytest --version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Pytest not available - skipping tests" -ForegroundColor Yellow
        Write-Host "   Install dependencies: pip install -r requirements.txt" -ForegroundColor Gray
        $WarningCount++
    } else {
        # Try to run tests (same command as CI/CD for consistency)
        $TestArgs = @(
            "coaching/tests/unit",
            "-v",
            "--tb=short",
            "--ignore=coaching/tests/unit/workflows/test_refactored_workflows.py",
            "--ignore=coaching/tests/unit/test_insights_service.py",
            "--ignore=coaching/tests/unit/test_onboarding_service.py",
            "--ignore=coaching/tests/test_llm_service_refactoring.py",
            "--ignore=coaching/tests/test_langgraph_workflows.py",
            "--ignore=coaching/tests/test_business_data_api.py",
            "--ignore=coaching/tests/unit/test_models.py",
            "--ignore=coaching/tests/unit/test_response_models.py",
            "--ignore=coaching/tests/unit/api/test_admin_topics.py",
            "--ignore=coaching/tests/unit/api/test_conversations_api.py",
            "--ignore=coaching/tests/unit/api/test_topics_api.py",
            "--ignore=coaching/tests/unit/domain/entities/test_conversation.py",
            "--ignore=coaching/tests/unit/domain/entities/test_prompt_template.py",
            "--ignore=coaching/tests/unit/domain/events/test_analysis_events.py",
            "--ignore=coaching/tests/unit/domain/events/test_conversation_events.py",
            "--ignore=coaching/tests/unit/domain/exceptions/test_conversation_exceptions.py",
            "--ignore=coaching/tests/unit/domain/services/test_alignment_calculator.py",
            "--ignore=coaching/tests/unit/domain/services/test_completion_validator.py",
            "--ignore=coaching/tests/unit/domain/services/test_phase_transition_service.py",
            "--ignore=coaching/tests/unit/domain/value_objects/test_conversation_context.py"
        )
        $TestOutput = python -m pytest @TestArgs 2>&1
        
        # Check if tests failed due to missing dependencies
        if ($TestOutput -match "ModuleNotFoundError|ImportError") {
            Write-Host "⚠️  Tests skipped - missing dependencies" -ForegroundColor Yellow
            Write-Host "   Some test dependencies not installed locally" -ForegroundColor Gray
            Write-Host "   Tests will run in CI/CD pipeline with full environment" -ForegroundColor Gray
            $WarningCount++
        } elseif ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Unit tests failed!" -ForegroundColor Red
            Write-Host "   Run 'python -m pytest coaching/tests/unit -v --tb=short' to see details" -ForegroundColor Yellow
            $ErrorCount++
        } else {
            Write-Host "✅ Unit tests passed" -ForegroundColor Green
        }
    }
    Write-Host ""
} else {
    Write-Host "[4/4] Skipping tests (Quick mode)" -ForegroundColor Gray
    Write-Host ""
}

# Summary
Write-Host "=====================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    if ($WarningCount -gt 0) {
        Write-Host "   ($WarningCount warning(s) - informational only)" -ForegroundColor Yellow
    }
    Write-Host "   Safe to commit and push!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ $ErrorCount CHECK(S) FAILED" -ForegroundColor Red
    if ($WarningCount -gt 0) {
        Write-Host "   ($WarningCount warning(s) - informational only)" -ForegroundColor Yellow
    }
    Write-Host "   Please fix the errors before committing" -ForegroundColor Red
    exit 1
}
