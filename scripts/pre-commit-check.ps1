#!/usr/bin/env pwsh
# Pre-commit validation script for PurposePath AI
# Run this before committing to ensure code quality

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Pre-Commit Quality Checks" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# Change to repo root
Set-Location $PSScriptRoot\..

# 1. Ruff Linting
Write-Host "[1/3] Running Ruff linting..." -ForegroundColor Yellow
python -m ruff check coaching/ shared/ --output-format=concise
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ruff linting failed!" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "✅ Ruff linting passed" -ForegroundColor Green
}
Write-Host ""

# 2. Ruff Formatting Check
Write-Host "[2/3] Checking code formatting..." -ForegroundColor Yellow
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
Write-Host "[3/3] Running type checks..." -ForegroundColor Yellow
python -m mypy coaching/src shared/ --explicit-package-bases --no-error-summary 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Type checking warnings present (not blocking)" -ForegroundColor Yellow
} else {
    Write-Host "✅ Type checking passed" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "=====================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "✅ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host "   Safe to commit and push!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ $ErrorCount CHECK(S) FAILED" -ForegroundColor Red
    Write-Host "   Please fix the errors before committing" -ForegroundColor Red
    exit 1
}
