#!/usr/bin/env pwsh
# Auto-format code with Ruff

Write-Host "Formatting Python code with Ruff..." -ForegroundColor Cyan

# Change to repo root
Set-Location $PSScriptRoot\..

# Format all Python files
python -m ruff format coaching/ shared/

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code formatted successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Formatting failed" -ForegroundColor Red
    exit 1
}
