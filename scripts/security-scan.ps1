#!/usr/bin/env pwsh
# Run repository security scans in a repo-scoped virtual environment.

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "PurposePath Security Scan" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "$PSScriptRoot\.."

$venvPath = ".venv-security"
$venvPython = "$venvPath\Scripts\python.exe"
$hasUv = $null -ne (Get-Command uv -ErrorAction SilentlyContinue)
$hasPython = $false

if ($null -ne (Get-Command python -ErrorAction SilentlyContinue)) {
    python --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $hasPython = $true
    }
}

if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creating .venv-security..." -ForegroundColor Yellow
    if ($hasPython) {
        python -m venv $venvPath
    }
    elseif ($hasUv) {
        uv venv $venvPath
    }
    else {
        Write-Host "❌ Neither 'python' nor 'uv' is available to create .venv-security." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "[1/3] Reusing .venv-security..." -ForegroundColor Yellow
}

Write-Host "[2/3] Installing pinned security tooling..." -ForegroundColor Yellow
if ($hasUv) {
    uv pip install --python $venvPython -r security/requirements-security.txt
}
else {
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r security/requirements-security.txt
}

Write-Host "[3/3] Running repository security scans..." -ForegroundColor Yellow
& $venvPython security/run_security_scans.py
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ Security scans completed successfully." -ForegroundColor Green
    Write-Host "   Reports: .artifacts/security/" -ForegroundColor Gray
}
else {
    Write-Host "❌ Security scans found issues or scan errors." -ForegroundColor Red
    Write-Host "   Review: .artifacts/security/summary.json" -ForegroundColor Yellow
}

exit $exitCode
