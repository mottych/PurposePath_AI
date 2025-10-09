#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive Python validation script for PurposePath API
.DESCRIPTION
    Runs ALL validation tools (Ruff, Pylance check reminder, Mypy, Tests)
    to ensure zero errors before closing GitHub issues.
.NOTES
    Always run from workspace root: pp_ai/
#>

param(
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$workspace = "c:\Projects\XBS\PurposePath\PurposePath_Api\pp_ai"

# Ensure we're in the right directory
if ($PWD.Path -ne $workspace) {
    Write-Host "📁 Changing to workspace root..." -ForegroundColor Cyan
    Set-Location $workspace
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║     PurposePath API - Comprehensive Validation Suite      ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

$allPassed = $true
$results = @()

# Step 1: Ruff Linting
Write-Host "`n🔍 Step 1: Ruff Linting (Style, Imports, Syntax)" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
$ruffOutput = python -m ruff check . --exclude=".venv,venv,__pycache__,.pytest_cache,htmlcov,mypy_boto3_dynamodb,stubs" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Ruff: All checks passed!" -ForegroundColor Green
    $results += "✅ Ruff Linting: PASSED"
}
else {
    Write-Host "❌ Ruff: Found errors" -ForegroundColor Red
    if ($Verbose) { $ruffOutput }
    $allPassed = $false
    $results += "❌ Ruff Linting: FAILED"
}

# Step 2: Pylance Check Reminder
Write-Host "`n🔍 Step 2: Pylance Type Checking (VS Code)" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "⚠️  MANUAL CHECK REQUIRED:" -ForegroundColor Yellow
Write-Host "    1. Open VS Code Problems panel (Ctrl+Shift+M)" -ForegroundColor Gray
Write-Host "    2. Filter by 'Errors' only" -ForegroundColor Gray
Write-Host "    3. Verify ZERO Python errors are shown" -ForegroundColor Gray
Write-Host "    4. This is what users see - must be clean!" -ForegroundColor Gray
$pylanceCheck = Read-Host "`n   Did Pylance show ZERO Python errors? (y/n)"
if ($pylanceCheck -eq 'y' -or $pylanceCheck -eq 'Y') {
    Write-Host "✅ Pylance: Confirmed clean" -ForegroundColor Green
    $results += "✅ Pylance Type Checking: PASSED (manual verification)"
}
else {
    Write-Host "❌ Pylance: Errors detected" -ForegroundColor Red
    $allPassed = $false
    $results += "❌ Pylance Type Checking: FAILED"
}

# Step 3: Mypy Type Checking - Coaching
Write-Host "`n🔍 Step 3a: Mypy Type Checking - Coaching Service" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Set-Location "$workspace\coaching"
$mypyCoaching = python -m mypy src/ --exclude="tests" 2>&1
if ($LASTEXITCODE -eq 0 -or $mypyCoaching -match "Success: no issues found") {
    Write-Host "✅ Mypy (Coaching): No issues found" -ForegroundColor Green
    $results += "✅ Mypy Coaching: PASSED"
}
else {
    Write-Host "❌ Mypy (Coaching): Found issues" -ForegroundColor Red
    if ($Verbose) { $mypyCoaching }
    $allPassed = $false
    $results += "❌ Mypy Coaching: FAILED"
}

# Step 3b: Mypy Type Checking - Account
Write-Host "`n🔍 Step 3b: Mypy Type Checking - Account Service" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Set-Location "$workspace\account"
$mypyAccount = python -m mypy src/ --exclude="tests" 2>&1
if ($LASTEXITCODE -eq 0 -or $mypyAccount -match "Success: no issues found") {
    Write-Host "✅ Mypy (Account): No issues found" -ForegroundColor Green
    $results += "✅ Mypy Account: PASSED"
}
else {
    Write-Host "❌ Mypy (Account): Found issues" -ForegroundColor Red
    if ($Verbose) { $mypyAccount }
    $allPassed = $false
    $results += "❌ Mypy Account: FAILED"
}

# Step 4: Tests
if (-not $SkipTests) {
    Write-Host "`n🧪 Step 4: Test Suite" -ForegroundColor Cyan
    Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Set-Location $workspace
    $testOutput = uv run pytest tests/ -v --tb=short 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tests: All passed" -ForegroundColor Green
        $results += "✅ Test Suite: PASSED"
    }
    else {
        Write-Host "❌ Tests: Some failures" -ForegroundColor Red
        if ($Verbose) { $testOutput }
        $allPassed = $false
        $results += "❌ Test Suite: FAILED"
    }
}
else {
    Write-Host "`n🧪 Step 4: Test Suite - SKIPPED" -ForegroundColor Yellow
    $results += "⚠️  Test Suite: SKIPPED"
}

# Summary
Write-Host "`n`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor $(if ($allPassed) { "Green" } else { "Red" })
Write-Host "║                   VALIDATION SUMMARY                       ║" -ForegroundColor $(if ($allPassed) { "Green" } else { "Red" })
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $(if ($allPassed) { "Green" } else { "Red" })

foreach ($result in $results) {
    Write-Host "  $result"
}

if ($allPassed) {
    Write-Host "`n🎉 ALL VALIDATIONS PASSED - Ready to close issue!" -ForegroundColor Green
    Write-Host "   ZERO errors across all validation tools" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n❌ VALIDATION FAILED - Fix errors before closing issue" -ForegroundColor Red
    Write-Host "   Review errors above and re-run validation" -ForegroundColor Red
    exit 1
}
