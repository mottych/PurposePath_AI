#!/usr/bin/env pwsh
# Install Git hooks for PurposePath AI
# This script sets up the pre-commit hook to catch issues before committing

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Installing Git Hooks" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Change to repo root
$RepoRoot = git rev-parse --show-toplevel 2>$null
if (-not $RepoRoot) {
    Write-Host "Error: Not a git repository" -ForegroundColor Red
    Write-Host "Please run this script from within the git repository" -ForegroundColor Yellow
    exit 1
}

Set-Location $RepoRoot

# Check if .git directory exists
if (-not (Test-Path ".git")) {
    Write-Host "Error: .git directory not found" -ForegroundColor Red
    exit 1
}

# Create hooks directory if it doesn't exist
$HooksDir = Join-Path ".git" "hooks"
if (-not (Test-Path $HooksDir)) {
    New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null
}

# Source hook file
$SourceHook = Join-Path "scripts" "pre-commit"
if (-not (Test-Path $SourceHook)) {
    Write-Host "Error: Source pre-commit hook not found: $SourceHook" -ForegroundColor Red
    exit 1
}

# Destination hook file
$DestHook = Join-Path $HooksDir "pre-commit"

# Backup existing hook if present
if (Test-Path $DestHook) {
    $BackupHook = "$DestHook.backup"
    Write-Host "Backing up existing hook to: $BackupHook" -ForegroundColor Yellow
    Copy-Item $DestHook $BackupHook -Force
}

# Copy the hook
Write-Host "Installing pre-commit hook..." -ForegroundColor Yellow
Copy-Item $SourceHook $DestHook -Force

Write-Host "Pre-commit hook installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The hook will now run automatically before each commit." -ForegroundColor Cyan
Write-Host ""
Write-Host "Hook performs:" -ForegroundColor White
Write-Host "  - Ruff linting" -ForegroundColor Gray
Write-Host "  - Code formatting check" -ForegroundColor Gray
Write-Host "  - MyPy type checking (warnings only)" -ForegroundColor Gray
Write-Host "  - Quick validation (tests run in CI/CD)" -ForegroundColor Gray
Write-Host ""
Write-Host "To run full checks manually:" -ForegroundColor White
Write-Host "  .\scripts\pre-commit-check.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "To bypass the hook (not recommended):" -ForegroundColor White
Write-Host "  git commit --no-verify" -ForegroundColor Cyan
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
