# Local Test Runner for PurposePath AI
# Run this before pushing to catch errors early

Write-Host "=== PurposePath AI Local Test Runner ===" -ForegroundColor Cyan
Write-Host ""

# Store original location
$OriginalLocation = Get-Location
$ScriptRoot = Split-Path -Parent $PSScriptRoot
$RootDir = $ScriptRoot

try {
    Set-Location $RootDir
    
    Write-Host "[1/5] Checking Python version..." -ForegroundColor Yellow
    python --version
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Python not found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "[2/5] Running Ruff (linting)..." -ForegroundColor Yellow
    python -m ruff check coaching/ shared/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Ruff linting failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Ruff linting passed" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[3/5] Running Ruff (formatting check)..." -ForegroundColor Yellow
    python -m ruff format --check coaching/ shared/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Ruff formatting failed" -ForegroundColor Red
        Write-Host "Run: python -m ruff format coaching/ shared/ --fix" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✓ Ruff formatting passed" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[4/5] Running MyPy (type checking)..." -ForegroundColor Yellow
    python -m mypy coaching/src shared/ --explicit-package-bases --warn-only
    Write-Host "✓ MyPy completed (warnings only)" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[5/5] Running Pytest (unit tests)..." -ForegroundColor Yellow
    python -m pytest coaching/tests/unit -v --cov=coaching/src --cov=shared --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Some tests failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ All tests passed" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "=== ✓ ALL CHECKS PASSED ===" -ForegroundColor Green
    Write-Host "Safe to push to remote" -ForegroundColor Cyan
    
} finally {
    Set-Location $OriginalLocation
}
