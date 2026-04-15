#!/usr/bin/env pwsh
# Quick fix script for common code quality issues
# Automatically fixes linting and formatting errors

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Quick Fix - Auto-correct Issues" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Change to repo root
Set-Location $PSScriptRoot\..

$RepoRoot = (Get-Location).Path
. (Join-Path $PSScriptRoot "Resolve-CoachingPython.ps1")
$PythonExe = Get-CoachingPythonExecutable -RepoRoot $RepoRoot
if (-not $PythonExe) {
    Write-Host "No venv Python found. Run: cd coaching && uv sync" -ForegroundColor Red
    exit 1
}
Write-Host "Using Python: $PythonExe" -ForegroundColor DarkGray
Write-Host ""

$FixCount = 0

# 1. Auto-fix Ruff linting issues
Write-Host "[1/2] Auto-fixing Ruff linting issues..." -ForegroundColor Yellow
& $PythonExe -m ruff check coaching/ shared/ --fix --silent 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Ruff linting issues fixed" -ForegroundColor Green
    $FixCount++
} else {
    Write-Host "⚠️  Some linting issues remain (may need manual fix)" -ForegroundColor Yellow
}
Write-Host ""

# 2. Auto-fix formatting
Write-Host "[2/2] Auto-fixing code formatting..." -ForegroundColor Yellow
$FormatOutput = & $PythonExe -m ruff format coaching/ shared/ 2>&1
if ($FormatOutput -match "reformatted") {
    Write-Host "✅ Code formatting fixed" -ForegroundColor Green
    $FixCount++
} else {
    Write-Host "✅ Code already formatted correctly" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Quick Fix Complete!" -ForegroundColor Green
Write-Host ""

if ($FixCount -gt 0) {
    Write-Host "📝 Files have been modified. Please review changes:" -ForegroundColor Yellow
    Write-Host "   git diff" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Review the changes: git diff" -ForegroundColor Gray
Write-Host "  2. Run full checks: .\scripts\pre-commit-check.ps1" -ForegroundColor Gray
Write-Host "  3. Commit your changes: git add . && git commit" -ForegroundColor Gray
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
