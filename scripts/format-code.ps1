#!/usr/bin/env pwsh
# Auto-format code with Ruff

Write-Host "Formatting Python code with Ruff..." -ForegroundColor Cyan

# Change to repo root
Set-Location $PSScriptRoot\..

$RepoRoot = (Get-Location).Path
. (Join-Path $PSScriptRoot "Resolve-CoachingPython.ps1")
$PythonExe = Get-CoachingPythonExecutable -RepoRoot $RepoRoot
if (-not $PythonExe) {
    Write-Host "No venv Python found. Run: cd coaching && uv sync" -ForegroundColor Red
    exit 1
}

# Format all Python files
& $PythonExe -m ruff format coaching/ shared/

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code formatted successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Formatting failed" -ForegroundColor Red
    exit 1
}
